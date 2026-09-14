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
from .capability_packages import unit_evidence, capability_packages
from .assumption_sensitivity import block_emphasis, requirement_comparisons
from .janus_distance import (
    archetypal_resolution, block_weighted_matrix, composite_scores,
    local_residuals, membership_entropy, pairwise_report, tier_sensitivity,
)

ROOT = Path(__file__).resolve().parents[2]
REVIEWED = ROOT / "studies/race_strategy_space/results/8.1.1"
ARTIFACTS = {
    "README.md", "race_capability_views.csv", "race_capability_composites.csv",
    "race_archetype_memberships.csv", "race_details.json", "jsd_report.json",
    "unit_tier_sensitivity.json", "unit_evidence.json",
    "capability_packages.json", "assumption_sensitivity.json",
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


def result_readme(report, residuals, sensitivity, packages, assumptions):
    atlas = report['archetypes']
    lines = ['# Janus: roster relationships and attainable capability packages', '',
             f"Locked patch 8.1.1; {report['eligible_units']} eligible units, 24 races, 54 preserved aggregate dimensions.", '',
             '## Relationships first', '',
             'Distances summarize roster profiles. Leading contrasts and local residuals explain their differences; unit evidence identifies the purchases behind the summaries.', '',
             '| Race | Nearest roster | Distance | Largest local distinction | View | Signed residual |',
             '|---|---|---:|---|---|---:|']
    for race, local in residuals.items():
        nearest = local['neighbors'][0]
        key, value = max(local['weighted_residual'].items(), key=lambda kv: abs(kv[1]))
        feature, view = key.split('__')
        lines.append(f"| {race} | {nearest['race']} | {nearest['distance']:.4f} | {feature} | {view} | {value:+.4f} |")
    lines += ['', 'Breadth, ceiling and cost access remain separate. Pairwise distances and leading signed contrasts are in `jsd_report.json`; local evidence is in `race_details.json` and contributing unit IDs in `unit_evidence.json`.', '',
              '## Attainable combinations', '',
              f"{len(packages['records'])} race/query families cover every pair of the 15 unit capability proxies, plus raw speed, armour and range comparisons. Each evaluates a 3×3 grid of positive-global-support quantiles (50%, 75%, 90%). Threshold values and their units are published.", '',
              'One-unit packages require both capabilities in the same purchase. Two-unit packages require distinct providers; the all-units-speed query instead requires both units to meet the speed floor. Cost is summed once per purchase. Scores are never summed into army power.', '',
              'The package file retains exact cost/capability Pareto frontiers and every minimum-cost tie on the requirement grid. Null cost means unattainable or no positive global support, with an explicit reason. Unit IDs resolve to original keys, costs, measurements and all proxy capabilities.', '',
              '### Requirement-dependent cost reversals', '',
              '| Requirement family | Rosters A / B | Requirements favoring A; costs A / B | Requirements favoring B; costs A / B |',
              '|---|---|---|---|']
    comparisons = assumptions['requirement_comparisons']
    shown, used_pairs = 0, set()
    families = sorted(comparisons, key=lambda r: (not r['a'].startswith('raw_'), -len(r['finite_cost_order_reversals']), r['a'], r['b'], r['two_unit_semantics']))
    for family in families:
        events = family['finite_cost_order_reversals']
        if events and shown < 6:
            event = next((e for e in events if (e['race_a'],e['race_b']) not in used_pairs), events[0])
            used_pairs.add((event['race_a'],event['race_b']))
            def describe(index):
                la, lb = family['requirement_levels'][index]
                ta, tb = packages['thresholds'][family['a']][la], packages['thresholds'][family['b']][lb]
                ca = family['minimum_costs_by_race'][family['races'].index(event['race_a'])][index]
                cb = family['minimum_costs_by_race'][family['races'].index(event['race_b'])][index]
                return f"{family['a']} ≥ {ta:.6g}, {family['b']} ≥ {tb:.6g}; {ca:g} / {cb:g}"
            mode = 'all-unit speed floor' if family['two_unit_semantics'] == 'all_units_a' else 'distinct providers allowed'
            lines.append(f"| {family['a']} + {family['b']} ({mode}) | {event['race_a']} / {event['race_b']} | {describe(event['a_cheaper_requirement'])} | {describe(event['b_cheaper_requirement'])} |")
            shown += 1
    if not shown:
        lines += ['| No finite cost-order reversals on this grid | — | — | — |']
    lines += ['', 'Examples prioritize raw-measure families, then proxy families with the most reversals, using distinct race pairs when available. Costs are minimum multiplayer prices with at most two units. These are navigation examples, not prevalence estimates. Exact thresholds, complete cost matrices and all witnesses are retained in the data files.', '',
              '## Assumptions and consequences', '',
              f"{len(assumptions['block_emphasis']['stable_nearest_neighbors'])} of 24 nearest-neighbor identities persist across equal weighting and each of four block-emphasis scenarios. All scenario distances, ranks and changed neighborhoods are retained.", '',
              'Each emphasis doubles one block relative to the others while retaining the original total squared weight. These scenarios change roster relationships; archetypes are not refitted under them.', '',
              '## Alternative compressed representations', '',
              f"The reconstruction-error knee is K={atlas['error_knee']}; it is descriptive and excludes no representation. No resolution is selected.", '',
              '| K | Relative squared error | Optimizer worst-race TV95 | Local mean TV | Local worst-race TV95 | Local worst-pole relative95 | Stress mean TV |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for c in atlas['candidate_resolutions']:
        d = c['diagnostics']; local = d['local_robustness']; pole = local['max_pole_relative_q95']
        pole_text = 'degenerate' if pole is None else f'{pole:.4f}'
        lines.append(f"| {c['k']} | {c['relative_squared_error']:.4f} | {d['optimization_repeatability']['max_race_tv_q95']:.4f} | {local['membership_tv_mean']:.4f} | {local['max_race_tv_q95']:.4f} | {pole_text} | {d['structural_stress']['membership_tv_mean']:.4f} |")
    lines += ['', 'TV (total variation) measures the fraction of membership mass reassigned. Pole displacement is measured in the original weighted space and normalized by nearest reference-pole separation. These are separate per-race/per-pole percentiles, not simultaneous guarantees for entire runs.', '',
              'Full memberships, pole profiles, movement distributions, optimizer attempts and profile-change intervals are retained for every K. Adjacent representations have nearest-profile correspondences in both directions, allowing many-to-one matches. Distances, ties and mapped membership changes accompany these correspondences; they do not establish ancestry or a causal split.', '',
              '### Tolerance comparisons without a winner', '',
              '| Membership limit | Pole limit | All resolutions within both limits |',
              '|---:|---:|---|']
    for cell in atlas['tolerance_grid']:
        ks = ', '.join(str(r['k']) for r in cell['resolutions'] if r['within_tolerances']) or 'None'
        lines.append(f"| {cell['membership_tolerance']:.2f} | {cell['pole_tolerance']:.2f} | {ks} |")
    lines += ['', 'Both unchanged-data optimization and local perturbations must satisfy the illustrative limits with converged fits and distinct reference poles. Structural stress is reported separately. No cutoff is adopted and none of these comparisons chooses K.', '',
              '## Evidence contract', '',
              '- `race_capability_views.csv`: preserved breadth, ceiling and cost access.',
              '- `race_capability_composites.csv`: sample-relative display summaries.',
              '- `race_archetype_memberships.csv`: all K/race memberships and diagnostics; blank pole columns mean the pole does not exist at that K.',
              '- `race_details.json`: capability summaries, local residuals and unit-evidence references.',
              '- `jsd_report.json`: pair contrasts, all representations and cross-resolution correspondences.',
              '- `unit_evidence.json`: unit keys, original measurements, scores and aggregate witnesses.',
              '- `capability_packages.json`: exact bounded frontiers, requirement grids, costs and tied witnesses.',
              '- `assumption_sensitivity.json`: block-emphasis relationships and requirement-dependent cost comparisons.',
              '- `unit_tier_sensitivity.json`: unit-classification topology sensitivity.', '',
              f"Primary/unit-tier distance correlation: {sensitivity['distance_pearson_correlation']:.6f}.", '',
              'These are roster-listed possibilities, not guarantees of faction recruitment legality, playable armies, tactical synergy, win rates or causal strategy modes. Packages contain at most two distinct units. Capability proxies retain their earlier scoring assumptions; raw-measure queries retain missingness. Entropy describes mixing in a fitted basis, not tactical versatility.', '']
    return '\n'.join(lines)


def build(ctw_root: Path, out_dir: Path, runs: int = 40, seed: int = 811, workers: int = 1):
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
    atlas, fits, diagnostics = archetypal_resolution(
        weighted, runs=runs, seed=seed, workers=workers,
        progress=lambda c: print(f"K={c['k']} error={c['relative_squared_error']:.4f} "
                                  f"local_tv={c['diagnostics']['local_robustness']['membership_tv_mean']:.4f} "
                                  f"stress_tv={c['diagnostics']['structural_stress']['membership_tv_mean']:.4f}", flush=True))
    frames = []
    for k, fit in fits.items():
        frame, poles = archetype_outputs(weighted, primary, fit, diagnostics[k])
        frame.insert(0, 'k', k)
        frames.append(frame)
        atlas['representations'][str(k)].update({'poles': poles, 'memberships': fit['memberships']})
    memberships = pd.concat(frames)
    print('Building unit evidence and exact one/two-unit package frontiers', flush=True)
    ordered, evidence = unit_evidence(unit_scores, units)
    packages = capability_packages(ordered, evidence)
    assumptions = {'block_emphasis': block_emphasis(weighted),
                   'requirement_comparisons': requirement_comparisons(packages)}
    residuals = local_residuals(primary, weighted)
    for race in details:
        details[race]["local_distinctiveness"] = residuals[race]
        details[race]["unit_evidence_reference"] = {"file": "unit_evidence.json", "race": race}
    sensitivity = tier_sensitivity(weighted, weighted_tier)
    report = {"name": "Janus Strategic Distance", "source": lock, "eligible_units": len(units),
              "primary_dimensions": len(primary.columns), "races": weighted.index.tolist(),
              "distance_definition": "sqrt(sum_j q_j * (z_Bj-z_Aj)^2)",
              "direction_definition": "sqrt(q_j) * (z_Bj-z_Aj)",
              "squared_weight_scale": "q_j = view_share / (3 * number_of_features_in_block); each block totals 1/3",
              "pair_component_limit_per_sign": 4, "archetypes": atlas,
              "pairs": pairwise_report(primary, weighted)}
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in [("race_capability_views.csv", primary),
                        ("race_capability_composites.csv", composite_scores(features)),
                        ("race_archetype_memberships.csv", memberships)]:
        frame.to_csv(out_dir / name, float_format="%.9f", lineterminator="\n")
    write_json(out_dir / "race_details.json", details)
    write_json(out_dir / "unit_evidence.json", evidence)
    # Compact indexed package rows keep exhaustive witnesses manageable.
    for name, content in [('capability_packages.json', packages), ('assumption_sensitivity.json', assumptions)]:
        (out_dir / name).write_text(json.dumps(json_ready(content), separators=(',', ':'), allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    write_json(out_dir / "jsd_report.json", report)
    write_json(out_dir / "unit_tier_sensitivity.json", sensitivity)
    (out_dir / "README.md").write_text(result_readme(report, residuals, sensitivity, packages, assumptions),
                                      encoding="utf-8", newline="\n")
    print(json.dumps({"representations": sorted(fits),
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
    print("All ten reviewed artifacts regenerate byte-identically", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Build Janus Strategic Distance from locked CTW data")
    parser.add_argument("--ctw-root", type=Path, default=Path(os.environ.get("CTW_ROOT", ROOT.parent / "computational-total-war")))
    parser.add_argument("--out-dir", type=Path, default=ROOT / "work/janus_output")
    parser.add_argument("--perturbations", type=int, default=40)
    parser.add_argument("--seed", type=int, default=811)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--verify-regeneration", action="store_true")
    args = parser.parse_args()
    if args.verify_regeneration:
        with tempfile.TemporaryDirectory(prefix="ctw-janus-") as temp:
            build(args.ctw_root, Path(temp), args.perturbations, args.seed, args.workers)
            verify_artifacts(Path(temp))
    else:
        build(args.ctw_root, args.out_dir, args.perturbations, args.seed, args.workers)


if __name__ == "__main__":
    main()
