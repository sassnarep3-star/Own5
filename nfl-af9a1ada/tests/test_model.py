"""Unit tests for the line-gate model and the build's hard invariants.

Run: python3 -m unittest discover -s nfl-af9a1ada/tests -v

Every test here exists because a real defect shipped past a review of this
desk at least once. The docstring names the defect.
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(DESK, "tools"))

from lib import (american_to_prob, devig_two_way, holm, inputs_hash,  # noqa: E402
                 pick_spread_winner, prob_to_american, total_result)

DATA = os.path.join(DESK, "data")


def read(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestPrices(unittest.TestCase):
    def test_american_prob_roundtrip(self):
        for p in (150, -150, 500, -500, 105, -105):
            self.assertAlmostEqual(prob_to_american(american_to_prob(p)), p, places=6)

    def test_devig_sums_to_one(self):
        a, b, over = devig_two_way(-250, 200)
        self.assertAlmostEqual(a + b, 1.0, places=12)
        self.assertGreater(over, 0.0)          # a book never prices a market at 100%

    def test_devig_rejects_a_free_market(self):
        a, b, over = devig_two_way(100, 100)
        self.assertAlmostEqual(a, 0.5, places=12)
        self.assertAlmostEqual(over, 0.0, places=12)

    def test_holm_is_monotone_and_bounded(self):
        out = holm({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertTrue(all(0 <= v <= 1 for v in out.values()))
        self.assertLessEqual(out["a"], out["b"])


class TestScoring(unittest.TestCase):
    def test_push_is_neither_side(self):
        self.assertEqual(pick_spread_winner(3.0, -3.0), "push")
        self.assertEqual(pick_spread_winner(4.0, -3.0), "home")
        self.assertEqual(pick_spread_winner(2.0, -3.0), "away")

    def test_total_push(self):
        self.assertEqual(total_result(44.0, 44.0), "push")
        self.assertEqual(total_result(45.0, 44.0), "over")


class TestRatings(unittest.TestCase):
    """The ratings must be a real opponent adjustment, not one number twice."""

    @classmethod
    def setUpClass(cls):
        cls.rows = read("ratings.csv")

    def test_every_club_present(self):
        self.assertEqual(len(self.rows), 32)

    def test_offence_sums_to_zero(self):
        # the published column is rounded to three decimals, so the identity
        # holds to within the rounding of 32 rows rather than exactly
        self.assertAlmostEqual(sum(float(r["offence"]) for r in self.rows), 0.0, delta=0.02)

    def test_defence_is_not_minus_offence(self):
        """DEFECT: an unidentifiable fit once returned def = -offence for every club."""
        negated = [r for r in self.rows
                   if abs(float(r["offence"]) + float(r["defence"])) < 1e-6]
        self.assertEqual(negated, [], f"{len(negated)} clubs have def == -offence")

    def test_offence_and_defence_are_not_collinear(self):
        o = [float(r["offence"]) for r in self.rows]
        d = [float(r["defence"]) for r in self.rows]
        self.assertGreater(statistics.pstdev(d), 0.25)
        self.assertLess(abs(statistics.correlation(o, d)), 0.9)

    def test_better_defence_concedes_fewer_points(self):
        """DEFECT: a plus-signed design made 'defence' a second offence."""
        clubs = {r["club"]: r for r in self.rows}
        pa = {c: float(r["pa"]) / max(1, float(r["w"]) + float(r["l"]) + float(r["t"] or 0))
              for c, r in clubs.items() if r["pa"]}
        d = [float(clubs[c]["defence"]) for c in pa]
        self.assertLess(statistics.correlation(d, [pa[c] for c in pa]), -0.4)

    def test_offence_tracks_points_scored(self):
        """DEFECT: fitting on 28 seasons produced corr(offence, points-for) = 0.027
        - Jacksonville scored 29.9 a game and was handed a negative offence."""
        clubs = {r["club"]: r for r in self.rows}
        pf = {c: float(r["pf"]) / max(1, float(r["w"]) + float(r["l"]) + float(r["t"] or 0))
              for c, r in clubs.items() if r["pf"]}
        self.assertGreater(
            statistics.correlation([float(clubs[c]["offence"]) for c in pf], [pf[c] for c in pf]),
            0.6)

    def test_no_last_club_outlier(self):
        """DEFECT: eliminating a club by substitution parked the invariance on
        the last club in alphabetical order, which came out at -18.8."""
        nets = [float(r["net_rating"]) for r in self.rows]
        self.assertLess(max(abs(v) for v in nets), 12.0)


class TestBacktest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(DATA, "backtest.json"), encoding="utf-8") as fh:
            cls.bt = json.load(fh)

    def test_skill_is_not_implausibly_good(self):
        """DEFECT: a cover probability centred on the closing line leaked the
        market into the model and produced a skill of +0.30 on a closing line."""
        for k in ("side", "total"):
            s = self.bt["scores"][k]
            if s:
                self.assertLess(s["skill"], 0.05, f"{k} skill {s['skill']:.3f} is not credible")
                self.assertGreater(s["skill"], -0.5, f"{k} skill {s['skill']:.3f} is broken, not bad")

    def test_clustered_interval_brackets_the_estimate(self):
        s = self.bt["scores"]["side"]
        self.assertLessEqual(s["ci_low"], s["skill"])
        self.assertGreaterEqual(s["ci_high"], s["skill"])

    def test_sign_is_measured(self):
        self.assertIn(self.bt["spread_sign"], (1.0, -1.0))
        self.assertIn("MAE", self.bt["spread_sign_evidence"])

    def test_forecast_error_is_beatable(self):
        fe = read("forecast_error.csv")[0]
        self.assertGreater(float(fe["margin_mae_model"]), 0.0)
        self.assertLess(float(fe["margin_mae_model"]), 20.0)


class TestOrigination(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read("origination.csv")

    def test_three_markets_in_order_per_game(self):
        games = {}
        for r in self.rows:
            games.setdefault(r["game_id"], []).append(r)
        self.assertEqual(len(games), 13)
        for gid, rs in games.items():
            self.assertEqual([r["market"] for r in rs], ["side", "total", "moneyline"])

    def test_difference_is_fair_minus_market(self):
        for r in self.rows:
            want = float(r["fair_line"]) - float(r["market_line"])
            self.assertAlmostEqual(float(r["difference"]), want, delta=0.002)

    def test_side_and_market_share_a_convention(self):
        """DEFECT: the fair line was published as a home margin while the market
        column was a printed line, so every sign was inverted and games the
        model and market agreed on showed 23-point edges."""
        sides = [r for r in self.rows if r["market"] == "side"]
        agree = sum(1 for r in sides if (float(r["fair_line"]) > 0) == (float(r["market_line"]) > 0))
        self.assertGreaterEqual(agree, 7, f"only {agree}/13 games agree on the favourite")
        self.assertLess(statistics.mean(abs(float(r["difference"])) for r in sides), 12.0)

    def test_every_row_has_an_inputs_hash(self):
        for r in self.rows:
            self.assertEqual(len(r["inputs_sha256"]), 64)
            self.assertTrue(r["inputs_json"].startswith("{"))

    def test_no_row_lacks_an_inputs_hash(self):
        self.assertEqual([r["game_id"] for r in self.rows if not r["inputs_sha256"]], [])

    def test_moneyline_probability_in_range(self):
        for r in self.rows:
            if r["market"] == "moneyline":
                self.assertTrue(0.0 < float(r["fair_line"]) < 1.0)
                self.assertTrue(0.0 < float(r["market_line"]) < 1.0)


class TestRegisters(unittest.TestCase):
    def test_no_strategy_has_a_score(self):
        for r in read("leaderboard.csv"):
            self.assertEqual(r["settled_bets"], "0")
            self.assertEqual(r["signal_score"], "")
            self.assertEqual(r["staking_units"], "")
            self.assertEqual(r["backtest_columns_present"], "no")

    def test_every_strategy_is_paper_or_blocked(self):
        for r in read("leaderboard.csv"):
            self.assertIn(r["status"], ("PAPER", "BLOCKED"))

    def test_requirements_are_complete(self):
        for r in read("requirements.csv"):
            self.assertTrue(r["blocking_gate"])
            self.assertTrue(r["number_that_clears"])
            self.assertIn(r["status"], ("MET", "PARTIAL", "BLOCKED", "REJECTED"))

    def test_blank_depth_rank_is_blank_not_zero(self):
        for r in read("deficiency.csv"):
            if not r["depth_rank"]:
                self.assertEqual(r["depth_source_url"], "")
            else:
                self.assertTrue(r["depth_source_url"].startswith("https://"))


class TestPricesStore(unittest.TestCase):
    def test_each_book_has_thirteen_games(self):
        rows = read("price_snapshots.csv")
        for book in ("DraftKings", "FanDuel"):
            games = {r["game"] for r in rows if r["book"] == book}
            self.assertEqual(len(games), 13)

    def test_every_price_has_a_clock_and_a_url(self):
        for r in read("price_snapshots.csv"):
            self.assertTrue(r["read_utc"].endswith("Z"))
            self.assertTrue(r["source_url"].startswith("https://"))

    def test_absent_phases_are_declared_absent(self):
        phases = {r["phase"]: r for r in read("price_store_phases.csv")}
        self.assertEqual(phases["open"]["available"], "no")
        self.assertEqual(phases["close"]["available"], "no")


if __name__ == "__main__":
    unittest.main(verbosity=2)
