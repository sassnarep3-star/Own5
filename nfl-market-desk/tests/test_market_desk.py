#!/usr/bin/env python3
"""Unit tests for the NFL market desk. Stdlib unittest only.

These are checks on the code and the committed data, not on NFL outcomes: a synthetic
fixture is used wherever a statistical property can be tested without touching a real game.
Run: python3 tests/test_market_desk.py
"""
import csv
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)
sys.path.insert(0, DESK)

import lib  # noqa: E402
import report  # noqa: E402


def rows(name):
    return lib.rcsv(name)


class TestStatistics(unittest.TestCase):
    def test_brier_bounds(self):
        self.assertEqual(lib.brier([0.5, 0.5], [1, 0]), 0.25)
        self.assertEqual(lib.brier([1.0, 0.0], [1, 0]), 0.0)
        self.assertEqual(lib.brier([0.0, 1.0], [1, 0]), 1.0)

    def test_cointoss_skill_is_zero(self):
        self.assertAlmostEqual(lib.brier_skill_score(0.25, 0.25), 0.0)

    def test_devig_sums_to_one(self):
        a, b = lib.devig_two(0.55, 0.50)
        self.assertAlmostEqual(a + b, 1.0, places=9)

    def test_american_roundtrip(self):
        for p in (0.25, 0.5, 0.75):
            ml = lib.prob_to_american(p)
            self.assertAlmostEqual(lib.american_to_prob(ml), p, places=6)

    def test_wilson_contains_point(self):
        lo, hi = lib.wilson(53, 81)
        self.assertLess(lo, 53 / 81)
        self.assertGreater(hi, 53 / 81)

    def test_holm_monotone_and_bounded(self):
        adj = lib.holm([0.01, 0.04, 0.03])
        self.assertTrue(all(0 <= x <= 1 for x in adj))
        self.assertLessEqual(adj[0], adj[2])

    def test_binom_symmetry(self):
        self.assertAlmostEqual(lib.binom_test_two_sided(5, 10, 0.5), 1.0, places=6)

    def test_normal_quantile(self):
        self.assertAlmostEqual(lib.norm_ppf(0.975), 1.959964, places=5)
        self.assertAlmostEqual(lib.norm_cdf(0.0), 0.5, places=9)

    def test_cluster_bootstrap_is_seeded(self):
        vals = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        cl = [1, 1, 2, 2, 3, 3]
        a = lib.boot_ci(vals, cl, n_boot=200, seed=7)
        b = lib.boot_ci(vals, cl, n_boot=200, seed=7)
        self.assertEqual(a, b)


class TestDataIntegrity(unittest.TestCase):
    def test_results_reconcile(self):
        rec = rows("standings_reconciliation.csv")
        self.assertEqual(len(rec), 32)
        bad = [r["club"] for r in rec if r["result"].lower() != "match"]
        self.assertEqual(bad, [], "standings reconciliation failed for %s" % bad)

    def test_every_result_has_an_official_source(self):
        for r in rows("results_feed.csv"):
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"),
                            "%s has no nfl.com source" % r["game_id"])
            self.assertEqual(r["source_tier"], "OFFICIAL")

    def test_originated_markets_have_three_separate_numbers(self):
        for r in rows("originated_markets.csv"):
            for col in ("fair_line", "market_line", "difference_fair_minus_market"):
                self.assertIn(col, r)
            self.assertNotEqual(r["fair_line"], "")
            # difference must actually be fair - market, to the published precision
            if r["market_line"]:
                d = float(r["fair_line"]) - float(r["market_line"])
                self.assertAlmostEqual(d, float(r["difference_fair_minus_market"]), places=2)

    def test_origination_order_is_side_total_moneyline(self):
        order = {}
        for r in rows("originated_markets.csv"):
            order.setdefault(r["market_type"], set()).add(r["origination_order"])
        self.assertEqual(order["SIDE"], {"1"})
        self.assertEqual(order["TOTAL"], {"2"})
        self.assertEqual(order["MONEYLINE"], {"3"})

    def test_no_lookahead_in_forecasts(self):
        for r in rows("forecasts.csv"):
            self.assertLessEqual(int(r["train_last_week"]), int(r["week"]) - 1,
                                 "%s trained on its own week" % r["game_id"])

    def test_injury_rows_are_sourced(self):
        for r in rows("injuries_wk10.csv"):
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"))

    def test_shared_and_empty_slots_preserved(self):
        shapes = {r["slot_shape"] for r in rows("depth_rows.csv")}
        self.assertIn("shared", shapes)
        self.assertIn("empty", shapes)

    def test_no_jersey_number_used_as_rank(self):
        for r in rows("depth_rows.csv"):
            if r["jersey_number"]:
                self.assertNotEqual(r["jersey_number"], r["rank"],
                                    "a jersey number is being used as a depth rank")

    def test_price_store_empties_are_flagged(self):
        for r in rows("price_snapshots.csv"):
            if r["line_value"] == "":
                self.assertTrue(r["flag_id"], "%s is empty without a flag" % r["snapshot_id"])

    def test_registration_hashes_match_files(self):
        import hashlib
        for r in rows("strategy_registration.csv"):
            p = os.path.join(DESK, "data", "preregistration",
                             r["registration_file"].split("/")[-1])
            self.assertTrue(os.path.exists(p), p)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            self.assertEqual(h, r["registration_sha256"], r["family_id"])

    def test_leaderboard_carries_no_backtest_universe(self):
        for r in rows("leaderboard.csv"):
            self.assertFalse(r["universe"].upper().startswith("BACKTEST"))

    def test_leaderboard_ranks_by_signal_not_roi(self):
        """The family with the best ROI must not automatically hold signal rank 1."""
        lb = [r for r in rows("leaderboard.csv") if r["staking_roi_pct"]]
        best_roi = max(lb, key=lambda r: float(r["staking_roi_pct"]))
        by_signal = [r for r in lb if r["signal_rank"] == "1"]
        self.assertTrue(by_signal)
        self.assertNotIn(best_roi["family_id"], [r["family_id"] for r in by_signal],
                         "ranking by season ROI has crept back in")

    def test_flags_are_namespaced_and_unique(self):
        ids = [f["flag_id"] for f in rows("flags.csv")]
        self.assertEqual(len(ids), len(set(ids)))
        for i in ids:
            self.assertTrue(i.startswith(("INH-", "OWN-")), i)

    def test_parlay_families_are_gated(self):
        gates = {g["gate_id"]: g for g in rows("gates.csv")}
        self.assertEqual(gates["G7"]["status"], "NOT MET")

    def test_requirements_status_vocabulary(self):
        vocab = {"MET", "PARTIAL", "NOT MET", "REJECTED", "NEEDS REVIEW"}
        for r in rows("requirements.csv"):
            self.assertIn(r["status"], vocab)


class TestSite(unittest.TestCase):
    def test_all_pages_exist(self):
        for slug, _t, _s, _b in report.PAGES:
            self.assertTrue(os.path.exists(os.path.join(DESK, slug + ".html")), slug)

    def test_every_page_declares_paper_only(self):
        for slug, _t, _s, _b in report.PAGES:
            html = open(os.path.join(DESK, slug + ".html"), encoding="utf-8").read()
            self.assertIn("Paper research only", html)

    def test_verify_passes_fast(self):
        r = subprocess.run([sys.executable, os.path.join(DESK, "verify.py"), "--fast"],
                           cwd=DESK, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
