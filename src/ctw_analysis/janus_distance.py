"""Continuous, directional race relationships and convex archetypal analysis."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import pdist, squareform, cdist
from sklearn.preprocessing import StandardScaler
from .race_features import BLOCKS


def distances(weighted: pd.DataFrame) -> np.ndarray:
    return squareform(pdist(weighted.to_numpy(float)))


def directional_delta(weighted: pd.DataFrame, a: str, b: str) -> pd.Series:
    """All components; their squared sum is exactly the squared distance."""
    return weighted.loc[b] - weighted.loc[a]


def neighbor_indices(distance: np.ndarray, i: int, count: int) -> np.ndarray:
    # Explicit self exclusion also handles duplicate feature positions.
    order = np.argsort(distance[i], kind="stable")
    return order[order != i][:count]


def components(delta: np.ndarray, raw_delta: np.ndarray, columns,
               limit: int = 4) -> dict:
    total = float(delta @ delta)
    def records(indices):
        return [{"dimension": str(columns[j]),
                 "view": str(columns[j]).split("__", 1)[1],
                 "raw_difference": float(raw_delta[j]),
                 "weighted_delta": float(delta[j]),
                 "squared_distance_contribution": float(delta[j] ** 2),
                 "fraction_of_squared_distance": float(delta[j] ** 2 / total) if total else 0.0}
                for j in indices]
    positive = np.flatnonzero(delta > 0)
    negative = np.flatnonzero(delta < 0)
    return {
        "increases": records(positive[np.argsort(-delta[positive], kind="stable")][:limit]),
        "decreases": records(negative[np.argsort(delta[negative], kind="stable")][:limit]),
    }


def pairwise_report(raw: pd.DataFrame, weighted: pd.DataFrame) -> list[dict]:
    d = distances(weighted)
    ranks = np.zeros(d.shape, int)
    for i in range(len(d)):
        ranks[i, neighbor_indices(d, i, len(d) - 1)] = np.arange(1, len(d))
    result = []
    for i, a in enumerate(weighted.index):
        for j in range(i + 1, len(weighted)):
            b = weighted.index[j]
            delta = directional_delta(weighted, a, b).to_numpy()
            result.append({"from": a, "to": b, "distance": float(d[i, j]),
                           "neighbor_rank_from_to": int(ranks[i, j]),
                           "neighbor_rank_to_from": int(ranks[j, i]),
                           **components(delta, (raw.loc[b] - raw.loc[a]).to_numpy(), weighted.columns)})
    return result


def local_residuals(raw: pd.DataFrame, weighted: pd.DataFrame, count: int = 4) -> dict:
    d = distances(weighted)
    out = {}
    for i, race in enumerate(weighted.index):
        neighbors = neighbor_indices(d, i, count)
        ds = d[i, neighbors]
        zero = ds < 1e-12
        weights = zero.astype(float) if zero.any() else 1.0 / ds
        weights /= weights.sum()
        delta = weighted.iloc[i].to_numpy() - weights @ weighted.iloc[neighbors].to_numpy()
        raw_delta = raw.iloc[i].to_numpy() - weights @ raw.iloc[neighbors].to_numpy()
        out[race] = {
            "neighbors": [{"race": weighted.index[j], "distance": float(d[i, j]),
                           "weight": float(w)} for j, w in zip(neighbors, weights)],
            "weighted_residual": dict(zip(weighted.columns, delta.tolist())),
            **components(delta, raw_delta, weighted.columns),
        }
    return out


def simplex_projection(x: np.ndarray) -> np.ndarray:
    """Euclidean projection of every row onto the probability simplex."""
    u = np.sort(x, axis=1)[:, ::-1]
    cssv = np.cumsum(u, axis=1) - 1.0
    ind = np.arange(1, x.shape[1] + 1)
    rho = (u - cssv / ind > 0).sum(axis=1) - 1
    theta = cssv[np.arange(len(x)), rho] / (rho + 1)
    return np.maximum(x - theta[:, None], 0)


def _simplex_quadratic(initial, gradient, lipschitz, iterations=40):
    """Accelerated projected gradient for a convex quadratic subproblem."""
    current = initial.copy()
    extrapolated = current.copy()
    t = 1.0
    for _ in range(iterations):
        new = simplex_projection(extrapolated - gradient(extrapolated) / max(lipschitz, 1e-12))
        if np.max(np.abs(new - current)) < 1e-9:
            return new
        t_new = (1 + np.sqrt(1 + 4 * t * t)) / 2
        extrapolated = new + (t - 1) / t_new * (new - current)
        current, t = new, t_new
    return current


def fit_archetypes(x: np.ndarray, k: int, seed: int = 811, starts: int = 5,
                   max_iter: int = 150, initial=None) -> dict:
    """Minimize ||X - W H X||²; W and H both have simplex rows.

    H constrains poles to the observed convex hull. W represents each race
    as a mixture. This is nonconvex: retain the best of seeded starts and
    expose optimization diagnostics rather than claiming a global optimum.
    """
    x = np.asarray(x, float)
    n = len(x)
    if not 2 <= k <= n:
        raise ValueError("archetypal resolution must lie between 2 and the number of rows")
    # Scaling improves optimization without altering the optimum.
    scale = max(float(np.linalg.norm(x)), 1e-12)
    y = x / scale
    gram = y @ y.T
    gram_norm = float(np.linalg.norm(gram, 2))
    rng = np.random.default_rng(seed)
    best = None
    diagnostics = []
    for start in range(starts):
        if start == 0 and initial is not None:
            w, h = (v.copy() for v in initial)
        else:
            # Seeded farthest-point initialization, with randomized first pole.
            selected = [int(rng.integers(n))]
            for _ in range(k - 1):
                ds = np.min(cdist(y, y[selected]) ** 2, axis=1)
                ds[selected] = 0
                available = np.setdiff1d(np.arange(n), selected)
                selected.append(int(rng.choice(n, p=ds / ds.sum())) if ds.sum() else int(available[0]))
            h = np.eye(n)[selected]
            w = rng.dirichlet(np.ones(k), size=n)
        previous = float("inf")
        converged = False
        for iteration in range(max_iter):
            old_w, old_h = w.copy(), h.copy()
            poles = h @ y
            pp = poles @ poles.T
            yp = y @ poles.T
            w = _simplex_quadratic(w, lambda a: a @ pp - yp, float(np.linalg.norm(pp, 2)))
            ww = w.T @ w
            wg = w.T @ gram
            h = _simplex_quadratic(h, lambda b: ww @ b @ gram - wg,
                                   float(np.linalg.norm(ww, 2)) * gram_norm)
            objective = float(np.sum((y - w @ h @ y) ** 2))
            # Finite accelerated substeps must not worsen the alternating objective.
            if objective > previous + 1e-12:
                w, h = old_w, old_h
                objective = previous
                break
            if abs(previous - objective) < 1e-8:
                converged = True
                break
            previous = objective
        diagnostics.append({"loss": objective * scale ** 2, "iterations": iteration + 1,
                            "converged": converged})
        if best is None or objective < best["objective"]:
            best = {"memberships": w, "hull_weights": h, "poles": h @ x,
                    "objective": objective, "loss": objective * scale ** 2,
                    "iterations": iteration + 1, "converged": converged}
    best["starts"] = diagnostics
    return best


def membership_entropy(w: np.ndarray) -> np.ndarray:
    return np.clip(-(w * np.log(np.maximum(w, 1e-300))).sum(axis=1) / np.log(w.shape[1]), 0, 1)


def align_archetypes(reference_poles, fitted: dict, original_x) -> tuple:
    """Match labels in the original metric, retaining both weights and poles."""
    poles = fitted["hull_weights"] @ original_x
    rows, cols = linear_sum_assignment(cdist(reference_poles, poles))
    permutation = cols[np.argsort(rows)]
    return fitted["memberships"][:, permutation], poles[permutation]


def total_variation(weights, reference):
    """Fraction of mixture mass reassigned; invariant to unused coordinates."""
    return np.clip(0.5 * np.abs(np.asarray(weights) - reference).sum(axis=-1), 0, 1)


def movement_distribution(values):
    """Rows are runs; columns are races or poles. Preserve the tails."""
    values = np.asarray(values)
    return {"values": values, "mean": float(values.mean()),
            "q95": float(np.quantile(values, .95)), "max": float(values.max()),
            "per_item_mean": values.mean(axis=0),
            "per_item_q95": np.quantile(values, .95, axis=0),
            "per_item_max": values.max(axis=0)}


def membership_uncertainty(samples: np.ndarray, reference: np.ndarray) -> dict:
    return {"mean": samples.mean(axis=0), "std": samples.std(axis=0, ddof=1),
            "q05": np.quantile(samples, 0.05, axis=0),
            "q95": np.quantile(samples, 0.95, axis=0),
            "total_variation": movement_distribution(total_variation(samples, reference))}


def pole_uncertainty(samples: np.ndarray, reference: np.ndarray) -> dict:
    separation = cdist(reference, reference)
    np.fill_diagonal(separation, np.inf)
    spacing = separation.min(axis=1)
    delta = samples - reference
    displacement = np.linalg.norm(delta, axis=-1)
    degenerate = bool((spacing < 1e-10).any())
    return {"nearest_reference_separation": spacing,
            "degenerate_reference": degenerate,
            "absolute_displacement": movement_distribution(displacement),
            "relative_displacement": None if degenerate else movement_distribution(displacement / spacing),
            "profile_delta_mean": delta.mean(axis=0),
            "profile_delta_std": delta.std(axis=0, ddof=1),
            "profile_delta_q05": np.quantile(delta, .05, axis=0),
            "profile_delta_q95": np.quantile(delta, .95, axis=0)}


def feature_perturbations(weighted: pd.DataFrame, runs: int, seed: int) -> dict:
    """Local weighting retains every coordinate and each block's total q."""
    columns = weighted.columns
    q = np.empty(len(columns))
    masks = []
    for members in BLOCKS.values():
        mask = np.array([col.split('__')[0] in members for col in columns])
        masks.append(mask)
        for j in np.flatnonzero(mask):
            q[j] = {'breadth': .5, 'ceiling': .25, 'cost_access': .25}[columns[j].split('__')[1]] / (3 * len(members))
    local_rng = np.random.default_rng(seed)
    stress_rng = np.random.default_rng(seed)
    local, stress = [], []
    for _ in range(runs):
        # Truncate the vanishingly rare negative multiplier to retain support.
        multiplier = np.maximum(local_rng.normal(1, .08, len(columns)), 1e-6)
        for mask in masks:
            multiplier[mask] *= np.sqrt(q[mask].sum() / (q[mask] * multiplier[mask] ** 2).sum())
        local.append(multiplier)
        counts = stress_rng.multinomial(len(columns), np.ones(len(columns)) / len(columns))
        stress.append(np.sqrt(counts) * stress_rng.normal(1, .08, len(columns)))
    return {'local_robustness': np.array(local), 'structural_stress': np.array(stress)}


