import unittest
import numpy as np
import pandas as pd

from ctw_analysis.janus_distance import (
    align_archetypes, block_weighted_matrix, directional_delta, distances,
    fit_archetypes, local_residuals, membership_entropy, membership_uncertainty,
    pairwise_report, simplex_projection, total_variation, pole_uncertainty,
    feature_perturbations, tolerance_comparison, archetypal_resolution, profile_correspondence, _checked_fit,
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
        aligned_w, aligned_poles = align_archetypes(first['poles'], trial, x)
        np.testing.assert_allclose(aligned_w, first['memberships'])
        np.testing.assert_allclose(aligned_poles, first['poles'])

    def test_stable_hybrid_has_high_entropy_and_zero_uncertainty(self):
        w = np.array([[.5, .5]])
        stable = np.repeat(w[None, :, :], 10, axis=0)
        uncertain = np.array([[[1., 0.]], [[0., 1.]]] * 5)
        self.assertAlmostEqual(membership_entropy(w)[0], 1)
        self.assertEqual(membership_uncertainty(stable, w)['total_variation']['mean'], 0)
        self.assertEqual(membership_uncertainty(uncertain, w)['total_variation']['mean'], .5)
        np.testing.assert_allclose(membership_uncertainty(stable, w)['mean'],
                                   membership_uncertainty(uncertain, w)['mean'])

    def test_projection_and_identical_rows_do_not_create_invalid_weights(self):
        projected = simplex_projection(np.array([[-1., 2., 0.], [0., 0., 0.]]))
        np.testing.assert_allclose(projected.sum(axis=1), 1)
        fit = fit_archetypes(np.zeros((5, 3)), 3, starts=2)
        self.assertEqual(fit['loss'], 0)
        self.assertTrue(np.isfinite(fit['memberships']).all())


class StabilityRevisionTests(unittest.TestCase):
    @staticmethod
    def feature_frame(n=8):
        columns = [f'{feature}__{view}' for members in BLOCKS.values() for feature in members
                   for view in ('breadth', 'ceiling', 'cost_access')]
        frame = pd.DataFrame(np.random.default_rng(19).normal(size=(n, 54)),
                             columns=columns, index=[f'r{i}' for i in range(n)])
        return block_weighted_matrix(frame)[1]

    @staticmethod
    def candidate(k=3, tv=.2, pole=.25):
        row = {'runs': 2, 'converged_runs': 2, 'degenerate_reference': False,
               'max_race_tv_q95': tv, 'max_pole_relative_q95': pole}
        return {'k': k, 'optimizer_converged': True,
                'diagnostics': {'optimization_repeatability': dict(row),
                                'local_robustness': dict(row),
                                'structural_stress': {**row, 'max_race_tv_q95': 1., 'max_pole_relative_q95': 100.}}}

    def test_twenty_point_transfer_is_invariant_to_unused_poles(self):
        for k in (3, 8):
            w = np.pad([[.6, .3, .1]], ((0, 0), (0, k-3)))
            v = np.pad([[.4, .5, .1]], ((0, 0), (0, k-3)))
            self.assertAlmostEqual(total_variation(v, w)[0], .20)
        self.assertEqual([r['k'] for r in tolerance_comparison([self.candidate(3), self.candidate(8)], .20, .25) if r['within_tolerances']], [3, 8])

    def test_fixed_memberships_do_not_hide_translated_poles(self):
        poles = np.array([[0., 0.], [4., 0.]])
        shifted = np.repeat((poles + [1., 0.])[None], 2, axis=0)
        movement = pole_uncertainty(shifted, poles)
        np.testing.assert_allclose(movement['absolute_displacement']['values'], 1.)
        np.testing.assert_allclose(movement['relative_displacement']['values'], .25)
        np.testing.assert_allclose(movement['profile_delta_mean'], [[1., 0.], [1., 0.]])
        w = np.array([[.5, .5]])
        self.assertEqual(membership_uncertainty(np.repeat(w[None], 2, axis=0), w)['total_variation']['mean'], 0)

    def test_degenerate_poles_are_explicitly_unidentifiable(self):
        poles = np.zeros((2, 3))
        movement = pole_uncertainty(np.zeros((2, 2, 3)), poles)
        self.assertTrue(movement['degenerate_reference'])
        self.assertIsNone(movement['relative_displacement'])
        candidate = self.candidate()
        candidate['diagnostics']['local_robustness']['degenerate_reference'] = True
        candidate['diagnostics']['local_robustness']['max_pole_relative_q95'] = None
        self.assertFalse(tolerance_comparison([candidate], 1., 1.)[0]['within_tolerances'])

    def test_local_perturbations_keep_support_and_each_block_total(self):
        frame = self.feature_frame()
        draws = feature_perturbations(frame, 10, 811)
        self.assertTrue((draws['local_robustness'] > 0).all())
        self.assertTrue((draws['structural_stress'] == 0).any())
        for members in BLOCKS.values():
            mask = np.array([c.split('__')[0] in members for c in frame.columns])
            q = np.array([{'breadth':.5,'ceiling':.25,'cost_access':.25}[c.split('__')[1]]/(3*len(members)) for c in frame.columns[mask]])
            np.testing.assert_allclose((draws['local_robustness'][:, mask] ** 2 * q).sum(axis=1), 1/3, atol=1e-12)
        again = feature_perturbations(frame, 10, 811)
        for key in draws:
            np.testing.assert_array_equal(draws[key], again[key])

    def test_joint_selection_ignores_stress_but_checks_both_local_movements(self):
        self.assertTrue(tolerance_comparison([self.candidate()], .20, .25)[0]['within_tolerances'])
        self.assertFalse(tolerance_comparison([self.candidate(tv=.21)], .20, .25)[0]['within_tolerances'])
        self.assertFalse(tolerance_comparison([self.candidate(pole=.26)], .20, .25)[0]['within_tolerances'])
        candidate = self.candidate()
        candidate['diagnostics']['optimization_repeatability']['max_race_tv_q95'] = .21
        self.assertFalse(tolerance_comparison([candidate], .20, .25)[0]['within_tolerances'])
        candidate = self.candidate()
        candidate['diagnostics']['local_robustness']['converged_runs'] = 1
        self.assertFalse(tolerance_comparison([candidate], .20, .25)[0]['within_tolerances'])

    def test_orchestration_is_seeded_and_worker_count_does_not_change_results(self):
        from ctw_analysis.build_race_strategy_space import json_ready
        import json
        frame = self.feature_frame()
        a = archetypal_resolution(frame, runs=2, control_runs=2, resolutions=(3, 4), workers=1)
        b = archetypal_resolution(frame, runs=2, control_runs=2, resolutions=(3, 4), workers=2)
        self.assertEqual(json.dumps(json_ready(a[0]), sort_keys=True), json.dumps(json_ready(b[0]), sort_keys=True))
        self.assertNotIn('selected_resolution', a[0])
        self.assertEqual(a[0]['status'], 'multiple_descriptive_representations')
        self.assertEqual(set(a[0]['representations']), {'3', '4'})
        self.assertEqual(len(a[0]['adjacent_correspondences']), 1)
        self.assertEqual(len(a[0]['tolerance_grid']), 12)
        for k in (3, 4):
            self.assertEqual(set(a[2][k]), {'optimization_repeatability','local_robustness','structural_stress'})
            self.assertEqual(len(a[2][k]['local_robustness']['optimizer_attempts']), 2)


class RepresentationTests(unittest.TestCase):
    def test_profile_correspondence_allows_split_and_records_ties(self):
        left = {'poles': np.array([[0., 0.], [4., 0.]]), 'memberships': np.array([[.2, .8]])}
        right = {'poles': np.array([[0., 0.], [3.9, 0.], [4.1, 0.]]), 'memberships': np.array([[.2, .3, .5]])}
        links = profile_correspondence(left, right)
        self.assertEqual([e['to_pole'] for e in links['reverse']['edges']], [1, 2, 2])
        self.assertEqual(links['forward']['edges'][1]['equally_near_poles'], [2, 3])
        np.testing.assert_allclose(links['reverse']['mapped_membership_tv_by_race'], 0.)
        perm = [2, 0, 1]
        permuted = {key: value[perm] if key == 'poles' else value[:, perm] for key,value in right.items()}
        other = profile_correspondence(left, permuted)
        np.testing.assert_allclose(other['reverse']['mapped_membership_tv_by_race'], 0.)

    def test_retry_keeps_both_attempt_histories(self):
        from unittest.mock import patch
        first = {'converged': False, 'starts': [{'loss': 2.}], 'memberships': np.eye(2), 'hull_weights': np.eye(2)}
        second = {**first, 'converged': True, 'starts': [{'loss': 1.}]}
        with patch('ctw_analysis.janus_distance.fit_archetypes', side_effect=[first, second]):
            result = _checked_fit(np.eye(2), 2, 42)
        self.assertEqual([a['starts'][0]['loss'] for a in result['attempts']], [2., 1.])
        self.assertEqual([a['seed'] for a in result['attempts']], [42, 100042])


if __name__ == '__main__':
    unittest.main()
