import math
import unittest

from model import (
    american_odds, binomial_critical_hits, binomial_upper_tail, build_derived,
    exact_permutation_p, holm_adjust, load_data, logistic_probability, pearson,
    project_game, round_half_up, round_to_half,
)


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data()
        cls.derived = build_derived(cls.data)

    def test_snapshot_cardinality(self):
        self.assertEqual(len(self.data["teams"]), 30)
        self.assertEqual(len(self.data["schedule"]), 16)
        self.assertEqual(len(self.data["player_games"]), 26)
        self.assertEqual(len(self.derived["correlations"]), 21)

    def test_schedule_records_and_coverage(self):
        scheduled = {row["away"] for row in self.data["schedule"]} | {row["home"] for row in self.data["schedule"]}
        self.assertEqual(scheduled, set(self.data["team_map"]))
        self.assertEqual(len({row["game_id"] for row in self.data["schedule"]}), 16)

    def test_player_means_reconcile(self):
        # load_data performs all 16 exact rounded-mean reconciliations.
        self.assertEqual(sum(int(row["gp"]) for row in self.data["players"]), 26)
        self.assertEqual(round_half_up(5.25), 5.3)

    def test_half_rounding_and_negative_zero(self):
        self.assertEqual(round_to_half(0.25), 0.5)
        self.assertEqual(round_to_half(-0.25), -0.5)
        self.assertEqual(round_to_half(0.24), 0.0)
        self.assertEqual(round_to_half(-0.24), 0.0)
        self.assertEqual(str(round_to_half(-0.01)), "0.0")

    def test_american_odds(self):
        self.assertEqual(american_odds(0.5), 100)
        self.assertEqual(american_odds(0.75), -300)
        self.assertEqual(american_odds(0.25), 300)
        with self.assertRaises(ValueError):
            american_odds(0)
        with self.assertRaises(ValueError):
            american_odds(1)

    def test_identical_team_projection(self):
        team = {"gp": 10, "off_rtg": "112", "def_rtg": "112", "pace": "100"}
        game = {"date": "2026-11-04", "time_et": "7:00 PM", "game_id": "0022600999", "away": "AAA", "home": "BBB", "slug": "aaa-vs-bbb-0022600999"}
        result = project_game(game, {"AAA": team, "BBB": dict(team)}, {"off_rtg": 112.0, "def_rtg": 112.0, "pace": 100.0})
        self.assertAlmostEqual(result["away_points"], 112.0)
        self.assertAlmostEqual(result["home_points"], 112.0)
        self.assertEqual(result["home_spread"], 0.0)
        self.assertEqual(result["away_fair_american"], 100)
        self.assertEqual(result["home_fair_american"], 100)

    def test_all_lines_are_internally_consistent(self):
        for row in self.derived["lines"]:
            self.assertAlmostEqual(row["home_probability"] + row["away_probability"], 1.0)
            self.assertEqual(row["home_spread"], -row["away_spread"])
            self.assertNotEqual(str(row["home_spread"]), "-0.0")
            self.assertNotEqual(str(row["away_spread"]), "-0.0")
            self.assertIsNone(row["market_spread"])
            self.assertIsNone(row["market_total"])
            self.assertIsNone(row["edge"])
            self.assertGreater(row["total"], 0)

    def test_logistic(self):
        self.assertEqual(logistic_probability(0), 0.5)
        self.assertGreater(logistic_probability(2), 0.5)
        with self.assertRaises(ValueError):
            logistic_probability(1, 0)

    def test_pearson(self):
        self.assertAlmostEqual(pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(pearson([1, 2, 3], [6, 4, 2]), -1.0)
        self.assertIsNone(pearson([1, 1, 1], [1, 2, 3]))

    def test_exact_permutation_p(self):
        self.assertAlmostEqual(exact_permutation_p([1, 2, 3], [1, 2, 3]), 2 / 6)
        self.assertAlmostEqual(exact_permutation_p([1, 2, 3], [3, 2, 1]), 2 / 6)

    def test_holm_adjustment(self):
        rows = [{"p_permutation": 0.04}, {"p_permutation": 0.01}, {"p_permutation": 0.03}]
        holm_adjust(rows)
        self.assertAlmostEqual(rows[0]["p_holm"], 0.06)
        self.assertAlmostEqual(rows[1]["p_holm"], 0.03)
        self.assertAlmostEqual(rows[2]["p_holm"], 0.06)

    def test_binomial_functions(self):
        self.assertAlmostEqual(binomial_upper_tail(2, 2, 0.5), 0.25)
        critical = binomial_critical_hits(100, 0.01, 0.5)
        self.assertIsNotNone(critical)
        self.assertLessEqual(binomial_upper_tail(critical, 100, 0.5), 0.01)
        self.assertGreater(binomial_upper_tail(critical - 1, 100, 0.5), 0.01)

    def test_all_strategies_fail_closed(self):
        self.assertEqual(len(self.derived["leaderboard"]), 7)
        for row in self.derived["leaderboard"]:
            self.assertFalse(row["qualified"])
            self.assertEqual(row["observed_n"], 0)
            self.assertEqual(row["reward_points"], 0)
            self.assertIsNone(row["rank"])
            self.assertIsNone(row["roi"])
            self.assertIn("G05", row["failed_gate_ids"])

    def test_out_player_and_unknowns_are_not_playable(self):
        props = {row["player"]: row for row in self.derived["player_props"]}
        self.assertIn("SUPPRESSED", props["Anthony Edwards"]["release_status"])
        for row in props.values():
            self.assertIsNone(row["playable_lines"])
        self.assertTrue(all("HELD" in row["release_status"] for name, row in props.items() if name != "Anthony Edwards"))

    def test_player_multiplicity_result(self):
        player_rows = [row for row in self.derived["correlations"] if row["scope"] == "Player-game"]
        self.assertEqual(len(player_rows), 16)
        self.assertTrue(all(row["p_holm"] >= row["p_permutation"] for row in player_rows))
        self.assertTrue(all(row["p_holm"] >= 0.05 for row in player_rows))


if __name__ == "__main__":
    unittest.main()
