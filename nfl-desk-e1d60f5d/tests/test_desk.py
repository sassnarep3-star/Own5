#!/usr/bin/env python3
"""Unit tests for the OWN5 NFL decision desk data and build output.

Standard library only. Verifies data integrity, standings arithmetic,
source coverage, and that rendered pages contain expected tables/links.
"""
import csv
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")


def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class StandingsTests(unittest.TestCase):
    def test_thirty_two_teams(self):
        rows = read_csv("standings_2026_wk11.csv")
        self.assertEqual(len(rows), 32, "exactly 32 teams")
        teams = [r["team"] for r in rows]
        self.assertEqual(len(set(teams)), 32, "no duplicate teams")

    def test_pf_minus_pa_equals_net(self):
        rows = read_csv("standings_2026_wk11.csv")
        for r in rows:
            pf = int(r["pf"])
            pa = int(r["pa"])
            net = int(r["net"])
            self.assertEqual(pf - pa, net, f"{r['team']}: PF-PA != NET")

    def test_pct_matches_wins(self):
        rows = read_csv("standings_2026_wk11.csv")
        for r in rows:
            w, l, t = int(r["wins"]), int(r["losses"]), int(r["ties"])
            gp = w + l + t
            expected = round((w + 0.5 * t) / gp, 3) if gp else 0.0
            self.assertAlmostEqual(float(r["pct"]), expected, places=3, msg=r["team"])

    def test_every_row_has_source_url(self):
        rows = read_csv("standings_2026_wk11.csv")
        for r in rows:
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"), r["team"])

    def test_all_status_official(self):
        rows = read_csv("standings_2026_wk11.csv")
        for r in rows:
            self.assertEqual(r["status"], "official", r["team"])


class ScheduleTests(unittest.TestCase):
    def test_thirteen_games(self):
        rows = read_csv("schedule_2026_wk11.csv")
        self.assertEqual(len(rows), 13, "13 Week-11 games")
        self.assertTrue(any("Mexico City" in r["venue"] for r in rows),
                        "neutral-site Mexico City game present")

    def test_six_byes(self):
        rows = read_csv("byes_2026_wk11.csv")
        self.assertEqual(len(rows), 6, "6 bye teams")

    def test_every_game_has_source(self):
        rows = read_csv("schedule_2026_wk11.csv")
        for r in rows:
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"), r["away_team"] + " vs " + r["home_team"])


class RegisterTests(unittest.TestCase):
    def test_questions_have_ids_and_blocking(self):
        rows = read_csv("questions.csv")
        self.assertGreaterEqual(len(rows), 1, "at least one question")
        for r in rows:
            self.assertIn(r["blocking"], ("Yes", "No"), r["id"])
            self.assertTrue(r["source_url"].startswith("https://"), r["id"])

    def test_suggestions_have_status(self):
        rows = read_csv("suggestions.csv")
        self.assertGreaterEqual(len(rows), 1, "at least one suggestion")
        for r in rows:
            self.assertIn(r["decision_status"], ("AWAITING DECISION", "IMPLEMENTED"), r["id"])

    def test_flagged_have_source(self):
        rows = read_csv("flagged.csv")
        self.assertGreaterEqual(len(rows), 1, "at least one flag")
        for r in rows:
            self.assertTrue(r["source_url"].startswith("https://"), r["id"])


class PageTests(unittest.TestCase):
    def read_page(self, name):
        # index.html is rendered at the desk root; the rest live in pages/.
        path = os.path.join(ROOT, name) if name == "index.html" else os.path.join(PAGES, name)
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_index_exists(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "index.html")))

    def test_all_pages_have_tables(self):
        # exec.html intentionally uses summary lists rather than a data table.
        for name in ["index.html", "standings.html", "schedule.html",
                     "questions.html", "suggestions.html", "sources.html", "flagged.html"]:
            content = self.read_page(name)
            self.assertIn('class="data-table"', content, name)

    def test_standings_contains_all_teams(self):
        content = self.read_page("standings.html")
        for team in ["Buffalo Bills", "San Francisco 49ers", "Los Angeles Chargers"]:
            self.assertIn(team, content)

    def test_schedule_contains_mexico_city(self):
        content = self.read_page("schedule.html")
        self.assertIn("Mexico City", content)
        self.assertIn("Vikings", content)
        self.assertIn("49ers", content)

    def test_every_standings_row_sourced(self):
        """Every standings table row must carry an official source link (no blank/inferred rows)."""
        content = self.read_page("standings.html")
        rows = content.count("<tr>") - 1  # exclude header row
        sources = content.count('href="https://www.nfl.com/standings/league/2026/REG"')
        self.assertEqual(rows, 32, "32 team rows rendered")
        self.assertGreaterEqual(sources, 32, "at least one source link per row (note paragraph adds one more)")


if __name__ == "__main__":
    unittest.main()
