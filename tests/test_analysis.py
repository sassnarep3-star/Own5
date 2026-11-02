import copy
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import analyze  # noqa: E402


class SourceDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = analyze.parse_games()
        cls.players = analyze.parse_players()

    def test_official_game_identity_and_source_links(self):
        self.assertEqual(len(self.games), 91)
        game = next(g for g in self.games if g["id"] == "2017090700")
        self.assertEqual((game["home"], game["away"], game["home_score"], game["away_score"]), ("NE", "KC", 27, 42))
        self.assertEqual(sum(g["home_score"] == g["away_score"] for g in self.games), 0)
        self.assertEqual(len({g["id"] for g in self.games}), 91)
        self.assertTrue(all(g["source"].startswith(analyze.GAME_SOURCE + "#L") for g in self.games))

    def test_every_player_value_against_rechecked_nfl_log_rows(self):
        # Independently transcribed from the four official NFL.com regular-season
        # tables on 2026-11-02. Values are passing yards, receiving yards and catches.
        burrow = {1:164, 2:258, 3:324, 4:232, 5:392, 6:208, 7:181, 8:234, 9:251, 10:428, 11:356, 13:309, 14:369, 15:271, 16:252, 17:412, 18:277}
        chase = {1:(62,6), 2:(35,4), 3:(118,6), 4:(85,3), 5:(193,10), 6:(72,5), 7:(55,5), 8:(54,9), 9:(43,7), 10:(264,11), 11:(75,7), 13:(86,6), 14:(177,14), 15:(94,9), 16:(97,6), 17:(102,9), 18:(96,10)}
        mahomes = {1:258, 2:187, 3:224, 4:270, 5:318, 6:257, 7:286, 8:299, 9:250, 11:276, 12:352, 13:261, 14:160, 15:189}
        kelce = {1:(47,2), 2:(61,4), 3:(26,4), 4:(48,5), 5:(61,7), 6:(78,6), 7:(54,3), 8:(99,6), 9:(66,4), 11:(91,9), 12:(43,4), 13:(45,5), 14:(8,1), 15:(70,7), 16:(6,1), 17:(36,5), 18:(12,3)}
        for year, qbs, recs in ((2024, burrow, chase), (2025, mahomes, kelce)):
            rows = [p for p in self.players if p["season"] == year]
            self.assertEqual({p["week"] for p in rows}, set(recs))
            for row in rows:
                with self.subTest(year=year, week=row["week"]):
                    week = row["week"]
                    self.assertEqual(row["qb_passing_yards"], qbs.get(week))
                    self.assertEqual((row["receiver_yards"], row["receiver_receptions"]), recs[week])
                    self.assertEqual(row["paired"], week in qbs)
                    self.assertIn("https://www.nfl.com/players/", row["qb_source"])
                    self.assertIn("https://www.nfl.com/players/", row["receiver_source"])
        self.assertEqual(sum(p["paired"] for p in self.players), 31)
        self.assertEqual(sum(not p["paired"] for p in self.players), 3)


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = analyze.parse_games()
        cls.predictions = analyze.walk_forward(cls.games)

    def test_exact_sample_and_virtual_cutoffs(self):
        self.assertEqual(len(self.predictions), 44)
        self.assertEqual({p["week"] for p in self.predictions}, {4, 5, 6})
        self.assertTrue(all(p["cutoff"] == f"end of week {p['week'] - 1}" for p in self.predictions))
        self.assertTrue(all(p["home_prior_games"] > 0 and p["away_prior_games"] > 0 for p in self.predictions))

    def test_week_result_cannot_change_same_week_forecasts(self):
        changed = copy.deepcopy(self.games)
        for game in changed:
            if game["week"] == 4:
                game["home_score"] += 100
        modified = analyze.walk_forward(changed)
        baseline = {p["id"]: p for p in self.predictions}
        for p in modified:
            if p["week"] == 4:
                old = baseline[p["id"]]
                for key in ("elo_home_p", "form_home_p", "projected_total", "baseline_total"):
                    self.assertEqual(old[key], p[key])
        # There should be a future impact, otherwise this is not a meaningful test.
        self.assertTrue(any(p["elo_home_p"] != baseline[p["id"]]["elo_home_p"] for p in modified if p["week"] == 5))

    def test_score_and_odds_math(self):
        scored = analyze.score_predictions(self.predictions)
        self.assertEqual(scored["binary_baseline"]["brier"], .25)
        self.assertAlmostEqual(scored["candidates"][0]["brier"], 0.2517738235470293)
        self.assertAlmostEqual(analyze.fair_odds(.6)["decimal"], 5/3)
        self.assertAlmostEqual(analyze.fair_odds(.6)["american"], -150)
        self.assertAlmostEqual(analyze.fair_odds(.25)["american"], 300)
        with self.assertRaises(ValueError):
            analyze.fair_odds(1)

    def test_correlation_and_joint_counts(self):
        self.assertAlmostEqual(analyze.correlation([1, 2, 3], [2, 4, 6]), 1)
        self.assertIsNone(analyze.correlation([1, 1], [0, 1]))
        binary = analyze.binary_comparison([1, 1, 0, 0], [1, 0, 1, 0])
        self.assertEqual((binary["n11"], binary["n10"], binary["n01"], binary["n00"]), (1, 1, 1, 1))
        self.assertEqual(binary["joint"], .25)
        self.assertEqual(binary["independent_product"], .25)
        self.assertAlmostEqual(binary["phi"], 0)
        report = analyze.build_report()
        vals = {r["id"]: r for r in report["correlations"]}
        self.assertAlmostEqual(vals["player_yards_2024"]["value"], 0.751595712897625)
        self.assertEqual(vals["player_overs_2024"]["comparison"]["n11"], 10)
        self.assertEqual(vals["team_parlay"]["comparison"]["n11"], 26)

    def test_calibration_bin_boundaries(self):
        diag = analyze.calibration_diagnostics([.2] * 20 + [1.] * 20, [0] * 16 + [1] * 4 + [1] * 20)
        self.assertTrue(diag["passes"])
        self.assertEqual([b["lower"] for b in diag["bins"]], [.2, .8])
        self.assertFalse(analyze.calibration_diagnostics([.5] * 19, [1] * 19)["passes"])

    def test_gates_fail_closed_and_reward_only_qualified(self):
        evidence = {
            "source_and_quality_verified": True, "chronology_verified": True, "market_type": "single",
            "n": 200, "seasons": 3, "week_blocks": 10, "calibration_pass": True,
            "brier_improvement": .02, "adjusted_ci_lower": .001,
            "multiplicity_adjusted": True, "week_blocked": True,
            "market_and_settlement_verified": True, "locked_forward_test_pass": True,
        }
        passed = analyze.evaluate_gates(evidence)
        self.assertTrue(all(status == "pass" for status in passed.values()))
        no_market = analyze.evaluate_gates({**evidence, "market_and_settlement_verified": None})
        self.assertEqual(no_market["market_and_settlement"], "unverified")
        self.assertEqual(analyze.evaluate_gates({**evidence, "n": 199})["sample"], "fail")
        self.assertEqual(analyze.evaluate_gates({**evidence, "brier_improvement": -.01})["skill"], "fail")
        self.assertEqual(analyze.evaluate_gates({**evidence, "adjusted_ci_lower": None})["skill"], "unverified")
        combo_gates = analyze.evaluate_gates({**evidence, "market_type": "player_combo"})
        self.assertEqual(combo_gates["joint_and_leg_terms"], "unverified")
        candidates = [
            {"id": "a", "market_type": "single", "brier": .2, "gates": passed, "eligible": False, "reward_credits": None},
            {"id": "b", "market_type": "single", "brier": .19, "gates": no_market, "eligible": False, "reward_credits": None},
            {"id": "c", "market_type": "single", "brier": .21, "gates": passed, "eligible": False, "reward_credits": None},
        ]
        result = analyze.reward_eligible(candidates)
        self.assertEqual([(r["id"], r["reward_credits"]) for r in result], [("a", 100), ("c", 60)])
        self.assertFalse(candidates[1]["eligible"])
        self.assertIsNone(candidates[1]["reward_credits"])
        candidates[0]["gates"] = {"provenance": "pass"}  # missing gates cannot qualify
        self.assertEqual([r["id"] for r in analyze.reward_eligible(candidates)], ["c"])
        self.assertFalse(candidates[0]["eligible"])
        self.assertIsNone(candidates[0]["reward_credits"])
        arbitrary = analyze.score_predictions(self.predictions)
        self.assertTrue(all(c["gates"]["provenance"] == "unverified" for c in arbitrary["candidates"]))

    def test_generated_report_reproducible(self):
        actual = json.loads(analyze.OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(actual, analyze.build_report())
        self.assertEqual(actual["counts"]["qualified_strategies"], 0)
        self.assertTrue(all(not c["eligible"] for c in actual["scores"]["candidates"]))
        self.assertFalse(any(math.isnan(c["value"]) for c in actual["correlations"]))


if __name__ == "__main__":
    unittest.main()
