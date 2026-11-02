import math
import unittest

from nfl_model.math_utils import (american_to_decimal, binary_ev, bootstrap_ci, brier,
                                  calibration_error, cluster_bootstrap_ci, decimal_to_american,
                                  devig_two_way, joint_bounds, log_loss, max_drawdown_units,
                                  pearson, phi, push_aware_ev, ranks, settle_binary,
                                  settle_parlay, spearman, wilson)


class MathTests(unittest.TestCase):
    def test_american_conversion(self):
        self.assertEqual(american_to_decimal(-110), 1 + 100 / 110)
        self.assertEqual(american_to_decimal(150), 2.5)
        self.assertEqual(decimal_to_american(2.5), 150)
        self.assertEqual(decimal_to_american(1.5), -200)
        self.assertIsNone(decimal_to_american(1))
        for bad in (0, 50, -50, float("nan")):
            with self.assertRaises(ValueError):
                american_to_decimal(bad)

    def test_devig(self):
        p = devig_two_way([1.9090909090909092, 1.9090909090909092])
        self.assertAlmostEqual(sum(p), 1)
        self.assertAlmostEqual(p[0], 0.5)
        self.assertIsNone(devig_two_way([1.0, 2.0]))

    def test_ev_and_push(self):
        self.assertAlmostEqual(binary_ev(0.55, 2.0), 0.1)
        self.assertAlmostEqual(push_aware_ev(0.4, 0.4, 1.9), -0.04)
        self.assertAlmostEqual(push_aware_ev(0.5, 0.5, 2.0), 0)
        self.assertIsNone(push_aware_ev(0.7, 0.7, 2.0))

    def test_binary_settlement(self):
        self.assertAlmostEqual(settle_binary("win", 1.9), 0.9)
        self.assertEqual(settle_binary("loss", 1.9), -1)
        self.assertEqual(settle_binary("push", 1.9), 0)
        self.assertEqual(settle_binary("void", 1.9), 0)
        with self.assertRaises(ValueError):
            settle_binary("unknown", 2)

    def test_parlay_settlement(self):
        self.assertEqual(settle_parlay(["win", "win"], [2, 3]), 5)
        self.assertEqual(settle_parlay(["win", "loss"], [2, 3]), -1)
        self.assertEqual(settle_parlay(["win", "push"], [2, 3]), 1)
        self.assertEqual(settle_parlay(["void", "void"], [2, 3]), 0)
        self.assertEqual(settle_parlay(["loss", "void"], [2, 3]), -1)

    def test_sgp_never_assumes_universal_repricing(self):
        with self.assertRaises(ValueError):
            settle_parlay(["win", "void"], [2, 3], same_game=True)
        self.assertEqual(settle_parlay(["win", "void"], [2, 3], same_game=True,
                                       sgp_reprice=lambda active: [1.5]), 0.5)
        with self.assertRaises(ValueError):
            settle_parlay(["win", "void"], [2, 3], same_game=True, sgp_reprice=lambda active: [1.0])

    def test_correlations(self):
        self.assertAlmostEqual(pearson([1, 2, 3], [2, 4, 6]), 1)
        self.assertAlmostEqual(pearson([1, 2, 3], [6, 4, 2]), -1)
        self.assertIsNone(pearson([1, 1], [2, 3]))
        self.assertEqual(ranks([10, 20, 20, 30]), [1, 2.5, 2.5, 4])
        self.assertAlmostEqual(spearman([1, 2, 3], [1, 4, 9]), 1)
        self.assertAlmostEqual(phi([1, 1, 0, 0], [1, 1, 0, 0]), 1)
        self.assertIsNone(phi([1, 1], [1, 0]))

    def test_wilson_and_bounds(self):
        self.assertEqual(wilson(0, 10)[0], 0)
        self.assertAlmostEqual(wilson(10, 10)[1], 1)
        self.assertIsNone(wilson(1, 0))
        lo, hi = joint_bounds(0.7, 0.6)
        self.assertAlmostEqual(lo, 0.3)
        self.assertAlmostEqual(hi, 0.6)
        self.assertEqual(joint_bounds(0.2, 0.3), (0, 0.2))

    def test_scores(self):
        self.assertEqual(brier([0.5, 0.5], [0, 1]), 0.25)
        self.assertAlmostEqual(log_loss([0.5, 0.5], [0, 1]), math.log(2))
        self.assertAlmostEqual(calibration_error([0.1, 0.9], [0, 1]), 0.1)
        self.assertIsNone(brier([], []))
        self.assertIsNone(log_loss([1.1], [1]))

    def test_drawdown(self):
        self.assertEqual(max_drawdown_units([1, -2, 3, -1]), 2)
        with self.assertRaises(ValueError):
            max_drawdown_units([float("nan")])

    def test_bootstrap_deterministic_and_degenerate(self):
        values = list(range(1, 18))
        a = bootstrap_ci(values, lambda s: sum(s) / len(s), draws=300)
        b = bootstrap_ci(values, lambda s: sum(s) / len(s), draws=300)
        self.assertEqual(a, b)
        self.assertLess(a[0], a[1])
        self.assertEqual(bootstrap_ci([1], lambda s: s[0]), (None, None))

    def test_cluster_bootstrap_keeps_week_together(self):
        records = [{"season_week": "2024-1", "profit": 2, "stake": 1},
                   {"season_week": "2024-1", "profit": -1, "stake": 1},
                   {"season_week": "2024-2", "profit": 1, "stake": 1},
                   {"season_week": "2024-2", "profit": 1, "stake": 1}]
        stat = lambda s: sum(r["profit"] for r in s) / sum(r["stake"] for r in s)
        lo, hi = cluster_bootstrap_ci(records, stat, draws=500)
        self.assertTrue(-0.5 <= lo <= hi <= 1)
        self.assertEqual((lo, hi), cluster_bootstrap_ci(records, stat, draws=500))
        block = cluster_bootstrap_ci(records, stat, draws=500, stationary_block=True, mean_block=2)
        self.assertTrue(math.isfinite(block[0]))
        with self.assertRaises(ValueError):
            cluster_bootstrap_ci([{"profit": 1}], stat)


if __name__ == "__main__":
    unittest.main()
