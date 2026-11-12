from __future__ import annotations
import csv
import json
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parent
sys.path.insert(0, str(PROJECT))
import engine


def rows(name):
    with (PROJECT / "data" / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class NFLWeek10SnapshotTests(unittest.TestCase):
    def test_reconciliation_and_schedule_contract(self):
        recon = json.loads((PROJECT / "data/game_reconciliation.json").read_text())
        self.assertEqual(recon["status"], "PASS")
        self.assertEqual(recon["games"], 136)
        self.assertEqual(recon["teams_reconciled"], 32)
        self.assertEqual(recon["mismatches"], [])
        self.assertEqual(len(rows("schedule_2026_w10.csv")), 18)
        self.assertEqual(sum(r["status"] == "SCHEDULED" for r in rows("schedule_2026_w10.csv")), 14)
        self.assertEqual(sum(r["status"] == "BYE" for r in rows("schedule_2026_w10.csv")), 4)

    def test_forecast_scope_is_descriptive_and_prior_week_only(self):
        summary = json.loads((PROJECT / "data/walk_forward_summary.json").read_text())
        self.assertEqual(summary["n_games"], 120)
        self.assertEqual(summary["mae_points"], "10.4048")
        self.assertEqual(summary["status"], "EXPLORATORY_DESCRIPTIVE_ONLY")
        for row in rows("walk_forward_2026_w2_w9.csv"):
            self.assertTrue(row["training_cutoff"].startswith("end_of_week_"))
            self.assertIn("no injuries", row["model_method"])

    def test_unvalidated_adjustments_and_prop_correlations_stay_blank(self):
        for row in rows("model_lines_2026_w10.csv"):
            self.assertEqual(row["injury_adjustment_away_points"], "")
            self.assertEqual(row["injury_adjustment_home_points"], "")
            self.assertEqual(row["injury_adjusted_home_spread"], "")
            self.assertEqual(row["injury_adjusted_total"], "")
        for row in rows("correlations_2026.csv"):
            if row["correlation_id"] in {"CORR-05", "CORR-06", "CORR-07"}:
                self.assertEqual(row["pearson_r"], "")
                self.assertEqual(row["n"], "")
                self.assertIn("NOT_COMPUTABLE", row["status"])
                self.assertTrue(row["caveat"])

    def test_team_chart_coverage_includes_byes_without_injury_inference(self):
        coverage = rows("depth_chart_coverage_2026_w10.csv")
        self.assertEqual(len(coverage), 32)
        byes = {row["team"] for row in coverage if row["week10_status"] == "BYE"}
        self.assertEqual(byes, {"CHI", "DEN", "PHI", "TB"})
        injury_teams = {row["team"] for row in rows("injuries_depth_w10.csv")}
        self.assertEqual(len(injury_teams), 17)
        self.assertTrue(byes.isdisjoint(injury_teams))

    def test_no_qualified_leaderboard_entry_or_reward_claim(self):
        for row in rows("leaderboard_2026.csv"):
            self.assertEqual(row["rank"], "")
            self.assertEqual(row["graded_bets"], "0")
            self.assertEqual(row["net_roi"], "")
            self.assertEqual(row["status"], "NO_QUALIFIED_ENTRY")
            self.assertIn("unfunded", row["proposed_reward"].lower())
        gates = rows("validation_gates_2026.csv")
        self.assertEqual(sum(row["status"] == "PASS" for row in gates), 1)
        self.assertEqual(sum(row["status"] == "BLOCKED" for row in gates), 10)

    def test_correlation_p_values_do_not_underflow_to_zero(self):
        result = engine.corr_stats([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 7])
        self.assertGreater(float(result["p"]), 0)
        self.assertLess(float(result["p"]), 1)
        strong = engine.corr_stats(list(range(1, 33)), list(range(1, 33)))
        self.assertGreater(float(strong["p"]), 0)

    def test_static_site_has_overview_and_twelve_pages(self):
        pages = {p.name for p in PROJECT.glob("*.html")}
        self.assertEqual(len(pages), 13)
        self.assertIn("index.html", pages)
        self.assertIn("audit.html", pages)
        self.assertTrue((PROJECT / "style.css").is_file())


if __name__ == "__main__":
    unittest.main()
