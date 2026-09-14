"""Traceable unit evidence and exact one/two-unit capability access frontiers.

Scores describe access to capabilities, never additive army power. Frontiers are
complete for this bounded model; recruitment legality and synergy are not modeled.
"""
from itertools import combinations
import math

import numpy as np
import pandas as pd

from .race_features import UNIT_FEATURES, role_name

LEVELS = (.50, .75, .90)
RAW_FIELDS = ('speed', 'armour', 'range', 'entity_count', 'total_hp', 'mass',
              'melee_attack', 'melee_defence', 'leadership', 'charge_bonus',
              'weapon_base_damage', 'weapon_ap_damage', 'ammunition', 'reload_time')


def pareto_indices(cost, a, b):
    """Exact cost-min / a-max / b-max skyline; retain every exact objective tie.

    A Fenwick prefix maximum over reversed a ranks avoids quadratic dominance
    comparisons. Equal triples are queried together before inserting their b.
    """
    cost, a, b = (np.asarray(v, float) for v in (cost, a, b))
    if not (len(cost) == len(a) == len(b)) or not np.isfinite([cost, a, b]).all():
        raise ValueError('Finite, equally sized objectives required')
    order = np.lexsort((-b, -a, cost))
    unique_a = np.unique(a)[::-1]
    ranks = {value: i + 1 for i, value in enumerate(unique_a)}
    tree = np.full(len(unique_a) + 1, -np.inf)
    kept, pos = [], 0
    while pos < len(order):
        i = order[pos]
        end = pos + 1
        while end < len(order) and (cost[order[end]], a[order[end]], b[order[end]]) == (cost[i], a[i], b[i]):
            end += 1
        rank = ranks[a[i]]
        best, j = -np.inf, rank
        while j:
            best = max(best, tree[j]); j -= j & -j
        if best < b[i]:
            kept.extend(order[pos:end].tolist())
        j = rank
        while j < len(tree):
            tree[j] = max(tree[j], b[i]); j += j & -j
        pos = end
    return np.array(kept, int)


def package_candidates(cost, a, b, mode):
    """Rows: provider/unit index A, provider/unit index B, cost, achieved A, B."""
    cost, a, b = (np.asarray(v, float) for v in (cost, a, b))
    n = len(cost)
    if not (len(a) == len(b) == n) or not np.isfinite(cost).all() or (cost <= 0).any():
        raise ValueError('Positive finite costs and aligned scores required')
    if mode == 'same_unit':
        i = j = np.arange(n)
        ca, aa, bb = cost, a, b
    elif mode == 'distinct_providers':
        i, j = np.where(~np.eye(n, dtype=bool))
        ca, aa, bb = cost[i] + cost[j], a[i], b[j]
    elif mode == 'all_units_a':
        i, j = np.triu_indices(n, 1)
        ca, aa, bb = cost[i] + cost[j], np.minimum(a[i], a[j]), np.maximum(b[i], b[j])
    else:
        raise ValueError('Unknown package semantics')
    valid = np.isfinite(aa) & np.isfinite(bb) & (aa > 0) & (bb > 0)
    return np.column_stack((i[valid], j[valid], ca[valid], aa[valid], bb[valid]))


def package_frontier(cost, a, b, mode):
    rows = package_candidates(cost, a, b, mode)
    if not len(rows):
        return rows
    return rows[pareto_indices(rows[:, 2], rows[:, 3], rows[:, 4])]


def minimum_packages(rows, threshold_a, threshold_b):
    if threshold_a is None or threshold_b is None:
        return {'minimum_cost': None, 'package_rows': [], 'reason': 'no_positive_global_support'}
    ids = np.flatnonzero((rows[:, 3] >= threshold_a) & (rows[:, 4] >= threshold_b))
    if not len(ids):
        return {'minimum_cost': None, 'package_rows': [], 'reason': 'unattainable_in_roster'}
    minimum = float(rows[ids, 2].min())
    return {'minimum_cost': minimum, 'package_rows': ids[rows[ids, 2] == minimum].tolist(), 'reason': None}


