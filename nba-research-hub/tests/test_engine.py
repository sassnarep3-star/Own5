from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import model, stats  # noqa: E402

DATA = ROOT / "data"


class StatsTests(unittest.TestCase):
    def test_binom_sf_matches_direct_sum(self) -> None:
        n, p, k = 10, 0.3, 7
        direct = sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))
        self.assertAlmostEqual(stats.binom_sf(k, n, p), direct, places=12)

    def test_binom_30_20_example(self) -> None:
        self.assertAlmostEqual(stats.binom_sf(20, 30, 110 / 210), 0.08224214991297389, places=10)

    def test_fisher_exact_known(self) -> None:
        self.assertAlmostEqual(stats.fisher_exact_two_sided(3, 1, 1, 3), 34 / 70, places=12)
        self.assertAlmostEqual(stats.fisher_exact_two_sided(1, 1, 1, 1), 1.0, places=12)

    def test_holm(self) -> None:
        self.assertEqual(stats.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
        self.assertEqual(stats.holm([None, 0.02]), [None, 0.04])

    def test_half_point_and_logistic(self) -> None:
        self.assertEqual(stats.half_point_line(230.2), 230.5)
        self.assertEqual(stats.half_point_line(-3.2), -3.5)
        self.assertAlmostEqual(stats.logistic(0, 6), 0.5)

    def test_bootstrap_deterministic(self) -> None:
        a = stats.cluster_bootstrap_mean_diff(["a", "a", "b"], [0.1, -0.2, 0.3], 200, 7)
        b = stats.cluster_bootstrap_mean_diff(["a", "a", "b"], [0.1, -0.2, 0.3], 200, 7)
        self.assertEqual(a, b)
        self.assertEqual(a["clusters"], 2)


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = json.loads((DATA / "protocol.json").read_text(encoding="utf-8"))
        cls.teams = model.read_csv(DATA / "team_snapshot.csv")
        cls.schedule = model.read_csv(DATA / "schedule.csv")
        cls.games = model.read_csv(DATA / "player_games.csv")
        cls.out = json.loads((DATA / "derived" / "outputs.json").read_text(encoding="utf-8"))

    def test_team_identities(self) -> None:
        for season in ["2025-26", "2026-27"]:
            rows = [t for t in self.teams if t["season"] == season]
            self.assertEqual(len(rows), 30)
            self.assertEqual(sum(int(t["gp"]) for t in rows), 2460 if season == "2025-26" else 242)
            self.assertEqual(sum(int(t["w"]) for t in rows), sum(int(t["l"]) for t in rows))
            for t in rows:
                self.assertEqual(int(t["gp"]), int(t["w"]) + int(t["l"]))
                self.assertAlmostEqual(float(t["win_pct"]), int(t["w"]) / int(t["gp"]), delta=0.00051)

    def test_lines_are_research_only(self) -> None:
        lines, sens = model.team_lines(self.teams, self.schedule, self.protocol)
        self.assertEqual(len(lines), 9)
        self.assertEqual(len(sens), 81)
        for r in lines:
            self.assertEqual(r["market_spread"], "")
            self.assertEqual(r["market_total"], "")
            self.assertEqual(r["market_odds"], "")
            self.assertEqual(r["edge"], "")
            self.assertAlmostEqual((r["research_total"] * 2) % 2, 1.0)
            self.assertAlmostEqual(r["expected_margin"], r["expected_home_pts"] - r["expected_away_pts"], delta=0.002)

    def test_forecast_counts_and_thresholds(self) -> None:
        forecasts, skill = model.player_forecasts(self.games, self.protocol)
        self.assertEqual(len(forecasts), 460)
        self.assertEqual(len(skill), 8)
        for r in forecasts:
            self.assertGreaterEqual(r["n_prior"], 5)
            self.assertEqual(r["threshold"], self.protocol["player_model"]["research_thresholds"][r["player_id"]][r["stat"]])
        self.assertFalse(any(s["passes_predictive_gate"] for s in skill))

    def test_gates_fail_closed(self) -> None:
        strategies, gates, leaderboard = model.strategies_and_gates(self.protocol, self.out["skill_summary"], self.out["lines"])
        self.assertEqual(len(strategies), 6)
        self.assertEqual(len(gates), 72)
        self.assertTrue(all(not s["eligible"] for s in strategies))
        self.assertTrue(all("G05" in s["blockers"] for s in strategies))
        self.assertTrue(all(r["rank"] == "" for r in leaderboard))
        self.assertEqual(self.out["summary"]["graded_bets"], 0)

    def test_correlation_and_combo_counts(self) -> None:
        self.assertEqual(len(self.out["correlations"]), 20)
        self.assertEqual(len(self.out["prop_combos"]), 20)
        self.assertEqual(sum(1 for c in self.out["prop_combos"] if c["legs"] == 2), 12)
        for c in self.out["prop_combos"]:
            if c["lift"] is not None and c["p_independent"]:
                self.assertAlmostEqual(c["lift"], c["p_joint"] / c["p_independent"], delta=0.002)


if __name__ == "__main__":
    unittest.main()
