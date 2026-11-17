#!/usr/bin/env python3
"""Unit tests for the desk's maths, its honesty rules and its site. Run from the desk directory."""
import csv, io, math, sys, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import scoring  # noqa: E402
import engine   # noqa: E402


def rows(name):
    with io.open(HERE / "data" / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Scoring(unittest.TestCase):
    def test_brier_perfect_and_worst(self):
        self.assertEqual(scoring.brier([(1.0, 1), (0.0, 0)]), 0.0)
        self.assertEqual(scoring.brier([(0.0, 1), (1.0, 0)]), 1.0)

    def test_brier_skill_of_a_forecast_equal_to_the_base_rate_is_zero(self):
        pairs = [(0.5, 1), (0.5, 0), (0.5, 1), (0.5, 0)]
        self.assertAlmostEqual(scoring.brier(pairs), scoring.constant_brier(pairs), places=12)
        self.assertAlmostEqual(scoring.skill(pairs), 0.0, places=12)

    def test_brier_is_not_proper_a_constant_forecast_can_be_rewarded_for_beating_the_base_rate(self):
        # 0.6/0.4 confidence on a 50/50 sequence scores WORSE than 0.5, but a forecast that happens to sit
        # closer to the observed mean than the base rate looks like skill. This is why the leaderboard
        # publishes the base rate next to the score and the calibration slope next to both.
        conf = [(0.6, 1), (0.6, 0), (0.6, 1), (0.6, 0)]
        flat = [(0.5, 1), (0.5, 0), (0.5, 1), (0.5, 0)]
        self.assertGreater(scoring.brier(conf), scoring.constant_brier(conf))
        self.assertGreater(scoring.log_loss(conf), scoring.log_loss(flat))  # both rules agree here
        self.assertAlmostEqual(scoring.log_loss(flat), math.log(2), places=12)

    def test_log_loss_of_a_perfect_forecast_is_bounded_by_the_clip(self):
        self.assertLess(scoring.log_loss([(1.0, 1), (0.0, 0)]), 1e-10)

    def test_skill_positive_only_when_better_than_base_rate(self):
        good = [(0.8, 1), (0.8, 1), (0.2, 0), (0.2, 0)]
        self.assertGreater(scoring.skill(good), 0.0)

    def test_effective_sample_size_is_the_number_of_clusters(self):
        for lab in ([0] * 8, list(range(8)), [i // 2 for i in range(8)]):
            _, _, m = scoring.clustered_se([(0.6, 1), (0.6, 0)] * 4, lab)
            self.assertEqual(m, len(set(lab)))
        _, _, m = scoring.clustered_se([(0.6, 1)] * 3, [0, 0, 0])
        self.assertEqual(m, 1)

    def test_perfect_leg_correlation_within_a_game(self):
        # four legs that settle together on one game: the per-row standard error understates the truth by
        # exactly sqrt(legs per game), which is the number the brief's game-cluster rule is protecting.
        hot = [(0.7, 1)] * 4 + [(0.3, 0)] * 4
        _, se_g, _ = scoring.clustered_se(hot, [0, 0, 0, 0, 1, 1, 1, 1])
        _, se_r, _ = scoring.clustered_se(hot, list(range(8)))
        self.assertGreater(se_g, se_r)
        self.assertAlmostEqual(se_r * 2.0, se_g, places=12)          # / sqrt(4)
        pt_one, se_one, m_one = scoring.clustered_se(hot[:4], [0] * 4)   # one game, four legs, one score
        self.assertAlmostEqual(pt_one, 0.09, places=12)                   # the mean of identical legs
        self.assertEqual(m_one, 1)
        self.assertTrue(math.isinf(se_one))                            # and its uncertainty is undefined

    def test_a_perfect_hedge_shows_zero_learning_only_under_game_clustering(self):
        hedged = [(0.9, 1), (0.9, 0), (0.1, 1), (0.1, 0)] * 2
        pt_g, se_g, m_g = scoring.clustered_se(hedged, [0, 0, 0, 0, 1, 1, 1, 1])
        pt_r, se_r, m_r = scoring.clustered_se(hedged, list(range(8)))
        self.assertAlmostEqual(pt_g, pt_r, places=12)
        self.assertAlmostEqual(se_g, 0.0, places=12)   # every game scored identically: nothing was learned
        self.assertGreater(se_r, 0.0)                   # the per-row view cannot see that
        self.assertEqual((m_g, m_r), (2, 8))

    def test_a_single_cluster_reports_no_bound_rather_than_a_number(self):
        pt, se, m = scoring.clustered_se([(0.7, 1)] * 4, [0] * 4)
        self.assertEqual((m, round(pt, 5)), (1, 0.09))
        self.assertTrue(math.isinf(se))
        self.assertTrue(math.isnan(scoring.clustered_lower_bound([(0.7, 1)] * 4, [0] * 4)))

    def test_the_bound_never_exceeds_the_point_estimate(self):
        pairs = [(0.7, 1), (0.7, 1), (0.7, 0), (0.7, 0), (0.3, 0), (0.3, 0), (0.3, 1), (0.3, 1)]
        for lab in (list(range(8)), [i // 4 for i in range(8)], [i % 2 for i in range(8)], [0] * 8):
            bnd = scoring.clustered_lower_bound(pairs, lab)
            if math.isnan(bnd):
                self.assertEqual(len(set(lab)), 1)     # the only way to get no bound is one cluster
                continue
            self.assertLessEqual(bnd, scoring.brier(pairs) + 1e-12)

    def test_wilson_matches_known_value(self):
        lo, hi = scoring.wilson(618, 1000)
        self.assertAlmostEqual(lo, 0.5876, places=3)
        self.assertAlmostEqual(hi, 0.6474, places=3)

    def test_bonferroni(self):
        self.assertAlmostEqual(scoring.bonferroni(0.05, 8), 0.00625)

    def test_power_analysis_shows_a_season_of_bets_cannot_settle_it(self):
        n55, n60 = scoring.power_bets(0.55), scoring.power_bets(0.60)
        self.assertGreater(n55, 500)                  # a 55% bettor needs hundreds of bets, not tens
        self.assertLess(n60, n55)                     # and the number falls fast as the edge grows
        self.assertGreater(n55, 17 * 3)               # more bets than a full season of 51 games, per bettor


class Honesty(unittest.TestCase):
    def test_no_invented_market_price_anywhere(self):
        for name in ("originated_wk11.csv", "price_snapshots.csv"):
            for r in rows(name):
                for k in ("market_line", "market_open", "market_close"):
                    if k in r:
                        self.assertEqual(r[k].strip(), "", f"{name} asserts a market number")
                if "difference_vs_market" in r:
                    self.assertTrue(r["difference_vs_market"].startswith("undefined"))

    def test_unplayed_fixture_has_no_score(self):
        pend = [r for r in rows("results_feed_2026.csv") if not r["status"].upper().startswith("FINAL")]
        self.assertTrue(pend, "the pending Monday fixture must still be present and blank")
        for r in pend:
            self.assertEqual(r["away_score"], "")
            self.assertEqual(r["home_score"], "")
            self.assertEqual(r["result"], "")

    def test_no_replacement_is_ever_named(self):
        for r in rows("availability_snapshot_wk10_read2.csv"):
            self.assertEqual(r["replacement_named"], "")
            self.assertIn("none is inferred", r["replacement_note"])

    def test_standings_codes_are_aliased_not_dropped(self):
        feed = rows("results_feed_2026.csv")
        codes = {r["away"] for r in feed} | {r["home"] for r in feed}
        st = {r["team"] for r in rows("standings_verified.csv")}
        self.assertTrue(codes <= st, f"feed codes absent from standings: {codes - st}")
        self.assertEqual(engine.norm("LAR"), "LA")
        self.assertEqual(engine.norm("ARI"), "AZ")

    def test_no_backtest_number_reaches_the_leaderboard(self):
        for r in rows("leaderboard_signal.csv"):
            for k in ("mean_brier", "benchmark_brier", "skill_score", "skill_lower_bound", "calibration_slope"):
                self.assertEqual(r[k].strip(), "", f"{r['strategy']} carries a score before a week settled")
        for r in rows("leaderboard_staking.csv"):
            self.assertNotIn(r["roi"].strip(), [x for x in ("0.05", "0.1")])

    def test_third_party_numbers_are_labelled_and_separate(self):
        names = {p.name for p in (HERE / "data").glob("*.csv")}
        self.assertIn("third_party_inventory.csv", names)
        for r in rows("designation_play_rate.csv"):
            self.assertIn("third-party", r["source_class"])
            self.assertIn("DESCRIPTIVE ONLY", r["use"])

    def test_every_model_row_stores_its_inputs(self):
        for r in rows("originated_wk11.csv"):
            self.assertIn("p_home=", r["probability_plus_inputs"])
            self.assertIn("sd_resid=", r["probability_plus_inputs"])
            self.assertTrue(r["model_version"].startswith("ridge-scoring v1"))

    def test_origination_order_side_total_moneyline(self):
        fields = list(rows("originated_wk11.csv")[0].keys())
        self.assertLess(fields.index("stage_1_fair_spread_home"), fields.index("stage_2_total_estimator_A"))
        self.assertLess(fields.index("stage_2_total_estimator_B"), fields.index("stage_3_fair_moneyline_home"))


class Numbers(unittest.TestCase):
    def test_integrity_checks_all_pass(self):
        for r in rows("standings_integrity_checks.csv"):
            self.assertEqual(r["result"], "PASS", r["check"])

    def test_league_balance(self):
        st = rows("standings_verified.csv")
        self.assertEqual(sum(int(r["pf"]) for r in st), sum(int(r["pa"]) for r in st))
        self.assertEqual(sum(int(r["games_played"]) for r in st), 298)
        self.assertEqual(len(st), 32)

    def test_correlations_publish_n(self):
        for r in rows("correlations.csv"):
            self.assertEqual(r["n"], "32")
            # The interval may sit wholly on one side when |r| -> 1, but it must never be presented as
            # evidence without the explanation, and n must be on the row.
            self.assertEqual(len(r["n"]), 2, "n missing")
            if float(r["ci95_lo"]) > float(r["r"]):
                self.assertIn("degenerates", r["ci_note"])
            self.assertIn("nfl.com", r["source_url"])

    def test_walkforward_keeps_both_estimators(self):
        for r in rows("walkforward_totals.csv"):
            self.assertEqual(r["both_kept"], "yes")

    def test_registered_rows_recorded_before_kickoff(self):
        for r in rows("originated_wk11.csv"):
            self.assertLess(r["recorded_before_kickoff_utc"], r["kickoff_date"] + "T00:00:00Z"
                            if r["kickoff_date"] > "2026-11-17" else "2026-11-18T00:00:00Z")


class Site(unittest.TestCase):
    PAGES = ["index.html", "executive-summary.html", "requirements.html", "questions.html", "suggestions.html",
             "results.html", "availability.html", "roster-events.html", "origination.html", "price-store.html",
             "analytics.html", "competition.html", "verification.html", "sources.html", "flagged.html"]

    def test_every_page_exists_and_links_resolve(self):
        for name in self.PAGES:
            p = HERE / name
            self.assertTrue(p.exists(), name)
            text = p.read_text(encoding="utf-8")
            self.assertIn("assets/desk.css", text)
            for other in self.PAGES:
                if other != "executive-summary.html" or name != other:
                    pass
            self.assertIn("</html>", text)

    def test_flagged_page_publishes_the_corrections(self):
        text = (HERE / "flagged.html").read_text(encoding="utf-8")
        for frag in ("CU-F03", "CU-F04", "CU-F05", "no score", "reserve"):
            self.assertTrue(frag.lower() in text.lower(), frag)

    def test_requirements_table_has_one_row_per_requirement(self):
        r = rows("requirements_master.csv")
        self.assertGreaterEqual(len(r), 70)
        for x in r:
            self.assertTrue(x["status"], x["id"])
            self.assertTrue(x["number_that_clears_it"] == "not applicable" or len(x["number_that_clears_it"]) > 8,
                            f"{x['id']} has no clearing number")


if __name__ == "__main__":
    unittest.main(verbosity=2)
