import unittest

import pandas as pd

from ctw_analysis.race_feature_analysis import (
    BLOCKS,
    aggregate_unit_views,
    block_weighted_matrix,
    bombardment_score,
    rank01,
)


class Rank01Tests(unittest.TestCase):
    def test_structural_zeros_remain_zero(self) -> None:
        ranked = rank01(pd.Series([0.0, 0.0, 10.0, 20.0]))
        self.assertEqual(ranked.iloc[0], 0.0)
        self.assertEqual(ranked.iloc[1], 0.0)
        self.assertEqual(ranked.iloc[2], 0.5)
        self.assertEqual(ranked.iloc[3], 1.0)

    def test_all_zero_input_remains_zero(self) -> None:
        ranked = rank01(pd.Series([0.0, 0.0, 0.0]))
        self.assertTrue(ranked.eq(0.0).all())

    def test_positive_ties_receive_average_rank(self) -> None:
        ranked = rank01(pd.Series([0.0, 10.0, 10.0, 20.0]))
        self.assertAlmostEqual(ranked.iloc[1], 0.5)
        self.assertAlmostEqual(ranked.iloc[2], 0.5)
        self.assertEqual(ranked.iloc[3], 1.0)

    def test_log_transform_preserves_structural_zero(self) -> None:
        ranked = rank01(pd.Series([0.0, 1.0, 100.0]), log=True)
        self.assertEqual(ranked.iloc[0], 0.0)
        self.assertEqual(ranked.iloc[1], 0.5)
        self.assertEqual(ranked.iloc[2], 1.0)

    def test_inversion_does_not_turn_absence_into_capability(self) -> None:
        ranked = rank01(pd.Series([0.0, 10.0, 20.0]), invert=True)
        self.assertEqual(ranked.iloc[0], 0.0)
        self.assertEqual(ranked.iloc[1], 1.0)
        self.assertEqual(ranked.iloc[2], 0.5)


class BombardmentTests(unittest.TestCase):
    def test_non_explosive_non_artillery_missile_has_no_bombardment(self) -> None:
        score = bombardment_score(
            missile=pd.Series([1.0]),
            range_rank=pd.Series([1.0]),
            explosion_rank=pd.Series([0.0]),
            artillery=pd.Series([0.0]),
            penetration=pd.Series([0.0]),
            raw_explosion_potency=pd.Series([0.0]),
        )
        self.assertEqual(score.iloc[0], 0.0)

    def test_non_explosive_artillery_retains_projection_score(self) -> None:
        score = bombardment_score(
            missile=pd.Series([1.0]),
            range_rank=pd.Series([0.8]),
            explosion_rank=pd.Series([0.0]),
            artillery=pd.Series([1.0]),
            penetration=pd.Series([1.0]),
            raw_explosion_potency=pd.Series([0.0]),
        )
        self.assertAlmostEqual(score.iloc[0], 0.54)

    def test_explosive_non_artillery_projectile_is_included(self) -> None:
        score = bombardment_score(
            missile=pd.Series([1.0]),
            range_rank=pd.Series([0.5]),
            explosion_rank=pd.Series([0.75]),
            artillery=pd.Series([0.0]),
            penetration=pd.Series([0.0]),
            raw_explosion_potency=pd.Series([10.0]),
        )
        self.assertAlmostEqual(score.iloc[0], 0.45)

    def test_non_missile_unit_is_always_zero(self) -> None:
        score = bombardment_score(
            missile=pd.Series([0.0]),
            range_rank=pd.Series([1.0]),
            explosion_rank=pd.Series([1.0]),
            artillery=pd.Series([1.0]),
            penetration=pd.Series([1.0]),
            raw_explosion_potency=pd.Series([10.0]),
        )
        self.assertEqual(score.iloc[0], 0.0)


class UnitTierSensitivityTests(unittest.TestCase):
    @staticmethod
    def units(tiers: list[int], scores: list[float]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "capability": scores,
                "role": ["line_infantry"] * len(tiers),
                "cost_band": ["cheap"] * len(tiers),
                "multiplayer_cost": [500] * len(tiers),
                "tier": tiers,
            }
        )

    def test_lower_unit_tier_scores_above_higher_unit_tier(self) -> None:
        global_units = self.units([1, 5], [1.0, 1.0])
        early = self.units([1], [1.0])
        late = self.units([5], [1.0])
        *_, lower_tier = aggregate_unit_views(early, "capability", global_units)
        *_, higher_tier = aggregate_unit_views(late, "capability", global_units)
        self.assertEqual(lower_tier, 1.0)
        self.assertEqual(higher_tier, 0.2)

    def test_unit_tier_view_is_excluded_from_primary_matrix(self) -> None:
        feature_names = [
            feature
            for members in BLOCKS.values()
            for feature in members
        ]
        rows = []
        for offset in (0.0, 0.1):
            row = {}
            for feature in feature_names:
                row[f"{feature}__breadth"] = 0.2 + offset
                row[f"{feature}__ceiling"] = 0.4 + offset
                row[f"{feature}__access"] = 0.6 + offset
                if feature not in {"role_coverage", "elite_orientation", "command_magic"}:
                    row[f"{feature}__unit_tier_sensitivity"] = 0.8 + offset
            rows.append(row)
        features = pd.DataFrame(rows, index=["a", "b"])
        _, primary = block_weighted_matrix(features)
        _, sensitivity = block_weighted_matrix(
            features, include_unit_tier_sensitivity=True
        )
        self.assertEqual(len(primary.columns), 54)
        self.assertEqual(len(sensitivity.columns), 69)
        self.assertFalse(
            any(column.endswith("__unit_tier_sensitivity") for column in primary)
        )


if __name__ == "__main__":
    unittest.main()
