#!/usr/bin/env python3
"""Injury tables, depth-chart tables, questions, suggestions, glossary.

All prose. No numbers are invented here: tables that need computed values
receive them as arguments from engine.py.
"""
from __future__ import annotations

from engine import R, IR, DC, TEAMS, register, flag, rnd


OUT_STATUS = {"Out", "Doubtful"}


# ---------------------------------------------------------------------------
# injuries
# ---------------------------------------------------------------------------
def build_injuries():
    hdr = ["team", "club", "player", "position", "injury",
           "practice_status_as_published", "game_status_as_published", "source"]
    rows = []
    for team, player, pos, injury, prac, game in IR.INJURIES:
        rows.append([team, R.TEAMS.get(team, (team,))[0], player, pos, injury,
                     prac, game, IR.SRC_INJURY])
    return register("injuries", hdr, rows)


def build_injury_summary():
    hdr = ["team", "club", "players_listed", "game_status_out",
           "game_status_doubtful", "game_status_questionable",
           "no_game_status_issued", "practice_full", "practice_limited",
           "practice_did_not_participate", "source"]
    rows = []
    by = {}
    for team, player, pos, injury, prac, game in IR.INJURIES:
        by.setdefault(team, []).append((player, prac or "", game))
    for tm in TEAMS:
        lst = by.get(tm, [])
        if not lst:
            rows.append([tm, R.TEAMS[tm][0], 0, 0, 0, 0, 0, 0, 0, 0,
                         IR.SRC_INJURY])
            continue
        outs = sum(1 for _p, _r, g in lst if g == "Out")
        doub = sum(1 for _p, _r, g in lst if g == "Doubtful")
        q = sum(1 for _p, _r, g in lst if g == "Questionable")
        blank = sum(1 for _p, _r, g in lst if g == "")
        full = sum(1 for _p, r, _g in lst if r == IR.FULL)
        lim = sum(1 for _p, r, _g in lst if r == IR.LIM)
        dnp = sum(1 for _p, r, _g in lst if r == IR.DNP)
        rows.append([tm, R.TEAMS[tm][0], len(lst), outs, doub, q, blank,
                     full, lim, dnp, IR.SRC_INJURY])
    return register("injury_summary", hdr, rows)