def _checked_fit(x, k, seed, initial=None):
    result = fit_archetypes(x, k, seed=seed, starts=5, initial=initial)
    attempts = [{'seed': seed, 'max_iter': 150, 'starts': result['starts']}]
    if not result['converged']:
        result = fit_archetypes(x, k, seed=seed + 100000, starts=5, max_iter=600,
                               initial=(result['memberships'], result['hull_weights']))
        attempts.append({'seed': seed + 100000, 'max_iter': 600, 'starts': result['starts']})
    result['attempts'] = attempts
    return result


def _regime_summary(membership, poles, converged, runs):
    tv = membership['total_variation']
    relative = poles['relative_displacement']
    return {'runs': runs, 'converged_runs': converged,
            'membership_tv_mean': tv['mean'], 'membership_tv_q95': tv['q95'],
            'membership_tv_max': tv['max'],
            'max_race_tv_q95': float(max(tv['per_item_q95'])),
            'pole_displacement_mean': poles['absolute_displacement']['mean'],
            'pole_displacement_max': poles['absolute_displacement']['max'],
            'max_pole_relative_q95': None if relative is None else float(max(relative['per_item_q95'])),
            'max_pole_relative_max': None if relative is None else relative['max'],
            'degenerate_reference': poles['degenerate_reference']}


