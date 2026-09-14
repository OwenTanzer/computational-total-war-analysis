import unittest
import numpy as np
import pandas as pd
from ctw_analysis.capability_packages import (pareto_indices, package_candidates, package_frontier,
                                             minimum_packages, unit_evidence, capability_packages)
from ctw_analysis.assumption_sensitivity import block_emphasis, requirement_comparisons
from ctw_analysis.race_features import UNIT_FEATURES, BLOCKS
from ctw_analysis.janus_distance import block_weighted_matrix


class PackageTests(unittest.TestCase):
    def test_skyline_matches_exhaustive_dominance_and_keeps_ties(self):
        rng = np.random.default_rng(42)
        points = rng.integers(1, 8, size=(100, 3)).astype(float)
        points = np.vstack([points, points[0]])
        keep = []
        for i, (c,a,b) in enumerate(points):
            weak = (points[:,0] <= c) & (points[:,1] >= a) & (points[:,2] >= b)
            strict = (points[:,0] < c) | (points[:,1] > a) | (points[:,2] > b)
            if not np.any(weak & strict): keep.append(i)
        self.assertEqual(set(pareto_indices(*points.T)), set(keep))
        self.assertEqual(pareto_indices([10,10], [.5,.5], [.6,.6]).tolist(), [0,1])

    def test_versatile_unit_vs_specialists_and_threshold_reversal(self):
        cost, a, b = [100, 40, 40], [.8, 1., 0.], [.8, 0., 1.]
        one = package_frontier(cost, a, b, 'same_unit')
        two = package_frontier(cost, a, b, 'distinct_providers')
        self.assertEqual(minimum_packages(one, .7, .7)['minimum_cost'], 100)
        self.assertEqual(minimum_packages(two, .7, .7)['minimum_cost'], 80)
        self.assertIsNone(minimum_packages(one, .9, .9)['minimum_cost'])
        self.assertEqual(minimum_packages(two, .9, .9)['minimum_cost'], 80)
        # Another roster is cheaper at low requirements but more expensive high.
        other = package_frontier([60, 120], [.7,1.], [.7,1.], 'same_unit')
        self.assertLess(minimum_packages(other,.7,.7)['minimum_cost'],80)
        self.assertGreater(minimum_packages(other,.9,.9)['minimum_cost'],80)

    def test_all_unit_speed_is_not_one_fast_provider(self):
        c, speed, ranged = [20,30], [100,20], [0,200]
        some = package_candidates(c,speed,ranged,'distinct_providers')
        every = package_candidates(c,speed,ranged,'all_units_a')
        self.assertEqual(minimum_packages(some,80,150)['minimum_cost'],50)
        self.assertIsNone(minimum_packages(every,80,150)['minimum_cost'])
        self.assertEqual(minimum_packages(every,10,150)['minimum_cost'],50)

    def test_distinct_providers_and_missingness_are_enforced(self):
        self.assertEqual(len(package_candidates([20],[1],[1],'distinct_providers')),0)
        one = package_candidates([20,30],[np.nan,1],[1,0],'same_unit')
        self.assertEqual(len(one),0)
        self.assertEqual(minimum_packages(one,None,1)['reason'],'no_positive_global_support')
        with self.assertRaises(ValueError): package_candidates([0],[1],[1],'same_unit')

    def test_grid_retains_cheapest_ties_even_when_one_is_dominated(self):
        rows=[]
        for i, score in enumerate((.5,.8,1.)):
            rows.append(dict(race_slug='r',unit_key=f'u{i}',multiplayer_cost=10 if i<2 else 100,
                             category='infantry',unit_class='x',caste='melee_infantry',
                             speed=10,armour=20,range=0,has_missile_weapon=False,
                             **{f:score for f in UNIT_FEATURES}))
        source=pd.DataFrame(rows)
        ordered,evidence=unit_evidence(source,source)
        report=capability_packages(ordered,evidence,levels=(0.,.5,1.))
        record=report['records'][0]
        query=record['requirements'][0]['same_unit']
        self.assertEqual(query['minimum_cost'],10)
        self.assertEqual(len(query['package_rows']),2)
        witnesses=record['packages']['same_unit']
        self.assertEqual({int(witnesses[j][0]) for j in query['package_rows']},{0,1})
        self.assertEqual(len(report['records']),109)
        self.assertEqual(evidence['race_feature_evidence']['r']['movement']['ceiling_units'],[2])

    def test_requirement_comparison_identifies_reversal(self):
        records=[]
        for race,costs in [('a',[10,30]),('b',[20,20])]:
            records.append({'race':race,'a':'x','b':'y','two_unit_semantics':'distinct_providers',
                            'requirements':[{'minimum_cost_at_most_two':c,'level_a':i,'level_b':0} for i,c in enumerate(costs)]})
        result=requirement_comparisons({'records':records})[0]
        self.assertEqual(result['finite_cost_order_reversals'],[{'race_a':'a','race_b':'b','a_cheaper_requirement':0,'b_cheaper_requirement':1}])

    def test_block_emphasis_preserves_total_and_exposes_all_distances(self):
        rng=np.random.default_rng(7)
        cols=[f'{f}__{v}' for fs in BLOCKS.values() for f in fs for v in ('breadth','ceiling','cost_access')]
        _,x=block_weighted_matrix(pd.DataFrame(rng.normal(size=(6,54)),columns=cols,index=list('abcdef')))
        result=block_emphasis(x)
        self.assertEqual(len(result['scenarios']),5)
        for s in result['scenarios']:
            self.assertAlmostEqual(sum(s['squared_block_totals'].values()),4/3)
            np.testing.assert_allclose(s['distances'],s['distances'].T)
            np.testing.assert_array_equal(np.diag(s['distances']),0)

if __name__=='__main__': unittest.main()
