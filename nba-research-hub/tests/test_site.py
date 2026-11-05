from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import check  # noqa: E402


class SiteTests(unittest.TestCase):
    def test_trusted_sources(self) -> None:
        self.assertTrue(check.trusted("https://www.nba.com/stats/leaders?Season=2025-26"))
        self.assertTrue(check.trusted("https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md"))
        self.assertFalse(check.trusted("https://github.com/other/repo"))
        self.assertFalse(check.trusted("https://example.com/nba"))

    def test_full_checker(self) -> None:
        check.main()

    def test_unverified_official_values_blank(self) -> None:
        with (ROOT / "audit" / "field_audit.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertTrue(rows)
        self.assertFalse(any(r["status"] == "MISMATCH" for r in rows))
        self.assertTrue(all(r["official_value"] == "" for r in rows if r["status"] == "UNVERIFIED"))

    def test_pages_exist(self) -> None:
        expected = {"index.html", "executive-summary.html", "lines.html", "players.html", "correlations.html", "strategies.html", "gates.html", "leaderboard.html", "luck.html", "sources.html", "requirements.html", "audit.html", "review.html"}
        self.assertEqual({p.name for p in ROOT.glob("*.html")}, expected)
        self.assertTrue((ROOT / "assets" / "style.css").exists())
        self.assertTrue((ROOT / "assets" / "app.js").exists())


if __name__ == "__main__":
    unittest.main()