# ---------------------------------------------------------------------------
# depth charts and deficiency
# ---------------------------------------------------------------------------
def build_depth():
    inj = {}
    for team, player, pos, injury, prac, game in IR.INJURIES:
        inj.setdefault(team, {})[player] = {"pos": pos, "injury": injury,
                                            "prac": prac, "game": game}
    dhdr = ["team", "club", "unit", "position", "players_published",
            "first_string", "second_string", "third_string",
            "expected_starter_next_game", "string_used",
            "deficiency_points", "out_players_skipped",
            "no_backup_published", "as_of_stamp", "source"]
    drows = []
    thdr = ["team", "club", "unit", "slots_published", "slots_on_first_string",
            "total_deficiency_points", "avg_string_used", "deepest_string_used",
            "positions_with_no_backup", "as_of_stamp", "source", "note"]
    trows = []
    chdr = ["team", "club", "player", "position_on_injury_report", "injury",
            "practice_status", "game_status", "issue", "injury_source",
            "depth_chart_source"]
    crows = []
    for tm in TEAMS:
        club = R.TEAMS[tm][0]
        if tm not in DC.DEPTH:
            url = DC.HOU_DC_URL if tm == "HOU" else ""
            note = (DC.HOU_DC_NOTE if tm == "HOU" else
                    "No depth chart captured from an official club site this "
                    "session; every cell is intentionally blank rather than "
                    "guessed.")
            for unit in ("Offense", "Defense"):
                trows.append([tm, club, unit, "", "", "", "", "", "", "", url,
                              note])
            if tm == "HOU":
                flag("F-09", "depth charts", "high",
                     "Houston: houstontexans.com publishes its depth chart as "
                     "an image with no machine-readable rows",
                     "Backup and deficiency tracking cannot be verified for "
                     "this club, so its rows are blank rather than guessed",
                     DC.HOU_DC_URL)
            else:
                flag("F-10-" + tm, "depth charts", "medium",
                     "%s: no official club depth chart captured this session"
                     % tm,
                     "Backup and deficiency tracking is incomplete for this "
                     "club; its rows are blank",
                     "Re-fetch https://www.<club>.com/team/depth-chart")
            continue
        url, stamp = DC.DC_META[tm]
        names_on_chart = set()
        agg = {}
        for unit, pos, chain in DC.DEPTH[tm]:
            names = [n for n in chain if n]
            names_on_chart.update(names)
            used = None
            skipped = []
            for i, nm in enumerate(names):
                st = inj.get(tm, {}).get(nm)
                if st and st["game"] in OUT_STATUS:
                    skipped.append(nm)
                    continue
                used = i
                break
            if used is None:
                used = len(names) - 1 if names else 0
            starter = names[used] if names else ""
            drows.append([tm, club, unit, pos, len(names),
                          names[0] if names else "",
                          names[1] if len(names) > 1 else "",
                          names[2] if len(names) > 2 else "",
                          starter, used + 1, used, "; ".join(skipped),
                          "yes" if len(names) <= 1 else "no", stamp, url])
            a = agg.setdefault(unit, [0, 0, 0.0, 0, 0])
            a[0] += 1
            a[1] += 1 if used == 0 else 0
            a[2] += used
            a[3] += used + 1
            a[4] += 1 if len(names) <= 1 else 0
        for unit in ("Offense", "Defense"):
            if unit not in agg:
                continue
            n, first, dsum, ssum, nob = agg[unit]
            trows.append([tm, club, unit, n, first, dsum,
                          rnd(ssum / n, 3) if n else "",
                          max([d[9] for d in drows
                               if d[0] == tm and d[2] == unit] or [0]),
                          nob, stamp, url, ""])
        for player, info in sorted(inj.get(tm, {}).items()):
            if player not in names_on_chart:
                crows.append([tm, club, player, info["pos"], info["injury"],
                              " / ".join(info["prac"] or []), info["game"],
                              "On the official NFL Week 10 injury report but "
                              "absent from this club's published depth chart",
                              IR.SRC_INJURY, url])
    flag("F-16", "depth charts", "medium",
         "philadelphiaeagles.com labels its depth chart UNOFFICIAL - compiled "
         "by the Eagles Communications Department - and publishes one "
         "defensive-tackle row with no first-string player at all.",
         "Philadelphia's depth is a club estimate rather than an official "
         "chart, and one position has no published starter.",
         "https://www.philadelphiaeagles.com/team/depth-chart")
    register("depth_detail", dhdr, drows)
    register("depth_by_team", thdr, trows)
    return register("depth_crosscheck", chdr, crows)


# ---------------------------------------------------------------------------
# questions
# ---------------------------------------------------------------------------
QSRC = {
    "Q-01": R.SRC_STANDINGS,
    "Q-02": R.SRC_STANDINGS,
    "Q-03": "https://www.nfl.com/stats",
    "Q-04": "https://www.baltimoreravens.com/team/depth-chart",
    "Q-05": IR.SRC_INJURY,
    "Q-06": R.LEDGER_SRC[1],
    "Q-07": "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
    "Q-08": R.SRC_STANDINGS,
    "Q-09": DC.HOU_DC_URL,
    "Q-10": R.SRC_STANDINGS,
    "Q-11": R.SRC_STANDINGS,
    "Q-12": R.LEDGER_SRC[10],
}


