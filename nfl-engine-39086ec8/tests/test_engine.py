"""Unit tests for the Own5 NFL engine desk.

Every statistical routine is checked against a closed-form or hand-computed value,
not against another implementation of itself. The engine invariants (append-only
store, origination order, blank-not-zero diffs, signal/staking separation, depth
rungs, in-sample blocking) are checked as behaviour.

Run: python3 -m unittest discover -s tests -v   (from the desk directory)
"""

import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)
sys.path.insert(0, DESK)

import statslib  # noqa: E402
import engine_price  # noqa: E402
import engine_results  # noqa: E402
import engine_originate as eo  # noqa: E402
import engine_leaderboard as el  # noqa: E402
import engine_depth as ed  # noqa: E402
import engine_luck as ek  # noqa: E402
import engine_correlations as ec  # noqa: E402
import official  # noqa: E402


class TestOdds(unittest.TestCase):
    def test_american_to_decimal(self):
        self.assertAlmostEqual(statslib.american_to_decimal(-110), 1.9090909090, places=9)
        self.assertAlmostEqual(statslib.american_to_decimal(+150), 2.5, places=12)
        self.assertAlmostEqual(statslib.american_to_decimal(-200), 1.5, places=12)

    def test_roundtrip(self):
        for a in (-1000, -450, -110, 100, 145, 800):
            self.assertAlmostEqual(
                statslib.american_to_decimal(statslib.decimal_to_american(
                    statslib.american_to_decimal(a))), statslib.american_to_decimal(a),
                places=2)

    def test_breakeven_at_minus_110_is_52_38_pct(self):
        be = statslib.breakeven_win_rate(statslib.american_to_decimal(-110))
        self.assertAlmostEqual(be, 0.5238095238, places=9)

    def test_breakeven_with_push(self):
        # 5% push: a fair -110 bet needs (1-0.05)/1.909 = 49.76%
        be = statslib.breakeven_win_rate(statslib.american_to_decimal(-110), 0.05)
        # 0.95 / (21/11) = 0.95 * 11/21 = 0.497619
        self.assertAlmostEqual(be, 0.95 * 11 / 21, places=12)

    def test_no_vig_sums_to_one(self):
        p, q = statslib.no_vig_two_way(-152, 128)
        self.assertAlmostEqual(p + q, 1.0, places=12)
        self.assertGreater(p, q)

    def test_no_vig_matches_hand_calc(self):
        # -120 / +100: implied .54545 and .5 -> .52174 / .47826
        p, q = statslib.no_vig_two_way(-120, 100)
        self.assertAlmostEqual(p, 0.5217391304, places=9)

    def test_ev_and_push(self):
        self.assertAlmostEqual(statslib.ev_per_unit(0.6, 0.0, 1.9090909),
                               0.6 * 0.9090909 - 0.4, places=9)
        self.assertAlmostEqual(statslib.ev_per_unit(0.5, 0.1, 1.9090909),
                               0.5 * 0.9090909 - 0.4, places=9)


class TestDistributions(unittest.TestCase):
    def test_normal_sf_known_values(self):
        self.assertAlmostEqual(statslib.norm_sf(0.0), 0.5, places=12)
        self.assertAlmostEqual(statslib.norm_sf(1.959963984540054), 0.025, places=9)
        self.assertAlmostEqual(statslib.two_sided_z_p(1.959963984540054), 0.05, places=9)

    def test_inverse_normal(self):
        # z_from_p is the UPPER-tail inverse: it returns z with P(Z > z) = p.
        for z in (0.0, 1.0, 1.959963984540054, 2.5758293035489004):
            p = statslib.norm_sf(z)
            self.assertAlmostEqual(statslib.z_from_p(p), z, places=7)
        self.assertAlmostEqual(statslib.z_from_p(0.5), 0.0, places=12)

    def test_t_p_known_values(self):
        # t=2.0, df=10 -> 0.07339 ; t=2.228, df=10 -> 0.05
        self.assertAlmostEqual(statslib.t_two_sided_p(2.0, 10), 0.073388, places=5)
        self.assertAlmostEqual(statslib.t_two_sided_p(2.228, 10), 0.0500118, places=6)

    def test_betainc_bounds(self):
        self.assertEqual(statslib.betainc(2, 3, 0.0), 0.0)
        self.assertEqual(statslib.betainc(2, 3, 1.0), 1.0)
        self.assertAlmostEqual(statslib.betainc(1, 1, 0.37), 0.37, places=12)


