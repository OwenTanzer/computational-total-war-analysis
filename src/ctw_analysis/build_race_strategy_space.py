"""Validate the source, build Janus relationships, and write reviewed artifacts."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import pandas as pd

from . import race_features as rf
from .janus_distance import (
    archetypal_resolution, block_weighted_matrix, composite_scores,
    local_residuals, membership_entropy, pairwise_report, tier_sensitivity,
)

ROOT = Path(__file__).resolve().parents[2]
REVIEWED = ROOT / "studies/race_strategy_space/results/8.1.1"
ARTIFACTS = {
    "README.md", "race_capability_views.csv", "race_capability_composites.csv",
    "race_archetype_memberships.csv", "race_details.json", "jsd_report.json",
    "unit_tier_sensitivity.json",
}


def validate_source_lock(ctw_root: Path, lock_path: Path = ROOT / "source_lock.json") -> dict:
    """Require both the precise commit and unmodified tracked source contents."""
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    try:
        actual_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ctw_root,
                                    check=True, capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                               cwd=ctw_root, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Source verification requires a readable CTW git checkout") from exc
    if actual_sha != lock["git_commit"]:
        raise RuntimeError(f"CTW commit mismatch: expected {lock['git_commit']}, found {actual_sha}")
    if dirty:
        raise RuntimeError("CTW has modified tracked files; the locked source must remain read-only")
    catalog = json.loads((ctw_root / "context_catalog.json").read_text(encoding="utf-8"))
    for key in ("patch", "steam_build_id", "unit_scale"):
        if catalog["snapshot"].get(key) != lock["snapshot"].get(key):
            raise RuntimeError(f"Source snapshot mismatch for {key}")
    return lock


def json_ready(value):
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [json_ready(v) for v in value]
    if isinstance(value, (np.floating, float)):
        if not np.isfinite(value):
            raise ValueError("Non-finite value in reviewed output")
        return round(float(value), 9)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(json_ready(value), indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def archetype_outputs(weighted, features, fit, uncertainty):
    memberships = pd.DataFrame(index=weighted.index)
    memberships.index.name = "race"
    if fit is None:
        return memberships, []
    w, h = fit["memberships"], fit["hull_weights"]
    for j in range(w.shape[1]):
        label = f"A{j+1}"
        memberships[label] = w[:, j]
        for regime, diagnostic in uncertainty.items():
            for stat in ("mean", "std", "q05", "q95"):
                memberships[f"{regime}__{label}__{stat}"] = diagnostic['membership'][stat][:, j]
    memberships["normalized_entropy"] = membership_entropy(w)
    for regime, diagnostic in uncertainty.items():
        tv = diagnostic['membership']['total_variation']
        for stat in ('mean', 'q95', 'max'):
            memberships[f'{regime}__tv_{stat}'] = tv[f'per_item_{stat}']
    poles = []
    for j, pole in enumerate(fit["poles"]):
        source_order = np.argsort(-h[j], kind="stable")[:5]
        race_order = np.argsort(-w[:, j], kind="stable")[:5]
        load_order = np.argsort(-np.abs(pole), kind="stable")[:8]
        poles.append({"id": f"A{j+1}",
                      "hull_weights": dict(zip(weighted.index, h[j])),
                      "weighted_coordinates": dict(zip(weighted.columns, pole)),
                      "raw_coordinates": dict(zip(features.columns, h[j] @ features.to_numpy())),
                      "leading_dimensions": [{"dimension": weighted.columns[c], "weighted_coordinate": float(pole[c])}
                                             for c in load_order],
                      "leading_source_races": [{"race": weighted.index[i], "hull_weight": float(h[j, i])} for i in source_order],
                      "leading_memberships": [{"race": weighted.index[i], "membership": float(w[i, j])} for i in race_order]})
    return memberships, poles


def result_readme(report, memberships, residuals, sensitivity):
    selection = report['archetypes']
    lines = ['# Janus Strategic Distance: patch 8.1.1', '',
             f"Source: `{report['source']['git_commit']}`; {report['eligible_units']} eligible units; 54 primary dimensions across 24 races.", '',
             f"Error knee: K={selection['error_knee']}. Reported basis: K={selection['reported_resolution']} ({selection['membership_status']}).",
             f"Selection status: {selection['status']}; selected resolution: {selection['selected_resolution']}.",
             'No numerical tolerance is adopted by default. The table below shows conditional choices; it does not declare natural strategic classes.', '',
             '## Separate diagnostics', '',
             '| K | Relative squared error | Optimizer worst race TV95 | Local mean TV | Local worst race TV95 | Local worst pole relative95 | Stress mean TV |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for c in selection['candidate_resolutions']:
        d = c['diagnostics']; local = d['local_robustness']; pole = local['max_pole_relative_q95']
        pole_text = 'degenerate' if pole is None else f'{pole:.4f}'
        lines.append(f"| {c['k']} | {c['relative_squared_error']:.4f} | {d['optimization_repeatability']['max_race_tv_q95']:.4f} | {local['membership_tv_mean']:.4f} | {local['max_race_tv_q95']:.4f} | {pole_text} | {d['structural_stress']['membership_tv_mean']:.4f} |")
    lines += ['', 'TV is total variation distance: the fraction of membership mass reassigned. TV95 is the 95th percentile across runs for each race; worst means the largest of those race-specific values. Pole displacement is divided by separation from the nearest other reference pole.', '',
              'Optimization repeats use unchanged data and independent starts. Local robustness retains every dimension and equal block totals. Structural stress resamples dimensions and reweights blocks; it never gates selection.', '',
              '## Conditional tolerance choices', '',
              '| Maximum worst-race TV95 | Maximum worst-pole relative95 | Smallest qualifying K at/after knee |',
              '|---:|---:|---:|']
    for row in selection['tolerance_grid']:
        lines.append(f"| {row['membership_tolerance']:.2f} | {row['pole_tolerance']:.2f} | {row['selected_resolution']} |")
    lines += ['', 'Both optimization repeatability and local robustness must satisfy both tolerances, with all reference/control/local fits converged. Structural stress is excluded. A membership tolerance of 0.20 allows 20 percentage points to move; a pole tolerance of 0.25 allows movement of one quarter of nearest-pole separation. These are interpretable policy choices, not significance thresholds.', '',
              '## Reported poles', '']
    for p in selection['poles']:
        members = ', '.join(f"{r['race']} {r['membership']:.3f}" for r in p['leading_memberships'][:3])
        dims = ', '.join(f"{r['dimension']} {r['weighted_coordinate']:+.3f}" for r in p['leading_dimensions'][:4])
        lines.append(f"- **{p['id']}** — leading memberships: {members}. Leading coordinates: {dims}.")
    lines += ['', '## Pole movement in the reported basis', '',
              '| Regime | Pole | Mean displacement | Largest displacement | Relative 95th percentile |',
              '|---|---|---:|---:|---:|']
    for regime, diagnostic in selection['reported_diagnostics'].items():
        poles = diagnostic['poles']; absolute = poles['absolute_displacement']; relative = poles['relative_displacement']
        for j in range(selection['reported_resolution']):
            rel = 'degenerate' if relative is None else f"{relative['per_item_q95'][j]:.4f}"
            lines.append(f"| {regime} | A{j+1} | {absolute['per_item_mean'][j]:.4f} | {absolute['per_item_max'][j]:.4f} | {rel} |")
    lines += ['', '## Local neighborhoods', '',
              '| Race | Nearest race | Distance | Entropy | Local mean TV | Local TV95 |',
              '|---|---|---:|---:|---:|---:|']
    for race, local in residuals.items():
        nearest = local['neighbors'][0]
        lines.append(f"| {race} | {nearest['race']} | {nearest['distance']:.4f} | {memberships.loc[race, 'normalized_entropy']:.3f} | {memberships.loc[race, 'local_robustness__tv_mean']:.3f} | {memberships.loc[race, 'local_robustness__tv_q95']:.3f} |")
    lines += ['', '## File contract', '',
              '- `race_capability_views.csv`: original breadth, ceiling and cost_access measurements.',
              '- `race_capability_composites.csv`: sample-relative 0–100 summaries; zero denotes the sample minimum.',
              '- `race_archetype_memberships.csv`: reference weights, entropy, and explicitly named statistics for each of the three diagnostic regimes.',
              '- `race_details.json`: capability evidence and local residuals against four distance-weighted neighbors.',
              '- `jsd_report.json`: all pair comparisons, per-resolution diagnostics, conditional tolerance choices, and full movement distributions and profile-change intervals for the reported basis. Distribution columns follow `races`, pole IDs and `profile_dimensions`.',
              '- `unit_tier_sensitivity.json`: topology changes only; unit tier does not establish campaign recruitment access.', '',
              f"Primary/sensitivity distance correlation: {sensitivity['distance_pearson_correlation']:.6f}.", '',
              'Pair records show up to four components per sign. Reversing the pair negates its components and exchanges ranks. Use `directional_delta` for the exact full-vector decomposition.', '',
              'Entropy describes mixing within the fitted basis, not overall tactical versatility. Pole movement and profile changes are measured in the original weighted space after label alignment. Tail events and failed optimization runs remain visible, even when a percentile tolerance accepts a representation.', '',
              'The measurements concern static roster possibilities and method sensitivity, not observed armies, causal tactical combinations, win rates, or confidence intervals over battles.', '']
    return '\n'.join(lines)


def build(ctw_root: Path, out_dir: Path, runs: int = 40, seed: int = 811, workers: int = 1,
          membership_tolerance=None, pole_tolerance=None):
    lock = validate_source_lock(ctw_root)
    rf.configure_source(ctw_root)
    units = rf.attach_lookup_flags(rf.load_units())
    unit_scores, _ = rf.build_unit_scores(units)
    features, details = rf.aggregate_features(unit_scores)
    scaled, weighted = block_weighted_matrix(features)
    _, weighted_tier = block_weighted_matrix(features, include_unit_tier_sensitivity=True)
    primary = features[weighted.columns]
    if primary.shape != (24, 54) or weighted_tier.shape != (24, 69):
        raise RuntimeError("Unexpected race/feature dimensions")
    print(f"Validated {len(units)} units; fitting archetypal resolutions", flush=True)
    selection, fit, uncertainty = archetypal_resolution(
        weighted, runs=runs, seed=seed, workers=workers,
        membership_tolerance=membership_tolerance, pole_tolerance=pole_tolerance,
        progress=lambda c: print(f"K={c['k']} error={c['relative_squared_error']:.4f} "
                                  f"local_tv={c['diagnostics']['local_robustness']['membership_tv_mean']:.4f} "
                                  f"stress_tv={c['diagnostics']['structural_stress']['membership_tv_mean']:.4f}", flush=True))
    memberships, poles = archetype_outputs(weighted, primary, fit, uncertainty)
    selection["poles"] = poles
    residuals = local_residuals(primary, weighted)
    for race in details:
        details[race]["local_distinctiveness"] = residuals[race]
    sensitivity = tier_sensitivity(weighted, weighted_tier)
    report = {"name": "Janus Strategic Distance", "source": lock, "eligible_units": len(units),
              "primary_dimensions": len(primary.columns), "races": weighted.index.tolist(),
              "distance_definition": "sqrt(sum_j q_j * (z_Bj-z_Aj)^2)",
              "direction_definition": "sqrt(q_j) * (z_Bj-z_Aj)",
              "squared_weight_scale": "q_j = view_share / (3 * number_of_features_in_block); each block totals 1/3",
              "pair_component_limit_per_sign": 4, "archetypes": selection,
              "pairs": pairwise_report(primary, weighted)}
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in [("race_capability_views.csv", primary),
                        ("race_capability_composites.csv", composite_scores(features)),
                        ("race_archetype_memberships.csv", memberships)]:
        frame.to_csv(out_dir / name, float_format="%.9f", lineterminator="\n")
    write_json(out_dir / "race_details.json", details)
    write_json(out_dir / "jsd_report.json", report)
    write_json(out_dir / "unit_tier_sensitivity.json", sensitivity)
    (out_dir / "README.md").write_text(result_readme(report, memberships, residuals, sensitivity),
                                      encoding="utf-8", newline="\n")
    print(json.dumps({"selected_resolution": selection["selected_resolution"],
                      "distance_correlation": sensitivity["distance_pearson_correlation"]}), flush=True)
    return report


def verify_artifacts(actual: Path, expected: Path = REVIEWED):
    actual_files = {p.name for p in actual.iterdir() if p.is_file()}
    expected_files = {p.name for p in expected.iterdir() if p.is_file()}
    if actual_files != ARTIFACTS or expected_files != ARTIFACTS:
        raise RuntimeError(f"Artifact contract mismatch: actual={sorted(actual_files)}, reviewed={sorted(expected_files)}")
    changed = [name for name in sorted(ARTIFACTS) if (actual / name).read_bytes() != (expected / name).read_bytes()]
    if changed:
        raise RuntimeError(f"Regeneration mismatch: {changed}")
    print("All seven reviewed artifacts regenerate byte-identically", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Build Janus Strategic Distance from locked CTW data")
    parser.add_argument("--ctw-root", type=Path, default=Path(os.environ.get("CTW_ROOT", ROOT.parent / "computational-total-war")))
    parser.add_argument("--out-dir", type=Path, default=ROOT / "work/janus_output")
    parser.add_argument("--perturbations", type=int, default=40)
    parser.add_argument("--seed", type=int, default=811)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--membership-tolerance", type=float)
    parser.add_argument("--pole-tolerance", type=float)
    parser.add_argument("--verify-regeneration", action="store_true")
    args = parser.parse_args()
    if args.verify_regeneration:
        with tempfile.TemporaryDirectory(prefix="ctw-janus-") as temp:
            build(args.ctw_root, Path(temp), args.perturbations, args.seed, args.workers, args.membership_tolerance, args.pole_tolerance)
            verify_artifacts(Path(temp))
    else:
        build(args.ctw_root, args.out_dir, args.perturbations, args.seed, args.workers, args.membership_tolerance, args.pole_tolerance)


if __name__ == "__main__":
    main()
