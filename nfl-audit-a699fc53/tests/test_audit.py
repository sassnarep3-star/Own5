"""Unit checks for the a699fc53 audit. Run: python3 -m unittest discover -s nfl-audit-a699fc53/tests -v"""
import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
DATA = HERE / "data"


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Rebuild in check mode: validates every source assertion without rewriting pages.
        cls.proc = subprocess.run([sys.executable, str(HERE / "build.py"), "--check"],
                                  capture_output=True, text=True, cwd=str(ROOT))
        cls.summary = json.loads((DATA / "summary.json").read_text(encoding="utf-8"))
        with (DATA / "official_injury_report_wk10_2026.csv").open(encoding="utf-8") as fh:
            cls.official = list(csv.DictReader(fh))
        with (DATA / "comparison_wk10.csv").open(encoding="utf-8") as fh:
            cls.compare = list(csv.DictReader(fh))

    def test_build_checks_pass(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stdout[-2000:])
        self.assertIn("ALL CHECKS PASS", self.proc.stdout)

    def test_official_totals(self):
        self.assertEqual(self.summary["official_rows"], 347)
        self.assertEqual(self.summary["official_clubs"], 28)
        self.assertEqual(self.summary["official_byes_wk10"], ["CHI", "DEN", "PHI", "TB"])

    def test_published_reconciles(self):
        s = self.summary
        self.assertEqual(s["published_rows"], 326)
        self.assertEqual(s["published_rows_carried_forward"], 277)
        self.assertEqual(s["published_rows_reread_e46"], 49)
        self.assertEqual(s["missing_from_published"], 21)
        self.assertEqual(s["identical"] + s["differs"] + s["missing_from_published"], s["official_rows"])

    def test_reread_cross_check(self):
        reread = [r for r in self.compare if r["published_read"].startswith("re-read")]
        self.assertEqual(len(reread), 49)
        self.assertTrue(all(r["row_status"] == "identical" for r in reread))

    def test_lions_designations(self):
        det = {r["player"]: r for r in self.official if r["team_official"] == "DET"}
        for p in ["Kerby Joseph", "Cade Mays", "D.J. Reed"]:
            self.assertEqual(det[p]["game_status"], "Out", p)

    def test_every_official_row_has_source(self):
        for r in self.official:
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"), r["player"])

    def test_every_flag_and_claim_has_source(self):
        for name in ["flagged.csv", "brief_claims_check.csv"]:
            with (DATA / name).open(encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    self.assertTrue(r["source_url"].startswith("https://"), (name, r["id"]))

    def test_no_blank_verdict(self):
        with (DATA / "brief_claims_check.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                self.assertTrue(r["verdict"].strip(), r["id"])


if __name__ == "__main__":
    unittest.main()