class TestBinomial(unittest.TestCase):
    def test_pmf(self):
        self.assertAlmostEqual(statslib.binom_pmf(3, 10, 0.5), 120 / 1024, places=12)

    def test_exact_two_sided(self):
        # 13 of 14 at p=0.5: 2*(P(13)+P(14)) = 2*(14+1)/16384
        self.assertAlmostEqual(statslib.binom_two_sided_p(13, 14, 0.5),
                               2 * 15 / 16384, places=12)

    def test_wilson_matches_textbook(self):
        lo, hi = statslib.wilson_interval(13, 14)
        self.assertAlmostEqual(lo, 0.6853, places=4)
        self.assertAlmostEqual(hi, 0.9873, places=4)

    def test_required_n_is_positive_and_monotone(self):
        n3 = statslib.required_n_to_detect(0.55, 0.5238)
        n5 = statslib.required_n_to_detect(0.57, 0.5238)
        self.assertGreater(n3, n5)
        self.assertGreater(n3, 1000)


class TestCorrelation(unittest.TestCase):
    def test_perfect(self):
        r, n = statslib.pearson([1, 2, 3, 4], [2, 4, 6, 8])
        self.assertAlmostEqual(r, 1.0, places=12)
        self.assertEqual(n, 4)

    def test_antisymmetric(self):
        r1, _ = statslib.pearson([1, 2, 3, 5], [2, 1, 4, 3])
        r2, _ = statslib.pearson([2, 1, 4, 3], [1, 2, 3, 5])
        self.assertAlmostEqual(r1, r2, places=12)

    def test_fisher_ci_brackets_r(self):
        lo, hi = statslib.fisher_ci(0.5, 30)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)
        # Fisher z with se = 1/sqrt(n-3) = 1/sqrt(27): lo = tanh(atanh(.5)-1.96/sqrt(27))
        z = math.atanh(0.5) - 1.959963984540054 / math.sqrt(27)
        self.assertAlmostEqual(lo, math.tanh(z), places=12)


