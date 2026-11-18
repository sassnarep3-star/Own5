"""Unit tests for the NFL Venue & Schedule-Announcement desk (390e13fd).

Pure functions of the committed files. Run:
  cd nfl-venue-390e13fd && python3 -m unittest discover -s tests -v
"""
import csv
import os
import subprocess
import sys
import unittest

DESK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(DESK, "data")
RAW = os.path.join(DESK, "raw")
REPO = os.path.abspath(os.path.join(DESK, "..", ".."))


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class TestVenueData(unittest.TestCase):
    def test_thirteen_fixtures(self):
        rows = load("venues.csv")
        self.assertEqual(len(rows), 13, "Week 11 has 13 fixtures")

    def test_no_blank_venue_cells(self):
        for r in load("venues.csv"):
            self.assertTrue(r["venue_location_as_printed"].strip(), r["game_slug"])
            self.assertTrue(r["venue_stadium_as_printed"].strip(), r["game_slug"])

    def test_all_verified(self):
        for r in load("venues.csv"):
            self.assertEqual(r["venue_status"], "VERIFIED", r["game_slug"])

    def test_source_urls_are_official(self):
        for r in load("venues.csv"):
            self.assertTrue(r["official_game_url"].startswith("https://www.nfl.com/"), r["game_slug"])

    def test_raw_extracts_reproduce_csv_values(self):
        """The committed raw extract must print exactly the transcribed values."""
        for r in load("venues.csv"):
            raw = open(os.path.join(DESK, r["raw_file"]), encoding="utf-8").read()
            self.assertIn(f"LocationLOCATION{r['venue_location_as_printed']}", raw, r["game_slug"])
            self.assertIn(f"StadiumSTADIUM{r['venue_stadium_as_printed']}", raw, r["game_slug"])

    def test_mexico_city_resolved(self):
        row = next(r for r in load("venues.csv") if r["game_slug"] == "vikings-at-49ers-2026-reg-11")
        self.assertEqual(row["venue_location_as_printed"], "MEXICO CITY")
        self.assertEqual(row["venue_stadium_as_printed"], "ESTADIO BANORTE")

    def test_byes_complete(self):
        self.assertEqual(len(load("byes.csv")), 6)


class TestAnnouncement(unittest.TestCase):
    def test_dated_items(self):
        rows = load("schedule_announcement.csv")
        self.assertTrue(rows)
        for r in rows:
            self.assertTrue(r["announcement_date_as_published"].strip(), r["item_id"])

    def test_may_14_release_recorded(self):
        rows = load("schedule_announcement.csv")
        self.assertTrue(any("May 14" in r["what_it_says"] for r in rows))


class TestVerifier(unittest.TestCase):
    def test_verify_passes(self):
        result = subprocess.run(
            [sys.executable, os.path.join(DESK, "verify.py")],
            capture_output=True, text=True, cwd=REPO,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("All checks passed.", result.stdout)


class TestBuild(unittest.TestCase):
    def test_pages_present(self):
        for page in ("index.html", "schedule.html", "announcement.html",
                     "sources.html", "flagged.html", "summary.html"):
            self.assertTrue(os.path.isfile(os.path.join(DESK, page)), page)

    def test_rebuild_is_deterministic(self):
        before = {}
        for page in ("index.html", "schedule.html", "announcement.html",
                     "sources.html", "flagged.html", "summary.html"):
            before[page] = open(os.path.join(DESK, page), encoding="utf-8").read()
        subprocess.run(
            [sys.executable, os.path.join(DESK, "tools", "build_site.py")],
            check=True, capture_output=True, text=True, cwd=REPO,
        )
        for page, content in before.items():
            after = open(os.path.join(DESK, page), encoding="utf-8").read()
            self.assertEqual(after, content, f"{page} is not deterministic")


if __name__ == "__main__":
    unittest.main()