def _fit_resolution(args):
    x, k, seed, perturbations, control_runs = args
    # Reference and controls have identical five-start budgets. Controls are
    # independently initialized, never warm-started at the reference.
    reference = _checked_fit(x, k, seed + k)
    initial_attempts = reference['attempts']
    controls = [_checked_fit(x, k, seed + 10000 * k + b) for b in range(control_runs)]
    reference = min([reference, *controls], key=lambda f: f['loss']).copy()
    order = sorted(range(k), key=lambda j: (int(np.argmax(reference['hull_weights'][j])), tuple(reference['poles'][j])))
    reference['memberships'] = reference['memberships'][:, order]
    reference['hull_weights'] = reference['hull_weights'][order]
    reference['poles'] = reference['poles'][order]
    diagnostics, summaries = {}, {}
    for number, regime in enumerate(('optimization_repeatability', 'local_robustness', 'structural_stress')):
        if regime == 'optimization_repeatability':
            trials = controls
        else:
            trials = [_checked_fit(x * multiplier, k, seed + 1000000 * (number + 1) + 1000 * k + b,
                                   initial=(reference['memberships'], reference['hull_weights']))
                      for b, multiplier in enumerate(perturbations[regime])]
        aligned = [align_archetypes(reference['poles'], trial, x) for trial in trials]
        memberships = membership_uncertainty(np.array([a[0] for a in aligned]), reference['memberships'])
        poles = pole_uncertainty(np.array([a[1] for a in aligned]), reference['poles'])
        diagnostics[regime] = {'membership': memberships, 'poles': poles,
                              'optimizer_losses': [trial['loss'] for trial in trials],
                              'optimizer_converged': [trial['converged'] for trial in trials],
                              'optimizer_attempts': [trial['attempts'] for trial in trials]}
        summaries[regime] = _regime_summary(memberships, poles, sum(t['converged'] for t in trials), len(trials))
    reference['initial_attempts'] = initial_attempts
    return k, reference, diagnostics, summaries


