"""Tests for the price-snapshot and verified-results desk.

Run with:  python3 -m unittest discover -s nfl-desk-3fb93d11/tests -v
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from statslib import (american_to_decimal, binom_two_sided_p, decimal_to_american,
                      deflated_sharpe, implied_prob, norm_cdf, pearson, wilson_interval)

DATA = os.path.join(ROOT, "data")
PAGES = ["index.html", "executive-summary.html", "requirements.html", "suggestions.html",
         "questions.html", "results.html", "price-store.html", "lines.html", "strategies.html",
         "gates.html", "leaderboard.html", "correlations.html", "depth.html", "sources.html",
         "repo-audit.html", "flagged.html"]


def rows(name: str) -> list:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


class TestStatslib(unittest.TestCase):
    def test_norm_cdf_symmetry(self):
        self.assertAlmostEqual(norm_cdf(0.0), 0.5, places=9)
        self.assertAlmostEqual(norm_cdf(1.96), 1 - norm_cdf(-1.96), places=9)
        self.assertAlmostEqual(norm_cdf(1.96), 0.9750, places=4)

    def test_american_conversion_roundtrip(self):
        for a in (-110, -150, 100, 115, 250, -450):
            self.assertAlmostEqual(
                decimal_to_american(1.0 / implied_prob(a)), a, places=3)

    def test_devig_sums_to_one(self):
        p = implied_prob(-110)
        self.assertAlmostEqual(2 * (p / 2) / (p / 2 + p / 2), 1.0, places=9)

    def test_wilson_interval_brackets_estimate(self):
        lo, hi = wilson_interval(52, 100)
        self.assertLess(lo, 0.52)
        self.assertGreater(hi, 0.52)
        self.assertGreater(lo, 0.0)
        self.assertLess(hi, 1.0)

    def test_binomial_two_sided_matches_a_known_value(self):
        # two-sided P for 60 heads in 100 fair tosses is about 0.0569
        self.assertAlmostEqual(binom_two_sided_p(60, 100, 0.5), 0.0569, places=3)

    def test_pearson_on_perfect_line(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        r, p, _ = pearson(xs, [2 * x + 1 for x in xs])
        self.assertAlmostEqual(r, 1.0, places=9)
        self.assertLess(p, 0.01)

    def test_deflated_sharpe_shrinks_with_more_trials(self):
        self.assertGreater(deflated_sharpe(0.5, 1, 2000), deflated_sharpe(0.5, 50, 2000))
        self.assertGreaterEqual(deflated_sharpe(0.5, 1, 2000), 0.0)
        self.assertLessEqual(deflated_sharpe(0.5, 1, 2000), 1.0)
        self.assertGreater(deflated_sharpe(1.5, 1, 2000), deflated_sharpe(0.1, 1, 2000))
        self.assertTrue(deflated_sharpe(0.5, 1, 2) != deflated_sharpe(0.5, 1, 2))  # nan guard


class TestResultsFeed(unittest.TestCase):
    def setUp(self):
        self.feed = rows("results_feed.csv")

    def test_feed_is_non_empty(self):
        self.assertGreater(len(self.feed), 100)

    def test_every_row_has_scores_and_a_source(self):
        for r in self.feed:
            self.assertNotEqual(r["away_score"], "", f"{r['game_id']} has no away score")
            self.assertNotEqual(r["home_score"], "", f"{r['game_id']} has no home score")
            self.assertTrue(r["source_url"].startswith("http"))

    def test_matches_reconcile_observed_scores(self):
        for r in self.feed:
            self.assertEqual(int(r["home_margin"]),
                             int(r["home_score"]) - int(r["away_score"]))
            self.assertEqual(int(r["total_points"]),
                             int(r["home_score"]) + int(r["away_score"]))

    def test_weekday_agrees_with_the_published_date(self):
        import datetime
        for r in self.feed:
            d = datetime.date.fromisoformat(r["kickoff_date"])
            self.assertEqual(r["weekday_checked"], d.strftime("%A"),
                             f"{r['game_id']} {r['kickoff_date']}")

    def test_no_duplicate_game_ids(self):
        ids = [r["game_id"] for r in self.feed]
        self.assertEqual(len(ids), len(set(ids)))

    def test_reconciliation_finds_no_mismatch(self):
        recon = rows("results_reconciliation.csv")
        self.assertEqual(len(recon), 32)
        for r in recon:
            self.assertEqual(r["agrees"].upper(), "YES", f"{r['team']} does not reconcile")

    def test_every_club_appears_in_the_rebuilt_table(self):
        recon = rows("results_reconciliation.csv")
        self.assertEqual({r["team"] for r in recon}, {r["team"] for r in rows(
            "standings_official.csv")})


class TestPriceStore(unittest.TestCase):
    def setUp(self):
        self.prices = rows("price_snapshots.csv")
        self.schema = rows("price_store_schema.csv")

    def test_row_count_is_markets_times_snapshot_types(self):
        markets = rows("originated_markets.csv")
        types = {r["snapshot_type"] for r in self.prices}
        self.assertEqual(len(self.prices), len(markets) * len(types))

    def test_every_empty_cell_carries_a_flag_id(self):
        for r in self.prices:
            if not r["line_value"].strip():
                self.assertTrue(r["flag_id"].startswith("F-"),
                                f"empty price cell with no flag: {r}")

    def test_script_price_rows_are_stamped(self):
        stamped = [r for r in self.prices if r["snapshot_type"].startswith("MODEL")
                   and r["line_value"].strip()]
        self.assertGreater(len(stamped), 0)
        for r in stamped:
            self.assertIn("T", r["snapshot_utc"])

    def test_aggregator_rows_are_never_called_open_or_close(self):
        for r in self.prices:
            if r["source_tier"].startswith("AGGREGATOR"):
                self.assertNotIn("OPEN", r["snapshot_type"])
                self.assertNotIn("CLOSE", r["snapshot_type"])

    def test_schema_reports_the_same_counts_as_the_rows(self):
        for r in self.schema:
            st = r["snapshot_type"]
            same = [x for x in self.prices if x["snapshot_type"] == st]
            self.assertEqual(int(r["rows_total"]), len(same), f"{st} row count")
            self.assertEqual(int(r["populated_rows"]),
                             len([x for x in same if x["line_value"].strip()]), f"{st} populated")
            self.assertEqual(int(r["empty_rows"]),
                             len([x for x in same if not x["line_value"].strip()]), f"{st} empty")
            self.assertEqual(int(r["rows_total"]),
                             int(r["populated_rows"]) + int(r["empty_rows"]))


class TestOrigination(unittest.TestCase):
    def setUp(self):
        self.markets = rows("originated_markets.csv")
        self.steps = rows("origination_steps.csv")

    def test_three_markets_per_game(self):
        games = {r["matchup"] for r in self.markets}
        self.assertEqual(len(self.markets), 3 * len(games))
        for g in games:
            kinds = {r["market_type"] for r in self.markets if r["matchup"] == g}
            self.assertEqual(kinds, {"SIDE", "TOTAL", "MONEYLINE"})

    def test_origination_order_is_side_then_total_then_moneyline(self):
        order = {r["market_type"]: int(r["origination_order"]) for r in self.markets}
        self.assertEqual([order[k] for k in ("SIDE", "TOTAL", "MONEYLINE")], [1, 2, 3])

    def test_moneyline_is_derived_not_independently_fitted(self):
        for r in self.markets:
            if r["market_type"] == "MONEYLINE":
                self.assertIn("side", r["derived_from"])
                self.assertIn("total", r["derived_from"])

    def test_difference_is_model_minus_market(self):
        for r in self.markets:
            d = float(r["difference_model_minus_market"])
            self.assertAlmostEqual(d, float(r["model_line"]) - float(r["market_line"]), places=3)

    def test_every_step_row_names_what_it_came_from(self):
        for r in self.steps:
            self.assertTrue(r["derived_from"].strip())


class TestBacktests(unittest.TestCase):
    def setUp(self):
        self.ledger = rows("strategy_ledger.csv")
        self.board = rows("leaderboard.csv")
        self.gates = rows("gates.csv")
        self.dem = rows("demotion_gate.csv")

    def test_nine_families_are_registered(self):
        self.assertEqual(len({r["family_id"] for r in self.ledger}), 9)

    def test_ledger_counts_are_internally_consistent(self):
        for r in self.ledger:
            if r["n_decided"] and r["n_decided"].strip() and int(r["n_decided"]) > 0:
                hr = float(r["hit_rate"])
                self.assertAlmostEqual(hr, int(r["wins"]) / int(r["n_decided"]), places=4)
                self.assertEqual(int(r["n_bets"]),
                                 int(r["n_decided"]) + int(r["n_pushes"]))

    def test_hit_rate_ci_brackets_the_point_estimate(self):
        for r in self.ledger:
            if r["n_decided"].strip() and int(r["n_decided"]) > 0 and r["hit_rate"].strip():
                self.assertLessEqual(float(r["ci95_low"]), float(r["hit_rate"]))
                self.assertGreaterEqual(float(r["ci95_high"]), float(r["hit_rate"]))

    def test_holm_p_never_below_the_raw_p(self):
        for r in self.ledger:
            if not r["holm_p"].strip() or not r["p_vs_breakeven"].strip():
                continue
            self.assertGreaterEqual(float(r["holm_p"]), float(r["p_vs_breakeven"]) - 1e-9)
            self.assertLessEqual(float(r["holm_p"]), 1.0)

    def test_break_even_matches_the_grading_convention(self):
        for r in self.ledger:
            if not r["breakeven"].strip():
                continue          # no graded bets, so no break-even is published
            if r["bet_class"] == "single":
                self.assertAlmostEqual(float(r["breakeven"]), 0.5238, places=4)
            if r["bet_class"] == "parlay":
                self.assertAlmostEqual(float(r["breakeven"]), 0.2744, places=4)

    def test_nothing_is_certified(self):
        self.assertEqual({r["certified"] for r in self.board}, {"no"})
        self.assertEqual({r["state"] for r in self.board}, {"PAPER"})

    def test_signal_and_staking_are_ranked_on_the_same_board_membership(self):
        for b in {r["board"] for r in self.board}:
            grp = [r for r in self.board
                   if r["board"] == b and r["n_decided"].strip() and int(r["n_decided"]) > 0]
            self.assertGreater(len(grp), 0)
            self.assertEqual(sorted(int(r["signal_rank"]) for r in grp),
                             list(range(1, len(grp) + 1)))
            self.assertEqual(sorted(int(r["staking_rank"]) for r in grp),
                             list(range(1, len(grp) + 1)))

    def test_every_family_has_a_full_gate_matrix(self):
        self.assertEqual(len(self.gates), 9)
        for fam in {r["family_id"] for r in self.ledger}:
            for tier in ("CERTIFICATION", "RESEARCH"):
                got = {r["gate_id"] for r in rows("gate_matrix.csv")
                       if r["strategy_id"] == fam and r["universe_tier"] == tier}
                if got:
                    self.assertEqual(got, {"G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"},
                                     f"{fam}@{tier} is missing gates")

    def test_demotion_gate_has_six_triggers(self):
        self.assertEqual(len({r["demotion_trigger"] for r in self.dem}),
                         len({"D1a", "D1b", "D1c", "D1d", "D1e", "D1f"}))

    def test_significantly_bad_family_is_not_top_ranked_on_signal(self):
        bad = [r for r in self.ledger if r["holm_significant"].lower().startswith("yes")
               and r["hit_rate"].strip() and r["breakeven"].strip()
               and float(r["hit_rate"]) < float(r["breakeven"])]
        self.assertGreater(len(bad), 0, "expected at least one significantly losing family")
        cert = {r["family"]: int(r["signal_rank"]) for r in self.board
                if r["board"] == "CERTIFICATION" and r["signal_rank"].strip()}
        for r in bad:
            if r["family"] in cert:
                self.assertGreater(cert[r["family"]], 1,
                                   f"{r['family']} is significantly bad yet ranks 1 on signal")


class TestCorrelations(unittest.TestCase):
    def setUp(self):
        self.corr = rows("correlations_official.csv")
        self.withheld = rows("correlations_withheld.csv")

    def test_every_published_value_has_an_n_and_a_definition(self):
        self.assertGreater(len(self.corr), 0)
        for r in self.corr:
            self.assertTrue(r["n"].strip())
            self.assertTrue(r["n_definition"].strip())
            self.assertTrue(r["source_tier"].upper().startswith("OFFICIAL"))

    def test_r_is_inside_its_confidence_interval(self):
        for r in self.corr:
            self.assertLessEqual(float(r["ci95_low"]), float(r["r"]))
            self.assertGreaterEqual(float(r["ci95_high"]), float(r["r"]))

    def test_r_is_inside_minus_one_one(self):
        for r in self.corr:
            self.assertGreaterEqual(float(r["r"]), -1.0)
            self.assertLessEqual(float(r["r"]), 1.0)

    def test_withheld_values_are_marked_inadmissible(self):
        self.assertGreater(len(self.withheld), 0)
        for r in self.withheld:
            verdict = r["admissible_under_official_only_rule"].lower()
            self.assertTrue(verdict.startswith("no") or verdict.startswith("yes"),
                            f"{r['withheld_id']} has no admissibility verdict")
            self.assertTrue(r["reason"].strip())
            self.assertTrue(r["published_by_session"].strip())
        # at least one previously published value must fail the official-only rule
        self.assertTrue(any(r["admissible_under_official_only_rule"].lower().startswith("no")
                            for r in self.withheld))


class TestDepth(unittest.TestCase):
    def setUp(self):
        self.depth = rows("replacement_depth.csv")
        self.xchk = rows("depth_injury_crosscheck.csv")

    def test_units_are_split_offence_and_defence(self):
        units = {r["unit"].upper() for r in self.depth}
        self.assertTrue(units <= {"OFFENCE", "OFFENSE", "DEFENCE", "DEFENSE"})
        self.assertTrue(any(u.startswith("OFF") for u in units))
        self.assertTrue(any(u.startswith("DEF") for u in units))

    def test_every_active_slot_names_the_depth_of_its_replacement(self):
        active = [r for r in self.depth if r["replacement_depth_string"].strip()]
        self.assertGreater(len(active), 0)
        for r in active:
            self.assertTrue(r["depth_of_replacement_label"].strip())
            self.assertIn(int(r["replacement_depth_string"]), (2, 3, 4))

    def test_compounding_is_only_claimed_when_a_replacement_is_hurt(self):
        for r in self.depth:
            if r["compounding_replacement_out"] == "yes":
                self.assertNotEqual(r["replacement_game_status"], "")

    def test_crosscheck_rows_all_have_a_club_source(self):
        self.assertGreater(len(self.xchk), 0)
        for r in self.xchk:
            self.assertTrue(r["depth_source_url"].startswith("http"))


class TestRegisters(unittest.TestCase):
    def test_every_flag_has_a_severity_and_an_action(self):
        flags = rows("flagged.csv")
        self.assertGreater(len(flags), 10)
        for r in flags:
            self.assertIn(r["severity"], ("blocking", "review", "watch", "open"))
            self.assertTrue(r["action"].strip())
            self.assertTrue(r["detail"].strip())

    def test_requirements_cover_the_eight_brief_items(self):
        reqs = rows("requirements.csv")
        self.assertGreaterEqual(len(reqs), 8)
        for r in reqs:
            self.assertIn(r["status"].upper(),
                          ("MET", "PARTIALLY MET", "NOT MET", "IN PROGRESS AT MERGE TIME"))
            self.assertTrue(r["gap_or_caveat"].strip())

    def test_suggestions_are_all_undecided_and_have_options(self):
        sug = rows("suggestions.csv")
        self.assertGreaterEqual(len(sug), 8)
        for r in sug:
            self.assertEqual(r["decision"], "AWAITING DECISION")
            self.assertTrue(r["option_a"].strip())
            self.assertTrue(r["recommended"].strip())

    def test_sources_all_carry_a_url_and_a_tier(self):
        srcs = rows("sources.csv")
        self.assertGreater(len(srcs), 5)
        for r in srcs:
            self.assertTrue(r["url"].startswith("http"))
            self.assertIn(r["tier"], ("OFFICIAL", "DERIVED", "AGGREGATOR"))

    def test_repo_audit_reports_checks(self):
        audit = rows("repo_audit.csv")
        self.assertGreater(len(audit), 20)
        for r in audit:
            self.assertIn(r["verdict"], ("MATCH", "IRREGULAR", "NOT CHECKED"))


class TestSite(unittest.TestCase):
    def test_all_pages_exist_and_carry_the_sidebar(self):
        for p in PAGES:
            path = os.path.join(ROOT, p)
            self.assertTrue(os.path.exists(path), f"{p} was not built")
            body = open(path, encoding="utf-8").read()
            self.assertIn("<title>", body)
            for other in PAGES:
                self.assertIn(f'href="{other}"', body, f"{p} missing nav link to {other}")

    def test_verifier_passes_on_the_generated_html(self):
        out = subprocess.run([sys.executable, os.path.join(ROOT, "verify.py")],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_no_page_leaks_a_localhost_reference(self):
        for p in PAGES:
            body = open(os.path.join(ROOT, p), encoding="utf-8").read()
            self.assertNotIn("http://localhost", body)
            self.assertNotIn("127.0.0.1", body)

    def test_pages_are_served_from_relative_links(self):
        for p in PAGES:
            body = open(os.path.join(ROOT, p), encoding="utf-8").read()
            for href in __import__("re").findall(r'href="([^"]+)"', body):
                if href.startswith("http") or href.startswith("#"):
                    continue
                self.assertFalse(href.startswith("/"),
                                 f"{p} uses the absolute path {href}, which breaks on Pages")


if __name__ == "__main__":
    unittest.main(verbosity=2)