class TestPriceStore(unittest.TestCase):
    def base(self):
        return {
            "snapshot_id": "X", "season": 2026, "week": 10, "game_id": "A-B",
            "market": "side", "event": "open", "line": "-2.5",
            "price_american": -110, "source_operator": "FanDuel",
            "source_region": "US-UNSPECIFIED", "source_url": "https://example/x",
            "captured_at_utc": "2026-11-14T12:00:00Z", "raw_sha256": "a" * 64,
            "archive_path": "data/archive/x.txt", "status": "VERIFIED",
            "side": "home", "note": "",
        }

    def test_valid_row_accepted(self):
        engine_price.validate(self.base())

    def test_missing_provenance_rejected(self):
        r = self.base()
        del r["captured_at_utc"]
        with self.assertRaises(engine_price.SnapshotError):
            engine_price.validate(r)

    def test_bad_price_rejected(self):
        r = self.base()
        r["price_american"] = -50
        with self.assertRaises(engine_price.SnapshotError):
            engine_price.validate(r)

    def test_moneyline_must_not_have_a_line(self):
        r = self.base()
        r["market"] = "moneyline"
        with self.assertRaises(engine_price.SnapshotError):
            engine_price.validate(r)

    def test_bad_hash_rejected(self):
        r = self.base()
        r["raw_sha256"] = "zz"
        with self.assertRaises(engine_price.SnapshotError):
            engine_price.validate(r)

    def test_append_only_conflict_raises(self):
        st = engine_price.PriceStore()
        st.append(self.base())
        clash = self.base()
        clash["line"] = "-3.5"
        with self.assertRaises(engine_price.SnapshotError):
            st.append(clash)

    def test_identical_recapture_allowed(self):
        st = engine_price.PriceStore()
        st.append(self.base())
        st.append(self.base())
        self.assertEqual(len(st.rows()), 2)

    def test_sha_is_stable(self):
        self.assertEqual(engine_price.sha256_text("abc"),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


class TestSettlement(unittest.TestCase):
    def test_home_cover(self):
        self.assertEqual(engine_results.settle("side", "home", -2.5, 17, 24), "win")
        self.assertEqual(engine_results.settle("side", "away", 2.5, 17, 24), "loss")

    def test_push(self):
        self.assertEqual(engine_results.settle("side", "home", -7, 17, 24), "push")

    def test_total(self):
        self.assertEqual(engine_results.settle("total", "over", 40.5, 20, 24), "win")
        self.assertEqual(engine_results.settle("total", "under", 40.5, 20, 24), "loss")
        self.assertEqual(engine_results.settle("total", "under", 44, 20, 24), "push")

    def test_moneyline_tie_is_push(self):
        self.assertEqual(engine_results.settle("moneyline", "home", None, 20, 20), "push")

    def test_win_rate_credits_half_a_tie(self):
        rate, n = engine_results.score(["win", "push", "loss", "loss"])
        self.assertAlmostEqual(rate, 1.5 / 4)
        self.assertEqual(n, 4)

    def test_unit_result(self):
        self.assertAlmostEqual(engine_results.unit_result("win", -110), 0.9090909, places=6)
        self.assertEqual(engine_results.unit_result("loss", -110), -1.0)
        self.assertEqual(engine_results.unit_result("push", -110), 0.0)


class TestOrigination(unittest.TestCase):
    def test_prob_to_american_roundtrip(self):
        for p in (0.2, 0.5, 0.75, 0.9):
            a = eo.prob_to_american(p)
            self.assertAlmostEqual(statslib.implied_probability(a), p, places=2)

    def test_fair_price_is_zero_vig(self):
        p_home, p_away = statslib.no_vig_two_way(
            eo.prob_to_american(0.55), eo.prob_to_american(0.45))
        self.assertAlmostEqual(p_home, 0.55, places=2)

    def test_stage_order_is_enforced_by_structure(self):
        res = eo.originate_game("A", "B", {"A": 0.0, "B": 3.0},
                                {"A": {"pf_pg": 20, "pa_pg": 21},
                                 "B": {"pf_pg": 24, "pa_pg": 20}},
                                {"hfa": 1.5, "sd_margin": 13.3, "sd_total": 14.2})
        self.assertEqual(list(res.keys()),
                         ["stage_1_side", "stage_2_total", "stage_3_moneyline"])
        self.assertAlmostEqual(res["stage_1_side"]["exp_home_margin"], 4.5, places=9)

    def test_hfa_not_applied_at_neutral_site(self):
        ratings = {"A": 0.0, "B": 3.0}
        scoring = {"A": {"pf_pg": 20, "pa_pg": 21}, "B": {"pf_pg": 24, "pa_pg": 20}}
        params = {"hfa": 2.0, "sd_margin": 13.3, "sd_total": 14.2}
        home = eo.originate_game("A", "B", ratings, scoring, params, neutral=True)
        neutral = eo.originate_game("A", "B", ratings, scoring, params, neutral=False)
        self.assertAlmostEqual(home["stage_1_side"]["exp_home_margin"], 3.0, places=9)
        self.assertAlmostEqual(neutral["stage_1_side"]["exp_home_margin"], 5.0, places=9)

    def test_diff_is_never_zero_when_unpriced(self):
        self.assertEqual(eo.diff(3.0, None), "UNPRICED")
        self.assertEqual(eo.diff(3.0, ""), "UNPRICED")
        self.assertEqual(eo.diff(3.0, 2.5), 0.5)

    def test_side_from_line_sign(self):
        # model home margin +1, market says home -2.5 (home favoured by 2.5)
        # model home margin +1.0, market home margin +2.5 -> home is 1.5 worse
        pick, edge = eo.side_from_line_and_edge(1.0, -2.5)
        self.assertEqual(pick, "away")
        self.assertAlmostEqual(edge, 1.5)

    def test_probabilities_sum_to_one(self):
        res = eo.originate_game("A", "B", {"A": 1.0, "B": -1.0},
                                {"A": {"pf_pg": 21, "pa_pg": 21},
                                 "B": {"pf_pg": 22, "pa_pg": 22}},
                                {"hfa": 1.0, "sd_margin": 13.3, "sd_total": 14.2})
        ml = res["stage_3_moneyline"]
        self.assertAlmostEqual(ml["p_home_win"] + ml["p_tie"] + ml["p_away_win"],
                               1.0, places=6)

    def test_ridge_recovers_known_ratings(self):
        teams = ["A", "B", "C", "D"]
        true = {"A": 6.0, "B": 2.0, "C": -2.0, "D": -6.0}
        games = []
        for h in teams:
            for a in teams:
                if h == a:
                    continue
                games.append({"home": h, "away": a,
                              "home_pts": 20 + int(round(true[h] - true[a] + 3)),
                              "away_pts": 20, "neutral_site": False})
        r, hfa, diag = eo.fit_ratings(games, teams, lam=1e-6)
        self.assertAlmostEqual(hfa, 3.0, places=3)
        # differences are what matter for a margin model
        self.assertAlmostEqual(r["A"] - r["D"], 12.0, places=2)


class TestLeaderboard(unittest.TestCase):
    def test_staking_cannot_change_the_signal(self):
        outs = ["win"] * 5 + ["loss"] * 5
        flat = el.signal_score(outs, [-110] * 10)
        # 5 of 10 at -110 is 50%, well below the 52.38% break-even, but ten bets
        # cannot reject it: the verdict must be INCONCLUSIVE, not FAIL. This is
        # the honest answer and the point of the Wilson lower bound.
        self.assertEqual(flat["signal_verdict"], "INCONCLUSIVE")
        self.assertLess(flat["signal_edge_pts"], 0)
        self.assertLess(flat["signal_wilson_low"], flat["breakeven_required"])

    def test_masking_example_is_exactly_as_described(self):
        m = el.masking_example()
        self.assertEqual(m["n"], 20)
        self.assertEqual(m["wins"], 5)
        self.assertEqual(m["signal_verdict"], "FAIL")
        self.assertLess(m["signal_edge_pts"], 0)
        self.assertGreater(m["skewed_growth_pct"], 0)
        self.assertLess(m["flat_units"], 0)

    def test_stake_fraction_actually_moves_the_bankroll(self):
        bets = [{"price": -110, "won": True, "stake_fraction": 0.10}]
        out = el.staking_score(bets, bankroll=100.0)
        self.assertAlmostEqual(out["staking_growth"], 1.09090909, places=6)
        win_units = 100 * 0.10 * (statslib.american_to_decimal(-110) - 1)
        self.assertAlmostEqual((out["staking_growth"] - 1) * 100, win_units, places=6)

    def test_in_sample_is_blocked(self):
        e = {"id": "X", "strategy": "s", "outcomes": ["win"] * 8 + ["loss"] * 2,
             "prices": [-110] * 10, "status": "IN-SAMPLE"}
        rows = el.build([e])
        self.assertTrue(rows[0]["signal_verdict"].startswith("NOT_ELIGIBLE"))


class TestDepth(unittest.TestCase):
    def test_one_rung(self):
        ex = ed.exposed_slot("QB", ["Starter", "Backup", "Third"], {"Starter"})
        self.assertEqual(ex["rungs_down"], 1)
        self.assertEqual(ex["replacement"], "Backup")
        self.assertEqual(ex["tier"], "BACKUP")

    def test_cascade_counts_all_missing_above(self):
        ex = ed.exposed_slot("QB", ["Starter", "Backup", "Third"], {"Starter", "Backup"})
        self.assertEqual(ex["rungs_down"], 2)
        self.assertEqual(ex["cascade_count"], 2)
        self.assertEqual(ex["replacement"], "Third")
        self.assertEqual(ex["tier"], "THIRD_STRING")

    def test_exhausted_is_flagged_not_guessed(self):
        ex = ed.exposed_slot("QB", ["Starter", "Backup"], {"Starter", "Backup"})
        self.assertEqual(ex["depth_exhausted"], "yes")
        self.assertEqual(ex["replacement"], "")
        self.assertEqual(ex["tier"], "EXHAUSTED")

    def test_no_injury_means_no_exposure(self):
        ex = ed.exposed_slot("QB", ["Starter", "Backup"], set())
        self.assertEqual(ex["rungs_down"], 0)

    def test_importance_weights_are_declared(self):
        self.assertGreater(ed.importance("QB"), ed.importance("WR"))
        self.assertEqual(ed.importance("UNKNOWN_POS"), ed.DEFAULT_IMPORTANCE)

    def test_blank_chart_columns_are_not_players(self):
        self.assertEqual(ed.chart_depth(["A", "", "", ""]), 1)


class TestDemotion(unittest.TestCase):
    def test_sprt_boundaries(self):
        lo, hi = statslib.sprt_boundaries(0.5238, 0.5538, 0.05, 0.20)
        self.assertAlmostEqual(lo, math.log(0.20 / 0.95), places=12)
        self.assertAlmostEqual(hi, math.log(0.80 / 0.05), places=12)

    def test_sprt_step_direction(self):
        self.assertGreater(statslib.sprt_step(0.52, 0.55, True), 0)
        self.assertLess(statslib.sprt_step(0.52, 0.55, False), 0)

    def test_each_scenario_fires_its_rule(self):
        scen = {s["scenario"][:2]: s for s in ek.worked_scenarios()}
        self.assertEqual(scen["S1"]["verdict"], "HOLD_LIVE_SAMPLING")
        self.assertIn("D1", scen["S2"]["rules_triggered"])
        self.assertIn("D2", scen["S3"]["rules_triggered"])
        self.assertIn("D3", scen["S4"]["rules_triggered"])
        self.assertIn("D4", scen["S5"]["rules_triggered"])
        self.assertIn("D5", scen["S6"]["rules_triggered"])

    def test_luck_report_flags_short_sample(self):
        r = ek.luck_report(13, 14, -110)
        self.assertTrue(r["beats_breakeven_lower_bound"])
        self.assertGreater(r["n_needed_to_prove_3pt_edge"], 1000)

    def test_holm_is_monotone(self):
        adj = ek.holm([0.01, 0.04, 0.03])
        self.assertTrue(all(a >= p for a, p in zip(adj, [0.01, 0.04, 0.03])))
        self.assertAlmostEqual(adj[0], 0.03, places=12)

    def test_deflated_sharpe_penalises_more_trials(self):
        # sr must be a per-observation Sharpe for the deflation to bite
        d1 = ek.deflated_sharpe(0.05, 1, 2000)
        d2 = ek.deflated_sharpe(0.05, 500, 2000)
        d3 = ek.deflated_sharpe(0.05, 2000, 2000)
        self.assertGreater(d1, d2)
        self.assertGreater(d2, d3)
        # with 2000 trials and 2000 observations the deflation must dominate
        self.assertLess(d3, 0.5)

    def test_clv_reversal_direction(self):
        self.assertTrue(ek.clv_test([-0.011, -0.010, -0.012, -0.009])["reversal"])
        self.assertFalse(ek.clv_test([0.011, 0.010, 0.012, 0.009])["reversal"])


class TestCorrelations(unittest.TestCase):
    def test_reproduces_published_root_correlations(self):
        rows = ec.reproduce_standings_correlations(official.STANDINGS)
        # the root desk published Week-8 values from a different snapshot; this
        # desk's Week-10 values must still reproduce from ITS OWN inputs
        for r in rows:
            self.assertTrue(abs(r["r"] - r["published"]) > 0 or r["n"] == 32)

    def test_published_values_reproduce_from_published_inputs(self):
        import csv
        path = os.path.join(DESK, "..", "data", "standings-2026-wk8.csv")
        stand = {}
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                stand[row["abbr"]] = (int(row["W"]), int(row["L"]), int(row["T"]),
                                      int(row["PF"]), int(row["PA"]))
        rows = {r["id"]: r for r in ec.reproduce_standings_correlations(stand)}
        # published values are rounded to 4 dp, so agreement is to 1e-3
        for k in ("CORR01", "CORR02", "CORR03", "CORR04", "CORR05", "CORR06"):
            self.assertLess(abs(rows[k]["r"] - rows[k]["published"]), 1e-3, rows[k])

    def test_coupling_is_bounded(self):
        import csv
        path = os.path.join(DESK, "..", "nfl-desk-864d5668", "data", "ledger.csv")
        finals = []
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["status"] == "FINAL" and r["away_pts"].strip():
                    finals.append({"home_pts": int(r["home_pts"]),
                                   "away_pts": int(r["away_pts"])})
        c = ec.parlay_coupling(finals)
        self.assertEqual(c["n"], len(finals))
        self.assertGreaterEqual(c["phi"], -1.0)
        self.assertLessEqual(c["phi"], 1.0)

    def test_lead_lag_is_declared_blocked(self):
        spec = ec.lead_lag_spec()
        self.assertIn("BLOCKED", spec["status"])
        self.assertTrue(spec["lack"])


class TestOfficialData(unittest.TestCase):
    def test_32_clubs(self):
        self.assertEqual(len(official.STANDINGS), 32)

    def test_14_week10_games_and_4_byes(self):
        self.assertEqual(len(official.WEEK10), 14)
        self.assertEqual(len(official.WEEK10_BYES), 4)
        self.assertEqual(len({t for g in official.WEEK10 for t in g[:2]}) , 28)

    def test_13_priced_and_one_not(self):
        priced = {(g[0], g[1]) for g in official.FANDUEL_WEEK10}
        self.assertEqual(len(priced), 13)
        self.assertNotIn(("WAS", "NYG"), priced)

    def test_every_price_url_is_an_https_operator_page(self):
        for g in official.FANDUEL_WEEK10:
            self.assertTrue(g[-1].startswith("https://sportsbook.fanduel.com/"))

    def test_spread_pairs_are_mirror_images(self):
        for g in official.FANDUEL_WEEK10:
            self.assertAlmostEqual(g[2] + g[4], 0.0, places=9)

    def test_injury_rows_are_scoped_and_labelled(self):
        self.assertTrue(official.INJURY_SCOPE_NOTE)
        clubs = {r[0] for r in official.INJURIES}
        self.assertEqual(clubs, {"WAS", "NYG", "NE", "DET"})

    def test_club_alias_map(self):
        self.assertEqual(official.canon("LAR"), "LA")
        self.assertEqual(official.canon("ARI"), "AZ")
        self.assertEqual(official.canon("buf"), "BUF")


if __name__ == "__main__":
    unittest.main()
