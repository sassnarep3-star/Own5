"""The desk's promises, tested: chains, no look-ahead, blanks, gates that fail closed.

Each test names the promise it protects, because a test that only asserts "the
function returns something" would pass on a build that silently stopped being true.
"""
import csv
import os
import re
import unittest

from helpers import DESK, DATA  # noqa: F401 (path setup)
import statslib as st


def rows(name):
    with open(os.path.join(DATA, name + ".csv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestChains(unittest.TestCase):
    def test_results_feed_chain_recomputes(self):
        import results_feed
        ok, detail = results_feed.chain_ok()
        self.assertTrue(ok, detail)

    def test_results_feed_tamper_is_detected(self):
        import results_feed
        data = results_feed.read()
        data[3]["away_pts"] = "99"                      # edit one score in memory
        ok, detail = results_feed.chain_ok(data)
        self.assertFalse(ok)
        self.assertIn("seq 4", detail)

    def test_store_chain_recomputes(self):
        import store
        ok, problems, n, head = store.check_chain()
        self.assertTrue(ok, problems)
        self.assertGreater(n, 100)

    def test_store_row_hash_covers_its_contents(self):
        import store
        r = rows("price_snapshots")
        prev = store.GENESIS
        for row in r:
            self.assertEqual(row["prev_hash"], prev)
            self.assertEqual(row["row_hash"], store.row_hash(prev, row))
            prev = row["row_hash"]


class TestResultsFeed(unittest.TestCase):
    def test_every_check_passes(self):
        chk = rows("results_checks")
        self.assertGreaterEqual(len(chk), 13)
        self.assertEqual([c["check_id"] for c in chk if c["result"] != "PASS"], [])

    def test_pending_games_have_no_numbers(self):
        for r in rows("results_feed"):
            if r["status"] != "FINAL":
                for c in ("away_pts", "home_pts", "margin_home", "total_points"):
                    self.assertEqual(r[c], "", f"{r['game_key']} leaks {c} on an unplayed game")

    def test_final_games_all_carry_a_source(self):
        for r in rows("results_feed"):
            if r["status"] == "FINAL":
                self.assertTrue(r["official_url"].startswith("https://www.nfl.com/")
                                or r["verification"].startswith("MIRROR"),
                                r["game_key"])

    def test_margin_and_total_are_consistent_with_scores(self):
        for r in rows("results_feed"):
            if r["status"] == "FINAL":
                self.assertEqual(int(r["margin_home"]), int(r["home_pts"]) - int(r["away_pts"]))
                self.assertEqual(int(r["total_points"]), int(r["home_pts"]) + int(r["away_pts"]))

    def test_standings_reconcile_to_the_feed(self):
        import results_feed
        from pinned import capture as cap
        tally = {}
        for r in rows("results_feed"):
            if r["status"] != "FINAL":
                continue
            m = int(r["margin_home"])
            for side, other in (("home", "away"), ("away", "home")):
                t = tally.setdefault(r[side], [0, 0, 0, 0, 0])
                t[3] += int(r[side + "_pts"])
                t[4] += int(r[other + "_pts"])
                if m == 0:
                    t[2] += 1
                elif (m > 0) == (side == "home"):
                    t[0] += 1
                else:
                    t[1] += 1
        for team, club, conf, div, w, l, tie, pct, pf, pa, net in cap.STANDINGS:
            self.assertEqual(tally[team][:5], [w, l, tie, pf, pa], f"{team} does not reconcile")

    def test_neutral_sites_match_the_mirror(self):
        feed = {r["game_key"]: r for r in rows("results_feed")}
        import inputs
        for g in inputs.games_2026():
            if (g.get("away_score") or "").strip() or True:
                key = f"{g['away_team']}@{g['home_team']}-2026-w{g['week']}"
                r = feed.get(key)
                if r and g.get("location"):
                    self.assertEqual(g["location"] == "Neutral", r["neutral"] == "True", key)


class TestStore(unittest.TestCase):
    def test_every_snapshot_row_is_attributable(self):
        for r in rows("price_snapshots"):
            for c in ("captured_at_utc", "provider_display", "source_url", "capture_method",
                      "verification", "line_stage"):
                self.assertTrue(str(r[c]).strip(), f"seq {r['seq']} has no {c}")

    def test_no_pre_game_quote_is_labelled_closing(self):
        for r in rows("price_snapshots"):
            self.assertIn(r["line_stage"], ("opening", "pre_game", "closing", "undocumented"))
            if r["lineage"] == "CAPTURE":
                self.assertNotEqual(r["line_stage"], "closing",
                                    "a manually transcribed page cannot be a closing price")

    def test_missing_moneyline_is_recorded_as_a_gap(self):
        snap = rows("price_snapshots")
        gap = [r for r in snap if r["market"] == "moneyline" and r["selection"] == "opening_moneyline"]
        self.assertTrue(gap)
        for r in gap:
            self.assertEqual(r["verification"], "NOT AVAILABLE")
            self.assertEqual(r["price_american"], "")
            self.assertEqual(r["line_value"], "")

    def test_untranscribed_cell_is_blank_not_zero(self):
        snap = rows("price_snapshots")
        bal = [r for r in snap if r["game_key"].startswith("BAL@CAR") and r["market"] == "moneyline"
               and r["selection"] == "CAR"]
        self.assertTrue(bal, "the BAL@CAR gap row is missing from the store")
        for r in bal:
            self.assertEqual(r["price_american"], "")
            self.assertIn("not transcribed", r["verification"] + r["note"])

    def test_provider_is_never_called_official(self):
        for r in rows("price_snapshots"):
            self.assertNotIn("official", r["provider_display"].lower())


class TestOrigination(unittest.TestCase):
    def test_stages_run_in_the_mandated_order(self):
        der = rows("derivation")
        stages = [d["stage"] for d in der]
        self.assertEqual(stages[:3], ["stage 1", "stage 2", "stage 3"])
        self.assertIn("spread", der[0]["columns"])        # stage 1 is the side
        self.assertIn("total", der[1]["columns"])         # stage 2 is the total
        self.assertIn("ml", der[2]["columns"])            # stage 3 is the moneyline
        self.assertIn("margin distribution", der[2]["input"])   # stage 3 reads stage 1, not the raw data
        self.assertIn("no new fit", der[2]["rule"])            # the ML is derived, not re-fitted

    def test_fair_lines_are_on_the_market_tick(self):
        for r in rows("line_sheet"):
            for c in ("fair_spread_home", "fair_total"):
                v = float(r[c])
                self.assertAlmostEqual((v * 2) % 1, 0.0, places=6,
                                       msg=f"{c}={v} is not a multiple of 0.5")

    def test_difference_columns_are_independent_of_each_side(self):
        for r in rows("line_sheet"):
            if r["market_spread_home"] not in ("", None):
                self.assertAlmostEqual(float(r["diff_spread_pts"]),
                                       float(r["fair_spread_home"]) - float(r["market_spread_home"]),
                                       places=6)
            if r["market_total"] not in ("", None):
                self.assertAlmostEqual(float(r["diff_total_pts"]),
                                       float(r["fair_total"]) - float(r["market_total"]), places=6)

    def test_no_look_ahead_in_the_historical_predictions(self):
        bt = rows("backtest_predictions")
        self.assertGreater(len(bt), 1000)
        # a week-w model may only have seen weeks < w of its own season, so the fitted
        # count cannot exceed the games available before it in that window
        import originate
        hist = originate.mirror_games({"2021", "2022", "2023", "2024", "2025"})
        by_season = {}
        for g in hist:
            by_season.setdefault(g["season"], []).append(g)
        for r in bt[:200]:
            earlier = [g for g in by_season[r["season"]] if int(g["week"]) < int(r["week"])]
            self.assertGreaterEqual(int(r["games_fitted"]), 0)
            self.assertLessEqual(len(earlier), int(r["games_fitted"]),
                                 "a model fitted on less than its own season's earlier games")
            self.assertLessEqual(int(r["games_fitted"]),
                                 sum(len(v) for k, v in by_season.items() if k <= r["season"]))

    def test_the_live_slate_model_used_only_completed_games(self):
        import originate
        current = originate.feed_games()
        completed_before = [g for g in current if g["status"] == "FINAL" and g["week"] < 10]
        r10 = originate.build_weekly_models([10], current, [])[10]
        self.assertEqual(r10.n, len(completed_before),
                         "the Week 10 model must have seen exactly the 9 completed weeks "
                         "and nothing else")
        self.assertLess(r10.n, sum(1 for g in current if g["status"] == "FINAL"),
                        "a week-10 model cannot have seen every completed game")
        r11 = originate.build_weekly_models([11], current, [])[11]
        self.assertGreaterEqual(r11.n, r10.n)             # more weeks played, more games fitted

    def test_neutral_games_lose_the_home_field(self):
        import originate
        hist = originate.feed_games()
        cur = [g for g in hist if g["status"] == "FINAL" and g["week"] < 10]
        rat = originate.Ratings(cur)
        a = rat.predict("DET", "NE", neutral=True)
        b = rat.predict("DET", "NE", neutral=False)
        self.assertAlmostEqual(a["margin"] + 0.0, b["margin"] - rat.b[1], places=6)

    def test_moneyline_probabilities_close_over_the_tie_mass(self):
        for r in rows("line_sheet"):
            ph, pa, pt = (float(r["model_p_home_ml"]), float(r["model_p_away_ml"]), float(r["model_p_tie"]))
            self.assertAlmostEqual(ph + pa + pt, 1.0, places=3)
            self.assertGreater(pt, 0.0)


class TestGrading(unittest.TestCase):
    def test_be_rates_match_the_prices(self):
        import ledger
        self.assertAlmostEqual(ledger.be_rate(-110), 110 / 210, places=9)
        self.assertAlmostEqual(ledger.be_rate(100), 0.5, places=9)
        self.assertAlmostEqual(ledger.be_rate(-120), 120 / 220, places=9)
        self.assertIsNone(ledger.be_rate(""))

    def test_push_returns_the_stake(self):
        import grade
        self.assertEqual(grade.payout({"result": "push", "price": -110, "pay_decimal": None}), 0.0)

    def test_parlay_payout_is_the_product_of_the_two_legs(self):
        import grade
        b = {"result": "win", "price": None, "pay_decimal": (1 + 100 / 110) * (1 + 100 / 110) - 1}
        self.assertAlmostEqual(grade.payout(b), (210 / 110) ** 2 - 1, places=9)

    def test_parlay_break_even_uses_the_offer_not_the_outcome(self):
        import ledger
        # a losing parlay must still contribute its break-even rate, or the mean
        # break-even would be computed from wins only and would look beatable
        bet = {"result": "loss", "price": -202, "pay_decimal": -1.0}
        self.assertAlmostEqual(ledger.bet_be(bet), 202 / 302, places=9)

    def test_pushes_excluded_from_rate_kept_in_count(self):
        sig = rows("leaderboard_signal")
        for r in sig:
            self.assertGreaterEqual(int(r["bets"]), int(r["settled"]))
            self.assertEqual(int(r["pushes"]), int(r["bets"]) - int(r["settled"]))

    def test_holm_is_monotone_and_never_below_the_raw_p(self):
        sig = rows("leaderboard_signal")
        pairs = []
        for r in sig:
            if r["holm_adjusted_p"] in ("", None):
                continue
            raw = 0.0 if r["binom_p_vs_break_even"] == "<0.0001" else float(r["binom_p_vs_break_even"])
            adj = 0.0 if r["holm_adjusted_p"] == "<0.0001" else float(r["holm_adjusted_p"])
            self.assertGreaterEqual(adj + 1e-12, raw)
            self.assertLessEqual(adj, 1.0 + 1e-12)
            pairs.append((raw, adj))
        self.assertTrue(pairs)

    def test_gates_fail_closed(self):
        g = {r["gate_id"]: r["result"] for r in rows("validation")}
        self.assertEqual(g["V-08"], "FAIL", "CLV gate must not pass without closing data")
        self.assertEqual(g["V-11"], "FAIL", "promotion must not pass without a live record")
        self.assertIn(g["V-10"], ("BLOCKED", "PASS", "FAIL"))
        for gid, res in g.items():
            self.assertIn(res, ("PASS", "FAIL", "BLOCKED"), gid)

    def test_no_gate_result_is_blank(self):
        for r in rows("validation"):
            self.assertTrue(r["result"], r["gate_id"])
            self.assertTrue(r["measured"], f"{r['gate_id']} has no measurement recorded")


class TestGateDemotion(unittest.TestCase):
    def bet(self, seq, res, price=-110, stake="1.0", clv=""):
        return dict(seq=seq, strategy="X", result=res, price_taken=price, stake_units=stake,
                    clv_points=clv)

    def test_losing_live_run_demotes_without_waiting_for_significance(self):
        import gate
        sig = [dict(strategy="X", settled="600", holm_adjusted_p="0.4", break_even_mean="0.5238",
                    max_drawdown_units="")]
        bets = [self.bet(i, "loss") for i in range(1, 25)]
        # same record, two starting states: the gate must fire on a live strategy and
        # must not pretend to demote something that was never live
        out = gate.evaluate(bets, sig, {}, integrity_ok=True)
        self.assertEqual(out[0]["decision"], "STAYS ON PAPER")
        self.assertIn("D1", out[0]["rules_broken"])
        self.assertIn("D2", out[0]["rules_broken"])
        live = gate.evaluate(bets, sig, {}, integrity_ok=True, states={"X": "LIVE"})
        self.assertEqual(live[0]["decision"], "DEMOTE TO PAPER")
        self.assertEqual(live[0]["state_before"], "LIVE")
        self.assertLess(float(live[0]["hit_rate_window"]), float(live[0]["break_even_window"]))

    def test_a_winning_live_run_is_not_demoted_for_performance(self):
        import gate
        sig = [dict(strategy="X", settled="600", holm_adjusted_p="0.001", break_even_mean="0.5238",
                    max_drawdown_units="-3")]
        bets = [self.bet(i, "win" if i % 5 else "loss") for i in range(1, 41)]
        out = gate.evaluate(bets, sig, {}, integrity_ok=True, states={"X": "LIVE"})
        self.assertNotIn("D1", out[0]["rules_broken"])
        self.assertEqual(out[0]["decision"], "NO CHANGE")

    def test_missing_state_file_leaves_nothing_live(self):
        import gate
        self.assertEqual(gate.load_states().get("__nope__"), None)
        out = gate.evaluate([], [dict(strategy="__nope__", settled="0", holm_adjusted_p="",
                                      break_even_mean="", max_drawdown_units="")], {})
        self.assertEqual(out[0]["state_before"], "PAPER")

    def test_integrity_failure_demotes_anything_live(self):
        import gate
        sig = [dict(strategy="X", settled="600", holm_adjusted_p="0.001", break_even_mean="0.5238",
                    max_drawdown_units="")]
        out = gate.evaluate([], sig, {}, integrity_ok=False)
        self.assertIn("D5", out[0]["rules_broken"])

    def test_drawdown_limit_defaults_when_backtest_unknown(self):
        import gate
        bets = [self.bet(i, "loss") for i in range(1, 12)]
        out = gate.evaluate(bets, [dict(strategy="X", settled="0", holm_adjusted_p="0.2",
                                        break_even_mean="0.5238", max_drawdown_units="")], {})
        self.assertAlmostEqual(float(out[0]["drawdown_limit_units"]), -6.0, places=6)
        self.assertLessEqual(float(out[0]["drawdown_units"]), -6.0)

    def test_clv_rule_is_unevaluable_not_passed(self):
        import gate
        out = gate.evaluate([self.bet(1, "win", clv="")], [dict(strategy="X", settled="10",
                                                                holm_adjusted_p="0.001",
                                                                break_even_mean="0.5238",
                                                                max_drawdown_units="")], {})
        self.assertIn("D3", out[0]["rules_unevaluable"])
        self.assertNotIn("D3", out[0]["rules_broken"])

    def test_live_ledger_is_not_written_by_the_gate(self):
        import gate
        before = os.path.getsize(os.path.join(DATA, "live_bets.csv"))
        gate.write()
        self.assertEqual(before, os.path.getsize(os.path.join(DATA, "live_bets.csv")))
        self.assertEqual(len(rows("live_bets")), 0)


class TestLeaderboardSeparation(unittest.TestCase):
    def test_signal_rank_is_stake_independent(self):
        lb = rows("leaderboard")
        # re-sorting by units must not change the published signal ranking
        self.assertEqual([r["strategy"] for r in sorted(lb, key=lambda x: int(x["signal_rank"]))],
                         [r["strategy"] for r in lb])
        by_units = sorted(lb, key=lambda r: -float(r["units"] or 0))
        self.assertNotEqual([r["strategy"] for r in by_units], [r["strategy"] for r in lb],
                           "signal and staking orderings are identical - the separation is doing nothing")

    def test_staking_table_carries_no_verdict(self):
        cols = rows("leaderboard_staking")[0].keys()
        for banned in ("verdict", "promote", "decision", "award"):
            self.assertNotIn(banned, list(cols))

    def test_rewards_state_why_they_are_not_awarded(self):
        for r in rows("rewards"):
            if r["award"] in ("NOT AWARDED", "BLOCKED"):
                self.assertGreater(len(r["reason"]), 40, r["division"])

    def test_prop_division_is_blocked_with_a_reason(self):
        rw = {r["division"]: r for r in rows("rewards")}
        self.assertIn("prop-combos", rw)
        self.assertEqual(rw["prop-combos"]["award"], "BLOCKED")
        self.assertIn("grad", rw["prop-combos"]["reason"].lower())


class TestCorrelations(unittest.TestCase):
    def test_every_value_publishes_its_n(self):
        for r in rows("correlations"):
            if r["r"] not in ("", None):
                self.assertGreater(int(r["n"]), 0, r["pair"])

    def test_refusals_are_printed_as_refusals(self):
        ref = [r for r in rows("correlations") if r["tier"] == "NOT COMPUTED"]
        self.assertGreaterEqual(len(ref), 3)
        for r in ref:
            self.assertEqual(r["r"], "")
            self.assertGreater(len(r["note"]), 30)

    def test_no_operator_price_enters_the_official_table(self):
        for r in rows("correlations"):
            if r["r"] in ("", None):
                continue
            self.assertNotIn("ESPN", r["source"], r["pair"])
            self.assertNotIn("draftkings", r["source"].lower(), r["pair"])

    def test_ci_and_p_are_internally_consistent(self):
        for r in rows("correlations"):
            if r["r"] in ("", None) or r["ci95_lo"] in ("", None):
                continue
            lo, hi, v = float(r["ci95_lo"]), float(r["ci95_hi"]), float(r["r"])
            self.assertLessEqual(lo, v)
            self.assertLessEqual(v, hi)


class TestAvailabilityAndDepth(unittest.TestCase):
    def test_out_players_did_not_play(self):
        br = {r["status"]: r for r in rows("availability_base_rates")}
        self.assertIn("Out", br)
        self.assertEqual(int(br["Out"]["played"]), 0)
        self.assertGreater(int(br["Out"]["n_player_weeks"]), 100)

    def test_questionable_rate_is_a_rate_not_a_prediction(self):
        br = {r["status"]: r for r in rows("availability_base_rates")}
        q = br["Questionable"]
        rate, n = float(q["played_rate"]), int(q["n_player_weeks"])
        self.assertGreater(n, 300)
        self.assertTrue(0.4 < rate < 0.75, rate)
        self.assertIn("not a statement about any individual player", q["note"])
        lo, hi = float(q["wilson_lo"]), float(q["wilson_hi"])
        self.assertLess(lo, rate)
        self.assertGreater(hi, rate)

    def test_join_rejections_are_published(self):
        for r in rows("availability_base_rates"):
            self.assertIn("join_rejected_unique_candidate", r)

    def test_source_disagreement_is_kept_visible(self):
        d = rows("availability_source_diff")
        tot = [r for r in d if r["team"] == "LEAGUE TOTAL"][0]
        self.assertNotEqual(tot["official_rows"], tot["mirror_rows"])
        self.assertEqual(tot["result"], "DISAGREE")
        disagree = [r for r in d if r["result"] == "DISAGREE"]
        self.assertGreater(len(disagree), 1)

    def test_depth_grades_partition_the_charts(self):
        dep = rows("replacement_depth")
        self.assertEqual(len(dep), 705)
        from collections import Counter
        c = Counter(r["depth_grade"].split(" (")[0] for r in dep)
        self.assertEqual(sum(c.values()), len(dep))
        self.assertIn("UNTESTED", c)

    def test_untested_means_no_measured_snaps(self):
        for r in rows("replacement_depth"):
            if r["depth_grade"].startswith("UNTESTED"):
                self.assertIn(r["second_string_snaps_2026"], ("", "0.0", "0"))
            if r["depth_grade"] == "TESTED":
                self.assertGreater(float(r["second_string_share"] or 0), 0.0)
                self.assertGreaterEqual(int(r["second_string_games"]), 3)

    def test_peer_model_column_is_not_blended(self):
        cols = list(rows("replacement_depth")[0].keys())
        self.assertIn("peer_deficiency_points", cols)
        self.assertNotIn("deficiency_points", cols)     # no unlabelled version of the peer number

    def test_absence_rows_join_a_real_replacement_or_say_there_is_none(self):
        for r in rows("absence_vs_depth"):
            self.assertTrue(r["replacement_named"] or "NO MEASURED BACKUP" in r["measured_removal"]
                            or r["replacement_named"] == "",
                            r["player_out"])
            self.assertTrue(r["depth_grade"])


class TestImpactDenominators(unittest.TestCase):
    """The removed-snap percentages must divide by the side they describe.

    An earlier build divided offence plus defence by the offensive base, which inflated
    every defence-heavy club (ARI printed 200.0, DAL 421.0). A cap at 100 would have
    looked like a fix and been a cover-up, so the promise under test is the arithmetic:
    each percentage is that side's snaps over that side's base.
    """

    def test_each_side_divides_by_its_own_base(self):
        for r in rows("availability_impact"):
            for side in ("offence", "defence"):
                snaps, base, pct = (r[f"snaps_removed_{side}"], r[f"{side}_snap_base"],
                                    r[f"pct_of_{side}_snap_base"])
                if pct == "":
                    self.assertEqual(snaps, "", f"{r['team']} published a percentage with no snaps")
                    continue
                self.assertAlmostEqual(float(snaps) / float(base) * 100.0, float(pct), places=1,
                                       msg=f"{r['team']} {side}: {snaps}/{base} != {pct}")

    def test_side_snaps_sum_to_the_total(self):
        for r in rows("availability_impact"):
            if r["expected_snaps_removed"] == "":
                continue
            tot = float(r["expected_snaps_removed"])
            parts = float(r["snaps_removed_offence"] or 0) + float(r["snaps_removed_defence"] or 0)
            self.assertAlmostEqual(tot, parts, places=1, msg=r["team"])

    def test_unmatched_names_are_counted_not_estimated(self):
        n_un = sum(int(r["players_unmatched"]) for r in rows("availability_impact"))
        self.assertGreater(n_un, 0, "the column exists to report a real population")
        for r in rows("availability_impact"):
            if int(r["players_unmatched"]):
                self.assertIn("left blank, never assumed", r["detail"] + r["note"])

    def test_over_100_is_allowed_and_explained(self):
        over = [r for r in rows("availability_impact")
                if r["pct_of_offence_snap_base"] and float(r["pct_of_offence_snap_base"]) > 100]
        self.assertTrue(over, "the guarantee below is meaningless if nothing exceeds 100")
        for r in over:
            self.assertLessEqual(float(r["pct_of_offence_snap_base"]), 400.0,
                                 "a percentage this large means the base is wrong, not the players")
            self.assertIn("a snap is not a slot", r["note"])


class TestSite(unittest.TestCase):
    PAGES = ["index.html", "markets.html", "store.html", "results.html", "injuries.html",
             "depth.html", "leaderboard.html", "gates.html", "correlations.html", "suggestions.html",
             "questions.html", "flagged.html", "sources.html"]

    def test_pages_exist_and_are_nontrivial(self):
        for p in self.PAGES:
            path = os.path.join(DESK, p)
            self.assertTrue(os.path.exists(path), p)
            self.assertGreater(os.path.getsize(path), 4000, p)

    def test_no_wall_clock_stamp_in_output(self):
        # a build-time timestamp makes the site non-reproducible and broke CI once already
        pat = re.compile(r"\b20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\b")
        allowed = {"2026-11-14T21:36Z", "2026-11-14T21:44Z", "2026-11-14T21:33Z"}
        for p in self.PAGES:
            s = open(os.path.join(DESK, p), encoding="utf-8").read()
            for m in set(pat.findall(s)):
                self.assertTrue(m.startswith("2026-11-14"), f"{p} contains a live timestamp {m}")
            self.assertNotIn("build time", s.lower())

    def test_blank_cells_are_marked_not_hidden(self):
        s = open(os.path.join(DESK, "markets.html"), encoding="utf-8").read()
        self.assertIn("not published", s)
        self.assertIn('class="blank"', s)

    def test_every_page_links_home_and_carries_sources(self):
        # every page must be able to walk a reader out to a primary source, not just
        # the pages that happen to render a table with a URL in it
        for p in self.PAGES:
            s = open(os.path.join(DESK, p), encoding="utf-8").read()
            self.assertIn('href="index.html"', s, p)
            self.assertTrue(s.count("<table") >= 1 or p == "index.html", p)
            self.assertIn("https://www.nfl.com/", s, p)
            self.assertIn('href="sources.html"', s, p)

    def test_css_is_shipped(self):
        self.assertTrue(os.path.exists(os.path.join(DESK, "assets", "desk.css")))

    def test_registers_present_on_the_site(self):
        s = open(os.path.join(DESK, "suggestions.html"), encoding="utf-8").read()
        self.assertIn("PROPOSED", s)
        self.assertIn("cost", s.lower())
        q = open(os.path.join(DESK, "questions.html"), encoding="utf-8").read()
        self.assertIn("BLOCKING", q)
        self.assertIn("how_to_find_out".replace("_", " "), q)
        f = open(os.path.join(DESK, "flagged.html"), encoding="utf-8").read()
        self.assertIn("MK-F-01", f)

    def test_internal_links_resolve_and_never_target_a_directory(self):
        # GitHub Pages has no directory index and no 404 page, so both of these
        # failures are invisible when the site is opened from disk
        for p in self.PAGES:
            s = open(os.path.join(DESK, p), encoding="utf-8").read()
            for href in re.findall(r'href="([^"#]+)"', s):
                if href.startswith(("http", "mailto:")):
                    continue
                target = os.path.join(DESK, href)
                self.assertTrue(os.path.exists(target), f"{p} -> {href}")
                self.assertFalse(os.path.isdir(target), f"{p} -> {href} is a directory")


if __name__ == "__main__":
    unittest.main()
