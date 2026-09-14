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
    return -(w * np.log(np.maximum(w, 1e-300))).sum(axis=1) / np.log(w.shape[1])


def align_memberships(reference_poles, fitted: dict, original_x) -> np.ndarray:
    # Compare hull positions in the same original space even when dimensions
    # are absent from a feature bootstrap; Hungarian matching fixes label swaps.
    rows, cols = linear_sum_assignment(cdist(reference_poles, fitted["hull_weights"] @ original_x))
    permutation = cols[np.argsort(rows)]
    return fitted["memberships"][:, permutation]


def membership_uncertainty(samples: np.ndarray, reference: np.ndarray) -> dict:
    return {"mean": samples.mean(axis=0), "std": samples.std(axis=0, ddof=1),
            "q05": np.quantile(samples, 0.05, axis=0),
            "q95": np.quantile(samples, 0.95, axis=0),
            "rmse": float(np.sqrt(np.mean((samples - reference) ** 2))),
            "race_rmse": np.sqrt(np.mean((samples - reference) ** 2, axis=(0, 2)))}


def archetypal_resolution(weighted: pd.DataFrame, runs: int = 40, seed: int = 811,
                         progress=None) -> tuple[dict, dict | None, dict]:
    if runs < 2:
        raise ValueError("At least two perturbations are required for uncertainty")
    x = weighted.to_numpy()
    total = float(np.sum((x - x.mean(axis=0)) ** 2))
    fits, uncertainties, candidates = {}, {}, []
    # Use the same perturbations at every resolution for a paired comparison.
    rng = np.random.default_rng(seed)
    multipliers = []
    for _ in range(runs):
        counts = rng.multinomial(x.shape[1], np.ones(x.shape[1]) / x.shape[1])
        multipliers.append(np.sqrt(counts) * rng.normal(1, 0.08, x.shape[1]))
    for k in range(3, 9):
        fit = fit_archetypes(x, k, seed=seed + k)
        # Stable identity ordering by strongest contributing source race.
        order = sorted(range(k), key=lambda j: (int(np.argmax(fit["hull_weights"][j])), tuple(fit["poles"][j])))
        fit["memberships"] = fit["memberships"][:, order]
        fit["hull_weights"] = fit["hull_weights"][order]
        fit["poles"] = fit["poles"][order]
        samples = []
        converged_trials = 0
        for b, multiplier in enumerate(multipliers):
            trial = fit_archetypes(x * multiplier, k, seed=seed + 1000 * k + b,
                                   starts=2, initial=(fit["memberships"], fit["hull_weights"]))
            converged_trials += int(trial["converged"])
            samples.append(align_memberships(fit["poles"], trial, x))
        uncertainty = membership_uncertainty(np.array(samples), fit["memberships"])
        stable = uncertainty["rmse"] <= 0.12 and float(uncertainty["race_rmse"].max()) <= 0.25
        candidates.append({"k": k, "relative_squared_error": fit["loss"] / total,
                           "membership_rmse": uncertainty["rmse"],
                           "max_race_membership_rmse": float(uncertainty["race_rmse"].max()),
                           "stable": bool(stable), "optimizer_converged": fit["converged"],
                           "perturbation_optimizer_converged_runs": converged_trials,
                           "optimizer_starts": fit["starts"]})
        fits[k], uncertainties[k] = fit, uncertainty
        if progress:
            progress(candidates[-1])
    errors = np.array([row["relative_squared_error"] for row in candidates])
    # Maximum improvement over the straight endpoint chord (normalized axes).
    gain = (errors[0] - errors) / max(float(errors[0] - errors[-1]), 1e-12)
    knee = int(np.argmax(gain - np.linspace(0, 1, len(errors)))) + 3
    stable_after = [row["k"] for row in candidates if row["k"] >= knee and row["stable"]]
    selected = min(stable_after) if stable_after else None
    diagnostic = selected if selected is not None else knee
    report = {"candidate_resolutions": candidates, "error_knee": knee,
              "selected_resolution": selected, "seed": seed, "perturbation_runs": runs,
              "reported_resolution": diagnostic,
              "membership_status": "stable" if selected is not None else "provisional_error_knee_basis",
              "stability_rule": {"global_membership_rmse_max": 0.12, "race_membership_rmse_max": 0.25},
              "selection_rule": "smallest stable resolution at or after maximum normalized error-curve chord deviation",
              "status": "selected" if selected else "no stable resolution at or after knee; reported memberships are diagnostic only"}
    return report, fits[diagnostic], uncertainties[diagnostic]


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