def _nullable(value):
    return None if pd.isna(value) else value.item() if isinstance(value, np.generic) else value


def unit_evidence(scores, source_units):
    """Stable ids, original measurements (including missingness), and witnesses."""
    ordered = scores.sort_values(['race_slug', 'unit_key'], kind='stable').copy().reset_index(drop=True)
    if ordered.duplicated(['race_slug', 'unit_key']).any():
        raise ValueError('Duplicate race/unit identities')
    ordered['evidence_id'] = np.arange(len(ordered))
    original = source_units.set_index(['race_slug', 'unit_key'], verify_integrity=True)
    catalog = []
    for _, row in ordered.iterrows():
        raw = original.loc[(row['race_slug'], row['unit_key'])]
        catalog.append({'id': int(row['evidence_id']), 'race': row['race_slug'],
                        'unit_key': row['unit_key'], 'multiplayer_cost': float(row['multiplayer_cost']),
                        'role': role_name(row),
                        'capabilities': {f: float(row[f]) for f in UNIT_FEATURES},
                        'measurements': {f: _nullable(raw.get(f, np.nan)) for f in RAW_FIELDS},
                        'attributes': sorted(row.get('attrs', set())),
                        'abilities': sorted(row.get('abilities', set())),
                        'contact_effects': sorted(row.get('contacts', set()))})
    ordered['role'] = ordered.apply(role_name, axis=1)
    ordered['cost_band'] = pd.cut(ordered['multiplayer_cost'], [-np.inf, 600, 1000, 1500, np.inf],
                                 labels=['cheap', 'mid', 'high', 'elite']).astype(str)
    caps = np.quantile(ordered['multiplayer_cost'], np.linspace(.10, .95, 12))
    evidence = {}
    for race, group in ordered.groupby('race_slug', sort=True):
        features = {}
        for f in UNIT_FEATURES:
            pos = ordered.loc[ordered[f] > 0, f]
            threshold = float(pos.quantile(.65)) if len(pos) else None
            high = group[(group[f] > 0) & (group[f] >= (threshold or 0))]
            top_n = max(1, min(3, math.ceil(len(group) * .08)))
            # Match aggregate_unit_views' nlargest tie order (original input index).
            original_group = scores[scores.race_slug == race]
            top_keys = original_group.nlargest(top_n, f)['unit_key'].tolist()
            by_key = group.set_index('unit_key')['evidence_id'].to_dict()
            frontier = []
            for cap in caps:
                eligible = group[group.multiplayer_cost <= cap]
                best = float(eligible[f].max()) if len(eligible) else 0.
                frontier.append({'cost_cap': float(cap), 'score': best,
                                 'units': eligible.loc[eligible[f] == best, 'evidence_id'].tolist() if best > 0 else []})
            features[f] = {'positive_units': group.loc[group[f] > 0, 'evidence_id'].tolist(),
                           'high_threshold': threshold, 'high_units': high.evidence_id.tolist(),
                           'high_cells': sorted(set(zip(high.role, high.cost_band))),
                           'ceiling_units': [int(by_key[k]) for k in top_keys],
                           'ceiling_weight_per_unit': 1 / top_n, 'cost_frontier': frontier}
        evidence[race] = features
    report = {'units': catalog, 'race_feature_evidence': evidence,
              'proxy_scope': UNIT_FEATURES,
              'limitations': 'Scores retain the baseline rank/flag formulas and zero imputation; original measurements retain missingness. Role coverage, elite orientation and command/magic are roster metadata, not unit package scores.'}
    return ordered, report


