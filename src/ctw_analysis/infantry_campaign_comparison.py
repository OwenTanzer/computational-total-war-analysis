"""Reproducible base screening and explicitly partial campaign modifier ledgers.

No engine simulation, localization-driven auto-targeting, or global ceiling claim.
Only standard-library dependencies. See the study methodology for model limits.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "studies/infantry_campaign_comparison"
STATS = ["total_hp", "armour", "leadership", "melee_attack", "melee_defence",
         "weapon_base_damage", "weapon_ap_damage", "speed", "charge_bonus",
         "physical_resistance", "missile_resistance", "spell_resistance",
         "ward_save", "shield_block_chance", "barrier_health",
         "bonus_vs_large", "bonus_vs_infantry"]
AXES = ["total_hp", "armour", "melee_attack", "melee_defence", "speed",
        "raw_rate", "ap_rate", "physical_resistance", "missile_resistance",
        "spell_resistance", "ward_save", "shield_block_chance", "barrier_health",
        "charge_bonus", "bonus_vs_large", "bonus_vs_infantry"]


def read_csv(path, delimiter=","):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter=delimiter)
                if not next(iter(r.values())).startswith("#")]


def number(value):
    if value is None or value == "":
        raise ValueError("Missing numeric value must not become zero")
    return float(value)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def render_report(summary, profiles, units, subtotals, residuals):
    lines = ["# Iron Claws and competing infantry: first data comparison", "",
        "**Campaign ceiling: unresolved.** Iron Claws occupy a strong combination of dimensions, "
        "but the available reconstruction does not establish the highest-stat doomstack.", "",
        f"Source: [{summary['source_commit'][:12]}](https://github.com/OwenTanzer/computational-total-war/tree/{summary['source_commit']}) "
        "— patch 8.1.1, Ultra scale. See [methodology](../../methodology.md) and the "
        "[reviewed modifier selections](../../profiles.json).", "",
        "## Full base screen", "",
        f"Read {summary['roster_rows']:,} roster rows ({summary['unique_unit_keys']:,} distinct unit keys); "
        f"{summary['small_melee_infantry_static_cap_candidates']} meet the small-target melee-infantry filters and static 19-copy cap check. "
        "Dynamic recruitment availability is not yet certified. Rankings count distinct unit keys, including different variants with the same name.", "",
        "| Dimension | Iron Claw value | Competition rank | Highest base value |",
        "|---|---:|---:|---|"]
    labels = {"total_hp": "Unit health", "armour": "Armour", "melee_attack": "Melee attack",
              "melee_defence": "Melee defence", "speed": "Speed (source units)",
              "raw_rate": "Raw attack-capacity proxy", "ap_rate": "Armour-piercing attack-capacity proxy"}
    for r in summary["tiger_rankings"]:
        top = r["leaders"][0]
        lines.append(f"| {labels[r['metric']]} | {r['tiger_value']:.2f} | {r['competition_rank']} / {r['candidate_count']} | {top['unit_name']}: {top['value']:.2f} |")
    lines += ["", f"Iron Claws are on the **base Pareto frontier**, alongside {summary['base_pareto_count'] - 1} other candidates. "
        "This broad frontier reflects trade-offs across many axes; it is not a ranking of elite units. No base candidate is removed from future campaign research.", "",
        "Attack-capacity proxies assume all models attack at the nominal interval and every attack connects. "
        "They are not battle damage measurements. Armour-piercing capacity is part of total capacity, not additional damage.", "",
        "## Selected base cards", "",
        "| Unit | Models | Health | Armour | Attack / defence | Weapon normal + piercing | Speed (source) |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for p in profiles:
        r = units[p["unit_key"]]
        lines.append(f"| {r['unit_name']} | {r['entity_count']} | {r['total_hp']} | {r['armour']} | {r['melee_attack']} / {r['melee_defence']} | {r['weapon_base_damage']} + {r['weapon_ap_damage']} | {r['speed']} |")
    lines += ["", "## Known modifiers at a rank-9 neutral condition", "",
        f"The ledger contains **{summary['reviewed_modifier_rows']} reviewed source effect rows** across five profiles. "
        "The following figures are **base stats plus selected known modifiers**, excluding native rank stat gains, "
        "unresolved faction systems, items, auras and other effects. They are neither complete cards nor attainable ceilings. "
        "Unequal missing coverage prevents using this table to declare a campaign winner.", "",
        "| Lord / unit | Armour subtotal | Attack / defence subtotal | Physical resistance subtotal | Weapon strength subtotal |",
        "|---|---:|---:|---:|---:|"]
    for r in subtotals:
        if r["state"] != "rank9_neutral":
            continue
        lo = r["weapon_base_damage_min"] + r["weapon_ap_damage_min"]
        hi = r["weapon_base_damage_max"] + r["weapon_ap_damage_max"]
        ws = f"{lo:.2f}" if abs(lo - hi) < 1e-9 else f"{lo:.2f}–{hi:.2f}"
        lines.append(f"| {r['profile'].split('_')[0].title()} / {r['unit_name']} | {r['armour_min']:.0f} | "
                     f"{r['melee_attack_min']:.0f} / {r['melee_defence_min']:.0f} | {r['physical_resistance_min']:.0f}% | {ws} |")
    lines += ["", "The weapon-strength range exposes two possible flat/percentage application orders; it is not an engine-certified bound. "
        "Attacking-ambush and defending-siege conditions are separate rows in the accompanying CSV, never combined.", "",
        "Notable source-backed contributions:", "",
        "* Bhashiva: +6 attack/+6 defence from terminal Unyielding, +10% physical resistance from Deadly & Graceful, "
        "and +5 defence at unit rank 7+ from Blades of the Bastion. Drill Training and Jade Stance supply +25 armour/+8 defence together. "
        "These are explicit text-supported targets; the underlying engine unit-set joins remain unavailable.",
        "* Thorgrim's Hammerers: +15% physical resistance from High King, +10% at rank 7+ from Honoured by Grimnir, "
        "and +5% from Royal Guard. Selected weapon-strength bonuses total +34% in the neutral subtotal.",
        "* Festus: Hideous Amputation supplies +3% weapon strength per experience rank to Great Weapons units—+27% at rank 9, "
        "separate from missing native experience bonuses.",
        "* Sigvald's Hellscourges retain a much more defensive profile; they are a useful alternative to a damage-first comparison.", "",
        "## Screenshot residual audit", "",
        "The displayed rank and active conditions are unverified. This diagnostic compares the supplied card with the "
        "rank-9 neutral known-modifier subtotal; it does not assume that this was the depicted state.", "",
        "| Stat | Screenshot | Known subtotal | Unexplained difference |", "|---|---:|---:|---:|"]
    for r in residuals:
        lines.append(f"| {r['stat']} | {r['observed']:.0f} | {r['known_subtotal_min']:.0f} | {r['unexplained_difference_min']:+.0f} |")
    lines += ["", "The missing differences do not imply that the screenshot is wrong. They show that this reconstruction is incomplete. "
        "Displayed speed is excluded from this diagnostic unless its source-to-card conversion is verified.", "",
        "## What prevents a ceiling verdict", "",
        "Effect-to-bonus operations and unit-set membership, native experience scaling, complete item/trait acquisition, "
        "ability activation/phase and targeting relations, faction upgrades/rituals and their caps, and dynamic recruitment limits "
        "must be resolved before an exhaustive campaign optimizer can run. Raw Ferocious Ambush phase data contains a 20-second "
        "duration, but missing activation relations prevent treating it as a sustained bonus or a verified peak stack.", "",
        "The present result supports **a strong, mobile, armour-piercing infantry package**, not an absolute numerical supremacy claim.", ""]
    if not residuals:
        start = lines.index("## Screenshot residual audit")
        end = lines.index("## What prevents a ceiling verdict")
        del lines[start:end]
    return "\n".join(lines)


def rates(row, engagement=1.0):
    n = number(row["entity_count"]) * engagement
    interval = number(row["attack_interval"])
    if interval <= 0 or not 0 < engagement <= 1:
        raise ValueError("Invalid interval or engagement fraction")
    return {"raw_rate": n * (number(row["weapon_base_damage"]) + number(row["weapon_ap_damage"])) / interval,
            "ap_rate": n * number(row["weapon_ap_damage"]) / interval}


def dominates(a, b, axes=AXES):
    return all(number(a[k]) >= number(b[k]) for k in axes) and any(
        number(a[k]) > number(b[k]) for k in axes)


def apply_modifiers(base, modifiers, conditions, rank, order):
    """Explicit sensitivity, not a claim to know the engine's modifier order."""
    if {"attacking", "defending"}.issubset(conditions):
        raise ValueError("An army cannot attack and defend in the same state")
    if rank not in range(10):
        raise ValueError("Unit rank must be from 0 to 9")
    if order not in {"flat_then_percent", "percent_then_flat"}:
        raise ValueError("Unknown modifier-order sensitivity")
    adds, pcts = defaultdict(float), defaultdict(float)
    for m in modifiers:
        if not set(m["conditions"]).issubset(conditions) or rank < m["minimum_unit_rank"]:
            continue
        value = number(m["value"]) * (rank if m["per_rank"] else 1)
        for stat in m["stats"]:
            (adds if m["operation"] == "add" else pcts)[stat] += value
    result = {k: number(base[k]) for k in STATS}
    for k in STATS:
        a, p = adds[k], pcts[k] / 100
        result[k] = ((result[k] + a) * (1 + p) if order == "flat_then_percent"
                     else result[k] * (1 + p) + a)
    return result


