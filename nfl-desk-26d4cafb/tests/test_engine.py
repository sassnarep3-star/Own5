"""Unit tests for the 26d4cafb NFL Decision Desk engine.

Run with:  python3 -m unittest discover -s nfl-desk-26d4cafb/tests -v
(or via the subsite CI workflow).

These tests protect the invariants that matter for the zero-hallucination policy:
the ledger must reconcile to the official standings, no value may be inferred into a
field that has no official source, and the statistics that "remove luck" must be
computable by hand.
"""

from __future__ import annotations

import csv
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.dirname(HERE)
DATA = os.path.join(SUB, "data")
sys.path.insert(0, SUB)

import engine as E          # noqa: E402
import registers as G       # noqa: E402
import raw_inputs as R      # noqa: E402


def rows(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger, cls.added = E.build_ledger()

    def test_ledger_has_all_completed_games(self):
        self.assertEqual(len(self.ledger), 136)

    def test_sixteen_games_added_after_repo_freeze(self):
        self.assertEqual(self.added, 16)

    def test_no_duplicate_games(self):
        keys = [(g["wk"], g["away"], g["home"]) for g in self.ledger]
        self.assertEqual(len(keys), len(set(keys)))

    def test_scores_are_non_negative_integers(self):
        for g in self.ledger:
            self.assertIsInstance(g["away_pts"], int)
            self.assertIsInstance(g["home_pts"], int)
            self.assertGreaterEqual(g["away_pts"], 0)
            self.assertGreaterEqual(g["home_pts"], 0)

    def test_margin_and_total_arithmetic(self):
        for g in self.ledger:
            self.assertEqual(g["margin_home"], g["home_pts"] - g["away_pts"])
            self.assertEqual(g["total"], g["home_pts"] + g["away_pts"])

    def test_washington_alias_normalised(self):
        # The repo ledger writes WSH; nfl.com writes WAS. Both must collapse to WAS.
        self.assertNotIn("WSH", {g["away"] for g in self.ledger} | {g["home"] for g in self.ledger})
        self.assertIn("WAS", {g["away"] for g in self.ledger} | {g["home"] for g in self.ledger})


class TestStandingsReconciliation(unittest.TestCase):
    def test_thirty_two_teams_zero_mismatches(self):
        led, _ = E.build_ledger()
        out, mismatches, nteams = E.reconcile_standings(led)
        self.assertEqual(nteams, 32)
        self.assertEqual(len(out), 32)
        self.assertEqual(mismatches, 0)
        self.assertTrue(all(r["match"] == "MATCH" for r in out))

    def test_computed_games_played_is_consistent(self):
        led, _ = E.build_ledger()
        out, _m, _n = E.reconcile_standings(led)
        for r in out:
            self.assertEqual(
                int(r["computed_GP"]),
                int(r["computed_W"]) + int(r["computed_L"]) + int(r["computed_T"]))


class TestOfficialChecksums(unittest.TestCase):
    def test_qb_game_logs_sum_to_official_season_totals(self):
        for qb, official in R.OFFICIAL_QB_YARDS_CHECKSUMS.items():
            total = sum(r[10] for r in R.PLAYER_GAME_LOGS_2026 if r[7] == qb)
            self.assertEqual(total, official, "checksum mismatch for %s" % qb)

    def test_at_least_six_qbs_have_checksums(self):
        self.assertGreaterEqual(len(R.OFFICIAL_QB_YARDS_CHECKSUMS), 6)


class TestHomeFieldAdvantage(unittest.TestCase):
    def test_neutral_games_excluded(self):
        led, _ = E.build_ledger()
        hfa = E.compute_hfa(led)
        self.assertEqual(hfa["n_non_neutral_games"], len(led) - len(E.NEUTRAL_TRIPLES)
                         - len(E.NEUTRAL_UNCONFIRMED_TRIPLES))

    def test_confidence_interval_brackets_the_estimate(self):
        led, _ = E.build_ledger()
        hfa = E.compute_hfa(led)
        self.assertLessEqual(hfa["ci95_low"], hfa["mean_home_margin"])
        self.assertLessEqual(hfa["mean_home_margin"], hfa["ci95_high"])

    def test_neutral_site_set_is_declared_not_guessed(self):
        # Two games have an international kickoff window but no confirmed venue, so they
        # must be excluded from the main estimate and reported separately.
        self.assertEqual(len(E.NEUTRAL_UNCONFIRMED_TRIPLES), 2)


class TestStatistics(unittest.TestCase):
    def test_pearson_perfect_positive(self):
        self.assertAlmostEqual(E.pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0, places=9)

    def test_pearson_perfect_negative(self):
        self.assertAlmostEqual(E.pearson([1, 2, 3, 4], [8, 6, 4, 2]), -1.0, places=9)

    def test_pearson_constant_series_is_none(self):
        self.assertIsNone(E.pearson([1, 1, 1, 1], [1, 2, 3, 4]))

    def test_poisson_binomial_pmf_sums_to_one(self):
        dist = E.poisson_binomial_pmf([0.3, 0.5, 0.7, 0.2])
        self.assertAlmostEqual(sum(dist), 1.0, places=12)

    def test_poisson_binomial_matches_plain_binomial_for_constant_p(self):
        n, p = 8, 0.4
        dist = E.poisson_binomial_pmf([p] * n)
        for k in range(n + 1):
            self.assertAlmostEqual(dist[k], math.comb(n, k) * p ** k * (1 - p) ** (n - k),
                                   places=12)

    def test_heterogeneous_null_changes_the_answer(self):
        # Guards the bug this module was written to fix: a single constant base rate is
        # NOT interchangeable with per-pick nulls when the pick mix is unbalanced.
        picks = [0.6] * 10 + [0.4] * 10     # mean 0.5, but heterogeneous
        k = 15                              # away from the centre, where the tails differ
        self.assertNotAlmostEqual(
            E.poisson_binomial_two_sided(k, picks),
            E.binom_two_sided_p(k, 20, 0.5), places=4)

    def test_poisson_binomial_mean_matches_sum_of_probabilities(self):
        probs = [0.2, 0.35, 0.5, 0.65, 0.8]
        dist = E.poisson_binomial_pmf(probs)
        self.assertAlmostEqual(sum(i * p for i, p in enumerate(dist)), sum(probs), places=12)

    def test_holm_is_monotone_and_capped(self):
        ps = [0.001, 0.02, 0.04, 0.5]
        adj = E.holm_bonferroni(ps)
        self.assertEqual(len(adj), len(ps))
        for a in adj:
            self.assertGreaterEqual(a, min(ps))
            self.assertLessEqual(a, 1.0)
        order = sorted(range(len(ps)), key=lambda i: ps[i])
        for a, b in zip(order, order[1:]):
            self.assertLessEqual(adj[a], adj[b] + 1e-12)

    def test_holm_handles_none_entries(self):
        adj = E.holm_bonferroni([0.01, None, 0.4])
        self.assertIsNone(adj[1])
        self.assertAlmostEqual(adj[0], 0.02, places=9)

    def test_deflated_sharpe_penalises_more_trials(self):
        rets = [0.9] * 12 + [-1.0] * 6
        few = E.deflated_sharpe_ratio(rets, 3)
        many = E.deflated_sharpe_ratio(rets, 500)
        self.assertGreater(few, many)

    def test_max_drawdown_is_non_negative(self):
        self.assertGreaterEqual(E.max_drawdown([1.0, -2.0, 0.5]), 0.0)
        self.assertAlmostEqual(E.max_drawdown([1.0, -2.0]), 2.0)

    def test_chi2_trend_detects_monotone_signal(self):
        _chi2, p = E.chi2_trend_p([5, 10, 15], [20, 20, 20])
        self.assertIsNotNone(p)
        self.assertLess(p, 0.05)

    def test_chi2_trend_flat_data_not_significant(self):
        _chi2, p = E.chi2_trend_p([10, 10, 10], [20, 20, 20])
        self.assertGreater(p, 0.05)


class TestRatings(unittest.TestCase):
    def test_ratings_are_shrunk_toward_zero(self):
        led, _ = E.build_ledger()
        raw = E.fit_ratings(led, k=0.0)
        shrunk = E.fit_ratings(led, k=6.0)
        for t in raw["teams"]:
            self.assertLessEqual(abs(shrunk["off"][t]), abs(raw["off"][t]) + 1e-9)
            self.assertLessEqual(abs(shrunk["def"][t]), abs(raw["def"][t]) + 1e-9)

    def test_league_mean_is_positive_and_plausible(self):
        led, _ = E.build_ledger()
        rt = E.fit_ratings(led)
        self.assertGreater(rt["lg"], 15.0)
        self.assertLess(rt["lg"], 35.0)

    def test_shrinkage_sensitivity_surface_is_flat(self):
        led, _ = E.build_ledger()
        surf = E.k_sensitivity(led)
        maes = [s["margin_MAE"] for s in surf]
        # The declared k must not be load-bearing: the spread across the grid is small.
        self.assertLess(max(maes) - min(maes), 1.5)


class TestWeek10Lines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        led, _ = E.build_ledger()
        hfa = E.compute_hfa(led)
        cls.lines, _ = E.originate_week10(led, hfa["mean_home_margin"], E.build_injury_tolls())

    def test_fourteen_lines(self):
        self.assertEqual(len(self.lines), 14)

    def test_probabilities_sum_to_one(self):
        for r in self.lines:
            s = r["p_home_win"] + r["p_away_win"] + r["p_tie"]
            self.assertAlmostEqual(s, 1.0, places=3)

    def test_two_way_probabilities_are_normalised(self):
        for r in self.lines:
            two = r["p_home_win"] + r["p_away_win"]
            if two > 0:
                self.assertAlmostEqual(r["p_home_two_way"], r["p_home_win"] / two, places=3)

    def test_market_columns_are_strictly_blank(self):
        for r in self.lines:
            for col in ("market_spread", "market_total", "market_ml", "edge", "clv",
                        "weather_adjustment"):
                self.assertEqual(r[col], "", "%s must stay blank (no official source)" % col)

    def test_neutral_site_game_has_zero_hfa(self):
        neutral = [r for r in self.lines if r["neutral"] == "YES"]
        self.assertEqual(len(neutral), 1)
        self.assertEqual(float(neutral[0]["hfa_applied"]), 0.0)

    def test_every_line_has_an_official_source_link(self):
        for r in self.lines:
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"))

    def test_every_team_appears_at_most_once(self):
        teams = [r["away"] for r in self.lines] + [r["home"] for r in self.lines]
        self.assertEqual(len(teams), len(set(teams)))

    def test_bye_teams_do_not_appear(self):
        teams = set([r["away"] for r in self.lines] + [r["home"] for r in self.lines])
        for t in R.WEEK10_BYE_TEAMS:
            self.assertNotIn(t, teams)


class TestWalkForward(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        led, _ = E.build_ledger()
        cls.wf = E.walk_forward_predictions(led)

    def test_no_week_before_the_minimum_is_graded(self):
        self.assertTrue(all(int(r["wk"]) >= E.GRADED_FROM_WEEK for r in self.wf))

    def test_lookahead_check_matches_the_week(self):
        for r in self.wf:
            self.assertEqual(r["lookahead_check"], "trained on weeks < %d only" % int(r["wk"]))

    def test_null_probability_is_within_range(self):
        for r in self.wf:
            self.assertGreaterEqual(float(r["null_p_home_win"]), 0.0)
            self.assertLessEqual(float(r["null_p_home_win"]), 1.0)


class TestStrategies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        led, _ = E.build_ledger()
        cls.wf = E.walk_forward_predictions(led)
        cls.sres = E.evaluate_strategies(cls.wf)
        cls.parlay = E.evaluate_parlays(cls.wf)
        cls.n_trials = len([k for k in cls.sres if cls.sres[k]["n"] > 0]) + 1
        cls.luck = E.build_luck_skill(cls.sres, cls.parlay, cls.n_trials)

    def test_every_graded_strategy_has_a_null_rate(self):
        for r in self.luck:
            self.assertNotEqual(r["mean_null_win_rate"], "")

    def test_lift_equals_win_rate_minus_null(self):
        for r in self.luck:
            self.assertAlmostEqual(float(r["lift_over_null"]),
                                   float(r["win_rate"]) - float(r["mean_null_win_rate"]),
                                   places=3)

    def test_parlay_legs_are_non_overlapping(self):
        seen = set()
        for r in self.parlay["rows"]:
            for leg in (r["leg_a"], r["leg_b"]):
                self.assertNotIn(leg, seen, "leg reused across parlays: %s" % leg)
                seen.add(leg)

    def test_parlay_hit_rate_within_frechet_bounds(self):
        p = self.parlay
        self.assertGreaterEqual(float(p["parlay_hit_rate"]), float(p["frechet_min"]) - 1e-9)
        self.assertLessEqual(float(p["parlay_hit_rate"]), float(p["frechet_max"]) + 1e-9)
        self.assertEqual(p["within_frechet_bounds"], "YES")

    def test_selectivity_report_is_honest_about_monotonicity(self):
        led, _ = E.build_ledger()
        wf = E.walk_forward_predictions(led)
        sel = E.selectivity_test(wf)
        self.assertIn(sel["monotone_increasing"], ("YES", "NO"))
        if sel["monotone_increasing"] == "NO":
            self.assertIn("NOT ESTABLISHED", sel["interpretation"])


class TestCorrelations(unittest.TestCase):
    def test_frechet_bounds_hold_for_every_combo(self):
        for r in rows("prop_combos.csv"):
            joint = float(r["p_joint_observed"])
            self.assertGreaterEqual(joint, float(r["frechet_min"]) - 1e-9)
            self.assertLessEqual(joint, float(r["frechet_max"]) + 1e-9)
            self.assertEqual(r["within_frechet_bounds"], "YES")

    def test_no_official_prop_line_is_fabricated(self):
        for r in rows("prop_combos.csv"):
            self.assertEqual(r["official_prop_line"], "")
            self.assertEqual(r["official_price"], "")

    def test_correlation_coefficients_in_range(self):
        for r in rows("correlations.csv"):
            if r["pearson_r"]:
                self.assertGreaterEqual(float(r["pearson_r"]), -1.0)
                self.assertLessEqual(float(r["pearson_r"]), 1.0)

    def test_net_points_correlates_positively_with_winning(self):
        corr = {r["pair_id"]: r for r in rows("correlations.csv")}
        self.assertGreater(float(corr["CORR-T03"]["pearson_r"]), 0.5)


class TestZeroHallucinationPolicy(unittest.TestCase):
    def test_injury_rows_never_carry_official_snap_epa(self):
        for r in rows("injuries.csv"):
            self.assertEqual(r["snap_epa_official"], "")

    def test_leaderboard_has_no_fabricated_pool(self):
        for r in rows("leaderboard.csv"):
            self.assertEqual(r["pool_size"], "")
            self.assertEqual(r["payout_rule"], "")

    def test_unissued_game_statuses_are_blank(self):
        for r in rows("injuries.csv"):
            if "Unconfirmed" in r["availability_tier"]:
                self.assertEqual(r["official_game_status"], "")

    def test_every_flagged_reference_is_defined(self):
        import re
        defined = {f["id"] for f in G.FLAGGED}
        referenced = set()
        for r in rows("injuries.csv"):
            referenced |= set(re.findall(r"\bFLG-\d{2}\b", r["flag_id"]))
        self.assertTrue(referenced <= defined)


class TestRegisters(unittest.TestCase):
    def test_ids_are_unique_within_each_register(self):
        for name, reg in (("REQUIREMENTS", G.REQUIREMENTS), ("SUGGESTIONS", G.SUGGESTIONS),
                          ("DECISION_PATHS", G.DECISION_PATHS),
                          ("PREDECISION_QUESTIONS", G.PREDECISION_QUESTIONS),
                          ("DISCOVERY_ACTIONS", G.DISCOVERY_ACTIONS),
                          ("SIGNALS", G.SIGNALS), ("STRATEGIES", G.STRATEGIES),
                          ("VALIDATION_GATES", G.VALIDATION_GATES),
                          ("REPO_AUDIT", G.REPO_AUDIT), ("OFFICIAL_SOURCES", G.OFFICIAL_SOURCES),
                          ("FLAGGED", G.FLAGGED)):
            ids = [x["id"] for x in reg]
            self.assertEqual(len(ids), len(set(ids)), "duplicate id in %s" % name)

    def test_every_gate_is_fail_closed(self):
        for g in G.VALIDATION_GATES:
            self.assertTrue(g["fail_closed"], "gate %s must be fail-closed" % g["id"])

    def test_ten_gates_ten_strategies(self):
        self.assertEqual(len(G.VALIDATION_GATES), 10)
        self.assertEqual(len(G.STRATEGIES), 10)

    def test_every_suggestion_maps_to_a_declared_path(self):
        paths = {p["id"] for p in G.DECISION_PATHS}
        for s in G.SUGGESTIONS:
            self.assertIn(s["path"], paths)

    def test_every_discovery_action_targets_a_real_question(self):
        qids = {q["id"] for q in G.PREDECISION_QUESTIONS}
        for d in G.DISCOVERY_ACTIONS:
            self.assertIn(d["target_question"], qids)

    def test_every_register_row_has_a_source_url(self):
        for name, reg in (("REQUIREMENTS", G.REQUIREMENTS), ("SUGGESTIONS", G.SUGGESTIONS),
                          ("DECISION_PATHS", G.DECISION_PATHS),
                          ("PREDECISION_QUESTIONS", G.PREDECISION_QUESTIONS),
                          ("DISCOVERY_ACTIONS", G.DISCOVERY_ACTIONS),
                          ("SIGNALS", G.SIGNALS), ("REPO_AUDIT", G.REPO_AUDIT),
                          ("FLAGGED", G.FLAGGED), ("OFFICIAL_SOURCES", G.OFFICIAL_SOURCES)):
            for x in reg:
                self.assertTrue(x.get("source_url") or x.get("url"),
                                "%s row %s has no source link" % (name, x["id"]))

    def test_official_sources_are_official_hosts(self):
        # League and league-operations domains, plus pages published by the clubs
        # themselves -- which the register must declare as "(official)".
        for s in G.OFFICIAL_SOURCES:
            host = s["url"].split("/")[2]
            if host.endswith("nfl.com"):
                continue
            self.assertTrue(s["publisher"].endswith("(official)"),
                            "non-league host %s is not declared an official club: %s"
                            % (host, s["publisher"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