def tolerance_comparison(candidates, membership_tolerance, pole_tolerance):
    """Report every resolution; no knee exclusion and no winning resolution."""
    if (not np.isfinite([membership_tolerance, pole_tolerance]).all()
            or not 0 <= membership_tolerance <= 1 or pole_tolerance < 0):
        raise ValueError('Invalid movement tolerance')
    rows = []
    for candidate in candidates:
        reasons = []
        if not candidate['optimizer_converged']:
            reasons.append('reference_not_converged')
        for regime in ('optimization_repeatability', 'local_robustness'):
            row = candidate['diagnostics'][regime]
            if row['converged_runs'] != row['runs']:
                reasons.append(regime + ':not_all_converged')
            if row['degenerate_reference']:
                reasons.append(regime + ':degenerate_poles')
            if row['max_race_tv_q95'] > membership_tolerance:
                reasons.append(regime + ':membership_movement')
            if row['max_pole_relative_q95'] is None or row['max_pole_relative_q95'] > pole_tolerance:
                reasons.append(regime + ':pole_movement')
        rows.append({'k': candidate['k'], 'within_tolerances': not reasons, 'reasons': reasons})
    return rows


def profile_correspondence(left, right):
    """Nearest profiles in both directions, allowing many-to-one correspondence.

    Memberships mapped by nearest profile are a descriptive comparison, not
    proof of pole ancestry or a causal split.
    """
    d = cdist(left['poles'], right['poles'])
    def direction(distance, source, target):
        nearest = distance.argmin(axis=1)
        mapped = np.zeros_like(target['memberships'])
        for i, j in enumerate(nearest):
            mapped[:, j] += source['memberships'][:, i]
        edges = []
        for i, j in enumerate(nearest):
            ties = np.flatnonzero(np.isclose(distance[i], distance[i, j], rtol=0, atol=1e-12))
            edges.append({'from_pole': int(i + 1), 'to_pole': int(j + 1),
                          'distance': float(distance[i, j]),
                          'equally_near_poles': (ties + 1).tolist()})
        return {'edges': edges, 'mapped_membership_tv_by_race': total_variation(mapped, target['memberships']),
                'tie_policy': 'first pole index; all equally near profiles also listed'}
    return {'profile_distances': d, 'forward': direction(d, left, right),
            'reverse': direction(d.T, right, left)}