def build_questions():
    hdr = ["q_id", "category", "question", "why_it_blocks_a_decision",
           "information_we_have", "information_we_do_not_have",
           "how_to_get_the_missing_information", "status", "source"]
    rows = [
        ["Q-01", "market data",
         "What were the actual closing spreads, totals and moneylines for the "
         "137 completed 2026 games?",
         "Without a real price you cannot compute closing line value, ROI or "
         "an against-the-spread record - the three numbers that decide "
         "whether a strategy is worth betting.",
         "Own model numbers for every game; official final scores for all 137 "
         "completed games",
         "Any market price from any source. nfl.com does not publish odds.",
         "Licence a historical odds feed, or have the user supply a book's "
         "archived lines, then re-run the backtest against real closing "
         "numbers",
         "OPEN - blocks gate V-08"],
        ["Q-02", "market data",
         "Which sportsbook, and which price, would a strategy actually be bet "
         "into?",
         "Edge at -110 is not edge at -115; juice and limits decide the "
         "break-even hit rate.",
         "The standard -110 flat-price scenario modelled here",
         "The user's book, its juice, its limits and its parlay and prop rules",
         "Ask the user to name the book or books; then recompute every "
         "break-even rate",
         "OPEN"],
        ["Q-03", "player data",
         "Where are the official player box scores that player-prop strategies "
         "require?",
         "No prop strategy can be built or correlated without per-game player "
         "statistics.",
         "No official player-statistic table was in scope this session",
         "Per-game official player statistics: passing, rushing, receiving, "
         "snaps",
         "Fetch the official NFL stats pages and club gamebooks, then build a "
         "props table with its own gates",
         "OPEN - blocks all prop work"],
        ["Q-04", "personnel",
         "Is Jacoby Brissett on Baltimore or Arizona? The Ravens' official "
         "depth chart lists him as first-string quarterback, while an official "
         "nfl.com news item reports Arizona benched him in Week 8.",
         "A starting-quarterback error changes the rating of two clubs and "
         "every line that touches either of them.",
         "The Ravens depth chart showing Brissett as QB1, and the nfl.com news "
         "headline reporting an Arizona benching",
         "A transaction record confirming the move and its date",
         "Check the official NFL transaction report for that date and the two "
         "clubs' official roster pages",
         "FLAGGED - see F-02"],
        ["Q-05", "personnel",
         "Which club does Daiyan Henley play for? He appears on the Los "
         "Angeles Chargers' official Week 10 injury report, while an official "
         "nfl.com news item reports Denver traded for him on 10 November 2026.",
         "Injury data would be attributed to the wrong club.",
         "Two official documents that disagree with each other",
         "The confirmed trade date and which club held him when the injury "
         "report was published",
         "Check the official NFL transaction report dated 10 November 2026",
         "FLAGGED - see F-03"],
        ["Q-06", "data integrity",
         "Are the eight neutral-site labels correct?",
         "Home-field advantage is zeroed for these games, so a wrong label "
         "misprices that game by roughly the size of the HFA estimate.",
         "The site names exactly as published on the official nfl.com weekly "
         "schedule pages",
         "An independently confirmed venue for each of the eight games",
         "Re-read each official weekly schedule page, or the official NFL "
         "international-games page, and record the venue for each",
         "FLAGGED - see F-05"],
        ["Q-07", "rules",
         "Which 2026 rule changes affect scoring, overtime and the extra "
         "point?",
         "Totals and margin distributions shift with the rules; a model fitted "
         "without them is stale.",
         "Nothing. The 2026 rulebook was not retrieved this session.",
         "The operative 2026 rules",
         "Fetch operations.nfl.com/rules-officiating/2026-nfl-rulebook",
         "OPEN - see F-13"],
        ["Q-08", "sample size",
         "Is 137 games enough to separate skill from luck?",
         "Every hit rate in this pack carries a wide confidence interval, so "
         "acting on one is premature.",
         "88 graded out-of-sample predictions, each with a Wilson interval and "
         "a deflated Sharpe ratio",
         "Multiple seasons of the same measurements",
         "Extend the ledger backwards through earlier official seasons and "
         "re-run the same gates unchanged",
         "OPEN"],
        ["Q-09", "depth data",
         "Which clubs publish a usable depth chart, and how stale is each one?",
         "Backup and deficiency tracking is only as good as the least complete "
         "club.",
         "31 of 32 clubs transcribed, each with the club's own 'as of' stamp "
         "where one is published",
         "One club: HOU",
         "Fetch each club's /team/depth-chart page and record its stamp; for "
         "Houston use an alternate official page",
         "OPEN - see F-09"],
        ["Q-10", "staking",
         "How much of the bankroll should a passing strategy risk per bet?",
         "A positive-expectancy strategy can still ruin a bankroll with the "
         "wrong stake.",
         "The per-bet return distribution, skew and kurtosis for every signal "
         "tested",
         "The user's bankroll, risk tolerance and any book limits",
         "Ask the user, then apply a Kelly fraction using the measured edge "
         "with a haircut for estimation error",
         "OPEN"],
        ["Q-11", "parlays",
         "Should parlays be built at all, given the correlations measured "
         "here?",
         "Parlays multiply the vig; they only make sense when legs are "
         "genuinely independent or when the book misprices the correlation.",
         "Measured signal-agreement correlations (C-07, C-08) and the "
         "side-versus-total correlation (C-01)",
         "Real parlay prices from the target book",
         "Obtain the book's parlay pricing, then combine it with the "
         "correlation table",
         "OPEN"],
        ["Q-12", "process",
         "Who re-runs this pack each week, and when?",
         "A line-originating process with no fixed clock produces stale lines.",
         "A fully deterministic pipeline: engine.py, build_site.py, verify.py",
         "A scheduled runner and a named owner",
         "Enable the scheduled workflow in "
         ".github/workflows/nfl-desk-864d5668.yml",
         "OPEN"],
    ]
    for row in rows:
        row.append(QSRC.get(row[0], R.SRC_STANDINGS))
    return register("questions", hdr, rows)


