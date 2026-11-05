"""Unit tests for the NBA Line Commission engine (standard library only).

Run: python3 -m unittest discover -s nba-commission/checks
"""
import importlib.util
import math
import sys
import unittest
from pathlib import Path

COMM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(COMM))

spec = importlib.util.spec_from_file_location("commission_compute", COMM / "compute.py")
compute = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compute)


class StatsTests(unittest.TestCase):
    def test_break_even_price(self):
        self.assertAlmostEqual(compute.breakeven_from_american(-110), 110 / 210, places=12)
        self.assertAlmostEqual(compute.breakeven_from_american(-150), 150 / 250, places=12)

    def test_pearson_known_values(self):
        self.assertAlmostEqual(compute.pearson([1, 2, 3, 4], [1, 2, 3, 4]), 1.0, places=12)
        self.assertAlmostEqual(compute.pearson([1, 2, 3, 4], [4, 3, 2, 1]), -1.0, places=12)
        self.assertIsNone(compute.pearson([1, 1, 1], [1, 2, 3]))

    def test_fisher_interval_contains_estimate(self):
        r = 0.6
        lo, hi = compute.fisher_ci(r, 100)
        self.assertLess(lo, r)
        self.assertGreater(hi, r)
        self.assertGreater(hi - lo, 0)

    def test_binomial_tails(self):
        self.assertAlmostEqual(compute.binom_sf(0, 10, 0.5), 1.0, places=12)
        self.assertAlmostEqual(compute.binom_sf(10, 10, 0.5), 0.5 ** 10, places=12)
        self.assertAlmostEqual(compute.binom_cdf(10, 10, 0.5), 1.0, places=10)
        self.assertAlmostEqual(compute.binom_pmf(5, 10, 0.5), 252 / 1024, places=12)

    def test_two_sided_exact_symmetry(self):
        p_low = compute.binom_p_two_sided(3, 20, 0.5)
        p_high = compute.binom_p_two_sided(17, 20, 0.5)
        self.assertAlmostEqual(p_low, p_high, places=10)

    def test_required_n_is_monotone_in_effect_size(self):
        be = compute.breakeven_from_american(-110)
        n55 = compute.required_n(be, 0.55)
        n60 = compute.required_n(be, 0.60)
        self.assertIsNotNone(n55)
        self.assertIsNotNone(n60)
        self.assertGreater(n55, n60)
        self.assertGreater(n55, 2000)  # a 55% edge is not certifiable in a few hundred bets
        self.assertLess(n55, 2500)

    def test_required_n_beyond_cap_returns_none(self):
        be = compute.breakeven_from_american(-110)
        self.assertIsNone(compute.required_n(be, 0.525))

    def test_round_half_up_matches_official_page(self):
        self.assertEqual(compute.round_half_up(33.25, 1), 33.3)
        self.assertEqual(compute.round_half_up(4.75, 1), 4.8)
        self.assertEqual(compute.round_half_up(8.125, 1), 8.1)

    def test_phi_bounds(self):
        self.assertAlmostEqual(compute.phi(9, 1, 1, 9), 0.8, places=4)
        self.assertIsNone(compute.phi(0, 0, 0, 0))


class OutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.out = json.loads((COMM / "data" / "outputs.json").read_text(encoding="utf-8"))

    def test_every_check_passed(self):
        failed = [c for c in self.out["checks"] if not c["passed"]]
        self.assertEqual(failed, [], f"failing checks: {failed}")

    def test_no_market_values_invented(self):
        for line in self.out["lines"]:
            self.assertEqual(line["market_spread"], "")
            self.assertEqual(line["market_total"], "")
        for prop in self.out["props"]:
            self.assertEqual(prop["market_line"], "")

    def test_nothing_certified(self):
        self.assertEqual(self.out["meta"]["strategies_certified"], 0)
        self.assertTrue(all(not s["certified"] for s in self.out["strategies"]))
        self.assertEqual(self.out["leaderboard"]["entries"], [])

    def test_lines_have_every_game(self):
        self.assertEqual(len(self.out["lines"]), 11)
        self.assertEqual(len({l["game_id"] for l in self.out["lines"]}), 11)

    def test_sensitivity_range_brackets_default(self):
        for line in self.out["lines"]:
            self.assertLessEqual(line["spread_min"], line["own_spread_home"])
            self.assertGreaterEqual(line["spread_max"], line["own_spread_home"])
            self.assertEqual(len(line["sensitivity"]), 7)

    def test_prop_over_and_push_rates_are_probabilities(self):
        for prop in self.out["props"]:
            self.assertGreaterEqual(prop["empirical_over_rate"], 0.0)
            self.assertLessEqual(prop["empirical_over_rate"], 1.0)
            self.assertGreaterEqual(prop["empirical_push_rate"], 0.0)
            self.assertLessEqual(prop["empirical_push_rate"], 1.0)
            self.assertLessEqual(prop["empirical_over_rate"] + prop["empirical_push_rate"], 1.0)

    def test_combo_lift_direction_matches_phi(self):
        for combo in self.out["prop_combos"]:
            if combo["lift"] > 1:
                self.assertGreater(combo["phi"], 0)
            elif combo["lift"] < 1:
                self.assertLess(combo["phi"], 0)

    def test_flags_cover_blank_market_and_availability(self):
        ids = {f["id"] for f in self.out["flags"]}
        for required in ("F01", "F04", "F08", "F10", "F11"):
            self.assertIn(required, ids)

    def test_gates_fail_closed(self):
        status = {g["id"]: g["status"] for g in self.out["gates"]}
        self.assertEqual(len(status), 12)
        self.assertIn("BLOCKED", status["G07"])
        self.assertEqual(status["G01"], "PASS this session")


if __name__ == "__main__":
    unittest.main()