def archetypal_resolution(weighted: pd.DataFrame, runs: int = 40, seed: int = 811,
                         progress=None, workers: int = 1, control_runs: int = 8,
                         resolutions=range(3, 9)) -> tuple[dict, dict, dict]:
    if runs < 2 or control_runs < 2 or workers < 1:
        raise ValueError('At least two runs per regime and one worker are required')
    x = weighted.to_numpy()
    total = float(np.sum((x - x.mean(axis=0)) ** 2))
    if total <= 1e-12:
        raise ValueError('Archetypal resolution requires nonzero between-race variation')
    ks = sorted(set(resolutions))
    if len(ks) < 2:
        raise ValueError('Resolution comparison requires at least two basis sizes')
    perturbations = feature_perturbations(weighted, runs, seed)
    tasks = [(x, k, seed, perturbations, control_runs) for k in ks]
    fits, diagnostics, candidates = {}, {}, []
    def collect(results):
        for k, fit, detail, summary in results:
            candidate = {'k': k, 'relative_squared_error': fit['loss'] / total,
                         'optimizer_converged': fit['converged'],
                         'reference_attempts': fit['attempts'],
                         'initial_attempts': fit['initial_attempts'],
                         'diagnostics': summary}
            candidates.append(candidate)
            fits[k], diagnostics[k] = fit, detail
            if progress:
                progress(candidate)
    if workers == 1:
        collect(map(_fit_resolution, tasks))
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers) as pool:
            collect(pool.map(_fit_resolution, tasks))
    errors = np.array([c['relative_squared_error'] for c in candidates])
    gain = (errors[0] - errors) / max(float(errors[0] - errors[-1]), 1e-12)
    knee = ks[int(np.argmax(gain - (np.array(ks) - ks[0]) / (ks[-1] - ks[0])))]
    grid = [{'membership_tolerance': tv, 'pole_tolerance': pole,
             'resolutions': tolerance_comparison(candidates, tv, pole)}
            for tv in (.05, .10, .20, .30) for pole in (.10, .25, .50)]
    correspondences = [{'from_k': ka, 'to_k': kb, **profile_correspondence(fits[ka], fits[kb])}
                       for ka, kb in zip(ks, ks[1:])]
    report = {'candidate_resolutions': candidates, 'error_knee': knee,
              'status': 'multiple_descriptive_representations',
              'seed': seed, 'perturbation_runs': runs, 'control_runs': control_runs,
              'profile_dimensions': weighted.columns.tolist(),
              'tolerance_grid': grid, 'adjacent_correspondences': correspondences,
              'representations': {str(k): {'diagnostics': diagnostics[k]} for k in ks},
              'interpretation': 'No selected resolution. Knee is descriptive only. Tolerances are per race/pole, not simultaneous run guarantees.'}
    return report, fits, diagnostics


