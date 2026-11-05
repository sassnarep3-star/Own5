import csv
import hashlib
import math
import unittest
from pathlib import Path

import model

ROOT = Path(__file__).resolve().parent


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.teams, self.games, self.logs = model.load_inputs()

    def test_reviewed_transcription_seals(self):
        expected = {
            "team_snapshot.csv": "c57a90a7365a59998a91cd298d5446df7e1177b3491121a42d5602b6f6c5eaa1",
            "schedule_snapshot.csv": "bad032f126e4675e691fa7494602df4980e63e07e600bd77da1c516d1f65af22",
            "edwards_sample.csv": "8df444e39ed148782f3d5d1ead307c29413e8ad75c030c605934bdbbc3d442c3",
        }
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((ROOT / "data" / name).read_bytes()).hexdigest(), digest, name)

    def test_selected_rows_agree_with_prior_transcription(self):
        # The separate official review is documented in VERIFICATION.md.
        with (ROOT.parent / "nba-signal-lab/data/game_logs_2025_26.csv").open(encoding="utf8", newline="") as f:
            older = {r["game_id"]: r for r in csv.DictReader(f) if r["player_id"] == "1630162"}
        mapping = {"game_date": "game_date", "matchup": "matchup", "result": "result", "minutes": "min",
                   "points": "pts", "three_made": "tpm", "rebounds": "reb", "assists": "ast"}
        for row in self.logs:
            old = older[row["game_id"]]
            for new_field, old_field in mapping.items():
                self.assertEqual(row[new_field], old[old_field], (row["game_id"], new_field))

    def test_exact_scope_and_unique_matchups(self):
        self.assertEqual((len(self.teams), len(self.games), len(self.logs)), (18, 9, 25))
        self.assertEqual(len({r["game_id"] for r in self.logs}), 25)
        self.assertEqual(len({r["abbr"] for r in self.teams}), 18)
        all_slate_teams = [r[k] for r in self.games for k in ("away", "home")]
        self.assertEqual(len(set(all_slate_teams)), 18)
        self.assertTrue(all(r["game_date"] == "2026-11-06" for r in self.games))

    def test_injury_snapshot_counts_not_treated_as_current(self):
        slots = [r[k] for r in self.games for k in ("away_report", "home_report")]
        self.assertEqual(slots.count("NOT YET SUBMITTED"), 17)
        self.assertTrue(all("NOT YET SUBMITTED" in (r["away_report"], r["home_report"]) for r in self.games))
        self.assertIn("Players listed; not a completeness check", slots)

    def test_nba_url_spoof_rejected(self):
        self.assertTrue(model.is_nba_url("https://official.nba.com/path"))
        self.assertFalse(model.is_nba_url("http://nba.com/path"))
        self.assertFalse(model.is_nba_url("https://nba.com.evil.example/path"))
        self.assertFalse(model.is_nba_url("https://nba.com@evil.example/path"))

    def test_data_tampering_fails_validation(self):
        self.teams[0]["pace"] = "nan"
        with self.assertRaises(ValueError):
            model.validate_inputs(self.teams, self.games, self.logs)

    def test_rounded_net_values_not_silently_replaced(self):
        teams = {t["abbr"]: t for t in self.teams}
        self.assertEqual(teams["OKC"]["net_rtg"], "0.8")
        self.assertEqual(teams["UTA"]["net_rtg"], "-11.3")
        self.assertAlmostEqual(float(teams["OKC"]["off_rtg"]) - float(teams["OKC"]["def_rtg"]), 0.9)