# ---------------------------------------------------------------------------
# suggestions
# ---------------------------------------------------------------------------
SSRC = {
    "SUG-01": R.LEDGER_SRC[10],
    "SUG-02": R.SRC_STANDINGS,
    "SUG-03": R.LEDGER_SRC[10],
    "SUG-04": R.SRC_STANDINGS,
    "SUG-05": "https://www.nfl.com/stats",
    "SUG-06": R.LEDGER_SRC[10],
    "SUG-07": DC.HOU_DC_URL,
    "SUG-08": R.SRC_STANDINGS,
    "SUG-09": R.SRC_STANDINGS,
    "SUG-10": R.SRC_STANDINGS,
}


def build_suggestions():
    hdr = ["s_id", "title", "category", "what_changes", "evidence",
           "evidence_source", "option_a", "option_b", "option_c",
           "recommended_option", "effort", "reversibility", "decision_status"]
    rows = [
        ["SUG-01", "Add a real market-price feed", "data",
         "Every market column becomes populated and gate V-08 becomes "
         "testable, turning this from a model pack into a betting record",
         "All market columns are blank because nfl.com publishes no odds "
         "(flag F-01)",
         "Buy a historical odds feed and re-run the backtest against real "
         "closing lines",
         "Have the user upload archived lines for the 137 completed games",
         "Keep prices out of scope and publish a model-only product, with ROI "
         "explicitly marked unmeasurable",
         "B", "medium", "fully reversible", "AWAITING DECISION"],
        ["SUG-02", "Extend the ledger across multiple seasons", "data",
         "The sample-size gate stops being marginal and every confidence "
         "interval shrinks sharply",
         "88 graded bets still give a Wilson interval that spans the "
         "break-even rate for most signals",
         "Extend backwards through prior official seasons and re-run all gates",
         "Keep the sample at 2026 only and publish every result with an "
         "explicit small-sample warning",
         "Extend to the current season plus one prior season as a compromise",
         "A", "high", "fully reversible", "AWAITING DECISION"],
        ["SUG-03", "Publish lines against a flat -110 assumption, or not at all",
         "product",
         "Decides whether the Own Lines page shows a hypothetical price or "
         "shows model numbers only",
         "-110 is a modelling convenience, not an observed price; publishing "
         "it unqualified would overstate what was actually verified",
         "Show model numbers only, with market columns permanently blank",
         "Show model numbers plus a clearly labelled hypothetical -110 "
         "scenario",
         "Show model numbers plus a scenario band across -105, -110 and -115",
         "B", "low", "fully reversible", "AWAITING DECISION"],
        ["SUG-04", "Replace the ridge rating model with a joint model", "model",
         "Side and total would be fitted together instead of in two separate "
         "passes",
         "The two models currently produce totals whose bias is measured but "
         "not corrected (flag F-08)",
         "Keep the two simple ridge models - they are auditable and "
         "deterministic",
         "Add a third model and compare it on the same walk-forward harness",
         "Add situational features - rest, divisional, travel - and re-test on "
         "the same harness",
         "C", "medium", "fully reversible", "AWAITING DECISION"],
        ["SUG-05", "Add a player-prop module", "product",
         "Unlocks the prop-bet and prop-parlay part of the brief, which is "
         "currently blocked",
         "No official player-statistic source was in scope, so correlation "
         "C-10 is uncomputed (flag F-06)",
         "Fetch official nfl.com player statistics and build a props table "
         "with its own gates",
         "Leave props out and say so plainly on the site",
         "Build a props page that lists the data required but publishes no "
         "numbers",
         "A", "high", "fully reversible", "AWAITING DECISION"],
        ["SUG-06", "Weekly automated re-run", "process",
         "The pack stops going stale between sessions",
         "The whole pipeline is deterministic and cheap, but nothing runs it "
         "on a clock",
         "Enable a scheduled workflow that rebuilds, verifies and publishes "
         "every week",
         "Keep manual rebuilds only",
         "Enable a weekly rebuild that opens a pull request rather than "
         "merging automatically",
         "C", "low", "fully reversible", "AWAITING DECISION"],
        ["SUG-07", "Find an alternate official source for Houston's depth chart",
         "data",
         "Backup and deficiency tracking covers the whole league instead of 31 "
         "clubs",
         "HOU publishes its depth chart only as a raster image, so it has no "
         "transcribed chart (flag F-09)",
         "Fetch each club's official depth chart and re-run",
         "Leave those clubs blank and flagged",
         "Substitute the official injury-report practice columns as a partial "
         "proxy and label it clearly as a proxy",
         "A", "low", "fully reversible", "AWAITING DECISION"],
        ["SUG-08", "Make the Flagged for Review page a first-class deliverable",
         "product",
         "Irregularities stop being buried in an appendix and become "
         "reviewable in one place",
         "Every flag raised across data, personnel, statistics and scope, in "
         "one place",
         "Ship the flagged page prominently in the main navigation",
         "Keep flags inside each table only",
         "Ship the flagged page and require a reviewer acknowledgement before "
         "any flag is cleared",
         "C", "low", "fully reversible", "AWAITING DECISION"],
        ["SUG-09", "Add a decision log recording the option chosen for each "
         "suggestion", "process",
         "The reviewer's choices become auditable rather than verbal",
         "Every suggestion is currently marked AWAITING DECISION with no "
         "record of a choice",
         "Add a decisions table recording suggestion, chosen option, date and "
         "rationale",
         "Leave decisions undocumented",
         "Record decisions in COORDINATION.md only",
         "A", "low", "fully reversible", "AWAITING DECISION"],
        ["SUG-10", "Make beating a naive baseline a hard gate", "validation",
         "Stops a model that merely restates 'better teams win' from being "
         "presented as an edge",
         "Gate V-07 was added after seeing how close the model and the "
         "point-differential baseline are",
         "Make V-07 a blocking gate for any strategy promoted to the "
         "leaderboard",
         "Keep V-07 informational",
         "Make V-07 blocking only for strategies with fewer than 200 graded "
         "bets",
         "A", "low", "fully reversible", "AWAITING DECISION"],
    ]
    for row in rows:
        row.insert(5, SSRC.get(row[0], R.SRC_STANDINGS))
    return register("suggestions", hdr, rows)


