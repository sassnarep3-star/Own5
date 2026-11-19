from __future__ import annotations

import csv
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DecisionBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(ROOT / "build.py")], check=True, cwd=ROOT)

    def test_all_questions_and_proposals_have_sources_and_gates(self) -> None:
        with (ROOT / "data" / "decision_register.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(7, sum(row["kind"] == "Question" for row in rows))
        self.assertEqual(5, sum(row["kind"] == "Suggestion" for row in rows))
        self.assertTrue(all(row["official_source_url"].startswith("https://") for row in rows))
        self.assertTrue(all(row["repo_evidence_url"] for row in rows))
        self.assertTrue(all(row["what_would_change_our_mind"] for row in rows))

    def test_page_does_not_promote_backtest_or_infer_availability(self) -> None:
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Keep the project in paper / shadow mode", page)
        self.assertIn("do not interpret blank designation cells or absent rows as availability", page)
        self.assertIn("backtest-only results", page)
        self.assertIn("Do not scrape/store or publish operator prices", page)
        self.assertIn("47 PASS / 3 FAIL", page)
        self.assertIn("not present in the local Git object database", page)

    def test_build_is_deterministic_and_verifier_passes(self) -> None:
        before = (ROOT / "index.html").read_bytes()
        subprocess.run([sys.executable, str(ROOT / "build.py")], check=True, cwd=ROOT)
        after = (ROOT / "index.html").read_bytes()
        self.assertEqual(before, after)
        result = subprocess.run([sys.executable, str(ROOT / "verify.py")], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
