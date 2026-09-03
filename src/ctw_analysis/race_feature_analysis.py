from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
CTW_ROOT = Path(
    os.environ.get("CTW_ROOT", ANALYSIS_ROOT.parent / "computational-total-war")
).resolve()
UNIT_DIR = CTW_ROOT / "data" / "unit_stats"
SKILL_DIR = CTW_ROOT / "data" / "skill_trees"
OUT_DIR = ANALYSIS_ROOT / "work" / "race_feature_output"

RACES = [
    "beastmen", "bretonnia", "chaos_dwarfs", "daemons_of_chaos",
    "dark_elves", "dwarfs", "empire", "grand_cathay", "greenskins",
    "high_elves", "khorne", "kislev", "lizardmen", "norsca", "nurgle",
    "ogre_kingdoms", "skaven", "slaanesh", "tomb_kings", "tzeentch",
    "vampire_coast", "vampire_counts", "warriors_of_chaos", "wood_elves",
]

BLOCKS = {
    "geometry": ["movement", "deployment", "shock", "contact_authority"],
    "damage": [
        "melee_pressure", "missile_pressure", "bombardment",
        "target_solutions", "burst", "sustain",
    ],
    "survival": ["material_durability", "avoidance", "morale", "restoration"],
    "architecture": [
        "role_coverage", "elite_orientation", "battlefield_control",
        "command_magic",
    ],
}

UNIT_FEATURES = [
    "movement", "deployment", "shock", "contact_authority", "melee_pressure",
    "missile_pressure", "bombardment", "target_solutions", "burst", "sustain",
    "material_durability", "avoidance", "morale", "restoration",
    "battlefield_control",
]


def load_units() -> pd.DataFrame:
    frames = []
    for race in RACES:
        path = UNIT_DIR / "normalized" / f"{race}__wh3__8.1.1__ultra.csv"
        frame = pd.read_csv(path, low_memory=False)
        frame["race_slug"] = race
        frames.append(frame)
    all_units = pd.concat(frames, ignore_index=True)
    keep = (
        all_units["category"].ne("character")
        & ~all_units["is_renown"].fillna(False).astype(bool)
        & all_units["roster_scope"].isin(["race_core", "race_core_and_variant"])
    )
    units = all_units.loc[keep].copy()
    units = units[units["multiplayer_cost"].fillna(0).gt(0)].copy()
    return units


def attach_lookup_flags(units: pd.DataFrame) -> pd.DataFrame:
    attrs = pd.read_csv(
        UNIT_DIR / "lookups" / "unit_attributes__wh3__8.1.1__ultra.csv"
    )
    abilities = pd.read_csv(
        UNIT_DIR / "lookups" / "unit_abilities__wh3__8.1.1__ultra.csv"
    )
    contacts = pd.read_csv(
        UNIT_DIR / "lookups" / "unit_contact_effects__wh3__8.1.1__ultra.csv"
    )
    attr_map = attrs.groupby("unit_key")["attribute_key"].agg(set).to_dict()
    ability_map = abilities.groupby("unit_key")["ability_key"].agg(set).to_dict()
    contact_map = contacts.groupby("unit_key")["effect_key"].agg(set).to_dict()
    units["attrs"] = units["unit_key"].map(attr_map).apply(
        lambda x: x if isinstance(x, set) else set()
    )
    units["abilities"] = units["unit_key"].map(ability_map).apply(
        lambda x: x if isinstance(x, set) else set()
    )
    units["contacts"] = units["unit_key"].map(contact_map).apply(
        lambda x: x if isinstance(x, set) else set()
    )
    return units


def contains_any(values: set[str], terms: tuple[str, ...]) -> bool:
    return any(any(term in value for term in terms) for value in values)


def rank01(series: pd.Series, log: bool = False, invert: bool = False) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce").fillna(0).clip(lower=0)
    if log:
        x = np.log1p(x)
    # Zero is structural absence for the source statistics used in this study.
    # Ranking it with positive observations gives absent capabilities a phantom
    # percentile, especially when a column is sparse (explosion damage, range,
    # barrier health, and similar fields).
    positive = x.gt(0)
    out = pd.Series(0.0, index=x.index, dtype=float)
    if positive.any():
        ranked = x.loc[positive].rank(method="average", pct=True)
        if invert:
            ranked = 1 - ranked
        out.loc[positive] = ranked
    return out.clip(0, 1)


