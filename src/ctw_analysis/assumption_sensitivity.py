"""Consequences of block emphasis and capability requirements, without winners."""
from itertools import combinations
import numpy as np
from .race_features import BLOCKS
from .janus_distance import distances, neighbor_indices


def block_emphasis(weighted):
    base = distances(weighted)
    scenarios = []
    for focus in [None, *BLOCKS]:
        squared = {b: (1. if focus is None else 1.6 if b == focus else .8) for b in BLOCKS}
        multipliers = np.array([np.sqrt(next(squared[b] for b, fs in BLOCKS.items() if c.split('__')[0] in fs)) for c in weighted.columns])
        d = distances(weighted * multipliers)
        ranks = np.zeros(d.shape, int)
        neighbors = []
        for i, race in enumerate(weighted.index):
            order = neighbor_indices(d, i, len(d) - 1)
            ranks[i, order] = np.arange(1, len(d))
            neighbors.append({'race': race, 'nearest': weighted.index[order[0]],
                              'retained_top4': len(set(order[:4]) & set(neighbor_indices(base, i, 4)))})
        scenarios.append({'name': 'equal_blocks' if focus is None else focus + '_emphasis',
                          'squared_block_totals': {b: v / 3 for b,v in squared.items()},
                          'distances': d, 'neighbor_ranks': ranks, 'neighborhoods': neighbors})
    return {'races': weighted.index.tolist(), 'scenarios': scenarios,
            'scope': 'fixed standardized measurements; double one block relative to others and preserve total squared weight 4/3; no archetypes refitted',
            'stable_nearest_neighbors': [r for i,r in enumerate(weighted.index)
                if len({s['neighborhoods'][i]['nearest'] for s in scenarios}) == 1]}


def requirement_comparisons(packages):
    groups = {}
    for r in packages['records']:
        groups.setdefault((r['a'], r['b'], r['two_unit_semantics']), []).append(r)
    reports = []
    for (a,b,mode), rows in groups.items():
        races = [r['race'] for r in rows]
        costs = np.array([[q['minimum_cost_at_most_two'] if q['minimum_cost_at_most_two'] is not None else np.inf
                           for q in r['requirements']] for r in rows])
        reversals = []
        for i,j in combinations(range(len(races)),2):
            both = np.isfinite(costs[i]) & np.isfinite(costs[j])
            win = np.flatnonzero(both & (costs[i] < costs[j]))
            lose = np.flatnonzero(both & (costs[i] > costs[j]))
            if len(win) and len(lose):
                reversals.append({'race_a': races[i], 'race_b': races[j],
                                  'a_cheaper_requirement': int(win[0]), 'b_cheaper_requirement': int(lose[0])})
        reports.append({'a': a, 'b': b, 'two_unit_semantics': mode, 'races': races,
                        'requirement_levels': [[q['level_a'],q['level_b']] for q in rows[0]['requirements']],
                        'minimum_costs_by_race': [[None if not np.isfinite(v) else float(v) for v in row] for row in costs],
                        'finite_cost_order_reversals': reversals})
    return reports