class MathematicsTests(unittest.TestCase):
    def test_pearson_identity_reversal_and_constant(self):
        x = [1.0, 2.0, 4.0]
        self.assertAlmostEqual(model.pearson(x, x), 1.0)
        self.assertAlmostEqual(model.pearson(x, [-v for v in x]), -1.0)
        self.assertIsNone(model.pearson(x, [1.0, 1.0, 1.0]))
        with self.assertRaises(ValueError):
            model.pearson([1.0], [2.0, 3.0])

    def test_phi_and_joint_identity(self):
        a = [True, True, False, False]
        b = [True, False, True, False]
        result = model.binary_stats(a, b)
        self.assertEqual((result["n11"], result["n10"], result["n01"], result["n00"]), (1, 1, 1, 1))
        self.assertAlmostEqual(result["phi"], 0.0)
        self.assertAlmostEqual(model.joint_from_phi(result["p_a"], result["p_b"], result["phi"]), result["joint"])

    def test_phi_feasibility_and_degenerate_marginals(self):
        with self.assertRaises(ValueError):
            model.joint_from_phi(0.9, 0.9, -1.0)
        with self.assertRaises(ValueError):
            model.joint_from_phi(1.0, 0.5, 0.0)
        self.assertIsNone(model.binary_stats([True, True], [True, False])["phi"])

    def test_joint_sample_direction(self):
        _, _, logs = model.load_inputs()
        result = model.analyze(logs)["binary"][0]
        self.assertEqual((result["n11"], result["n10"], result["n01"], result["n00"]), (12, 3, 5, 5))
        self.assertAlmostEqual(result["joint"], .48)
        self.assertAlmostEqual(result["product"], .408)
        self.assertGreater(result["joint"], result["product"])
        self.assertAlmostEqual(result["phi"], .3150630189, places=8)

    def test_three_leg_joint_is_not_pairwise_phi(self):
        _, _, logs = model.load_inputs()
        triple = model.analyze(logs)["triple"]
        self.assertEqual(triple["joint_count"], 4)
        self.assertAlmostEqual(triple["joint"], .16)
        self.assertNotIn("phi", triple)

    def test_american_odds_and_invalid_values(self):
        self.assertAlmostEqual(model.american_decimal(-110), 1 + 100 / 110)
        self.assertAlmostEqual(1 / model.american_decimal(-110), 110 / 210)
        self.assertAlmostEqual(model.american_decimal(150), 2.5)
        for odds in (0, 99, -99, True, 100.5):
            with self.assertRaises(ValueError):
                model.american_decimal(odds)

    def test_exact_binomial_small_n_against_combinations(self):
        n, p, k = 10, .4, 6
        expected = sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))
        self.assertAlmostEqual(model.binomial_tail(k, n, p), expected, places=12)
        self.assertEqual(model.binomial_tail(0, n, p), 1.0)
        self.assertEqual(model.binomial_tail(n + 1, n, p), 0.0)
        self.assertEqual(model.binomial_tail(1, n, 0.0), 0.0)
        self.assertEqual(model.binomial_tail(n, n, 1.0), 1.0)

    def test_exact_critical_values_and_power(self):
        null = 110 / 210
        k = model.critical_wins(50, null, .05)
        self.assertEqual(k, 33)
        self.assertLessEqual(model.binomial_tail(k, 50, null), .05)
        self.assertGreater(model.binomial_tail(k - 1, 50, null), .05)
        self.assertAlmostEqual(model.binomial_tail(30, 50, null), .1744762784884093, places=10)
        k2243 = model.critical_wins(2243, null, .05)
        self.assertEqual(k2243, 1215)
        self.assertAlmostEqual(model.binomial_tail(k2243, 2243, .55), .7918904276333087, places=9)
        self.assertGreater(model.critical_wins(2243, null, .05 / 6), k2243)

    def test_proper_log_score(self):
        self.assertAlmostEqual(model.log_score_lift(1, .6, .5), math.log(1.2))
        self.assertAlmostEqual(model.log_score_lift(0, .6, .5), math.log(.8))
        for args in ((True, .6, .5), (1.0, .6, .5), (1, 0, .5), (1, float("nan"), .5)):
            with self.assertRaises(ValueError):
                model.log_score_lift(*args)

    def test_originated_lines_match_formula_and_are_not_market_quotes(self):
        teams, games, _ = model.load_inputs()
        lines = model.originate(teams, games)
        self.assertEqual(len(lines), 9)
        for line in lines:
            self.assertAlmostEqual(line["model_home_spread"], -line["model_home_margin"])
            self.assertIsNone(line["market_spread"])
            self.assertIsNone(line["market_total"])
            self.assertIsNone(line["market_odds"])
        self.assertAlmostEqual(lines[0]["model_total"], 213.42924, places=5)


class GateTests(unittest.TestCase):
    def valid_attestation(self):
        return {"source_reviewed": True, "feature_cutoff": "2026-11-05T18:00:00Z",
                "quote_time": "2026-11-05T19:00:00Z", "decision_time": "2026-11-05T19:01:00Z",
                "event_time": "2026-11-06T00:00:00Z", "registered_at": "2026-10-01T00:00:00Z",
                "holdout_start": "2026-11-01T00:00:00Z", "registration_audited": True,
                "quote_and_rules_reviewed": True, "outcomes_reviewed": True, "holdout_disjoint": True,
                "graded_bets": 200, "dependence_reviewed": True, "registered_trials": 7,
                "raw_p_value": .001, "test_validated": True, "independent_replication": True,
                "reproducible": True, "risk_and_reward_controls": True}

    def test_no_evidence_fails_every_gate(self):
        self.assertFalse(any(model.evaluate_gates({}).values()))

    def test_complete_example_attestations_pass_only_as_a_formal_shape_check(self):
        # Synthetic data tests validation mechanics; it is not a real strategy or proof.
        self.assertTrue(all(model.evaluate_gates(self.valid_attestation()).values()))

    def test_missing_false_or_string_attestations_fail_closed(self):
        record = self.valid_attestation()
        record["quote_and_rules_reviewed"] = "true"
        record["source_reviewed"] = None
        record.pop("independent_replication")
        gates = model.evaluate_gates(record)
        self.assertFalse(gates["G01"])
        self.assertFalse(gates["G04"])
        self.assertFalse(gates["G09"])

    def test_timestamp_leakage_and_missing_timezone_fail(self):
        record = self.valid_attestation()
        record["feature_cutoff"] = "2026-11-05T19:02:00Z"
        self.assertFalse(model.evaluate_gates(record)["G02"])
        record = self.valid_attestation()
        record["decision_time"] = "2026-11-05T19:01:00"
        self.assertFalse(model.evaluate_gates(record)["G02"])
        record = self.valid_attestation()
        record["holdout_start"] = "2026-11-07T00:00:00Z"
        self.assertFalse(model.evaluate_gates(record)["G03"])

    def test_bad_p_values_and_multiple_testing_fail(self):
        for value in (float("nan"), float("inf"), -0.1, 1.1, True, .01):
            record = self.valid_attestation()
            record["raw_p_value"] = value
            self.assertFalse(model.evaluate_gates(record)["G08"], value)
        record = self.valid_attestation()
        record["registered_trials"] = 0
        self.assertFalse(model.evaluate_gates(record)["G08"])

    def test_minimum_size_is_necessary_not_sufficient(self):
        record = self.valid_attestation()
        record["graded_bets"] = 199
        self.assertFalse(model.evaluate_gates(record)["G06"])
        record["graded_bets"] = True
        self.assertFalse(model.evaluate_gates(record)["G06"])
        record = self.valid_attestation()
        record["independent_replication"] = False
        self.assertTrue(model.evaluate_gates(record)["G06"])
        self.assertFalse(all(model.evaluate_gates(record).values()))


if __name__ == "__main__":
    unittest.main()
