"""Checks for consequential aggregation and conditional-modifier mistakes."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("comparison", ROOT / "src/ctw_analysis/infantry_campaign_comparison.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.base = {k: 0.0 for k in m.STATS}
        self.base.update(weapon_base_damage=12, weapon_ap_damage=38,
                         melee_attack=40, melee_defence=46, speed=4.4,
                         entity_count=80, attack_interval=3.8)

    def modifier(self, **kw):
        return dict(dict(stats=["melee_attack"], value=6, operation="add",
                         conditions=[], minimum_unit_rank=0, per_rank=False), **kw)

    def test_missing_is_not_zero(self):
        with self.assertRaises(ValueError):
            m.number("")

    def test_ap_is_part_of_total_not_extra(self):
        self.assertAlmostEqual(m.rates(self.base)["ap_rate"], 800)
        self.assertAlmostEqual(m.rates(self.base)["raw_rate"], 80 * 50 / 3.8)
        self.assertAlmostEqual(m.rates(self.base, 0.25)["ap_rate"], 200)

    def test_conditional_bonuses_do_not_leak(self):
        bonuses = [self.modifier(conditions=["ambush"]), self.modifier(value=5, minimum_unit_rank=7)]
        r = m.apply_modifiers(self.base, bonuses, set(), 0, "flat_then_percent")
        self.assertEqual(r["melee_attack"], 40)
        r = m.apply_modifiers(self.base, bonuses, {"ambush"}, 9, "flat_then_percent")
        self.assertEqual(r["melee_attack"], 51)
        with self.assertRaises(ValueError):
            m.apply_modifiers(self.base, bonuses, {"attacking", "defending"}, 9, "flat_then_percent")

    def test_per_rank_weapon_bonus(self):
        bonus = self.modifier(stats=["weapon_base_damage", "weapon_ap_damage"],
                              value=3, operation="percent", per_rank=True)
        r = m.apply_modifiers(self.base, [bonus], set(), 9, "flat_then_percent")
        self.assertAlmostEqual(r["weapon_base_damage"] + r["weapon_ap_damage"], 63.5)

    def test_modifier_order_is_exposed(self):
        bonuses = [self.modifier(stats=["weapon_ap_damage"], value=9),
                   self.modifier(stats=["weapon_ap_damage"], value=17, operation="percent")]
        a = m.apply_modifiers(self.base, bonuses, set(), 0, "flat_then_percent")
        b = m.apply_modifiers(self.base, bonuses, set(), 0, "percent_then_flat")
        self.assertAlmostEqual(a["weapon_ap_damage"], 54.99)
        self.assertAlmostEqual(b["weapon_ap_damage"], 53.46)

    def test_equal_profiles_do_not_dominate(self):
        self.assertFalse(m.dominates({"x": 3}, {"x": 3}, ["x"]))
        self.assertTrue(m.dominates({"x": 4}, {"x": 3}, ["x"]))

    def test_reviewed_skill_levels_are_not_summed(self):
        config = json.loads((m.STUDY / "profiles.json").read_text())
        tiger = next(p for p in config["profiles"] if p["id"] == "bhashiva_iron_claws")
        rows = [r for r in tiger["rules"] if "Melee attack: %+n for Peasant Long" in r["expected_description"]]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["value"], 6)


if __name__ == "__main__":
    unittest.main()