def capability_packages(ordered, evidence, levels=LEVELS):
    catalog = evidence['units']
    measures = {f: ordered[f].to_numpy(float) for f in UNIT_FEATURES}
    for raw in ('speed', 'armour', 'range'):
        measures['raw_' + raw] = np.array([u['measurements'][raw] if u['measurements'][raw] is not None else np.nan for u in catalog], float)
    # A range without a missile weapon is not positive ranged access.
    if 'has_missile_weapon' in ordered:
        measures['raw_range'] = np.where(ordered.has_missile_weapon.fillna(False).astype(bool), measures['raw_range'], 0.)
    definitions = {f: {'kind': 'baseline_capability_proxy', 'units': 'score_0_to_1'} for f in UNIT_FEATURES}
    definitions.update({f'raw_{f}': {'kind': 'source_measurement', 'units': f'game_{f}_units'} for f in ('speed','armour','range')})
    thresholds = {}
    for f, values in measures.items():
        positive = values[np.isfinite(values) & (values > 0)]
        thresholds[f] = [float(np.quantile(positive, level)) if len(positive) else None for level in levels]
    specs = [(a, b, 'distinct_providers') for a, b in combinations(UNIT_FEATURES, 2)]
    specs += [('raw_speed','raw_range','distinct_providers'), ('raw_armour','raw_range','distinct_providers'),
              ('raw_speed','raw_armour','distinct_providers'), ('raw_speed','raw_range','all_units_a')]
    records = []
    for race, group in ordered.groupby('race_slug', sort=True):
        ids = group.evidence_id.to_numpy(int)
        cost = group.multiplayer_cost.to_numpy(float)
        for a, b, mode in specs:
            packages, pareto_rows, local_rows = {}, {}, {}
            for label, semantics in (('same_unit','same_unit'), ('two_units',mode)):
                all_rows = package_candidates(cost, measures[a][ids], measures[b][ids], semantics)
                efficient = pareto_indices(all_rows[:, 2], all_rows[:, 3], all_rows[:, 4])
                keep = set(efficient.tolist())
                for ta in thresholds[a]:
                    for tb in thresholds[b]:
                        keep.update(minimum_packages(all_rows, ta, tb)['package_rows'])
                indices = sorted(keep)
                rows = all_rows[indices]
                local_rows[label] = rows
                lookup = {old: new for new, old in enumerate(indices)}
                pareto_rows[label] = [lookup[int(i)] for i in efficient]
                packages[label] = [[int(ids[int(r[0])]), int(ids[int(r[1])]), *r[2:].tolist()] for r in rows]
            queries = []
            for ia, ta in enumerate(thresholds[a]):
                for ib, tb in enumerate(thresholds[b]):
                    solutions = {label: minimum_packages(rows, ta, tb) for label, rows in local_rows.items()}
                    costs = [s['minimum_cost'] for s in solutions.values() if s['minimum_cost'] is not None]
                    best = min(costs) if costs else None
                    queries.append({'level_a': ia, 'level_b': ib, **solutions,
                                    'minimum_cost_at_most_two': best,
                                    'cheapest_modes': [label for label,s in solutions.items() if best is not None and s['minimum_cost'] == best]})
            records.append({'race': race, 'a': a, 'b': b, 'two_unit_semantics': mode,
                            'packages': packages, 'pareto_rows': pareto_rows, 'requirements': queries})
    return {'levels': list(levels), 'measures': definitions, 'thresholds': thresholds,
            'package_columns': ['unit_a_id','unit_b_id','multiplayer_cost','achieved_a','achieved_b'],
            'records': records,
            'model': {'unit_limit': 2, 'repeats': False,
                      'same_unit': 'one unit supplies both requirements; its cost is counted once',
                      'distinct_providers': 'two distinct units, first witnesses A, second witnesses B; unused capabilities are not summed',
                      'all_units_a': 'both units meet A; at least one meets B; achieved A=min, B=max',
                      'ties': 'all minimum-cost witnesses on the requirement grid and all exact-objective frontier ties retained',
                      'budget': 'minimum_cost_at_most_two <= budget iff a package is attainable in this model',
                      'scope': 'roster-listed access only; not faction/campaign legality, an army recommendation, synergy, additive power or a battle outcome'}}
