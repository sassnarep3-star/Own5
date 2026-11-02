import json
import unittest
from pathlib import Path

from nfl_model.audit import audit_data
from nfl_model.correlation import analyze_pair
from nfl_model.ratings import MAX_SCORE, poisson_pmf, project_game, team_ratings
from nfl_model.strategies import registered_strategies
from nfl_model.validation import PER_TEST_ALPHA, build_leaderboard, evaluate_gates, is_eligible

ROOT = Path(__file__).resolve().parents[1]


def passing_metrics():
    return dict(provenance_complete=True, point_in_time_complete=True, settlement_complete=True,
                settled_bets=600, week_clusters=120, seasons=4, walk_forward_folds=4,
                embargo_weeks=1, holdout_untouched=True, brier_skill=0.02, brier_skill_lb=0.01,
                log_loss_skill_lb=0.01, calibration_error=0.02, net_roi_lb=0.01, clv_lb=0.005,
                trials_registered=6, family_alpha=0.05, multiplicity_adjusted=True,
                joint_calibration_pass=True, cluster_bootstrap=True, positive_season_fraction=0.75,
                max_drawdown_units=10, sensitivity_pass=True, config_locked=True, tests_pass=True,
                build_pass=True, deterministic=True)


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((ROOT / "research/official_snapshot.json").read_text())
        cls.ratings, cls.mu = team_ratings(cls.snapshot["teams"])

    def test_official_snapshot_audit(self):
        report = audit_data(ROOT)
        self.assertEqual(report["status"], "pass", report["failures"])
        self.assertEqual(report["fact_rows"], 78)

    def test_ratings_use_team_game_denominator(self):
        self.assertEqual(len(self.ratings), 32)
        total_games = sum(t["wins"] + t["losses"] + t["ties"] for t in self.snapshot["teams"])
        self.assertAlmostEqual(self.mu, 5528 / total_games)
        self.assertGreater(self.mu, 0)

    def test_all_research_lines_are_derived_and_blank_markets(self):
        for game in self.snapshot["schedule"]:
            line = project_game(game, self.ratings, self.mu)
            self.assertTrue(line["derived"])
            self.assertEqual(len(line["source_urls"]), 2)
            for key in ("market_spread", "market_total", "market_american", "market_edge", "clv", "empirical_home_advantage"):
                self.assertIsNone(line[key])
            self.assertAlmostEqual(line["home_win_probability"] + line["tie_probability"] + line["away_win_probability"], 1)
            self.assertAlmostEqual(line["over_probability_at_fair_total"] + line["under_probability_at_fair_total"] + line["total_push_probability"], 1)
            self.assertLess(line["truncation_tail_mass"], 1e-12)
            self.assertLessEqual(abs(line["fair_spread_home"]), MAX_SCORE)
            self.assertLessEqual(abs(line["fair_spread_home"] + line["expected_margin_home"]), 3)
            self.assertEqual(line["home_advantage_assumption"], 0)
        madrid = next(g for g in self.snapshot["schedule"] if g["neutral_site"])
        self.assertTrue(project_game(madrid, self.ratings, self.mu)["neutral_site"])

    def test_poisson_tail_and_invalid_rates(self):
        p = poisson_pmf(20)
        self.assertEqual(len(p), MAX_SCORE + 1)
        self.assertGreater(sum(p), 0.999999999)
        for bad in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                poisson_pmf(bad)

    def test_shrinkage_sensitivity_is_real_not_hardcoded(self):
        r4, _ = team_ratings(self.snapshot["teams"], k=4)
        r16, _ = team_ratings(self.snapshot["teams"], k=16)
        game = self.snapshot["schedule"][0]
        a = project_game(game, r4, self.mu, k=4)
        b = project_game(game, r16, self.mu, k=16)
        self.assertNotEqual(a["lambda_home"], b["lambda_home"])

    def test_pair_analysis_uses_empirical_joint_not_product(self):
        result = analyze_pair(self.snapshot["paired_player_games"], draws=500)
        self.assertEqual(result["n_games"], 17)
        self.assertEqual(result["joint_hits"], sum(g["burrow_passing_yards"] >= 250 and g["chase_receiving_yards"] >= 75 for g in self.snapshot["paired_player_games"]))
        self.assertAlmostEqual(result["joint_rate"], result["joint_hits"] / 17)
        self.assertNotEqual(result["joint_rate"], result["independence_product"])
        self.assertIsNone(result["current_pair_correlation"])
        self.assertIsNone(result["sgp_fair_price"])

    def test_unknown_gates_block(self):
        gates = evaluate_gates({})
        self.assertEqual(len(gates), 11)
        self.assertTrue(all(g["status"] == "blocked" for g in gates))
        self.assertFalse(is_eligible(gates))
        self.assertFalse(is_eligible([]))

    def test_all_gates_required(self):
        metrics = passing_metrics()
        self.assertTrue(is_eligible(evaluate_gates(metrics)))
        metrics["clv_lb"] = 0.002
        self.assertFalse(is_eligible(evaluate_gates(metrics)))
        metrics["clv_lb"] = None
        self.assertFalse(is_eligible(evaluate_gates(metrics)))
        self.assertAlmostEqual(PER_TEST_ALPHA, 0.05 / 6)

    def test_registry_is_six_blocked_families(self):
        strategies = registered_strategies()
        self.assertEqual(len(strategies), 6)
        self.assertEqual(len({s["id"] for s in strategies}), 6)
        self.assertTrue(all(not s["eligible"] and s["reward_points"] == 0 for s in strategies))
        self.assertEqual(build_leaderboard(strategies), [])

    def test_synthetic_leaderboard_is_never_real_data(self):
        strategies = registered_strategies()
        for i, s in enumerate(strategies[:3]):
            s["metrics"] = passing_metrics()
            s["metrics"]["net_roi_lb"] = 0.03 - i * 0.005
            s["gates"] = evaluate_gates(s["metrics"])
        board = build_leaderboard(strategies)
        self.assertEqual([r["rank"] for r in board], [1, 2, 3])
        self.assertEqual([r["reward_points"] for r in board], [100, 60, 40])
        self.assertEqual(len(board), 3)


if __name__ == "__main__":
    unittest.main()
