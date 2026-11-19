#!/usr/bin/env python3
"""Unit tests for the 7e228db8 desk (stdlib unittest), including negative controls
that prove the verifier has teeth."""
from __future__ import annotations

import csv
import io
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESK = HERE.parent
DATA = DESK.parent / "data" / "nfl-desk-7e228db8"
sys.path.insert(0, str(DESK))

import build_desk  # noqa: E402


def rows(rel):
    with io.open(DATA / rel, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestModel(unittest.TestCase):
    def test_norm_cdf_bounds(self):
        self.assertAlmostEqual(build_desk.norm_cdf(0.0), 0.5, places=12)
        self.assertLess(build_desk.norm_cdf(-5), 1e-5)
        self.assertGreater(build_desk.norm_cdf(5), 1 - 1e-5)

    def test_pearson_known_value(self):
        r, n = build_desk.pearson([1, 2, 3], [2, 4, 6])
        self.assertAlmostEqual(r, 1.0)
        self.assertEqual(n, 3)
        r, n = build_desk.pearson([1, 2, 3], [3, 2, 1])
        self.assertAlmostEqual(r, -1.0)

    def test_fisher_ci_monotone(self):
        lo, hi = build_desk.fisher_ci(0.5, 32)
        self.assertLess(float(lo), 0.5)
        self.assertGreater(float(hi), 0.5)
        self.assertEqual(build_desk.fisher_ci(0.5, 3), ("", ""))

    def test_solve_linear_roundtrip(self):
        A = [[4.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 2.0]]
        b = [1.0, 2.0, 3.0]
        x = build_desk.solve_linear(A, b)
        for i in range(3):
            self.assertAlmostEqual(sum(A[i][j] * x[j] for j in range(3)), b[i], places=8)

    def test_solve_linear_singular_raises(self):
        with self.assertRaises(ValueError):
            build_desk.solve_linear([[1.0, 1.0], [1.0, 1.0]], [1.0, 2.0])

    def test_ratings_residuals_zero_meanish_and_hfa_finite(self):
        st = build_desk.load_standings()
        games, _ = build_desk.load_corpus(st)
        ratings, hfa, resid = build_desk.fit_ratings(games, build_desk.LEAGUE)
        self.assertEqual(len(ratings), 32)
        self.assertAlmostEqual(sum(ratings.values()), 0.0, places=6)
        self.assertLess(abs(hfa), 10.0)
        self.assertEqual(len(resid), len(games))

    def test_total_model_pace_positive(self):
        st = build_desk.load_standings()
        games, _ = build_desk.load_corpus(st)
        pace, resid = build_desk.total_model(st, games)
        for t, p in pace.items():
            self.assertGreater(p, 20.0)
            self.assertLess(p, 70.0)
        self.assertEqual(len(resid), len(games))


class TestData(unittest.TestCase):
    def test_standings_cover_32_and_are_arithmetically_sound(self):
        st = rows("standings_2026_wk10.csv")
        self.assertEqual(len(st), 32)
        for r in st:
            self.assertEqual(int(r["w"]) + int(r["l"]) + int(r["t"]),
                             int(round((int(r["w"]) + 0.5 * int(r["t"])) / float(r["pct"]) * 1)))
            self.assertEqual(int(r["net"]), int(r["pf"]) - int(r["pa"]))

    def test_results_feed_complete_and_consistent(self):
        feed = rows("results_feed_2026_through_wk10.csv")
        self.assertEqual(len(feed), 150)
        weeks = {}
        ties = 0
        for r in feed:
            weeks[r["week"]] = weeks.get(r["week"], 0) + 1
            if r["away_pts"] == r["home_pts"]:
                ties += 1
        self.assertEqual(weeks["9"], 15)
        self.assertEqual(weeks["10"], 14)
        self.assertEqual(ties, 1, "two team-ties (NYG, WAS) = exactly one tied game")

    def test_schedule_covers_26_clubs_six_byes(self):
        sch = rows("schedule_2026_week11.csv")
        self.assertEqual(len(sch), 13)
        clubs = set()
        for g in sch:
            clubs.add(g["away"]); clubs.add(g["home"])
            self.assertTrue(g["venue_from_schedule_page"], "venue missing on " + g["game_id"])
            self.assertTrue(g["venue_source"].startswith("https://"), "venue source missing")
        ctx = json.loads((DATA / "build_context.json").read_text())
        self.assertEqual(sorted(clubs | set(ctx["byes"])), sorted(build_desk.LEAGUE))
        self.assertEqual(len(ctx["byes"]), 6)

    def test_injuries_shape(self):
        inj = rows("injuries_2026_week11.csv")
        self.assertEqual(len(inj), 255)
        markers = [r for r in inj if r["practice_status"] == "No Injuries Reported"]
        self.assertEqual(len(markers), 2)
        statuses = {"Did Not Participate In Practice", "Limited Participation in Practice",
                    "Full Participation in Practice", "No Injuries Reported", ""}
        for r in inj:
            self.assertIn(r["practice_status"], statuses)
            self.assertIn(r["game_status"], {"Out", "Questionable", "Doubtful", ""})

    def test_lines_order_and_blank_market_columns(self):
        lines = rows("lines_week11.csv")
        self.assertEqual(len(lines), 13)
        hdr_line = None
        with io.open(DATA / "lines_week11.csv", newline="", encoding="utf-8") as f:
            hdr_line = next(csv.reader(f))
        side_idx = hdr_line.index("fair_spread_home")
        total_idx = hdr_line.index("fair_total")
        ml_idx = hdr_line.index("p_home_win_novig")
        self.assertLess(side_idx, total_idx)
        self.assertLess(total_idx, ml_idx)
        for r in lines:
            self.assertEqual(r["market_spread"], "")
            self.assertEqual(r["market_total"], "")
            self.assertEqual(r["market_p_home"], "")
            self.assertEqual(r["spread_diff"], "")
            self.assertEqual(r["total_diff"], "")
            self.assertEqual(len(r["inputs_sha256"]), 64)

    def test_snapshots_immutable_shape(self):
        snaps = rows("price_snapshots.csv")
        self.assertEqual(len(snaps), 39)
        ids = [s["snapshot_id"] for s in snaps]
        self.assertEqual(len(ids), len(set(ids)))
        for s in snaps:
            self.assertEqual(s["market_close"], "")
            self.assertEqual(s["residual_vs_market"], "")
            self.assertIn("F7-P01", s["policy_note"])

    def test_leaderboard_separates_signal_from_staking(self):
        lb = rows("leaderboard.csv")
        self.assertEqual(len(lb), 6)
        for r in lb:
            self.assertIn(r["signal_status"], {"control", "pre_registered"})
            self.assertIn(r["staking_status"], {"control", "pre_registered"})
            self.assertEqual(r["brier_skill"], "", "no backtest numbers may appear on the board")
            self.assertEqual(r["n_prospective"], "")

    def test_readiness_covers_registry(self):
        ready = rows("readiness.csv")
        self.assertEqual(len(ready), 80)
        ids = [r["id"] for r in ready]
        self.assertEqual(len(set(ids)), 80)
        self.assertTrue(ids[0].startswith("R0"))

    def test_flags_have_evidence_links(self):
        for f in rows("flagged.csv"):
            self.assertTrue(f["evidence_url"] or f["evidence_source"],
                            f"{f['id']} has neither evidence link nor evidence source")


class TestVerifier(unittest.TestCase):
    def test_verify_passes(self):
        proc = subprocess.run([sys.executable, str(DESK / "verify_desk.py")],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_negative_control_lines_market_column(self):
        """Plant a market value into a blank column; the verifier must fail loudly."""
        import shutil
        target = DATA / "lines_week11.csv"
        backup = target.read_bytes()
        try:
            text = backup.decode("utf-8")
            text = text.replace(",-6.5,,,49.0,,,", ",-6.5,-3.5,,49.0,45.5,,", 1)
            target.write_text(text, encoding="utf-8")
            proc = subprocess.run([sys.executable, str(DESK / "verify_desk.py")],
                                  capture_output=True, text=True, timeout=120)
            self.assertNotEqual(proc.returncode, 0, "verifier accepted a filled market column")
        finally:
            target.write_bytes(backup)

    def test_negative_control_drift_alarm(self):
        """Drop one snapshot row; the pinned-count drift alarm must fire."""
        target = DATA / "price_snapshots.csv"
        backup = target.read_bytes()
        try:
            lines = backup.decode("utf-8").splitlines(keepends=True)
            del lines[-1]
            target.write_text("".join(lines), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(DESK / "verify_desk.py")],
                                  capture_output=True, text=True, timeout=120)
            self.assertNotEqual(proc.returncode, 0, "drift alarm did not fire")
            self.assertIn("drift alarm", proc.stdout)
        finally:
            target.write_bytes(backup)


if __name__ == "__main__":
    unittest.main(verbosity=2)
