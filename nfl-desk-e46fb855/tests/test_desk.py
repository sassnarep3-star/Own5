"""Unit tests for the e46fb855 desk.

These prove the arithmetic, the model and the honesty rules, not the numbers
themselves: the numbers are proved row by row against the official sources by
verify.py and published on the audit page.
"""
from __future__ import annotations

import csv
import hashlib
import math
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engine  # noqa: E402
import content  # noqa: E402

DATA = ROOT / "data"


def read(name):
    with open(DATA / name, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


class TestStatistics(unittest.TestCase):
    def test_pearson_perfect_and_inverse(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        self.assertAlmostEqual(engine.pearson(xs, xs), 1.0)
        self.assertAlmostEqual(engine.pearson(xs, list(reversed(xs))), -1.0)

    def test_pearson_known_value(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [2.0, 4.0, 5.0, 4.0, 5.0]
        r = engine.pearson(xs, ys)
        self.assertTrue(0.6 < r < 0.8)

    def test_fisher_ci_brackets_the_estimate(self):
        r = engine.pearson([1, 2, 3, 4, 5, 6], [2, 1, 4, 3, 6, 5])
        lo, hi = engine.fisher_ci(r, 6)
        self.assertLess(lo, r)
        self.assertGreater(hi, r)

    def test_binomial_two_sided_is_symmetric_at_the_centre(self):
        p = engine.binom_two_sided_p(5, 10, 0.5)
        self.assertAlmostEqual(p, 1.0, places=6)

    def test_binomial_two_sided_detects_an_extreme(self):
        self.assertLess(engine.binom_two_sided_p(10, 10, 0.5), 0.01)

    def test_wilson_interval_contains_the_estimate(self):
        lo, hi = engine.wilson_interval(70, 100)
        self.assertLess(lo, 0.70)
        self.assertGreater(hi, 0.70)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 1.0)

    def test_holm_is_monotone_and_no_smaller_than_raw(self):
        raw = [0.01, 0.02, 0.04, 0.5]
        adj = engine.holm(raw)
        for a, b in zip(adj, raw):
            self.assertGreaterEqual(a, b - 1e-12)
        self.assertLessEqual(adj[0], adj[1])
        self.assertLessEqual(adj[1], adj[2])
        self.assertLessEqual(adj[2], adj[3])

    def test_american_price_round_trip(self):
        self.assertAlmostEqual(engine.american_from_prob(0.5), -100.0, places=6)
        self.assertAlmostEqual(engine.american_from_prob(0.75), -300.0, places=6)
        self.assertAlmostEqual(engine.american_from_prob(0.25), 300.0, places=6)


class TestLinearAlgebra(unittest.TestCase):
    def test_solve_recovers_a_known_solution(self):
        a = [[4.0, 1.0], [1.0, 3.0]]
        x = engine.solve(a, [1.0, 2.0])
        self.assertAlmostEqual(4 * x[0] + x[1], 1.0, places=9)
        self.assertAlmostEqual(x[0] + 3 * x[1], 2.0, places=9)

    def test_inverse_times_matrix_is_identity(self):
        a = [[4.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 2.0]]
        inv = engine.mat_inverse(a)
        for i in range(3):
            for j in range(3):
                expected = 1.0 if i == j else 0.0
                self.assertAlmostEqual(sum(a[i][k] * inv[k][j] for k in range(3)),
                                       expected, places=9)

    def test_ridge_makes_an_unidentifiable_schedule_solvable(self):
        # two rounds in which every team has one home game and one away game:
        # home advantage is not separable from team strength without a penalty
        rows, ys = [], []
        n = 6
        for i in range(n):
            row = [0.0] * (n + 1)
            row[i] = 1.0
            row[(i + 1) % n] = -1.0
            row[n] = 1.0
            rows.append(row)
            ys.append(3.0)
        a, b = engine.normal_equations(rows, ys, n, 0.0)
        with self.assertRaises(ValueError):
            engine.solve(a, b)
        a2, b2 = engine.normal_equations(rows, ys, n, engine.RIDGE)
        sol = engine.solve(a2, b2)
        self.assertEqual(len(sol), n + 1)


class TestRatingModel(unittest.TestCase):
    def test_ratings_recover_a_planted_effect(self):
        # Four teams, planted ratings -6, -2, +2, +6, home field +3, and every
        # pair meeting once at each venue.
        teams = ["A", "B", "C", "D"]
        truth = {"A": -6.0, "B": -2.0, "C": 2.0, "D": 6.0}
        hfa = 3.0
        tix = {t: i for i, t in enumerate(teams)}
        rows, ys = [], []
        for i, h in enumerate(teams):
            for a in teams:
                if a == h:
                    continue
                row = [0.0] * 5
                row[tix[h]] = 1.0
                row[tix[a]] = -1.0
                row[4] = 1.0
                rows.append(row)
                ys.append(truth[h] - truth[a] + hfa)
        # With no penalty at all the system is singular: adding the same constant
        # to every rating leaves every margin unchanged. A negligible penalty
        # makes it solvable without materially moving the answer, so the
        # estimator can be checked for bias.
        with self.assertRaises(ValueError):
            engine.solve(*engine.normal_equations(rows, ys, 4, 0.0))
        sol = engine.solve(*engine.normal_equations(rows, ys, 4, 1e-9))
        recovered = {t: sol[tix[t]] - sum(sol[tix[x]] for x in teams) / 4 for t in teams}
        for t in teams:
            self.assertAlmostEqual(recovered[t], truth[t], places=4)
        self.assertAlmostEqual(sol[4], hfa, places=4)

        # penalised: the same fit must shrink every rating toward zero
        shrunk = engine.solve(*engine.normal_equations(rows, ys, 4, engine.RIDGE))
        centre = sum(shrunk[tix[x]] for x in teams) / 4
        for t in teams:
            self.assertLess(abs(shrunk[tix[t]] - centre), abs(truth[t]),
                            "the ridge penalty should shrink each rating toward zero")

    def test_neutral_site_games_are_excluded_from_home_field(self):
        markets = read("originated_markets.csv")
        mins = [m for m in markets if "MIN" in m["matchup"] and "SF" in m["matchup"]]
        self.assertTrue(mins, "the Mexico City game should be in the week-11 slate")
        for m in mins:
            self.assertEqual(m["neutral_site"], "YES")
            self.assertIn("hfa=0.0000", m["model_inputs"],
                          "a neutral-site market must not carry a home-field term")


class TestHonestyRules(unittest.TestCase):
    def test_no_market_price_was_invented(self):
        for row in read("originated_markets.csv"):
            self.assertEqual(row["market_line"], "")
            self.assertEqual(row["difference_model_minus_market"], "")
            self.assertIn("UNVERIFIED", row["market_line_status"])

    def test_no_roi_was_invented(self):
        for row in read("strategies.csv"):
            self.assertEqual(row["roi"], "")
            self.assertIn("UNVERIFIED", row["roi_status"])
            self.assertEqual(row["certified"], "NO")

    def test_staking_board_is_empty_by_design(self):
        for row in read("leaderboard_staking.csv"):
            self.assertEqual(row["roi"], "")
            self.assertEqual(row["clv"], "")
            self.assertEqual(row["stake"], "")

    def test_pending_games_carry_no_score(self):
        for row in read("results_pending.csv"):
            self.assertEqual(row["away_score"], "")
            self.assertEqual(row["home_score"], "")

    def test_houston_has_no_depth_rows(self):
        teams_with_slots = {r["team"] for r in read("depth_slots.csv") if r["position"]}
        self.assertNotIn("HOU", teams_with_slots)

    def test_clubs_without_a_game_status_are_blank_not_zero(self):
        rows = read("team_availability.csv")
        self.assertEqual(len(rows), 32)
        for r in rows:
            if r["game_status_published"] == "NO":
                self.assertEqual(r["players_out"], "")
                self.assertEqual(r["net_injury_count"], "")
                self.assertIn("UNVERIFIED", r["status_note"])

    def test_withheld_correlations_are_not_republished_as_values(self):
        withheld = {r["id"] for r in read("correlations_withheld.csv")}
        for r in read("correlations.csv"):
            self.assertNotIn(r["correlation_id"], withheld)
        for r in read("correlations.csv"):
            self.assertEqual(r["input_tier"], "OFFICIAL")
            self.assertTrue(int(r["n"]) >= 4)


class TestDataIntegrity(unittest.TestCase):
    def test_feed_reconciles_to_the_official_standings(self):
        feed = read("results_feed.csv")
        std = {r["team"]: r for r in read("standings_official.csv")}
        derived = {t: [0, 0, 0, 0, 0] for t in std}  # W, L, T, PF, PA
        for f in feed:
            # compare as integers: as strings, "23" sorts before "6"
            for side, other in (("home", "away"), ("away", "home")):
                d = derived[f[side]]
                mine, theirs = int(f[f"{side}_score"]), int(f[f"{other}_score"])
                d[3] += mine
                d[4] += theirs
                if mine > theirs:
                    d[0] += 1
                elif mine < theirs:
                    d[1] += 1
                else:
                    d[2] += 1
        for team, row in std.items():
            for i, key in enumerate(("w", "l", "t", "pf", "pa")):
                self.assertEqual(int(float(row[key])), derived[team][i],
                                 f"{team}: {key} does not reconcile")

    def test_every_feed_row_has_a_margin_and_total(self):
        for f in read("results_feed.csv"):
            self.assertEqual(int(f["home_margin"]),
                             int(f["home_score"]) - int(f["away_score"]))
            self.assertEqual(int(f["total_points"]),
                             int(f["home_score"]) + int(f["away_score"]))

    def test_originated_markets_cover_the_whole_slate(self):
        slate = read("slate_wk11.csv")
        markets = read("originated_markets.csv")
        self.assertEqual(len(slate) * 3, len(markets))
        for g in slate:
            ids = {m["market_type"] for m in markets if m["game_id"] == g["game_id"]}
            self.assertEqual(ids, {"SIDE", "TOTAL", "MONEYLINE"})

    def test_origination_order_is_side_then_total_then_moneyline(self):
        steps = {(m["market_type"]): int(m["origination_order"])
                 for m in read("originated_markets.csv")}
        self.assertEqual(steps["SIDE"], 1)
        self.assertEqual(steps["TOTAL"], 2)
        self.assertEqual(steps["MONEYLINE"], 3)

    def test_build_is_deterministic(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(DATA.glob("*.csv"))}
        engine.build()
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(DATA.glob("*.csv"))}
        self.assertEqual(before, after, "a rebuild changed the committed data")

    def test_registers_are_complete(self):
        self.assertEqual(len(content.REQUIREMENTS), len(read("requirements.csv")))
        self.assertEqual(len(content.QUESTIONS), len(read("questions.csv")))
        self.assertEqual(len(content.SUGGESTIONS), len(read("suggestions.csv")))
        for r in content.REQUIREMENTS:
            self.assertEqual(len(r), 6, f"{r[0]} is missing a field")
            self.assertIn(r[2], ("met", "partial", "blocked"))
            self.assertTrue(r[5].endswith(".html"))


class TestSite(unittest.TestCase):
    def test_every_page_exists_and_carries_the_masthead(self):
        pages = sorted(p.name for p in ROOT.glob("*.html"))
        self.assertGreaterEqual(len(pages), 21)
        for name in pages:
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("OWN5", html, f"{name} is missing the masthead")
            self.assertIn("</html>", html)

    def test_nav_links_resolve(self):
        pages = {p.name for p in ROOT.glob("*.html")}
        import re
        for name in pages:
            html = (ROOT / name).read_text(encoding="utf-8")
            for target in re.findall(r'href="([a-z0-9\-]+\.html)"', html):
                self.assertIn(target, pages, f"{name} links to a missing page")


if __name__ == "__main__":
    unittest.main(verbosity=2)