def skill_support(rows, selected_nodes):
    """Conservative structural witness: fully buy every prerequisite ancestor.

    All SUBSET parents are included, so the witness does not rely on whether
    the subset threshold counts ranks or nodes. It is not a minimum-cost plan.
    """
    nodes = {r["node_key"]: r for r in rows if r["record_type"] == "node"}
    parents = defaultdict(list)
    for r in rows:
        if r["record_type"] == "prerequisite":
            if r["link_type"] not in {"REQUIRED", "SUBSET_REQUIRED"}:
                raise ValueError("Unsupported skill prerequisite type")
            parents[r["child_node_key"]].append(r["parent_node_key"])
    selected = set(selected_nodes)
    todo = list(selected)
    while todo:
        child = todo.pop()
        for parent in parents[child]:
            if parent not in selected:
                selected.add(parent)
                todo.append(parent)
    selected_skills = {nodes[n]["skill_key"] for n in selected}
    conflicts = [r["source_key"] for r in rows if r["record_type"] == "skill_lock"
                 and r["skill_key"] in selected_skills and r["locked_skill_key"] in selected_skills]
    plan = [{"node_key": n, "skill_name": nodes[n]["skill_name"],
             "level": int(number(nodes[n]["skill_max_level"])),
             "initial_points": int(number(nodes[n]["points_on_creation"])),
             "unlock_rank": number(nodes[n]["skill_unlocked_at_rank"])} for n in sorted(selected)]
    cost = sum(max(0, p["level"] - p["initial_points"]) for p in plan)
    return {"nodes": plan, "points_beyond_creation": cost,
            "selected_skill_lock_conflicts": conflicts,
            "within_declared_49_point_budget": cost <= 49,
            "scope": "structural witness only; not a simulated campaign or minimum-cost allocation"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ctw-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "work/infantry_campaign_comparison")
    args = parser.parse_args()
    ctw = args.ctw_root.resolve()
    lock = json.loads((STUDY / "source_lock.json").read_text())
    head = subprocess.check_output(["git", "-C", str(ctw), "rev-parse", "HEAD"], text=True).strip()
    if head != lock["git_commit"]:
        raise ValueError(f"Study requires {lock['git_commit']}, got {head}")
    if subprocess.check_output(["git", "-C", str(ctw), "status", "--porcelain", "--", "data", "context_catalog.json"], text=True).strip():
        raise ValueError("Source data checkout is dirty")
    catalog = json.loads((ctw / "context_catalog.json").read_text())
    if catalog["snapshot"] != lock["snapshot"]:
        raise ValueError("Source snapshot mismatch")
    inputs = set()

    def read(rel, delimiter=","):
        inputs.add(rel)
        return read_csv(ctw / rel, delimiter)

    audits = {}
    for dataset in ["unit_stats", "skill_trees", "technology_trees"]:
        rel = f"data/{dataset}/audit_report.json"
        inputs.add(rel)
        audit = json.loads((ctw / rel).read_text())
        if audit["status"].lower() != "passed":
            raise ValueError(f"Source audit failed: {dataset}")
        audits[dataset] = {"status": audit["status"], "warnings": audit.get("warnings", []),
                           "unresolved_scripted_cases": audit.get("unresolved_scripted_cases", 0)}
    units, race_memberships = {}, defaultdict(set)
    count = 0
    for p in sorted((ctw / "data/unit_stats/normalized").glob("*.csv")):
        for r in read(str(p.relative_to(ctw))):
            count += 1
            key = r["unit_key"]
            if key in units and any(units[key][k] != r[k] for k in STATS + ["entity_count", "attack_interval"]):
                raise ValueError(f"Cross-roster stat mismatch: {key}")
            units[key] = r
            race_memberships[key].add(p.name.split("__")[0])
    main_units = {r["unit"]: r for r in read("data/unit_stats/source_exports/db/main_units_tables/data__.tsv", "\t")}
    candidates = []
    for key, r in sorted(units.items()):
        if not (r["tactical_category"] == "infantry" and r["source_caste"] == "melee_infantry"
                and r["has_missile_weapon"] == "false" and r["is_renown"] == "false"
                and r["in_encyclopedia"] == "true" and r["is_large"] == "false"):
            continue
        cap = int(number(main_units[key]["campaign_cap"]))
        if cap != -1 and cap < 19:
            continue
        row = {"unit_key": key, "unit_name": r["unit_name"],
               "races": ";".join(sorted(race_memberships[key])),
               "campaign_cap_raw": cap, "repeatability_status": "static_cap_passes; campaign acquisition not fully verified",
               "entity_count": number(r["entity_count"]), "attack_interval": number(r["attack_interval"]),
               **{k: number(r[k]) for k in STATS}, **rates(r)}
        row["army_19_health"] = 19 * row["total_hp"]
        row["army_19_raw_rate"] = 19 * row["raw_rate"]
        row["army_19_ap_rate"] = 19 * row["ap_rate"]
        candidates.append(row)
    for r in candidates:
        r["base_pareto_frontier"] = not any(dominates(o, r) for o in candidates)
    write_csv(args.output / "base_candidates.csv", candidates)
    tiger = next(r for r in candidates if r["unit_key"] == "wh3_cp1_cth_inf_iron_claw_guandao")
    rankings = [{"metric": k, "tiger_value": tiger[k],
                 "competition_rank": 1 + sum(r[k] > tiger[k] + 1e-9 for r in candidates),
                 "candidate_count": len(candidates),
                 "leaders": [{"unit_key": r["unit_key"], "unit_name": r["unit_name"], "value": r[k]}
                             for r in sorted(candidates, key=lambda r: (-r[k], r["unit_key"]))[:5]]}
                for k in ["total_hp", "armour", "melee_attack", "melee_defence", "speed", "raw_rate", "ap_rate"]]
    configs = json.loads((STUDY / "profiles.json").read_text())
    ledger, scenario_rows, support, screen_residuals, omitted = [], [], {}, [], []
    for profile in configs["profiles"]:
        base = units[profile["unit_key"]]
        source_rows = {kind: read(profile[kind + "_path"]) for kind in ["skill", "technology"]}
        for kind in source_rows:
            variant_column = "node_set_key" if kind == "skill" else "variant_key"
            variants = {r[variant_column] for r in source_rows[kind] if r[variant_column]}
            if len(variants) != 1:
                raise ValueError(f"Explicit variant selection required: {profile['id']}")
        modifiers = []
        for rule in profile["rules"]:
            matches = [r for r in source_rows[rule["kind"]] if r["record_type"] == "effect"
                       and r["source_key"] == rule["source_key"]]
            if len(matches) != 1:
                raise ValueError(f"Ambiguous or absent modifier {rule['source_key']}")
            r = matches[0]
            if r["effect_description"] != rule["expected_description"] or number(r["effect_value"]) != rule["value"]:
                raise ValueError("Reviewed modifier changed")
            if "force_own" not in r["effect_scope"]:
                raise ValueError("Non-army scope cannot modify the infantry block")
            modifier = {**rule, "effect_key": r["effect_key"], "scope": r["effect_scope"],
                        "node_key": r["node_key"], "source_path": profile[rule["kind"] + "_path"],
                        "source_name": r.get("skill_name") or r.get("technology_name"),
                        "target_evidence": "explicit reviewed localization; engine unit-set junction absent"}
            modifiers.append(modifier)
            ledger.append({"profile": profile["id"], **modifier})
        selected_records = {(m["kind"], m["source_key"]) for m in modifiers}
        for kind, records in source_rows.items():
            for r in records:
                if r["record_type"] == "effect" and (kind, r["source_key"]) not in selected_records:
                    omitted.append({"profile": profile["id"], "kind": kind,
                                    "source_path": profile[kind + "_path"],
                                    "source_key": r["source_key"], "effect_key": r["effect_key"],
                                    "scope": r["effect_scope"], "value": r["effect_value"],
                                    "description": r["effect_description"],
                                    "status": "not applied; superseded level, other target, non-card effect, or unreviewed"})
        selected_nodes = {m["node_key"] for m in modifiers if m["kind"] == "skill"}
        witness = skill_support(source_rows["skill"], selected_nodes)
        if witness["selected_skill_lock_conflicts"] or not witness["within_declared_49_point_budget"]:
            raise ValueError(f"Unsupported skill allocation: {profile['id']}")
        tech_rows = source_rows["technology"]
        support[profile["id"]] = {"skill": witness,
            "research_qualification": "Selected effects are present in this faction's active tree; full campaign unlock feasibility remains unverified.",
            "technology_structural_conditions": [{k: r[k] for k in ["record_type", "technology_key", "node_key", "source_key"]}
                for r in tech_rows if r["record_type"] in {"script_lock", "scripted_requirement", "building_requirement", "technology_prerequisite"}]}
        for state in configs["states"]:
            results = [apply_modifiers(base, modifiers, set(state["conditions"]), state["unit_rank"], order)
                       for order in ["flat_then_percent", "percent_then_flat"]]
            out = {"profile": profile["id"], "unit_name": base["unit_name"], "state": state["id"],
                   "status": "known_modifier_subtotal; not a complete card or ceiling",
                   "unit_rank_condition": state["unit_rank"]}
            for k in STATS:
                out[k + "_min"] = min(r[k] for r in results)
                out[k + "_max"] = max(r[k] for r in results)
            for metric in ["raw_rate", "ap_rate"]:
                vals = [rates({**base, **r})[metric] for r in results]
                out[metric + "_min"] = min(vals)
                out[metric + "_max"] = max(vals)
            scenario_rows.append(out)
            if configs.get("screenshot_observation") and profile["id"] == "bhashiva_iron_claws" and state["id"] == "rank9_neutral":
                obs = configs["screenshot_observation"]
                for stat, observed in obs["stats"].items():
                    values = ([r["weapon_base_damage"] + r["weapon_ap_damage"] for r in results]
                              if stat == "weapon_strength" else [r[stat] for r in results])
                    screen_residuals.append({"stat": stat, "observed": observed,
                        "known_subtotal_min": min(values), "known_subtotal_max": max(values),
                        "unexplained_difference_min": observed - max(values),
                        "unexplained_difference_max": observed - min(values),
                        "note": "Rank 9 is a model condition, not inferred from screenshot; speed excluded because UI conversion unverified."})
    write_csv(args.output / "known_modifier_subtotals.csv", scenario_rows)
    write_csv(args.output / "screenshot_residuals.csv", screen_residuals)
    dump(args.output / "modifier_ledger.json", ledger)
    dump(args.output / "structural_support.json", support)
    write_csv(args.output / "unapplied_source_effects.csv", omitted)
    # These are source facts, not resolved ability-to-phase activation paths.
    phase_keys = {"wh3_cp1_unit_passive_ferocious_ambush", "wh3_cp1_lord_passive_white_tiger"}
    phase_evidence = {"status": "unapplied: ability activation/phase junction missing",
                      "warning": "Same identifier is an evidence lead, not a recovered activation relation"}
    for table, column in [("special_ability_phases_tables", "id"),
                          ("special_ability_phase_stat_effects_tables", "phase")]:
        phase_evidence[table] = [r for r in read(f"data/unit_stats/source_exports/db/{table}/data__.tsv", "\t")
                                 if r[column] in phase_keys]
    dump(args.output / "unapplied_phase_evidence.json", phase_evidence)
    sensitivity = []
    focus_keys = {p["unit_key"] for p in configs["profiles"]}
    for key in sorted(focus_keys):
        for engagement in [0.25, 0.5, 0.75, 1.0]:
            sensitivity.append({"unit_key": key, "engagement_fraction": engagement,
                                **rates(units[key], engagement)})
    write_csv(args.output / "engagement_sensitivity.csv", sensitivity)
    coverage = {"complete_campaign_ceiling": False,
        "available": ["normalized base cards", "skill effects and graph", "active technology effects and graph",
                      "static main_units campaign caps", "selected faction guides", "partial ability phase exports"],
        "blocking_gaps": [
            "Effect-to-bonus operation and unit-set membership junctions absent; reviewed localizations used only for explicit exemplars.",
            "Experience-to-stat tables absent; rank-conditioned bonuses modeled separately from missing native experience bonuses.",
            "Complete trait/item/ancillary effect acquisition and compatibility model absent.",
            "Ability phase membership, activation, cooldown and targeting relations incomplete; no sustainable or peak burst ceiling produced.",
            "Faction rituals, unit upgrades, recruitment-pool rules and repeatable bonus caps not reconstructed.",
            "Modifier order and UI rounding not verified; arithmetic sensitivities are not certified engine bounds.",
            "No exhaustive lord/faction/hero optimization or guaranteed campaign reachability of 19-unit blocks."],
        "excluded_from_claim": ["battle winner prediction", "global doomstack ranking", "theoretical subtotal as attainable unit card"]}
    dump(args.output / "coverage.json", coverage)
    summary = {"source_commit": head, "roster_rows": count, "unique_unit_keys": len(units),
        "small_melee_infantry_static_cap_candidates": len(candidates),
        "base_pareto_count": sum(r["base_pareto_frontier"] for r in candidates),
        "tiger_on_base_frontier": tiger["base_pareto_frontier"], "tiger_rankings": rankings,
        "profiles": len(configs["profiles"]), "reviewed_modifier_rows": len(ledger),
        "source_audits": audits, "ceiling_status": "unresolved"}
    dump(args.output / "summary.json", summary)
    dump(args.output / "input_hashes.json", {rel: hashlib.sha256((ctw / rel).read_bytes()).hexdigest() for rel in sorted(inputs)})
    (args.output / "README.md").write_text(render_report(summary, configs["profiles"], units, scenario_rows, screen_residuals))
    print(json.dumps({k: summary[k] for k in ["roster_rows", "unique_unit_keys", "small_melee_infantry_static_cap_candidates", "base_pareto_count", "tiger_on_base_frontier", "reviewed_modifier_rows", "ceiling_status"]}, indent=2))


if __name__ == "__main__":
    main()