def bombardment_score(
    missile: pd.Series,
    range_rank: pd.Series,
    explosion_rank: pd.Series,
    artillery: pd.Series,
    penetration: pd.Series,
    raw_explosion_potency: pd.Series,
) -> pd.Series:
    """Score artillery/explosive projection without granting archers phantom blast."""
    bombardment_capable = missile * (
        artillery.gt(0) | raw_explosion_potency.gt(0)
    ).astype(float)
    return bombardment_capable * (
        0.30 * range_rank + 0.40 * explosion_rank
        + 0.20 * artillery + 0.10 * penetration
    )


def build_unit_scores(units: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    u = units.copy()
    numeric = [
        "entity_count", "hp_per_entity", "total_hp", "barrier_health", "armour",
        "shield_block_chance", "melee_defence", "leadership", "physical_resistance",
        "missile_resistance", "spell_resistance", "ward_save", "fire_resistance",
        "melee_attack", "weapon_base_damage", "weapon_ap_damage", "charge_bonus",
        "bonus_vs_infantry", "bonus_vs_large", "attack_interval", "max_splash_targets",
        "speed", "mass", "accuracy", "ammunition", "range", "reload_time",
        "missile_base_damage", "missile_ap_damage", "projectiles_per_shot",
        "shots_per_volley", "burst_size", "burst_shot_delay", "projectile_velocity",
        "projectile_spread", "marksmanship_bonus", "calibration_distance",
        "calibration_area", "explosion_base_damage", "explosion_ap_damage",
        "explosion_radius", "multiplayer_cost",
    ]
    for col in numeric:
        u[col] = pd.to_numeric(u[col], errors="coerce").fillna(0)

    attr_terms = {
        "vanguard": ("guerrilla_deploy",),
        "stalk": ("stalk", "snipe", "unspottable"),
        "flying": ("flying",),
        "terrain": ("strider", "ignore_trees"),
        "fire_move": ("mounted_fire_move",),
        "devastating_flanker": ("devastating_flanker", "glorious_charge"),
        "charge_defence": ("charge_defense", "charge_reflection"),
        "fear": ("causes_fear",),
        "terror": ("causes_terror",),
        "itp": ("immune_to_psychology",),
        "unbreakable": ("unbreakable",),
        "expendable": ("expendable",),
        "fatigue_immune": ("fatigue_immune",),
        "undead": ("undead", "construct"),
        "daemonic": ("daemonic",),
    }
    for name, terms in attr_terms.items():
        u[f"flag_{name}"] = u["attrs"].apply(lambda s: float(contains_any(s, terms)))

    u["flag_regen"] = u["abilities"].apply(
        lambda s: float(contains_any(s, ("regeneration", "the_hunger", "gorefeast", "regen")))
    )
    u["flag_snare"] = u["abilities"].apply(
        lambda s: float(contains_any(s, ("snare", "net", "chilling_aura", "petrifying", "burrow")))
    )
    u["flag_summon"] = u["abilities"].apply(
        lambda s: float(contains_any(s, ("summon", "raise_dead", "emergence", "another_takes")))
    )
    u["flag_formation"] = u["abilities"].apply(
        lambda s: float(contains_any(s, ("formation", "defensive_stance", "lance")))
    )
    u["flag_contact_control"] = u["contacts"].apply(
        lambda s: float(contains_any(s, (
            "poison", "frostbite", "suppressive", "soporific", "charmed",
            "slow_death", "sticky_webs", "blinded", "disrupted", "dampen",
        )))
    )
    u["flag_armour_control"] = u["contacts"].apply(
        lambda s: float(contains_any(s, ("sundered_armour", "weeping_blade", "flammable")))
    )
    u["flag_morale_contact"] = u["contacts"].apply(
        lambda s: float(contains_any(s, ("morale", "discouraged")))
    )

    missile = u["has_missile_weapon"].fillna(False).astype(bool).astype(float)
    ap_total = u["weapon_ap_damage"] + u["missile_ap_damage"] + u["explosion_ap_damage"]
    base_total = u["weapon_base_damage"] + u["missile_base_damage"] + u["explosion_base_damage"]
    u["ap_ratio"] = ap_total / (ap_total + base_total).replace(0, np.nan)
    u["ap_ratio"] = u["ap_ratio"].fillna(0)
    u["melee_rate"] = (
        (u["weapon_base_damage"] + u["weapon_ap_damage"])
        / u["attack_interval"].replace(0, np.nan)
    ).fillna(0)
    projectile_mult = (
        u["projectiles_per_shot"].clip(lower=1)
        * u["shots_per_volley"].clip(lower=1)
        * u["burst_size"].clip(lower=1)
    )
    u["missile_launch_power"] = (
        (u["missile_base_damage"] + u["missile_ap_damage"])
        * projectile_mult
        * np.sqrt(u["entity_count"].clip(lower=1))
        / u["reload_time"].replace(0, np.nan)
    ).fillna(0) * missile
    u["missile_reserve"] = u["missile_launch_power"] * u["ammunition"] * missile
    u["explosion_potency"] = (
        (u["explosion_base_damage"] + u["explosion_ap_damage"])
        * np.square(u["explosion_radius"])
    )
    u["anti_peak"] = u[["bonus_vs_infantry", "bonus_vs_large", "missile_bonus_vs_infantry", "missile_bonus_vs_large"]].max(axis=1)
    u["anti_breadth"] = (
        (u[["bonus_vs_infantry", "missile_bonus_vs_infantry"]].max(axis=1) > 0).astype(float)
        + (u[["bonus_vs_large", "missile_bonus_vs_large"]].max(axis=1) > 0).astype(float)
    ) / 2
    u["resistance_sum"] = (
        u["physical_resistance"].clip(lower=0)
        + u["missile_resistance"].clip(lower=0)
        + u["spell_resistance"].clip(lower=0)
        + u["ward_save"].clip(lower=0)
    )

    q = {}
    log_cols = {
        "entity_count", "hp_per_entity", "total_hp", "mass", "melee_rate",
        "missile_launch_power", "missile_reserve", "explosion_potency",
    }
    derived = [
        "ap_ratio", "melee_rate", "missile_launch_power", "missile_reserve",
        "explosion_potency", "anti_peak", "resistance_sum",
    ]
    for col in set(numeric + derived):
        q[col] = rank01(u[col], log=col in log_cols)

    artillery = (u["category"].eq("artillery") | u["unit_class"].eq("art_fld")).astype(float)
    penetration = u["projectile_penetration_class"].fillna("").ne("").astype(float)
    magical = (
        u["melee_is_magical"].eq(True)
        | u["missile_is_magical"].eq(True)
    ).astype(float)
    flaming = (
        u["melee_is_flaming"].eq(True)
        | u["missile_is_flaming"].eq(True)
    ).astype(float)

    u["movement"] = (
        0.75 * q["speed"] + 0.15 * u["flag_terrain"] + 0.10 * u["flag_fire_move"]
    )
    u["deployment"] = (
        0.30 * u["flag_vanguard"] + 0.25 * u["flag_stalk"]
        + 0.30 * u["flag_flying"] + 0.15 * u["flag_terrain"]
    )
    u["shock"] = (
        0.30 * q["speed"] + 0.30 * q["charge_bonus"] + 0.25 * q["mass"]
        + 0.15 * u["flag_devastating_flanker"]
    )
    u["contact_authority"] = (
        0.40 * q["mass"] + 0.20 * q["anti_peak"]
        + 0.20 * u["flag_charge_defence"]
        + 0.10 * u["is_large"].fillna(False).astype(bool).astype(float)
        + 0.10 * u["is_single_entity"].fillna(False).astype(bool).astype(float)
    )
    u["melee_pressure"] = (
        0.30 * q["melee_attack"] + 0.35 * q["melee_rate"]
        + 0.20 * q["weapon_ap_damage"] + 0.15 * q["anti_peak"]
    )
    delivery = (
        0.35 * q["accuracy"] + 0.25 * q["projectile_velocity"]
        + 0.20 * (1 - q["projectile_spread"]) + 0.20 * q["marksmanship_bonus"]
    )
    u["missile_pressure"] = missile * (
        0.50 * q["missile_launch_power"] + 0.20 * q["range"]
        + 0.15 * delivery + 0.15 * q["ammunition"]
    )
    u["bombardment"] = bombardment_score(
        missile=missile,
        range_rank=q["range"],
        explosion_rank=q["explosion_potency"],
        artillery=artillery,
        penetration=penetration,
        raw_explosion_potency=u["explosion_potency"],
    )
    u["target_solutions"] = (
        0.35 * q["ap_ratio"] + 0.20 * q["anti_peak"] + 0.15 * u["anti_breadth"]
        + 0.10 * magical + 0.05 * flaming + 0.15 * u["flag_armour_control"]
    )
    missile_alpha = q["missile_launch_power"] * (
        (u["shots_per_volley"] > 1).astype(float) + (u["burst_size"] > 1).astype(float)
    ).clip(lower=0.5)
    u["burst"] = (
        0.35 * q["charge_bonus"] + 0.20 * q["mass"]
        + 0.25 * missile_alpha + 0.20 * q["explosion_potency"]
    )
    u["sustain"] = (
        0.35 * q["melee_rate"] + 0.30 * q["missile_reserve"]
        + 0.15 * q["ammunition"] * missile + 0.10 * u["flag_fatigue_immune"]
        + 0.10 * u["flag_regen"]
    )
    u["material_durability"] = (
        0.22 * q["total_hp"] + 0.08 * q["hp_per_entity"] + 0.18 * q["armour"]
        + 0.20 * q["melee_defence"] + 0.12 * q["shield_block_chance"]
        + 0.20 * q["resistance_sum"]
    )
    u["avoidance"] = (
        0.25 * q["speed"] + 0.15 * q["range"] * missile
        + 0.15 * u["flag_stalk"] + 0.15 * u["flag_flying"]
        + 0.10 * u["flag_terrain"] + 0.20 * q["missile_resistance"]
    )
    anchor = (
        0.55 * q["leadership"] + 0.20 * u["flag_itp"]
        + 0.25 * u["flag_unbreakable"]
    )
    redundancy = (
        0.45 * u["flag_expendable"] + 0.30 * (1 - q["multiplayer_cost"])
        + 0.25 * q["entity_count"]
    )
    u["morale"] = 0.65 * anchor + 0.35 * redundancy
    u["restoration"] = (
        0.50 * q["barrier_health"] + 0.35 * u["flag_regen"] + 0.15 * u["flag_summon"]
    )
    u["battlefield_control"] = (
        0.18 * u["flag_contact_control"] + 0.12 * u["flag_armour_control"]
        + 0.12 * u["flag_morale_contact"] + 0.12 * u["flag_snare"]
        + 0.12 * u["flag_formation"] + 0.12 * u["flag_charge_defence"]
        + 0.10 * u["flag_fear"] + 0.12 * u["flag_terror"]
    )

    for feature in UNIT_FEATURES:
        u[feature] = u[feature].clip(0, 1)
    return u, UNIT_FEATURES


def role_name(row: pd.Series) -> str:
    if row["category"] == "artillery" or row["unit_class"] == "art_fld":
        return "artillery"
    caste = str(row["caste"])
    if caste in {"missile_infantry", "missile_cavalry"}:
        return "missile"
    if caste in {"melee_cavalry", "monstrous_cavalry", "chariot"}:
        return "mobile_shock"
    if caste in {"monster", "war_beast"}:
        return "monster"
    if caste == "monstrous_infantry":
        return "monstrous_infantry"
    return "line_infantry"


def aggregate_triplet(
    units: pd.DataFrame, feature: str, global_units: pd.DataFrame
) -> tuple[float, float, float, float]:
    positive = global_units.loc[global_units[feature] > 0, feature]
    threshold = float(positive.quantile(0.65)) if not positive.empty else 0.0
    global_cells = set(
        zip(
            global_units.loc[
                (global_units[feature] > 0) & (global_units[feature] >= threshold), "role"
            ],
            global_units.loc[
                (global_units[feature] > 0) & (global_units[feature] >= threshold), "cost_band"
            ],
        )
    )
    race_cells = set(
        zip(
            units.loc[(units[feature] > 0) & (units[feature] >= threshold), "role"],
            units.loc[(units[feature] > 0) & (units[feature] >= threshold), "cost_band"],
        )
    )
    cell_coverage = len(race_cells & global_cells) / max(1, len(global_cells))
    positive_share = float((units[feature] > 0).mean())
    high_share = float(((units[feature] > 0) & (units[feature] >= threshold)).mean())
    breadth = 0.40 * cell_coverage + 0.30 * positive_share + 0.30 * high_share
    top_n = max(1, min(3, math.ceil(len(units) * 0.08)))
    ceiling = float(units[feature].nlargest(top_n).mean())
    grid = np.quantile(global_units["multiplayer_cost"], np.linspace(0.10, 0.95, 12))
    frontier = []
    for cap in grid:
        eligible = units.loc[units["multiplayer_cost"] <= cap, feature]
        frontier.append(float(eligible.max()) if not eligible.empty else 0.0)
    access = float(np.mean(frontier))
    campaign_frontier = []
    for tier_cap in range(1, 6):
        eligible = units.loc[units["tier"] <= tier_cap, feature]
        campaign_frontier.append(float(eligible.max()) if not eligible.empty else 0.0)
    campaign_access = float(np.mean(campaign_frontier))
    return breadth, ceiling, access, campaign_access


def generic_command_metadata() -> dict[str, dict[str, object]]:
    index = pd.read_csv(SKILL_DIR / "character_index__wh3__8.1.1.csv")
    output: dict[str, dict[str, object]] = {}
    lore_patterns = {
        "beasts": r"magic_beasts", "death": r"magic_death", "shadows": r"magic_shadow",
        "wild": r"magic_wild", "life": r"magic_life", "heavens": r"magic_heavens",
        "light": r"magic_light", "metal": r"magic_(metal|gold)", "fire": r"magic_fire",
        "vampires": r"magic_(vampires|strigoi)", "nehekhara": r"magic_nehekhara",
        "deep": r"magic_(deep|deeps)", "tzeentch": r"magic_tzeentch",
        "nurgle": r"magic_nurgle", "slaanesh": r"magic_slaanesh", "yin": r"magic_yin",
        "yang": r"magic_yang", "maw": r"magic_(maw|great_maw)", "ice": r"magic_ice",
        "tempest": r"magic_tempest", "hag": r"magic_hag", "high": r"magic_high",
        "dark": r"magic_dark", "plague": r"magic_plague", "ruin": r"magic_ruin",
        "stealth": r"magic_stealth", "little_waagh": r"magic_little_waagh",
        "big_waagh": r"magic_big_waagh", "hashut": r"magic_hashut",
    }
    category_patterns = {
        "healing": re.compile(r"heal|regrowth|earth_blood|invocation|nehek|fleshy_abundance|life_bloom", re.I),
        "summoning": re.compile(r"summon|raise_dead|awakening|vortex_beast|manticore", re.I),
        "control": re.compile(r"net|slow|curse|hex|miasma|acquiescence|enfeebling|withering|blizzard|pestilence", re.I),
        "protection": re.compile(r"shield|ward|protection|flesh_to_stone|pha.*protection|transmutation_of_lead", re.I),
        "damage": re.compile(r"fireball|wind_of_death|pendulum|pit_of_shades|burning_head|comet|lightning|flames|spirit_leech|searing_doom", re.I),
    }
    for race in RACES:
        rows = index[
            (index["race_slug"] == race)
            & ~index["is_legendary_lord"].astype(bool)
            & ~index["is_unique_agent"].astype(bool)
        ]
        if rows.empty and race == "daemons_of_chaos":
            rows = index[index["race_slug"] == race]
        generic_count = 0
        casters = 0
        lores: set[str] = set()
        categories: set[str] = set()
        for rel in rows["relative_path"]:
            path = SKILL_DIR / rel
            first = pd.read_csv(path, nrows=1).iloc[0]
            if not bool(first.get("is_recruitable", False)) or not bool(first.get("show_in_ui", False)):
                continue
            generic_count += 1
            if not bool(first.get("is_caster", False)):
                continue
            casters += 1
            lore = str(first.get("magic_lore", "")).lower()
            tree = pd.read_csv(path, usecols=["record_type", "skill_key", "skill_name"])
            spell_nodes = tree.loc[tree["record_type"].eq("node"), ["skill_key", "skill_name"]].drop_duplicates()
            spell_keys = " ".join(spell_nodes["skill_key"].fillna("").astype(str)).lower()
            command_nodes = spell_nodes[
                spell_nodes["skill_key"].fillna("").str.contains(
                    r"magic|spell|rune|prayer|invocation|nehek", case=False, regex=True
                )
            ]
            if command_nodes.empty:
                command_text = ""
            else:
                command_text = " ".join(
                    command_nodes.fillna("").astype(str).apply(
                        lambda row: " ".join(row.tolist()), axis=1
                    ).tolist()
                ).lower()
            lore_text = lore + " " + spell_keys
            for label, pattern in lore_patterns.items():
                if re.search(pattern, lore_text):
                    lores.add(label)
            for category, pattern in category_patterns.items():
                if pattern.search(command_text):
                    categories.add(category)
        output[race] = {
            "generic_count": generic_count,
            "casters": casters,
            "lores": sorted(lores),
            "categories": sorted(categories),
        }
    return output


def aggregate_features(u: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    u = u.copy()
    u["role"] = u.apply(role_name, axis=1)
    u["cost_band"] = pd.cut(
        u["multiplayer_cost"], bins=[-np.inf, 600, 1000, 1500, np.inf],
        labels=["cheap", "mid", "high", "elite"],
    ).astype(str)
    rows = []
    details: dict[str, object] = {}
    command = generic_command_metadata()
    all_roles = [
        "line_infantry", "missile", "mobile_shock", "monster",
        "monstrous_infantry", "artillery",
    ]
    for race in RACES:
        r = u[u["race_slug"] == race].copy()
        row: dict[str, float | str] = {"race": race}
        race_detail: dict[str, object] = {"n_units": len(r)}
        for feature in UNIT_FEATURES:
            b, c, a, campaign_a = aggregate_triplet(r, feature, u)
            row[f"{feature}__breadth"] = b
            row[f"{feature}__ceiling"] = c
            row[f"{feature}__access"] = a
            row[f"{feature}__campaign_access"] = campaign_a
            race_detail[feature] = {
                "breadth": b,
                "ceiling": c,
                "access": a,
                "campaign_access": campaign_a,
            }

        role_presence = {role: float((r["role"] == role).any()) for role in all_roles}
        role_breadth = float(np.mean(list(role_presence.values())))
        role_cost_cells = r[["role", "cost_band"]].drop_duplicates().shape[0] / (len(all_roles) * 4)
        counts = r["role"].value_counts().reindex(all_roles, fill_value=0).to_numpy(float)
        probs = counts / counts.sum()
        entropy = float(-(probs[probs > 0] * np.log(probs[probs > 0])).sum() / np.log(len(all_roles)))
        row["role_coverage__breadth"] = role_breadth
        row["role_coverage__ceiling"] = entropy
        row["role_coverage__access"] = role_cost_cells

        median_cost = float(r["multiplayer_cost"].median())
        elite_share = float((r["multiplayer_cost"] > u["multiplayer_cost"].quantile(0.75)).mean())
        feature_mean = r[UNIT_FEATURES].mean(axis=1)
        corr = float(pd.Series(feature_mean).corr(r["multiplayer_cost"], method="spearman"))
        if not np.isfinite(corr):
            corr = 0.0
        champion_costs = []
        for feature in UNIT_FEATURES:
            idx = r[feature].idxmax()
            champion_costs.append(float(r.loc[idx, "multiplayer_cost"]))
        champion_elite = float(np.mean(np.array(champion_costs) > u["multiplayer_cost"].quantile(0.75)))
        row["elite_orientation__breadth"] = elite_share
        row["elite_orientation__ceiling"] = champion_elite
        row["elite_orientation__access"] = corr

        cmd = command[race]
        caster_access = min(1.0, float(cmd["casters"]) / 4.0)
        lore_breadth = min(1.0, len(cmd["lores"]) / 8.0)
        category_breadth = len(cmd["categories"]) / 5.0
        row["command_magic__breadth"] = lore_breadth
        row["command_magic__ceiling"] = category_breadth
        row["command_magic__access"] = caster_access

        race_detail["role_coverage"] = role_presence
        race_detail["elite_orientation"] = {
            "median_cost": median_cost,
            "elite_share": elite_share,
            "champion_elite": champion_elite,
            "cost_quality_corr": corr,
        }
        race_detail["command_magic"] = cmd
        race_detail["campaign_access"] = {
            "proxy": "cumulative best capability across unit tiers 1 through 5",
            "tier_counts": {
                str(int(tier)): int(count)
                for tier, count in r["tier"].value_counts().sort_index().items()
            },
            "scope": "race_core and race_core_and_variant units only",
            "known_missing": "exact building, technology, resource, landmark, and scripted recruitment gates",
        }
        details[race] = race_detail
        rows.append(row)
    return pd.DataFrame(rows).set_index("race"), details


def block_weighted_matrix(
    features: pd.DataFrame,
    include_campaign_access: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scaled = pd.DataFrame(index=features.index)
    weighted = pd.DataFrame(index=features.index)
    for block, members in BLOCKS.items():
        cols = [
            c for c in features.columns
            if c.split("__", 1)[0] in members
            and (include_campaign_access or not c.endswith("__campaign_access"))
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
            # total weight. Where campaign access exists, split the original
            # access allocation between cost and campaign progression.
            feature_weight = 1 / math.sqrt(3 * len(members))
            has_campaign = any(c.endswith("__campaign_access") for c in feature_cols)
            view_weights = {
                "breadth": 0.50,
                "ceiling": 0.25,
                "access": 0.125 if has_campaign else 0.25,
                "campaign_access": 0.125,
            }
            for col in feature_cols:
                view = col.split("__", 1)[1]
                weighted[col] = (
                    block_scaled[col] * feature_weight * math.sqrt(view_weights[view])
                )
    return scaled, weighted


def clustering_report(weighted: pd.DataFrame) -> dict[str, object]:
    X = weighted.to_numpy()
    silhouette = {}
    solutions = {}
    for k in range(4, 9):
        labels = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X)
        silhouette[str(k)] = float(silhouette_score(X, labels))
        solutions[str(k)] = {
            race: int(label) for race, label in zip(weighted.index, labels, strict=True)
        }
    best_k = max(silhouette, key=silhouette.get)

    rng = np.random.default_rng(811)
    consensus = np.zeros((len(weighted), len(weighted)), float)
    runs = 500
    columns = np.arange(X.shape[1])
    for _ in range(runs):
        sampled = rng.choice(columns, size=max(2, int(0.8 * len(columns))), replace=False)
        noise = rng.normal(1.0, 0.08, size=len(sampled))
        Xp = X[:, sampled] * noise
        labels = KMeans(n_clusters=int(best_k), n_init=10, random_state=int(rng.integers(1_000_000))).fit_predict(Xp)
        consensus += labels[:, None] == labels[None, :]
    consensus /= runs
    consensus_distance = 1 - consensus
    np.fill_diagonal(consensus_distance, 0)
    final_labels = fcluster(
        linkage(squareform(consensus_distance, checks=False), method="average"),
        t=int(best_k), criterion="maxclust",
    ) - 1
    distance = squareform(pdist(X, metric="euclidean"))
    nearest = {}
    for i, race in enumerate(weighted.index):
        order = np.argsort(distance[i])
        nearest[race] = [
            {"race": weighted.index[j], "distance": float(distance[i, j]), "consensus": float(consensus[i, j])}
            for j in order[1:5]
        ]
    return {
        "silhouette": silhouette,
        "best_k": int(best_k),
        "ward_solutions": solutions,
        "consensus_labels": {
            race: int(label) for race, label in zip(weighted.index, final_labels, strict=True)
        },
        "nearest": nearest,
        "consensus": consensus.tolist(),
        "races": weighted.index.tolist(),
    }


def composite_scores(
    features: pd.DataFrame,
    include_campaign_access: bool = True,
) -> pd.DataFrame:
    out = pd.DataFrame(index=features.index)
    for block, members in BLOCKS.items():
        for feature in members:
            cols = [c for c in features.columns if c.startswith(feature + "__")]
            has_campaign = (
                include_campaign_access
                and f"{feature}__campaign_access" in features.columns
            )
            vals = 0.50 * features[f"{feature}__breadth"]
            vals += 0.25 * features[f"{feature}__ceiling"]
            if has_campaign:
                vals += 0.125 * features[f"{feature}__access"]
                vals += 0.125 * features[f"{feature}__campaign_access"]
            else:
                vals += 0.25 * features[f"{feature}__access"]
            lo, hi = vals.min(), vals.max()
            out[feature] = 100 * (vals - lo) / (hi - lo if hi > lo else 1)
        out[f"block_{block}"] = out[members].mean(axis=1)
    return out


def configure_paths(ctw_root: Path, out_dir: Path) -> None:
    global CTW_ROOT, UNIT_DIR, SKILL_DIR, OUT_DIR
    CTW_ROOT = ctw_root.resolve()
    UNIT_DIR = CTW_ROOT / "data" / "unit_stats"
    SKILL_DIR = CTW_ROOT / "data" / "skill_trees"
    OUT_DIR = out_dir.resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def validate_source_lock() -> None:
    lock = json.loads((ANALYSIS_ROOT / "source_lock.json").read_text(encoding="utf-8"))
    catalog_path = CTW_ROOT / "context_catalog.json"
    if not catalog_path.exists():
        raise FileNotFoundError(
            f"CTW context catalog not found at {catalog_path}. Pass --ctw-root."
        )
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    snapshot = catalog["snapshot"]
    expected = lock["snapshot"]
    for key in ("patch", "steam_build_id", "unit_scale"):
        if snapshot.get(key) != expected.get(key):
            raise RuntimeError(
                f"Source snapshot mismatch for {key}: "
                f"expected {expected.get(key)!r}, found {snapshot.get(key)!r}"
            )
    try:
        actual_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=CTW_ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        actual_sha = ""
    if actual_sha and actual_sha != lock["git_commit"]:
        raise RuntimeError(
            f"CTW commit mismatch: expected {lock['git_commit']}, found {actual_sha}"
        )


def main(ctw_root: Path = CTW_ROOT, out_dir: Path = OUT_DIR) -> None:
    configure_paths(ctw_root, out_dir)
    validate_source_lock()
    units = attach_lookup_flags(load_units())
    unit_scores, _ = build_unit_scores(units)
    features, details = aggregate_features(unit_scores)
    scaled, weighted = block_weighted_matrix(features, include_campaign_access=True)
    _, weighted_cost_only = block_weighted_matrix(
        features, include_campaign_access=False
    )
    report = clustering_report(weighted)
    report_cost_only = clustering_report(weighted_cost_only)
    composites = composite_scores(features, include_campaign_access=True)
    composites_cost_only = composite_scores(
        features, include_campaign_access=False
    )
    features.to_csv(OUT_DIR / "race_feature_triplets.csv")
    scaled.to_csv(OUT_DIR / "race_feature_triplets_scaled.csv")
    weighted.to_csv(OUT_DIR / "race_feature_matrix_weighted.csv")
    weighted_cost_only.to_csv(OUT_DIR / "race_feature_matrix_weighted_cost_only.csv")
    composites.to_csv(OUT_DIR / "race_feature_composites_0_100.csv")
    composites_cost_only.to_csv(
        OUT_DIR / "race_feature_composites_cost_only_0_100.csv"
    )
    unit_scores.to_csv(OUT_DIR / "eligible_unit_scores.csv", index=False)
    (OUT_DIR / "race_details.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
    (OUT_DIR / "clustering_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT_DIR / "clustering_report_cost_only.json").write_text(
        json.dumps(report_cost_only, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "eligible_units": len(unit_scores),
        "feature_dimensions": len(features.columns),
        "best_k": report["best_k"],
        "silhouette": report["silhouette"],
        "consensus_labels": report["consensus_labels"],
        "cost_only_sensitivity": {
            "feature_dimensions": len(weighted_cost_only.columns),
            "best_k": report_cost_only["best_k"],
            "silhouette": report_cost_only["silhouette"],
            "consensus_labels": report_cost_only["consensus_labels"],
        },
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build the patch-locked CTW race strategy feature space."
    )
    parser.add_argument(
        "--ctw-root", type=Path, default=CTW_ROOT,
        help="Path to a Computational Total War checkout (default: sibling repo).",
    )
    parser.add_argument(
        "--out-dir", type=Path, default=OUT_DIR,
        help="Generated output directory (default: work/race_feature_output).",
    )
    args = parser.parse_args()
    main(args.ctw_root, args.out_dir)