def tier_sensitivity(primary: pd.DataFrame, sensitivity: pd.DataFrame) -> dict:
    dp, ds = distances(primary), distances(sensitivity)
    upper = np.triu_indices(len(dp), 1)
    changes = []
    for i, race in enumerate(primary.index):
        p = neighbor_indices(dp, i, 4)
        s = neighbor_indices(ds, i, 4)
        differences = np.abs(ds[i] - dp[i])
        j = int(np.argmax(differences))
        before = directional_delta(primary, race, primary.index[j]).reindex(sensitivity.columns, fill_value=0)
        after = directional_delta(sensitivity, race, primary.index[j])
        delta = after - before
        leading = delta.abs().sort_values(ascending=False, kind="stable").head(6).index
        changes.append({"race": race, "primary_neighbors": primary.index[p].tolist(),
                        "sensitivity_neighbors": primary.index[s].tolist(),
                        "profile_rms_change": float(np.sqrt(np.mean(np.delete((ds[i] - dp[i]) ** 2, i)))),
                        "largest_changed_pair": {"to": primary.index[j], "before": float(dp[i, j]),
                                                 "after": float(ds[i, j]),
                            "leading_directional_changes": [{"dimension": col,
                                "before": float(before[col]), "after": float(after[col]),
                                "change": float(delta[col])} for col in leading]}})
    return {"distance_pearson_correlation": float(np.corrcoef(dp[upper], ds[upper])[0, 1]),
            "meaning": "unit classification sensitivity, not campaign recruitment access",
            "races": sorted(changes, key=lambda r: -r["profile_rms_change"])}


def block_weighted_matrix(
    features: pd.DataFrame,
    include_unit_tier_sensitivity: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scaled = pd.DataFrame(index=features.index)
    weighted = pd.DataFrame(index=features.index)
    for block, members in BLOCKS.items():
        cols = [
            c for c in features.columns
            if c.split("__", 1)[0] in members
            and (
                include_unit_tier_sensitivity
                or not c.endswith("__unit_tier_sensitivity")
            )
        ]
        block_scaled = pd.DataFrame(
            StandardScaler().fit_transform(features[cols]),
            index=features.index,
            columns=cols,
        )
        scaled[cols] = block_scaled
        for feature in members:
            feature_cols = [c for c in cols if c.startswith(feature + "__")]
            # Preserve the original block scale while giving each feature equal
            # total weight. In the optional unit-tier sensitivity, split the
            # original access allocation between cost and unit classification.
            feature_weight = 1 / math.sqrt(3 * len(members))
            has_unit_tier = any(
                c.endswith("__unit_tier_sensitivity") for c in feature_cols
            )
            view_weights = {
                "breadth": 0.50,
                "ceiling": 0.25,
                "cost_access": 0.125 if has_unit_tier else 0.25,
                "unit_tier_sensitivity": 0.125,
            }
            for col in feature_cols:
                view = col.split("__", 1)[1]
                weighted[col] = (
                    block_scaled[col] * feature_weight * math.sqrt(view_weights[view])
                )
    return scaled, weighted


def composite_scores(
    features: pd.DataFrame,
    include_unit_tier_sensitivity: bool = False,
) -> pd.DataFrame:
    out = pd.DataFrame(index=features.index)
    for block, members in BLOCKS.items():
        for feature in members:
            has_unit_tier = (
                include_unit_tier_sensitivity
                and f"{feature}__unit_tier_sensitivity" in features.columns
            )
            vals = 0.50 * features[f"{feature}__breadth"]
            vals += 0.25 * features[f"{feature}__ceiling"]
            if has_unit_tier:
                vals += 0.125 * features[f"{feature}__cost_access"]
                vals += 0.125 * features[
                    f"{feature}__unit_tier_sensitivity"
                ]
            else:
                vals += 0.25 * features[f"{feature}__cost_access"]
            lo, hi = vals.min(), vals.max()
            out[feature] = 100 * (vals - lo) / (hi - lo if hi > lo else 1)
        out[f"block_{block}"] = out[members].mean(axis=1)
    return out
