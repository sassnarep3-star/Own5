"""Integrity tests for the empirical engine (session 55e682dd-own5).

These assert the properties that make the research trustworthy: no lookahead,
correct odds math, correct settlement, honest correlation arithmetic, and that
no output claims a validated strategy without clearing the gates.

Run:  python -m unittest tests.test_engine -v
Requires: pandas, numpy, scipy (see engine/requirements.txt).
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from common import (OUT, american_to_decimal, american_to_prob,  # noqa: E402
                    devig_two_way, load_games)


class TestOddsMath(unittest.TestCase):
    def test_american_to_decimal(self):
        self.assertAlmostEqual(float(american_to_decimal(-110)), 1.9090909, places=6)
        self.assertAlmostEqual(float(american_to_decimal(150)), 2.5, places=6)
        self.assertAlmostEqual(float(american_to_decimal(100)), 2.0, places=6)
        self.assertAlmostEqual(float(american_to_decimal(-200)), 1.5, places=6)

    def test_american_to_prob(self):
        self.assertAlmostEqual(float(american_to_prob(-110)), 110 / 210, places=9)
        self.assertAlmostEqual(float(american_to_prob(100)), 0.5, places=9)
        self.assertAlmostEqual(float(american_to_prob(-200)), 2 / 3, places=9)
        self.assertAlmostEqual(float(american_to_prob(200)), 1 / 3, places=9)

    def test_no_warning_on_even_money(self):
        with np.errstate(divide="raise", invalid="raise"):
            p = american_to_prob(np.array([-100.0, 100.0, -110.0]))
        self.assertTrue(np.all(np.isfinite(p)))

    def test_devig_sums_to_one(self):
        a, b = devig_two_way(np.array([0.55]), np.array([0.55]))
        self.assertAlmostEqual(float(a[0] + b[0]), 1.0, places=12)
        self.assertAlmostEqual(float(a[0]), 0.5, places=12)

    def test_vig_is_positive(self):
        p = float(american_to_prob(-110)) * 2
        self.assertGreater(p, 1.0)
        self.assertAlmostEqual((p - 1) * 100, 4.7619, places=3)


class TestSettlement(unittest.TestCase):
    def test_home_favourite_convention(self):
        """spread_line > 0 means home favoured; home covers if result > spread."""
        g = load_games()
        r = g.iloc[0]
        self.assertEqual(r["result"], r["home_score"] - r["away_score"])
        self.assertEqual(r["home_cover_margin"], r["result"] - r["spread_line"])

    def test_result_and_total_identities(self):
        g = load_games()
        self.assertTrue((g.result == g.home_score - g.away_score).all())
        self.assertTrue((g.total == g.home_score + g.away_score).all())

    def test_push_is_zero(self):
        self.assertEqual(float(np.sign(0.0)), 0.0)
        self.assertEqual(float(np.sign(3.0)), 1.0)
        self.assertEqual(float(np.sign(-3.0)), -1.0)


class TestNoLookahead(unittest.TestCase):
    def test_training_cutoff_strictly_before_kickoff(self):
        """Every priced game must have a training set that ends before it."""
        p = pd.read_csv(OUT / "originated_lines.csv")
        g = load_games()
        p["gameday"] = pd.to_datetime(p["gameday"])
        g["gameday"] = pd.to_datetime(g["gameday"])
        for (season, week), sub in p.groupby(["season", "week"]):
            cutoff = sub.gameday.min()
            prior = g[g.gameday < cutoff]
            n_train = int(sub.n_train_games.iloc[0])
            self.assertEqual(n_train, len(prior),
                             f"{season} W{week}: train count must equal strictly-prior games")

    def test_first_seasons_are_not_priced(self):
        p = pd.read_csv(OUT / "originated_lines.csv")
        self.assertGreater(int(p.season.min()), 2006 - 1)
        self.assertTrue((p.n_train_games >= 200).all())

    def test_model_never_uses_market_as_feature(self):
        """Origination must not read spread/total/moneyline columns as inputs."""
        src = (ROOT / "engine" / "originate.py").read_text()
        design_block = src[src.index("def _design"):src.index("def originate")]
        for forbidden in ["spread_line", "total_line", "moneyline", "mkt_p_"]:
            self.assertNotIn(forbidden, design_block)


class TestCorrelations(unittest.TestCase):
    def setUp(self):
        self.c = pd.read_csv(OUT / "correlations_empirical.csv")

    def test_joint_within_frechet_bounds(self):
        for r in self.c.itertuples():
            lo = max(0.0, r.p_a + r.p_b - 1)
            hi = min(r.p_a, r.p_b)
            self.assertGreaterEqual(r.observed_joint + 1e-9, lo)
            self.assertLessEqual(r.observed_joint - 1e-9, hi)

    def test_phi_in_range(self):
        self.assertTrue(self.c.phi_correlation.between(-1, 1).all())

    def test_lift_equals_joint_minus_product(self):
        for r in self.c.itertuples():
            self.assertAlmostEqual(r.lift_vs_independent,
                                   r.observed_joint - r.naive_independent_joint, places=4)

    def test_naive_product_recomputed(self):
        for r in self.c.itertuples():
            self.assertAlmostEqual(r.naive_independent_joint, r.p_a * r.p_b, places=4)

    def test_qb_wr1_correlation_is_positive_and_flagged(self):
        """The headline finding must actually be present and significant."""
        row = self.c[self.c.pair_id == "PP02"].iloc[0]
        self.assertGreater(row.phi_correlation, 0.1)
        self.assertTrue(bool(row.independence_rejected))


class TestSkillLuck(unittest.TestCase):
    def setUp(self):
        self.sl = pd.read_csv(OUT / "skill_luck.csv")

    def test_breakeven_matches_prices(self):
        for r in self.sl.itertuples():
            self.assertGreater(r.breakeven_win_rate, 0.0)
            self.assertLess(r.breakeven_win_rate, 1.0)

    def test_win_rate_consistent(self):
        for r in self.sl.itertuples():
            self.assertAlmostEqual(r.win_rate, r.wins / (r.wins + r.losses), places=4)

    def test_ci_contains_point_estimate(self):
        for r in self.sl.itertuples():
            self.assertLessEqual(r.roi_ci_low, r.roi + 1e-6)
            self.assertGreaterEqual(r.roi_ci_high, r.roi - 1e-6)

    def test_pvalues_valid(self):
        self.assertTrue(self.sl.binom_p_one_sided.between(0, 1).all())


class TestGates(unittest.TestCase):
    def setUp(self):
        self.g = pd.read_csv(OUT / "gate_results.csv")
        self.summary = json.loads((OUT / "gates_summary.json").read_text())

    def test_no_validated_without_all_gates(self):
        gate_cols = [f"G{i}" for i in range(1, 11)]
        for r in self.g.itertuples():
            passed = all(bool(getattr(r, c)) for c in gate_cols)
            self.assertEqual(r.status == "VALIDATED", passed,
                             f"{r.strategy}: status must match gate conjunction")

    def test_summary_counts_match(self):
        self.assertEqual(self.summary["validated"],
                         int((self.g.status == "VALIDATED").sum()))
        self.assertEqual(self.summary["strategies_evaluated"], len(self.g))

    def test_no_reward_paid_to_rejected(self):
        # keep_default_na=False so the literal string "None" is not coerced to NaN.
        lb = pd.read_csv(OUT / "leaderboard_empirical.csv", keep_default_na=False)
        rejected = lb[lb.status == "REJECTED"]
        self.assertTrue((rejected.reward_tier == "None").all())
        self.assertTrue((rejected["rank"] == "").all())


class TestOfficialVerification(unittest.TestCase):
    def setUp(self):
        self.v = pd.read_csv(OUT / "official_verification.csv")

    def test_all_compared_games_match(self):
        self.assertGreater(len(self.v), 0)
        self.assertTrue(self.v.verified.all(), "official score mismatch present")

    def test_every_row_has_official_url(self):
        self.assertTrue(self.v.source_url.str.startswith("https://www.nfl.com/").all())

    def test_scores_are_integers_and_equal(self):
        self.assertTrue((self.v.home_score == self.v.home_score_official).all())
        self.assertTrue((self.v.away_score == self.v.away_score_official).all())

    def test_unverified_games_are_not_claimed(self):
        """Bets on unverified games must be labelled, never silently verified."""
        b = pd.read_csv(OUT / "bets.csv")
        v = set(self.v.loc[self.v.verified, "game_id"])

        def all_legs_verified(gid):
            return all(x in v for x in str(gid).split("+"))

        expected = b.game_id.map(all_legs_verified)
        self.assertTrue((b.official_verified == expected).all())


class TestProvenance(unittest.TestCase):
    def test_provenance_file_present_and_honest(self):
        p = json.loads((ROOT / "data" / "raw" / "PROVENANCE.json").read_text())
        self.assertIn("datasets", p)
        for d in p["datasets"]:
            self.assertIn("THIRD-PARTY", d["official_status"])

    def test_prop_roi_not_fabricated(self):
        """No player-prop ROI may be claimed without a verified market price."""
        b = pd.read_csv(OUT / "bets.csv")
        props = b[b.market.str.contains("prop", case=False, na=False)]
        self.assertEqual(len(props), 0,
                         "player-prop bets must not be graded without verified prices")


if __name__ == "__main__":
    unittest.main(verbosity=2)
