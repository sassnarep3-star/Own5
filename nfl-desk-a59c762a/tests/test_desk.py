#!/usr/bin/env python3
"""Unit tests for the NFL Decision Console (session a59c762a).

Standard library only. The suite has two halves:

1. Positive tests: the committed data layer satisfies the invariants that the
   brief demands.
2. Negative controls: each of eight deliberate defects is injected into a
   throwaway copy of the desk, and the verifier must REJECT every one of them.
   A verifier that cannot fail is worthless, so these are the real tests.

Run:  python3 -m unittest discover -s nfl-desk-a59c762a/tests -v
"""
from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

DESK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(DESK)
sys.path.insert(0, DESK)

import build_data as bd  # noqa: E402
import verify_desk as vd  # noqa: E402


def rows(name):
    with open(os.path.join(DESK, "data", name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_rows(path, name, data, fields):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in data:
            w.writerow(r)


class CopyMixin:
    """Give each test a throwaway copy of the desk's data and pages."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="a59-test-")
        self.data = os.path.join(self.tmp, "data")
        self.pages = os.path.join(self.tmp, "pages")
        os.makedirs(self.data)
        os.makedirs(self.pages)
        for f in os.listdir(os.path.join(DESK, "data")):
            shutil.copy(os.path.join(DESK, "data", f), os.path.join(self.data, f))
        for f in os.listdir(DESK):
            if f.endswith(".html") or f == "style.css":
                shutil.copy(os.path.join(DESK, f), os.path.join(self.pages, f))
        # Stub the sibling desk entry pages that sources.html links to.
        for r in rows("desk_index.csv"):
            d = os.path.join(self.tmp, r["desk_id"])
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
                fh.write("<!doctype html><title>stub</title>")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_verify(self, skip="v6,v9"):
        env = dict(os.environ)
        env["A59_DATA_DIR"] = self.data
        env["A59_PAGE_DIR"] = self.pages
        env["A59_REPO_DIR"] = REPO
        env["A59_SKIP"] = skip
        p = subprocess.run([sys.executable, os.path.join(DESK, "verify_desk.py")],
                           capture_output=True, text=True, env=env)
        return p.returncode, p.stdout + p.stderr


class TestPositiveInvariants(unittest.TestCase):
    def test_results_feed_reconciles_with_the_official_standings(self):
        standings = bd.load_standings()
        games, mismatches = bd.load_results(standings)
        self.assertEqual(len(standings), 32)
        self.assertEqual(len(games), 150)
        self.assertEqual(mismatches, [], "a club does not reconcile: %s" % (mismatches,))

    def test_every_club_played_the_same_number_of_games_in_total(self):
        standings = bd.load_standings()
        games, _ = bd.load_results(standings)
        self.assertEqual(sum(s["gp"] for s in standings.values()), 2 * len(games))

    def test_availability_capture_is_the_published_row_count(self):
        av = bd.load_availability()
        self.assertEqual(len(av), 253)
        clubs = {r["club"] for r in av}
        self.assertEqual(len(clubs), 24)
        out = sum(1 for r in av if r["game_status"] == "Out")
        ques = sum(1 for r in av if r["game_status"] == "Questionable")
        self.assertEqual((out, ques), (9, 7))

    def test_every_requirement_row_carries_a_gate_or_is_satisfied(self):
        for r in rows("requirements.csv"):
            self.assertTrue(r["blocking_gate"] or r["status"] in ("MET", "REJECTED_AS_DESIGNED"),
                            "%s has neither a gate nor a settled status" % r["requirement_id"])

    def test_leaderboard_carries_no_score(self):
        for r in rows("leaderboard.csv"):
            self.assertEqual(r["signal_score"].strip(), "")
            self.assertEqual(r["staking_return"].strip(), "")
            self.assertEqual(r["n_prospective"], "0")

    def test_market_cells_are_blank_and_flagged(self):
        for r in rows("price_snapshots.csv"):
            self.assertEqual(r["opening_line"].strip(), "")
            self.assertEqual(r["closing_line"].strip(), "")
            self.assertTrue(r["flag"].strip())
        for r in rows("originated_lines.csv"):
            self.assertEqual(r["market_line"].strip(), "")
            self.assertEqual(r["difference_vs_market"].strip(), "")

    def test_every_correlation_publishes_n(self):
        for r in rows("correlations.csv"):
            self.assertTrue(r["n"].strip(), "%s has no n" % r["correlation_id"])
            self.assertTrue(r["source_url"].startswith("https://"))

    def test_lines_are_emitted_side_then_total_then_moneyline(self):
        seen = {}
        for r in rows("originated_lines.csv"):
            seen.setdefault(r["game_id"], []).append(int(r["market_order"]))
        self.assertEqual(len(seen), 13)
        for game, orders in seen.items():
            self.assertEqual(orders, [1, 2, 3], "%s is out of order" % game)

    def test_every_strategy_has_both_sides_of_the_change_our_mind_field(self):
        for r in rows("pre_registration.csv"):
            self.assertTrue(r["what_would_change_our_mind_a"].strip())
            self.assertTrue(r["what_would_change_our_mind_b"].strip())

    def test_depth_route_a_is_not_verified_for_all_32_clubs(self):
        dc = rows("depth_coverage.csv")
        verified = [r for r in dc if r["verified_for_all_32"] == "yes"]
        self.assertEqual(len(dc), 32)
        self.assertLess(len(verified), 32,
                        "the desk asserts route (a) is complete; the repository says it is not")

    def test_committed_tree_verifies_clean(self):
        p = subprocess.run([sys.executable, os.path.join(DESK, "verify_desk.py")],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)


class TestNegativeControls(CopyMixin, unittest.TestCase):
    """Each test injects one defect and requires the verifier to reject it."""

    def _mutate_csv(self, name, fn):
        path = os.path.join(self.data, name)
        with open(path, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            fields = rdr.fieldnames
            data = list(rdr)
        fn(data)
        write_rows(path, name, data, fields)

    def test_stripped_source_link_is_rejected(self):
        def strip(data):
            data[0]["repo_evidence_url"] = ""
            data[0]["official_source_url"] = ""
            data[0]["flag"] = ""
        self._mutate_csv("requirements.csv", strip)
        code, out = self.run_verify()
        self.assertNotEqual(code, 0, "a row without a source link must fail the verifier")
        self.assertIn("V2", out)

    def test_filled_blank_without_a_flag_is_rejected(self):
        def fill(data):
            data[0]["opening_line"] = "-3.5"
            data[0]["closing_line"] = "-3.5"
            data[0]["flag"] = ""
        self._mutate_csv("price_snapshots.csv", fill)
        code, out = self.run_verify()
        self.assertNotEqual(code, 0)
        self.assertIn("V14", out)

    def test_deleted_flag_is_rejected(self):
        def strip(data):
            for r in data:
                r["flag"] = ""
        self._mutate_csv("team_availability.csv", strip)
        code, out = self.run_verify()
        self.assertNotEqual(code, 0)
        self.assertIn("V10", out)

    def test_backtest_score_on_the_leaderboard_is_rejected(self):
        def fill(data):
            data[0]["signal_score"] = "0.44"
        self._mutate_csv("leaderboard.csv", fill)
        code, out = self.run_verify()
        self.assertNotEqual(code, 0)
        self.assertIn("V7", out)

    def test_broken_internal_link_is_rejected(self):
        page = os.path.join(self.pages, "index.html")
        with open(page, encoding="utf-8") as fh:
            text = fh.read().replace('href="requirements.html"',
                                     'href="does-not-exist.html"', 1)
        with open(page, "w", encoding="utf-8") as fh:
            fh.write(text)
        code, out = self.run_verify()
        self.assertNotEqual(code, 0)
        self.assertIn("V3", out)

    def test_wrong_row_count_is_rejected(self):
        def drop(data):
            data.pop()
        self._mutate_csv("results_2026.csv", drop)
        code, out = self.run_verify()
        self.assertNotEqual(code, 0)
        self.assertIn("V5", out)

    def test_non_official_source_is_rejected(self):
        def swap(data):
            data[0]["repo_evidence_url"] = "https://example.com/odds"
        self._mutate_csv("requirements.csv", swap)
        code, out = self.run_verify()
        self.assertNotEqual(code, 0)
        self.assertIn("V2", out)

    def test_tampered_model_output_is_rejected(self):
        def tamper(data):
            data[0]["sigma_points"] = "99.9"
            data[0]["hfa_points"] = "42.0"
        self._mutate_csv("shadow_backtest.csv", tamper)
        code, out = self.run_verify()
        self.assertNotEqual(code, 0, "a tampered model output must fail the build")
        self.assertIn("V13", out)


class TestModelMath(unittest.TestCase):
    def test_rating_fit_reproduces_the_training_margins(self):
        standings = bd.load_standings()
        games, _ = bd.load_results(standings)
        teams = sorted(standings)
        train = [g for g in games if g["week"] <= 8]
        ratings, hfa, sigma, resid = bd.fit_ratings(train, teams)
        self.assertAlmostEqual(sum(ratings.values()), 0.0, places=6)
        self.assertGreater(sigma, 5.0)
        self.assertLess(sigma, 25.0)
        self.assertEqual(len(resid), len(train))

    def test_home_field_is_estimated_not_assumed(self):
        standings = bd.load_standings()
        games, _ = bd.load_results(standings)
        teams = sorted(standings)
        train = [g for g in games if g["week"] <= 8]
        ratings, hfa, sigma, _ = bd.fit_ratings(train, teams)
        self.assertGreater(hfa, 0.0)
        self.assertLess(hfa, 4.0)

    def test_neutral_site_games_carry_no_home_field_term(self):
        standings = bd.load_standings()
        games, _ = bd.load_results(standings)
        neutral = [g for g in games if g["neutral"]]
        self.assertEqual(len(neutral), 8)
        self.assertIn(("NE", "DET"), {(g["away"], g["home"]) for g in neutral})

    def test_probability_is_a_probability(self):
        for r in rows("originated_lines.csv"):
            if r["probability"]:
                p = float(r["probability"])
                self.assertGreater(p, 0.0)
                self.assertLess(p, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
