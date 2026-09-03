import unittest

import pandas as pd

from ctw_analysis.race_feature_analysis import (
    aggregate_triplet,
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
        self.assertEqual(ranked.iloc[1], 0.5)
        self.assertEqual(ranked.iloc[2], 0.0)


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


class CampaignAccessTests(unittest.TestCase):
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

    def test_early_capability_scores_above_late_capability(self) -> None:
        global_units = self.units([1, 5], [1.0, 1.0])
        early = self.units([1], [1.0])
        late = self.units([5], [1.0])
        *_, early_access = aggregate_triplet(early, "capability", global_units)
        *_, late_access = aggregate_triplet(late, "capability", global_units)
        self.assertEqual(early_access, 1.0)
        self.assertEqual(late_access, 0.2)


if __name__ == "__main__":
    unittest.main()