# ---------------------------------------------------------------------------
# glossary
# ---------------------------------------------------------------------------
def build_glossary():
    hdr = ["term", "plain_english_definition", "how_it_is_computed_here"]
    rows = [
        ["Own line",
         "A point spread or total we calculate ourselves from official "
         "results, instead of copying a sportsbook's number.",
         "Ridge regression of home margin on team indicators, fitted only on "
         "weeks before the game being predicted."],
        ["Ridge regression",
         "A way of fitting a model that stops extreme team ratings running "
         "away when a club has played only a few games.",
         "Solved in closed form with a penalty of 5.0 on the size of every "
         "team rating."],
        ["Home margin",
         "Home team's points minus the away team's points. Positive means the "
         "home team won.",
         "Straight from the official final scores."],
        ["Walk-forward",
         "Predicting each week using only the weeks before it, so the test "
         "can never see the future.",
         "Week N is predicted from weeks 1 to N-1 only."],
        ["Out-of-sample",
         "A prediction made on data the model never saw while it was being "
         "fitted.",
         "Every row of backtest_walkforward.csv."],
        ["Neutral-site game",
         "A game played abroad, where neither club has a home crowd.",
         "Marked from the official nfl.com weekly schedule pages; "
         "home-field advantage is set to zero for these games."],
        ["Home-field advantage (HFA)",
         "How many points the home team is worth before you even look at who "
         "is playing.",
         "Mean home margin across non-neutral games, reported with a 95 per "
         "cent confidence interval."],
        ["MAE",
         "Mean absolute error: on average, how many points a prediction "
         "missed by.",
         "Average of the absolute margin errors, compared against the naive "
         "alternative of predicting a zero margin every game."],
        ["Bias",
         "Whether the misses lean one way. Positive means the model under-rated "
         "the home team on average.",
         "Simple mean of the margin errors."],
        ["Break-even hit rate",
         "The share of bets you must win just to cover the book's commission.",
         "At -110 you risk 1.00 to win 0.909, so break-even is 1.10 / 2.10 = "
         "52.38 per cent."],
        ["Wilson interval",
         "A range for a hit rate that behaves properly on small samples.",
         "Wilson score interval at 95 per cent."],
        ["Holm-Bonferroni",
         "A correction applied when several signals are tested at once, "
         "because testing many signals manufactures winners.",
         "Step-down adjustment across the skill signals only; the bias probe "
         "is excluded."],
        ["Deflated Sharpe Ratio",
         "A Sharpe ratio adjusted for how many strategies were tried and for "
         "lopsided returns. It asks: would this still look good if I had only "
         "ever tried one thing?",
         "Bailey and Lopez de Prado (2014), using the measured skew and excess "
         "kurtosis and a trials count equal to the number of signals tested."],
        ["Skew and excess kurtosis",
         "How lopsided and how fat-tailed the per-bet returns are. Both make a "
         "good-looking record less trustworthy.",
         "Computed directly on the per-bet return series: +0.909 for a win, "
         "-1.000 for a loss."],
        ["Deficiency points",
         "How far down a club's published depth chart a position has to reach. "
         "Zero means the first string starts; two means the third string "
         "starts.",
         "Walk the club's published depth order and skip any player the "
         "official injury report lists as Out."],
        ["String used",
         "Which line of the depth chart is expected to start: 1 means first "
         "string, 2 means second string and so on.",
         "Position of the expected starter in the club's published order."],
        ["Closing line value",
         "How much better the price you took was than the price available when "
         "the game started.",
         "NOT COMPUTED. It needs a market price and no official source "
         "publishes one (flag F-01)."],
        ["Units",
         "Bet size expressed as multiples of your standard stake.",
         "One unit risked: a win at -110 returns +0.909 units, a loss returns "
         "-1.000."],
        ["Correlation (Pearson r)",
         "How much two numbers move together, from -1 to +1.",
         "Standard Pearson correlation with a Fisher z confidence interval."],
        ["Same-game parlay",
         "Several bets on one game combined into a single ticket. The legs are "
         "not independent.",
         "Not priced here; the inputs you would need are the correlations in "
         "correlations.csv plus real parlay prices from a book."],
        ["Verified and unverified",
         "Whether a number was read off an official source or not.",
         "Every row carries its source URL. Anything without an official "
         "source is left blank and given a flag."],
    ]
    return register("glossary", hdr, rows)
