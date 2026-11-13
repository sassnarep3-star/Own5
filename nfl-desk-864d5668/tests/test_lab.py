#!/usr/bin/env python3
"""Unit tests for the Own5 NFL Own-Line Lab.

Run:  python3 -m unittest discover -s tests -v
"""
from __future__ import annotations
import csv
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import statslib as S
import raw_inputs as R
import injuries_raw as IR
import depthcharts_raw as DC

DATA = os.path.join(ROOT, "data")


def load(name):
    with open(os.path.join(DATA, name + ".csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestStatslib(unittest.TestCase):
    """Every closed-form statistic is checked against a hand-computed value."""

    def test_mean_variance_stdev(self):
        xs = [1, 2, 3, 4]
        self.assertAlmostEqual(S.mean(xs), 2.5)
        self.assertAlmostEqual(S.variance(xs), 5.0 / 3.0)
        self.assertAlmostEqual(S.stdev(xs), math.sqrt(5.0 / 3.0))

    def test_pearson_perfect_and_negative(self):
        self.assertAlmostEqual(S.pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(S.pearson([1, 2, 3], [6, 4, 2]), -1.0)

    def test_pearson_constant_returns_none(self):
        self.assertIsNone(S.pearson([1, 1, 1], [1, 2, 3]))

    def test_norm_ppf_matches_known_quantiles(self):
        self.assertAlmostEqual(S.norm_ppf(0.975), 1.959963984540054, places=9)
        self.assertAlmostEqual(S.norm_ppf(0.5), 0.0, places=9)
        self.assertAlmostEqual(S.norm_ppf(0.995), 2.5758293035489004, places=7)

    def test_norm_cdf_round_trips_ppf(self):
        for p in (0.01, 0.2, 0.5, 0.8, 0.99):
            self.assertAlmostEqual(S.norm_cdf(S.norm_ppf(p)), p, places=9)

    def test_binomial_tail_is_exact(self):
        # P(X >= 7) for Bin(10, 0.5) = (120+45+10+1)/1024
        self.assertAlmostEqual(S.binom_sf(7, 10, 0.5), 176.0 / 1024.0, places=12)

    def test_binomial_pmf_sums_to_one(self):
        total = sum(S.binom_pmf(k, 12, 0.37) for k in range(13))
        self.assertAlmostEqual(total, 1.0, places=12)

    def test_pearson_p_against_known_t_value(self):
        # r = 0.5, n = 20 -> t = 0.5*sqrt(18/0.75) = 2.4495, df = 18
        p = S.pearson_p(0.5, 20)
        self.assertTrue(0.02 < p < 0.03, p)

    def test_t_sf_monotone(self):
        prev = 1.0
        for t in (0.5, 1.0, 1.5, 2.0, 3.0):
            v = S._t_sf(t, 10)
            self.assertLess(v, prev)
            prev = v

    def test_wilson_interval_brackets_the_point_estimate(self):
        lo, hi = S.wilson_ci(60, 89)
        self.assertLess(lo, 60 / 89)
        self.assertGreater(hi, 60 / 89)
        self.assertGreater(lo, 0.0)
        self.assertLess(hi, 1.0)

    def test_wilson_interval_widens_as_n_shrinks(self):
        a = S.wilson_ci(7, 10)
        b = S.wilson_ci(70, 100)
        self.assertGreater(a[1] - a[0], b[1] - b[0])

    def test_skew_and_kurtosis_of_a_binary_series(self):
        # 75 wins, 25 losses
        xs = [1.0] * 75 + [0.0] * 25
        self.assertAlmostEqual(S.skewness(xs), (1 - 2 * 0.75) / math.sqrt(0.75 * 0.25),
                               places=9)
        self.assertAlmostEqual(S.kurtosis(xs), (1 - 6 * 0.75 * 0.25) / (0.75 * 0.25),
                               places=9)

    def test_deflated_sharpe_penalises_more_trials(self):
        small = S.deflated_sharpe(0.34, 89, -0.73, -1.48, 2)
        large = S.deflated_sharpe(0.34, 89, -0.73, -1.48, 200)
        self.assertGreater(small, large)

    def test_deflated_sharpe_in_unit_interval(self):
        v = S.deflated_sharpe(0.34, 89, -0.73, -1.48, 9)
        self.assertTrue(0.0 <= v <= 1.0)

    def test_holm_bonferroni_is_monotone_and_capped(self):
        res = S.holm_bonferroni([0.001, 0.02, 0.04, 0.9])
        adj = [r[2] for r in res]
        for a, b in zip(adj, adj[1:]):
            self.assertLessEqual(a, b)
        self.assertLessEqual(max(adj), 1.0)
        self.assertTrue(res[0][3])

    def test_holm_stops_at_the_first_failure(self):
        res = S.holm_bonferroni([0.001, 0.02, 0.9])
        self.assertTrue(res[0][3])
        self.assertFalse(res[2][3])

    def test_solve_linear_recovers_a_known_solution(self):
        A = [[2.0, 1.0], [1.0, 3.0]]
        b = [3.0, 5.0]
        x = S.solve_linear(A, b)
        self.assertAlmostEqual(2 * x[0] + x[1], 3.0, places=9)
        self.assertAlmostEqual(x[0] + 3 * x[1], 5.0, places=9)

    def test_ridge_shrinks_towards_zero(self):
        X = [[1.0, 0.0], [0.0, 1.0]]
        y = [10.0, -10.0]
        w0 = S.ridge_solve(X, y, 0.0)
        w5 = S.ridge_solve(X, y, 5.0)
        w50 = S.ridge_solve(X, y, 50.0)
        self.assertAlmostEqual(w0[0], 10.0, places=9)
        self.assertLess(abs(w5[0]), abs(w0[0]))
        self.assertLess(abs(w50[0]), abs(w5[0]))

    def test_required_n_decreases_with_a_bigger_edge(self):
        a = S.required_n(0.55, 0.5238095238095238)
        b = S.required_n(0.60, 0.5238095238095238)
        self.assertGreater(a, b)
        self.assertGreater(a, 1000)


class TestRawInputs(unittest.TestCase):

    def test_thirty_two_teams_with_conference_and_division(self):
        self.assertEqual(len(R.TEAMS), 32)
        confs = set(v[1] for v in R.TEAMS.values())
        self.assertEqual(confs, {"AFC", "NFC"})
        by_div = {}
        for tm, (_n, c, d) in R.TEAMS.items():
            by_div.setdefault((c, d), []).append(tm)
        self.assertEqual(len(by_div), 8)
        for teams in by_div.values():
            self.assertEqual(len(teams), 4)

    def test_standings_cover_every_team(self):
        self.assertEqual(set(R.STANDINGS), set(R.TEAMS))
        for tm, rec in R.STANDINGS.items():
            w, l, t, pct, pf, pa = rec
            self.assertGreaterEqual(w + l + t, 1)
            self.assertLessEqual(w + l + t, 10)

    def test_ledger_scores_are_integers_or_none(self):
        for wk, a, h, ap, hp, date, neutral in R.LEDGER:
            self.assertIn(a, R.TEAMS)
            self.assertIn(h, R.TEAMS)
            self.assertNotEqual(a, h)
            self.assertIn(wk, range(1, 11))
            for v in (ap, hp):
                self.assertTrue(v is None or (isinstance(v, int) and 0 <= v < 100))

    def test_ledger_has_no_duplicate_matchups_in_a_week(self):
        seen = set()
        for wk, a, h, _ap, _hp, _d, _n in R.LEDGER:
            key = (wk, tuple(sorted((a, h))))
            self.assertNotIn(key, seen, "duplicate game %s" % (key,))
            seen.add(key)

    def test_byes_only_contain_real_teams(self):
        for wk, teams in R.BYES.items():
            for tm in teams:
                self.assertIn(tm, R.TEAMS)
            self.assertEqual(len(teams), len(set(teams)))

    def test_ledger_source_url_exists_for_every_week(self):
        for wk in range(1, 11):
            self.assertTrue(R.LEDGER_SRC[wk].startswith("https://www.nfl.com/"))


class TestInjuriesRaw(unittest.TestCase):

    def test_row_shape(self):
        for row in IR.INJURIES:
            self.assertEqual(len(row), 6)
            team, player, pos, injury, prac, game = row
            self.assertIn(team, R.TEAMS)
            self.assertTrue(player.strip())
            self.assertIsInstance(prac, str)

    def test_practice_status_uses_official_wording(self):
        allowed = {IR.FULL, IR.LIM, IR.DNP, ""}
        for _t, _p, _pos, _i, prac, _g in IR.INJURIES:
            self.assertIn(prac, allowed)

    def test_game_status_uses_issued_values_or_blank(self):
        allowed = {"", "Out", "Doubtful", "Questionable"}
        for _t, _p, _pos, _i, _pr, game in IR.INJURIES:
            self.assertIn(game, allowed)

    def test_no_duplicate_player_within_a_team(self):
        seen = set()
        for team, player, *_ in IR.INJURIES:
            key = (team, player)
            self.assertNotIn(key, seen, key)
            seen.add(key)


class TestDepthChartsRaw(unittest.TestCase):

    def test_every_charted_club_has_a_url_and_a_stamp_slot(self):
        for tm in DC.DEPTH:
            self.assertIn(tm, DC.DC_META)
            url, stamp = DC.DC_META[tm]
            self.assertTrue(url.startswith("https://www."))
            self.assertIsInstance(stamp, str)

    def test_meta_and_depth_keys_agree(self):
        self.assertEqual(set(DC.DEPTH), set(DC.DC_META))

    def test_no_empty_position_groups(self):
        for tm, slots in DC.DEPTH.items():
            for unit, pos, chain in slots:
                self.assertIn(unit, ("Offense", "Defense"))
                self.assertTrue(pos.strip(), tm)
                self.assertIsInstance(chain, list)

    def test_houston_is_the_only_club_without_a_chart(self):
        self.assertNotIn("HOU", DC.DEPTH)
        self.assertTrue(DC.HOU_DC_URL.startswith("https://www.houstontexans.com"))


class TestGeneratedTables(unittest.TestCase):

    def test_ledger_counts(self):
        rows = load("ledger")
        self.assertEqual(len(rows), 150)
        self.assertEqual(sum(1 for r in rows if r["status"] == "FINAL"), 137)
        self.assertEqual(sum(1 for r in rows if r["status"] == "scheduled"), 13)

    def test_reconciliation_is_clean_for_all_32(self):
        for r in load("standings_reconciliation"):
            self.assertEqual(r["reconciles"], "YES", r["team"])
            self.assertEqual(r["differences"], "none")

    def test_injury_table_is_a_faithful_copy(self):
        rows = load("injuries")
        self.assertEqual(len(rows), len(IR.INJURIES))
        for got, (_t, player, _p, _i, prac, game) in zip(rows, IR.INJURIES):
            self.assertEqual(got["player"], player)
            self.assertEqual(got["practice_status_as_published"], prac)
            self.assertEqual(got["game_status_as_published"], game)

    def test_own_lines_never_invent_a_market_price(self):
        for r in load("own_lines"):
            self.assertEqual(r["market_spread_home"], "")
            self.assertEqual(r["market_total"], "")
            self.assertEqual(r["market_moneyline"], "")
            self.assertEqual(r["closing_line_value"], "")
            self.assertNotEqual(r["own_spread_home_pts"], "")

    def test_signal_hit_rates_are_reproducible(self):
        for r in load("signal_tests"):
            g, w = int(r["graded_bets"]), int(r["wins"])
            self.assertAlmostEqual(w / g, float(r["hit_rate"]), places=3)

    def test_break_even_rate_is_minus_110(self):
        # risk 1.00 to win 0.909: break-even = 1.00 / (1.00 + 0.909)
        self.assertAlmostEqual(1.0 / (1.0 + 100.0 / 110.0),
                               0.5238095238095238, places=12)

    def test_no_signal_is_marked_promoted(self):
        for r in load("leaderboard"):
            self.assertFalse(r["reward_tier"].startswith("promoted"),
                             r["signal"])

    def test_every_flag_has_a_unique_id(self):
        ids = [r["flag_id"] for r in load("flags")]
        self.assertEqual(len(ids), len(set(ids)))

    def test_depth_covers_31_clubs(self):
        teams = set(r["team"] for r in load("depth_by_team"))
        self.assertEqual(len(teams), 32)
        charted = set(r["team"] for r in load("depth_detail"))
        self.assertEqual(len(charted), 31)
        self.assertNotIn("HOU", charted)

    def test_glossary_defines_everything_it_uses(self):
        rows = load("glossary")
        terms = set(r["term"] for r in rows)
        for t in ("Own line", "Deflated Sharpe Ratio", "Deficiency points",
                  "Closing line value", "Break-even hit rate"):
            self.assertIn(t, terms)


if __name__ == "__main__":
    unittest.main()
