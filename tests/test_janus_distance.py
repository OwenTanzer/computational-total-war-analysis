import unittest
import numpy as np
import pandas as pd

from ctw_analysis.janus_distance import (
    align_memberships, block_weighted_matrix, directional_delta, distances,
    fit_archetypes, local_residuals, membership_entropy, membership_uncertainty,
    pairwise_report, simplex_projection,
)
from ctw_analysis.race_features import BLOCKS


class DistanceTests(unittest.TestCase):
    def setUp(self):
        self.raw = pd.DataFrame([[0., 1.], [2., 0.], [2., 0.], [4., 3.]],
                                index=list('abcd'), columns=['movement__breadth', 'shock__ceiling'])

    def test_symmetric_distance_and_directional_identity_for_every_pair(self):
        d = distances(self.raw)
        np.testing.assert_array_equal(d, d.T)
        np.testing.assert_array_equal(np.diag(d), 0)
        for i, a in enumerate(self.raw.index):
            for j, b in enumerate(self.raw.index):
                delta = directional_delta(self.raw, a, b)
                np.testing.assert_array_equal(delta, -directional_delta(self.raw, b, a))
                self.assertAlmostEqual(float(delta @ delta), d[i, j] ** 2, places=12)

    def test_pairs_keep_both_ranks_and_signed_raw_differences(self):
        reports = pairwise_report(self.raw, self.raw)
        self.assertEqual(len(reports), 6)
        ab = reports[0]
        self.assertEqual((ab['from'], ab['to']), ('a', 'b'))
        self.assertEqual(ab['increases'][0]['raw_difference'], 2)
        self.assertEqual(ab['decreases'][0]['raw_difference'], -1)
        bc = next(r for r in reports if r['from'] == 'b' and r['to'] == 'c')
        self.assertEqual(bc['distance'], 0)
        self.assertEqual(bc['neighbor_rank_from_to'], 1)

    def test_local_residual_excludes_self_and_handles_duplicate_positions(self):
        local = local_residuals(self.raw, self.raw, count=2)
        self.assertEqual(local['b']['neighbors'][0]['race'], 'c')
        self.assertEqual(local['b']['neighbors'][0]['weight'], 1)
        self.assertTrue(all(v == 0 for v in local['b']['weighted_residual'].values()))
        self.assertGreater(local['d']['weighted_residual']['shock__ceiling'], 0)
        self.assertNotIn('d', [r['race'] for r in local['d']['neighbors']])

    def test_weights_keep_blocks_equal_and_tier_cannot_change_primary(self):
        rng = np.random.default_rng(42)
        data = {}
        for members in BLOCKS.values():
            for feature in members:
                for view in ('breadth', 'ceiling', 'cost_access'):
                    data[f'{feature}__{view}'] = rng.normal(size=10)
                if feature not in ('role_coverage', 'elite_orientation', 'command_magic'):
                    data[f'{feature}__unit_tier_sensitivity'] = rng.normal(size=10)
        raw = pd.DataFrame(data)
        _, base = block_weighted_matrix(raw)
        for members in BLOCKS.values():
            cols = [c for c in base if c.split('__')[0] in members]
            self.assertAlmostEqual(float(np.var(base[cols].to_numpy(), axis=0).sum()), 1/3)
        raw.loc[:, raw.columns.str.endswith('__unit_tier_sensitivity')] = 1e9
        _, again = block_weighted_matrix(raw)
        pd.testing.assert_frame_equal(base, again)


class ArchetypeTests(unittest.TestCase):
    def test_convex_hull_triangle_reconstructs_vertices_and_mixtures(self):
        x = np.array([[0., 0.], [1., 0.], [0., 1.], [.2, .3], [.5, .1]])
        fit = fit_archetypes(x, 3, seed=123, starts=4)
        for weights in (fit['memberships'], fit['hull_weights']):
            self.assertGreaterEqual(float(weights.min()), 0)
            np.testing.assert_allclose(weights.sum(axis=1), 1, atol=1e-12)
        np.testing.assert_allclose(fit['poles'], fit['hull_weights'] @ x)
        np.testing.assert_allclose(fit['memberships'] @ fit['poles'], x, atol=1e-4)
        self.assertLess(fit['loss'], 1e-8)

    def test_seeded_output_and_label_alignment(self):
        x = np.random.default_rng(7).normal(size=(7, 4))
        first = fit_archetypes(x, 3, seed=5, starts=2)
        second = fit_archetypes(x, 3, seed=5, starts=2)
        np.testing.assert_array_equal(first['memberships'], second['memberships'])
        permutation = [2, 0, 1]
        trial = {'memberships': first['memberships'][:, permutation],
                 'hull_weights': first['hull_weights'][permutation]}
        np.testing.assert_allclose(align_memberships(first['poles'], trial, x), first['memberships'])

    def test_stable_hybrid_has_high_entropy_and_zero_uncertainty(self):
        w = np.array([[.5, .5]])
        stable = np.repeat(w[None, :, :], 10, axis=0)
        uncertain = np.array([[[1., 0.]], [[0., 1.]]] * 5)
        self.assertAlmostEqual(membership_entropy(w)[0], 1)
        self.assertEqual(membership_uncertainty(stable, w)['rmse'], 0)
        self.assertEqual(membership_uncertainty(uncertain, w)['rmse'], .5)
        np.testing.assert_allclose(membership_uncertainty(stable, w)['mean'],
                                   membership_uncertainty(uncertain, w)['mean'])

    def test_projection_and_identical_rows_do_not_create_invalid_weights(self):
        projected = simplex_projection(np.array([[-1., 2., 0.], [0., 0., 0.]]))
        np.testing.assert_allclose(projected.sum(axis=1), 1)
        fit = fit_archetypes(np.zeros((5, 3)), 3, starts=2)
        self.assertEqual(fit['loss'], 0)
        self.assertTrue(np.isfinite(fit['memberships']).all())


if __name__ == '__main__':
    unittest.main()
