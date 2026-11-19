#!/usr/bin/env python3
"""Unit tests for nfl-desk-067f2314 (stdlib only).

Positive controls: the committed desk passes verify_desk.py; pinned counts,
reconciliations and provenance rules hold on the real data.
Negative controls: corrupted data (a broken NET value, a row losing its source
link and flag) must FAIL the verifier — the drift alarm is fail-closed.
"""
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def run_verify(cwd):
    return subprocess.run(
        [sys.executable, os.path.join(cwd, "verify_desk.py")],
        cwd=cwd, capture_output=True, text=True,
    )


class TestDeskData(unittest.TestCase):
    def test_pinned_counts(self):
        expected = {
            "standings_2026.csv": 32, "schedule_2026_wk11.csv": 19,
            "results_2026_wk10.csv": 14, "injuries_2026_wk11.csv": 255,
            "lines_originated_wk11.csv": 39, "price_snapshots.csv": 39,
            "correlations.csv": 4, "gates.csv": 12, "leaderboard.csv": 10,
            "requirements.csv": 79, "questions.csv": 15, "suggestions.csv": 12,
            "flagged.csv": 33, "sources.csv": 8,
        }
        for name, n in expected.items():
            with self.subTest(name=name):
                with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), n)
                self.assertNotIn(None, rows[0], "row has an unparsed extra field")

    def test_standings_reconcile(self):
        with open(os.path.join(DATA, "standings_2026.csv"), newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                w, l, t = int(r["W"]), int(r["L"]), int(r["T"])
                self.assertEqual(w + l + t, int(r["GP"]))
                self.assertEqual(int(r["PF"]) - int(r["PA"]), int(r["NET"]))

    def test_results_winners(self):
        with open(os.path.join(DATA, "results_2026_wk10.csv"), newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                a, h = int(r["away_score"]), int(r["home_score"])
                expected = r["home_team"] if h > a else r["away_team"]
                self.assertEqual(r["winner"], expected)
                self.assertEqual(int(r["margin"]), abs(h - a))

    def test_lines_order_and_flags(self):
        with open(os.path.join(DATA, "lines_originated_wk11.csv"), newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        order = {"side": 0, "total": 1, "moneyline": 2}
        seen = {}
        for r in rows:
            self.assertTrue(r["model_line"] or r["model_prob_home"], "model value missing")
            self.assertEqual(r["market_line"], "")
            self.assertEqual(r["difference"], "")
            self.assertEqual(r["flag_id"], "F06-03")
            seen.setdefault(r["game_id"], []).append(order[r["market"]])
        for gid, seq in seen.items():
            self.assertEqual(seq, [0, 1, 2], f"{gid} not in side->total->moneyline order")

    def test_snapshots_hashes(self):
        with open(os.path.join(DATA, "price_snapshots.csv"), newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.assertEqual(len(r["inputs_sha256"]), 64)
                self.assertEqual(r["closed_utc"], "")
                self.assertEqual(r["flag_id"], "F06-03")

    def test_no_certified_strategies(self):
        with open(os.path.join(DATA, "leaderboard.csv"), newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.assertEqual(r["certified"], "NO")
                self.assertTrue(r["what_would_change_our_mind"])

    def test_requirements_have_gate_and_clearing(self):
        with open(os.path.join(DATA, "requirements.csv"), newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.assertTrue(r["gate"], f"{r['req_id']} missing gate")
                self.assertTrue(r["clearing_number"], f"{r['req_id']} missing clearing number")
                if not r["observed_today"]:
                    self.assertTrue(r["flag_id"], f"{r['req_id']} blank observed without flag")
                if not r["source_url"]:
                    self.assertTrue(r["flag_id"], f"{r['req_id']} no source and no flag")


class TestVerifier(unittest.TestCase):
    def test_committed_desk_passes(self):
        proc = run_verify(ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PASS", proc.stdout)

    def test_negative_control_broken_net(self):
        with tempfile.TemporaryDirectory() as tmp:
            desk = os.path.join(tmp, "desk")
            shutil.copytree(ROOT, desk)
            path = os.path.join(desk, "data", "standings_2026.csv")
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            rows[0]["NET"] = str(int(rows[0]["NET"]) + 100)  # break reconciliation
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=rows[0].keys())
                w.writeheader()
                w.writerows(rows)
            proc = run_verify(desk)
            self.assertEqual(proc.returncode, 1, "corrupted NET must fail the verifier")
            self.assertIn("FAIL", proc.stdout)

    def test_negative_control_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            desk = os.path.join(tmp, "desk")
            shutil.copytree(ROOT, desk)
            path = os.path.join(desk, "data", "requirements.csv")
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            rows[0]["source_url"] = ""
            rows[0]["flag_id"] = ""
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=rows[0].keys())
                w.writeheader()
                w.writerows(rows)
            proc = run_verify(desk)
            self.assertEqual(proc.returncode, 1, "row without source/flag must fail the verifier")
            self.assertIn("FAIL", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
