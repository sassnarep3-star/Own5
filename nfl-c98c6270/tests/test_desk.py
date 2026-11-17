#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Own5 NFL Decision Console (session c98c6270).

Run with:  python3 -W ignore -m unittest discover -s tests

The tests split into four groups, mirroring the four promises the desk makes:

  A. statistics    - the maths is right, and it is exact where it claims to be
  B. honesty       - no price, score, depth rank or ROI is ever invented
  C. provenance    - every published row carries a source or an UNVERIFIED badge
  D. reproduction  - the build is deterministic and the pages hang together
"""

from __future__ import annotations

import csv
import math
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)
DATA = os.path.join(DESK, "data")
sys.path.insert(0, DESK)

import content as C  # noqa: E402
import engine as E  # noqa: E402


def rows_of(text):
    lines = [l for l in text.strip().splitlines() if l.strip()]
    header = lines[0].split("|")
    return [dict(zip(header, l.split("|"))) for l in lines[1:]]


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def pages():
    return sorted(f for f in os.listdir(DESK) if f.endswith(".html"))


# ---------------------------------------------------------------------------
# A. statistics
# ---------------------------------------------------------------------------

class TestStatistics(unittest.TestCase):

    def test_binomial_tail_is_a_probability(self):
        for n in (10, 50, 200, 1000):
            for k in (0, n // 2, n):
                p = E._binom_tail(k, n, 0.5)
                self.assertGreaterEqual(p, 0.0)
                self.assertLessEqual(p, 1.0)

    def test_binomial_tail_matches_known_values(self):
        # P(X >= 1) for n=10, p=0.5  = 1 - 0.5^10
        self.assertAlmostEqual(E._binom_tail(1, 10, 0.5), 1 - 0.5 ** 10, places=12)
        # P(X >= 10) for n=10 = 0.5^10
        self.assertAlmostEqual(E._binom_tail(10, 10, 0.5), 0.5 ** 10, places=12)
        # P(X >= 11) > n is impossible
        self.assertEqual(E._binom_tail(11, 10, 0.5), 0.0)

    def test_binomial_tail_does_not_overflow_at_large_n(self):
        # the original implementation raised OverflowError here
        self.assertIsInstance(E._binom_tail(2000, 4000, 0.5), float)
        self.assertGreaterEqual(E._binom_tail(2000, 4000, 0.5), 0.0)

    def test_binomial_tail_monte_carlo_agreement(self):
        import random
        rng = random.Random(20261117)
        n, p = 12, 0.4
        trials = 60000
        hits = sum(1 for _ in range(trials)
                   if sum(1 for _ in range(n) if rng.random() < p) >= 7)
        self.assertAlmostEqual(E._binom_tail(7, n, p), hits / trials, delta=0.01)

    def test_pearson_matches_a_hand_computed_value(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        ys = [2.0, 4.0, 6.0, 8.0]
        r, lo, hi = E.pearson(xs, ys)
        self.assertAlmostEqual(r, 1.0, places=5)
        r2, _, _ = E.pearson(xs, ys[::-1])
        self.assertAlmostEqual(r2, -1.0, places=5)

    def test_pearson_returns_none_when_there_is_no_variance(self):
        self.assertEqual(E.pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]),
                         (None, None, None))
        self.assertEqual(E.pearson([1.0, 2.0], [1.0, 2.0]), (None, None, None))

    def test_pearson_is_bounded(self):
        import random
        rng = random.Random(7)
        for _ in range(200):
            xs = [rng.random() for _ in range(12)]
            ys = [rng.random() for _ in range(12)]
            r, lo, hi = E.pearson(xs, ys)
            self.assertGreaterEqual(r, -1.0)
            self.assertLessEqual(r, 1.0)
            self.assertLessEqual(lo, hi)

    def test_fisher_interval_contains_the_point_estimate(self):
        import random
        rng = random.Random(11)
        for _ in range(100):
            xs = [rng.random() for _ in range(64)]
            ys = [rng.random() for _ in range(64)]
            r, lo, hi = E.pearson(xs, ys)
            if r is None:
                continue
            self.assertLessEqual(lo, r)
            self.assertGreaterEqual(hi, r)

    def test_fisher_interval_narrows_as_n_grows(self):
        import random
        rng = random.Random(3)
        xs = [rng.random() * 10 for _ in range(2000)]
        ys = [x * 0.5 + rng.random() for x in xs]
        _, lo1, hi1 = E.pearson(xs[:20], ys[:20])
        _, lo2, hi2 = E.pearson(xs, ys)
        self.assertGreater(hi1 - lo1, hi2 - lo2)

    def test_power_curve_is_monotone_in_n(self):
        rows = read("luck_power.csv")
        powers = [float(r["power_at_true_55pct"]) for r in rows]
        self.assertEqual(powers, sorted(powers))
        self.assertLess(min(powers), 0.5)
        self.assertGreater(max(powers), 0.75)

    def test_the_critical_value_always_sits_below_alpha(self):
        # the bar is set so a break-even bettor clears it less than 1 time in 20
        for r in read("luck_power.csv"):
            self.assertLess(float(r["break_even_runner_probability_of_passing"]), 0.05)

    def test_the_critical_value_never_exceeds_the_sample(self):
        for r in read("luck_power.csv"):
            self.assertLessEqual(int(r["critical_hits_at_alpha_0.05"]),
                                 int(r["n_bets"]))

    def test_residual_equals_actual_minus_pythagorean(self):
        for r in read("luck_panel.csv"):
            self.assertAlmostEqual(
                float(r["win_pct_residual"]),
                float(r["actual_win_pct"]) - float(r["pythagorean_win_pct"]),
                delta=2e-4)

    def test_one_score_win_pct_is_a_real_rate(self):
        for r in read("luck_panel.csv"):
            g, w = int(r["one_score_games"]), int(r["one_score_wins"])
            self.assertLessEqual(w, g)
            if g:
                self.assertAlmostEqual(float(r["one_score_win_pct"]), w / g,
                                       places=4)

    def test_american_odds_round_trip(self):
        # the moneyline is derived from the side probability; check the shape
        for r in read("originated_markets.csv"):
            if r["market"] != "home moneyline":
                continue
            p = float(r["model_probability"])
            ml = int(r["model_value"])
            if p > 0.5:
                self.assertLess(ml, 0)
                self.assertAlmostEqual(p, -ml / (-ml + 100.0), delta=0.01)
            else:
                self.assertGreater(ml, 0)
                self.assertAlmostEqual(p, 100.0 / (ml + 100.0), delta=0.01)


# ---------------------------------------------------------------------------
# B. honesty
# ---------------------------------------------------------------------------

class TestHonesty(unittest.TestCase):

    def test_no_market_price_appears_anywhere(self):
        for r in read("originated_markets.csv"):
            self.assertEqual(r["market_value"], "")
            self.assertEqual(r["difference"], "")

    def test_no_roi_clv_or_record_is_published(self):
        ban = re.compile(r"\b(roi|roas|closing line value|clv)\s*[:=]\s*\d", re.I)
        for p in pages():
            text = open(os.path.join(DESK, p), encoding="utf-8").read()
            self.assertIsNone(ban.search(text), p)

    def test_no_leaderboard_row_is_ranked(self):
        for r in read("leaderboard_divisions.csv"):
            self.assertEqual(int(r["rows_ranked"]), 0)
        for r in read("leaderboard_signal.csv") + read("leaderboard_staking.csv"):
            self.assertNotIn("ranked", r["status"].lower())

    def test_no_strategy_is_certified(self):
        for s in rows_of(C.STRATEGIES_CSV):
            self.assertEqual(s["status"], "PAPER")

    def test_no_suggestion_is_implemented(self):
        for s in rows_of(C.SUGGESTIONS_CSV):
            self.assertEqual(s["decision_status"], "PROPOSED")

    def test_depth_is_never_derived_from_jersey_number(self):
        for s in read("depth_slots.csv"):
            if s["rank1"]:
                self.assertFalse(re.match(r"^\d", s["rank1"]),
                                 "jersey-number depth: %s" % s["rank1"])

    def test_houston_is_not_transcribed_from_an_image(self):
        hou = [s for s in read("depth_slots.csv") if s["club"] == "HOU"]
        self.assertEqual(len(hou), 1)
        self.assertEqual(hou[0]["rank1"], "")
        self.assertIn("image", hou[0]["note"])

    def test_empty_slots_stay_empty(self):
        for s in read("depth_slots.csv"):
            if s["empty_first_string"] == "yes":
                self.assertEqual(s["rank1"], "")

    def test_shared_slots_keep_both_names(self):
        shared = [s for s in read("depth_slots.csv") if s["shared_rank1"] == "yes"]
        self.assertTrue(shared)
        for s in shared:
            self.assertIn("+", s["rank1"])

    def test_as_of_dates_are_only_published_where_the_club_publishes_them(self):
        dated = [s for s in read("depth_slots.csv") if s["as_of_published"]]
        self.assertTrue(dated)
        self.assertLess(len(dated), 200)  # only 4 of 31 clubs date their chart

    def test_pending_games_are_never_scored(self):
        for r in read("results_feed.csv"):
            if r["status"] != "FINAL":
                self.assertEqual(r["away_score"], "")
                self.assertEqual(r["home_score"], "")

    def test_injury_levels_are_never_published_as_a_delta_that_does_not_exist(self):
        for r in read("injuries.csv"):
            if not r["second_read_utc"]:
                self.assertTrue(r["delta"].startswith("not covered"))

    def test_withheld_correlation_never_shows_a_number(self):
        for r in read("correlations.csv"):
            if r["published"] == "withheld":
                self.assertEqual(r["pearson_r"], "")
                self.assertTrue(r["withheld_reason"])

    def test_a_missing_replacement_is_called_unknown_not_available(self):
        for r in read("replacement_depth.csv"):
            if r["depth_rank"] == "1" and not r["replacement_named"]:
                self.assertIn("no replacement named", r["status"])


# ---------------------------------------------------------------------------
# C. provenance
# ---------------------------------------------------------------------------

class TestProvenance(unittest.TestCase):

    BLOCKED_HOSTS = ("raw.githubusercontent", "localhost", "127.0.0.1")

    def test_every_depth_row_has_an_official_club_source(self):
        for s in read("depth_slots.csv"):
            if s["club"] == "HOU":
                continue
            self.assertTrue(s["source_url"].endswith("/team/depth-chart"))
            self.assertTrue(s["captured_utc"])

    def test_every_result_row_has_an_official_source(self):
        for r in read("results_feed.csv"):
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"),
                            r["game_id"])

    def test_every_injury_row_cites_the_official_report(self):
        for r in read("injuries.csv"):
            self.assertIn("/injuries/league/", r["source_url"])

    def test_every_requirement_names_the_gate_that_blocks_it(self):
        gates = {g["id"] for g in rows_of(C.GATES_CSV)}
        for r in rows_of(C.REQUIREMENTS_CSV):
            gid = r["blocking_gate"].split()[0]
            self.assertTrue(gid in gates or gid in ("none", "n/a"),
                            "%s: %s" % (r["id"], r["blocking_gate"]))

    def test_every_flag_points_at_evidence(self):
        files = set(os.listdir(DATA))
        for f in rows_of(C.FLAGS_CSV):
            self.assertTrue(f["evidence"])
            for token in re.findall(r"data/([A-Za-z0-9_.-]+)", f["evidence"]):
                self.assertIn(token, files, f["id"])

    def test_no_page_links_somewhere_unofficial_for_a_value(self):
        # values must come from nfl.com or a club domain, never a third party
        allowed = (".nfl.com",) + tuple(E.CLUB_URL[k].split("/")[2]
                                        for k in E.CLUB_URL)
        for r in read("depth_slots.csv"):
            host = r["source_url"].split("/")[2]
            self.assertIn(host, allowed, host)

    def test_every_page_body_row_badges_its_provenance(self):
        badge = re.compile(r'class="badge b-(source|computed|governance|unverified)"')
        for p in pages():
            html = open(os.path.join(DESK, p), encoding="utf-8").read()
            bodies = "".join(re.findall(r"<tbody>(.*?)</tbody>", html, re.S))
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", bodies, re.S):
                self.assertTrue(badge.search(tr), "%s: %s" % (p, tr[:60]))

    def test_no_page_links_to_a_blocked_host(self):
        for p in pages():
            html = open(os.path.join(DESK, p), encoding="utf-8").read()
            for host in self.BLOCKED_HOSTS:
                self.assertNotIn(host, html)


# ---------------------------------------------------------------------------
# D. reproduction
# ---------------------------------------------------------------------------

class TestReproduction(unittest.TestCase):

    def test_every_nav_page_exists(self):
        for f in pages():
            html = open(os.path.join(DESK, f), encoding="utf-8").read()
            for href in re.findall(r'class="navlink[^"]*" href="([^"]+)"', html):
                self.assertTrue(os.path.exists(os.path.join(DESK, href)), href)

    def test_every_page_is_reachable_from_the_nav(self):
        index = open(os.path.join(DESK, "index.html"), encoding="utf-8").read()
        nav = set(re.findall(r'class="navlink[^"]*" href="([^"]+)"', index))
        self.assertTrue(set(pages()) - {"index.html"} <= nav)

    def test_build_report_matches_the_data_on_disk(self):
        import json
        rep = json.load(open(os.path.join(DATA, "build_report.json"),
                             encoding="utf-8"))
        self.assertEqual(rep["originated_markets"],
                         len(read("originated_markets.csv")))
        machine = [s for s in read("depth_slots.csv") if s["club"] != "HOU"]
        self.assertEqual(rep["depth_rows"], len(machine))
        self.assertEqual(rep["requirements"], len(rows_of(C.REQUIREMENTS_CSV)))

    def test_standings_reconcile_for_every_club(self):
        for r in read("standings_reconciliation.csv"):
            self.assertEqual(r["match"], "yes", r["team"])

    def test_the_two_totals_estimators_are_distinct(self):
        per_game = {}
        for r in read("originated_markets.csv"):
            if r["market"] == "game total (estimator A)":
                per_game.setdefault(r["game_id"], {})["a"] = float(r["model_value"])
            if r["market"] == "game total (estimator B)":
                per_game.setdefault(r["game_id"], {})["b"] = float(r["model_value"])
        self.assertEqual(len(per_game), 13)
        self.assertTrue(any(abs(v["a"] - v["b"]) > 0.01 for v in per_game.values()))

    def test_origination_order_is_side_then_total_then_moneyline(self):
        steps = read("origination_steps.csv")
        for gid in sorted({s["game_id"] for s in steps}):
            got = [s["step"] for s in steps if s["game_id"] == gid]
            self.assertEqual(got, ["1", "2", "3"])
        for s in steps:
            if s["step"] == "3":
                self.assertEqual(s["depends_on"], "1 side")

    def test_ratings_are_centred(self):
        ratings = [float(r["rating"]) for r in read("team_ratings.csv")]
        self.assertAlmostEqual(sum(ratings) / len(ratings), 0.0, places=1)

    def test_engine_is_deterministic(self):
        # a second pass over the same inputs must give the same numbers
        slots = E.load_depth()
        first = [(s["club"], s["position"], s["rank1"]) for s in slots]
        second = [(s["club"], s["position"], s["rank1"]) for s in E.load_depth()]
        self.assertEqual(first, second)

    def test_css_and_js_assets_are_present(self):
        for f in ("style.css", "app.js", "favicon.svg"):
            self.assertTrue(os.path.exists(os.path.join(DESK, "assets", f)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
