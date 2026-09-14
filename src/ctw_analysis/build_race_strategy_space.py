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
        for stat in ("mean", "std", "q05", "q95"):
            memberships[f"{label}__{stat}"] = uncertainty[stat][:, j]
    memberships["normalized_entropy"] = membership_entropy(w)
    memberships["membership_rmse"] = uncertainty["race_rmse"]
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
    selection = report["archetypes"]
    lines = ["# Janus Strategic Distance: patch 8.1.1", "",
             f"Source: `{report['source']['git_commit']}`; {report['eligible_units']} eligible units; "
             f"{report['primary_dimensions']} primary dimensions across {len(report['races'])} races.", "",
             f"Error knee: K={selection['error_knee']}. Selected resolution: {selection['selected_resolution']}.",
             f"Reported membership basis: K={selection['reported_resolution']} ({selection['membership_status']}).",
             "K controls descriptive resolution; poles are mixtures within the observed roster space.", "",
             "| K | Relative squared error | Membership RMSE | Largest race RMSE | Stable |",
             "|---|---:|---:|---:|---|"]
    for c in selection["candidate_resolutions"]:
        lines.append(f"| {c['k']} | {c['relative_squared_error']:.4f} | {c['membership_rmse']:.4f} | "
                     f"{c['max_race_membership_rmse']:.4f} | {c['stable']} |")
    lines += ["", "RMSE means root mean squared error in membership weights. Feature perturbation uncertainty "
              "is separate from normalized membership entropy, which measures mixture breadth.", "",
              "## Derived poles", ""]
    for p in selection["poles"]:
        members = ", ".join(f"{r['race']} {r['membership']:.3f}" for r in p["leading_memberships"][:3])
        dims = ", ".join(f"{r['dimension']} {r['weighted_coordinate']:+.3f}" for r in p["leading_dimensions"][:4])
        lines += [f"- **{p['id']}** — leading memberships: {members}. Leading coordinates: {dims}."]
    lines += ["", "## Local neighborhoods", "", "| Race | Nearest race | Distance | Entropy | Membership RMSE |",
              "|---|---|---:|---:|---:|"]
    for race, local in residuals.items():
        nearest = local["neighbors"][0]
        entropy = f"{memberships.loc[race, 'normalized_entropy']:.3f}" if selection["poles"] else "unselected"
        rmse = f"{memberships.loc[race, 'membership_rmse']:.3f}" if selection["poles"] else "unselected"
        lines.append(f"| {race} | {nearest['race']} | {nearest['distance']:.4f} | {entropy} | {rmse} |")
    lines += ["", "## Reading the files", "",
              "- `race_capability_views.csv`: original breadth, ceiling, and cost_access measurements.",
              "- `race_capability_composites.csv`: sample-relative 0–100 summaries; zero means the sample minimum, not absence.",
              "- `race_archetype_memberships.csv`: fitted weights, perturbation means, standard deviations, 5th/95th percentiles, entropy and membership RMSE.",
              "- `race_details.json`: underlying capability evidence and local residuals against four distance-weighted neighbors.",
              "- `jsd_report.json`: all unordered pair distances, neighbor ranks in both directions, leading signed components, resolution audit and pole coordinates.",
              "- `unit_tier_sensitivity.json`: topology changes only; unit tier does not establish campaign recruitment access.", "",
              f"Primary/sensitivity distance correlation: {sensitivity['distance_pearson_correlation']:.6f}.", "",
              "Pair records give up to four positive and four negative components for the documented from→to direction. "
              "Reversing a pair negates its components and exchanges its neighbor ranks. The full 54-component decomposition "
              "is available through `directional_delta`; it is not approximated by summing the displayed leading components.", "",
              "Archetypes summarize static roster possibilities. They do not estimate played army compositions, win rates, "
              "or causal tactical combinations. Feature perturbations are sensitivity intervals, not confidence intervals over sampled battles.", ""]
    return "\n".join(lines)


def build(ctw_root: Path, out_dir: Path, runs: int = 40, seed: int = 811):
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
        weighted, runs=runs, seed=seed,
        progress=lambda c: print(f"K={c['k']} error={c['relative_squared_error']:.4f} "
                                  f"membership_rmse={c['membership_rmse']:.4f} stable={c['stable']}", flush=True))
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
    parser.add_argument("--verify-regeneration", action="store_true")
    args = parser.parse_args()
    if args.verify_regeneration:
        with tempfile.TemporaryDirectory(prefix="ctw-janus-") as temp:
            build(args.ctw_root, Path(temp), args.perturbations, args.seed)
            verify_artifacts(Path(temp))
    else:
        build(args.ctw_root, args.out_dir, args.perturbations, args.seed)


if __name__ == "__main__":
    main()
