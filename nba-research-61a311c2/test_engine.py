import json
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as e


class MathTests(unittest.TestCase):
    """Synthetic fixtures only; not NBA observations."""

    def test_american(self):
        self.assertAlmostEqual(e.decimal_from_american(-110), 1 + 100 / 110)
        self.assertEqual(e.decimal_from_american(150), 2.5)

    def test_invalid_american(self):
        for x in (0, 99, -99, True, None):
            with self.assertRaises(ValueError):
                e.decimal_from_american(x)

    def test_fair_decimal(self):
        self.assertEqual(e.fair_decimal(0.5), 2)
        self.assertAlmostEqual(e.fair_decimal(0.45, 0.1), 1 + 0.45 / 0.45)

    def test_invalid_fair(self):
        for args in ((0, 0), (0.8, 0.3), (-0.1, 0), (1.1, 0)):
            with self.assertRaises(ValueError):
                e.fair_decimal(*args)

    def test_expected_return(self):
        self.assertAlmostEqual(e.expected_return(0.5, 2), 0)
        self.assertAlmostEqual(e.expected_return(0.6, 2), 0.2)

    def test_joint_bounds(self):
        lo, hi = e.joint_bounds(0.8, 0.5)
        self.assertAlmostEqual(lo, 0.3)
        self.assertAlmostEqual(hi, 0.5)

    def test_binom_sf(self):
        self.assertAlmostEqual(e.binom_sf(10, 10, 0.5), 1 / 1024)
        self.assertAlmostEqual(e.binom_sf(6, 10, 0.5), 386 / 1024)
        self.assertEqual(e.binom_sf(0, 10, 0.5), 1)
        self.assertEqual(e.binom_sf(11, 10, 0.5), 0)

    def test_wilson(self):
        lo, hi = e.wilson(23, 47)
        self.assertLess(lo, 23 / 47)
        self.assertGreater(hi, 23 / 47)
        self.assertGreaterEqual(lo, 0)
        self.assertLessEqual(hi, 1)

    def test_holm(self):
        self.assertEqual(e.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])

    def test_gate_fail_closed(self):
        gates = {f"G{i:02}": True for i in range(1, 13)}
        self.assertTrue(e.gate_decision(gates)["eligible"])
        gates["G04"] = None
        d = e.gate_decision(gates)
        self.assertFalse(d["eligible"])
        self.assertIn("G04", d["blocked"])

    def test_truthy_not_evidence(self):
        gates = {f"G{i:02}": "passed" for i in range(1, 13)}
        self.assertFalse(e.gate_decision(gates)["eligible"])

    def test_half_step(self):
        self.assertEqual(e.half_step_threshold(30), 30.5)
        self.assertEqual(e.half_step_threshold(30.5), 30.5)

    def test_pearson_constant(self):
        self.assertIsNone(e.pearson([1, 1, 1], [2, 3, 4]))

    def test_phi_counts(self):
        self.assertAlmostEqual(e.phi_from_counts(4, 1, 1, 1, 1), 0)
        with self.assertRaises(ValueError):
            e.phi_from_counts(3, 1, 1, 1, 1)


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.D = json.loads((HERE / "data" / "derived.json").read_text())
        cls.inp = e.load_inputs()

    def test_counts(self):
        self.assertEqual(len(self.inp["hist"]), 125)
        self.assertEqual(len(self.inp["cur_players"]), 29)
        self.assertEqual(len(self.inp["prior"]), 30)
        self.assertEqual(len(self.inp["current"]), 30)
        self.assertEqual(len(self.inp["slate"]), 11)
        self.assertEqual(len(self.inp["quotes"]), 12)

    def test_sources_allowed(self):
        for s in self.inp["sources"]:
            self.assertTrue(e.official_url(s["url"]))

    def test_unknowns_stay_null(self):
        for s in self.D["strategies"]:
            self.assertIsNone(s["roi"])
            self.assertIsNone(s["reward"])
            self.assertIsNone(s["rank"])
            self.assertEqual(s["graded_bets"], 0)
        for l in self.D["leaderboard"]:
            self.assertIsNone(l["rank"])
            self.assertIsNone(l["score"])
            self.assertIsNone(l["net_units"])
            self.assertIsNone(l["monetary_reward"])
            self.assertEqual(l["reward_points"], 0)
        self.assertIsNone(self.D["cross_game_correlation"]["r"])
        for line in self.D["lines"]:
            self.assertIsNone(line["model_win_prob"])
            self.assertIsNone(line["fair_moneyline"])
            self.assertIsNone(line["edge"])

    def test_market_blanks_for_nov6(self):
        for line in self.D["lines"]:
            if line["date"] == "2026-11-06":
                self.assertIsNone(line["market_home_spread"])
                self.assertIsNone(line["market_total"])

    def test_availability_blank(self):
        for p in self.D["player_refs"]:
            self.assertIsNone(p["availability_status"])
            self.assertIsNone(p["market_prop_line"])
            self.assertIsNone(p["market_prop_price"])

    def test_correlations_bounds(self):
        for c in self.D["correlations"]:
            self.assertGreaterEqual(c["r"], -1)
            self.assertLessEqual(c["r"], 1)
            self.assertLessEqual(c["ci_low"], c["r"])
            self.assertGreaterEqual(c["ci_high"], c["r"])

    def test_walk_forward_no_leakage(self):
        hist = {}
        for r in self.inp["hist"]:
            hist.setdefault(r["player_id"], []).append(r)
        for rows in hist.values():
            rows.sort(key=lambda r: r["game_date"])
        for p in self.D["predictions"]:
            rows = hist[p["player_id"]]
            i = next(i for i, r in enumerate(rows) if r["game_id"] == p["game_id"])
            self.assertEqual(p["prior_n"], i)
            self.assertGreaterEqual(i, 20)
            prior_pts = [float(r["pts"]) for r in rows[:i]]
            med = e.statistics.median(prior_pts)
            self.assertEqual(p["reference_line"], e.half_step_threshold(med))

    def test_gate_decision(self):
        self.assertFalse(self.D["summary"]["gate_decision"]["eligible"])
        self.assertEqual(self.D["summary"]["qualified_strategies"], 0)

    def test_unique_strategy_ids(self):
        ids = [s["id"] for s in self.D["strategies"]]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
