"""The three decision registers: suggestions, questions, flags.

Why they are separate tables and not prose
------------------------------------------
The brief asks for something specific: a reviewer should be able to pick a path
*before* anything is implemented. So a suggestion is not an idea in a paragraph, it
is a row with the options, the cost of each, what changes on the site if it is
chosen, and which rows of which tables move. Nothing in this file has been
implemented from its own contents: every entry whose state is `PROPOSED` is
exactly that, and the build refuses to render a suggestion as a decision.

Questions carry the other half of the discipline: a `BLOCKING` question means a
decision genuinely cannot be made without the answer, and each one ships with a
route to the answer (who publishes it, where, and what it would cost to obtain),
so "we don't know" is a step in a process instead of a dead end.

Flags are the irregularities - things that look wrong, are unverifiable, or were
refused by a rule. A flag is not a failure; a *hidden* flag is.
"""
from __future__ import annotations

import csv
import os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SUGGESTIONS = [
    dict(id="MK-SG-01",
         area="Landing page",
         suggestion="Put the decision on the landing page instead of the summary: today's slate, the "
                    "desk's number, the market's number, the difference, and what the gate says about "
                    "acting on it.",
         options="A: restructure index.html around the line sheet. B: keep the executive summary and add "
                 "a four-number decision strip above it. C: leave as is.",
         cost="A: about an hour, moves one table up. B: fifteen minutes, adds one block. C: nothing.",
         what_changes="The first thing a reviewer reads changes from 'what we did' to 'what the numbers "
                      "say right now'. No table content moves.",
         recommendation="B - the decision strip is the part that gets used; the summary still needs to "
                        "exist for the provenance.",
         state="PROPOSED"),
    dict(id="MK-SG-02",
         area="Line sheet",
         suggestion="Show the model's uncertainty next to every difference (in ticks of the 0.5 point), "
                    "so a 1-tick disagreement and a 6-tick disagreement do not look like the same kind "
                    "of event.",
         options="A: add a ticks column (already computed). B: add a shaded band instead of a number. "
                 "C: add both, number in the table and band in the chart.",
         cost="A: trivial, the column exists in data/line_sheet.csv. B: needs a chart, about an hour. "
              "C: both.",
         what_changes="Readers can dismiss sub-tick disagreement without being told to; currently the "
                      "table invites treating 0.5 and 4.5 the same.",
         recommendation="A now, B only if someone will actually read a chart.",
         state="PROPOSED"),
    dict(id="MK-SG-03",
         area="Leaderboard",
         suggestion="Freeze the strategy list for a fixed period (say six weeks) and publish the freeze "
                    "date, so the board measures strategies rather than measuring how fast we can "
                    "re-tune them.",
         options="A: hard freeze, no new variants for six weeks. B: new variants allowed but they enter "
                 "the competition only at the next freeze. C: status quo.",
         cost="A and B: a policy, not code - plus one column in multiplicity.csv. C: nothing.",
         what_changes="Every p-value on the board becomes interpretable: multiplicity correction over a "
                      "closed set is meaningful, over an open one it is theatre.",
         recommendation="B: it keeps exploration free while making the scoreboard honest.",
         state="PROPOSED"),
    dict(id="MK-SG-04",
         area="Availability",
         suggestion="Publish the injury ladder as a per-position table joined to snap share, and delete "
                    "any presentation that implies a player-level 'will he play' prediction.",
         options="A: replace the status list with the position-level table. B: keep both, clearly split. "
                 "C: status quo.",
         cost="A: small render change. B: no change to data, one more section.",
         what_changes="Removes the most-abused number on any NFL desk page. The base rate (Questionable "
                      "played 58.6% of 590 player-weeks) stays as context and stops being used as a "
                      "player forecast.",
         recommendation="A.",
         state="PROPOSED"),
    dict(id="MK-SG-05",
         area="Depth",
         suggestion="Add a 'price of the absence' column that is explicitly unpriced where the "
                    "replacement is UNTESTED, rather than defaulting to a league-average replacement.",
         options="A: blank cell plus a warning glyph, as now - formalise it. B: show a league-average "
                 "value in a separate, clearly labelled 'what-if' column. C: hide untested rows.",
         cost="A: documentation only. B: one derived column and a rule for it.",
         what_changes="Decides what the desk admits to not knowing. C is the wrong answer: hiding a row "
                      "hides the fact that it was hidden.",
         recommendation="B, with the what-if column never used in any gate or leaderboard number.",
         state="PROPOSED"),
    dict(id="MK-SG-06",
         area="Price store",
         suggestion="Run the capture job twice per game-day (at kickoff and 30 minutes before) so the "
                    "closing stage exists from the next live week onward.",
         options="A: two scheduled runs per slate day. B: hourly on game days. C: one run.",
         cost="A: schedule entries plus a re-run guard. B: more rows, more noise, no new information "
              "beyond A for closing purposes.",
         what_changes="Unblocks gate V-08 (CLV) and rule D3 in the demotion gate - both are currently "
                      "blocked by data, not by method. Roughly 20-30 closing rows per week.",
         recommendation="A.",
         state="PROPOSED"),
    dict(id="MK-SG-07",
         area="Correlations",
         suggestion="Print the refusal table (correlations the desk will not compute) beside the values it "
                    "does print, not in a separate appendix.",
         options="A: one table, refusals as rows with blank r and a reason. B: two tables.",
         cost="Trivial - the rows already exist in data/correlations.csv.",
         what_changes="A reviewer can see what is missing without hunting, which is how a missing "
                      "correlation stops being mistaken for a zero one.",
         recommendation="A, already implemented in the data; the page layout needs the same choice.",
         state="PROPOSED"),
    dict(id="MK-SG-08",
         area="Backtest",
         suggestion="Publish a per-season table (2021-2025) beside the pooled one, since a pooled "
                    "average over five seasons is dominated by whichever year the model happened to "
                    "like.",
         options="A: add season rows to the signal table. B: separate page. C: skip.",
         cost="Small: the rows carry a season column already.",
         what_changes="Stability becomes visible: a signal present in 2 of 5 seasons reads differently "
                      "from one present in 5 of 5, and today the board cannot show that.",
         recommendation="A.",
         state="PROPOSED"),
    dict(id="MK-SG-09",
         area="Governance",
         suggestion="Make 'no source link, no row' a machine-checked rule with a named exception list, "
                    "rather than a convention the builder follows.",
         options="A: verify.py fails the build on any table row lacking a source column value or an "
                 "explicit blank-and-flag marker. B: keep it as a convention.",
         cost="A: one check in verify.py plus an exceptions file.",
         what_changes="A convention breaks the first time someone is in a hurry; a check does not.",
         recommendation="A. The exception list is where an unavoidable gap gets argued about in the open.",
         state="PROPOSED"),
    dict(id="MK-SG-10",
         area="Scope",
         suggestion="Decide whether this desk's product is a decision tool or an evidence archive, and "
                    "drop the half that is not chosen.",
         options="A: decision tool - the archive moves behind a 'how we know' link. B: archive - the "
                 "decision strip loses its prominence. C: both, and accept that it does neither well.",
         cost="A layout and tone decision, no compute.",
         what_changes="Everything: it decides what a reader sees first, what gets refreshed, and what is "
                      "allowed to be stale.",
         recommendation="A. Lines rot in hours; archives do not.",
         state="PROPOSED"),
]

QUESTIONS = [
    dict(id="MK-Q-01", blocking="BLOCKING",
         question="Where does a legitimate *opening* price come from for a market we originate on?",
         why_it_blocks="Requirement 1 asks for opening and closing numbers for every originated market. "
                       "The aggregator page we can read publishes an open spread and open total for some "
                       "games and no open moneyline at all, so 'opening' is currently only half-fillable "
                       "and the store carries the gap as a gap.",
         who_publishes_it="The sportsbook itself, or a licensed odds feed with a timestamped open.",
         how_to_find_out="Ask the data owner whether the site's odds history endpoint exposes a first-post "
                         "timestamp per market; if not, a paid feed is the only honest route. Cost: an "
                         "API plan, or one row per game left permanently blank.",
         fallback_used="Opening rows recorded where the page shows them; the moneyline opening row is "
                       "written with state ABSENT FROM SOURCE rather than inferred from the pre-game price.",
         state="OPEN"),
    dict(id="MK-Q-02", blocking="BLOCKING",
         question="Which timestamp counts as the close for grading: kickoff, or the last pre-game quote?",
         why_it_blocks="CLV, the demotion gate's D3 rule and every 'did we beat the market' claim depend "
                       "on it. A 30-minute-early price and a kickoff price can differ by a tick on half "
                       "the slate, which is larger than most of the edges on the board.",
         who_publishes_it="No official source: this is a house convention, so it must be chosen, not "
                          "discovered.",
         how_to_find_out="Pick one, write it down, and never look back. Industry convention is kickoff; "
                         "the reason to consider 'last quote before kickoff' is that kickoff quotes are "
                         "sometimes pulled early on weather.",
         fallback_used="Store records the capture timestamp per row and treats every current row as "
                       "pre_game, never as closing.",
         state="OPEN - needs a decision, not more data"),
    dict(id="MK-Q-03", blocking="NON-BLOCKING",
         question="Does the aggregator's split 'Open' cell mean the same thing for both team rows?",
         why_it_blocks="It does not block: the number is recorded verbatim and the ambiguity is flagged "
                       "(MK-F-02). It blocks *interpretation*, so no line-move statistic is published.",
         who_publishes_it="Nobody - it is a rendering convention of one page.",
         how_to_find_out="Compare the same game's Open cell across two capture times; if the open never "
                         "moves while the pre-game does, the convention is stable enough to use.",
         fallback_used="Open total stored as displayed with the o/u prefix unexplained and excluded from "
                       "any computed move statistic.",
         state="OPEN"),
    dict(id="MK-Q-04", blocking="BLOCKING",
         question="Which injury-report vintage is authoritative when the league report and the mirror "
                  "disagree on row counts (326 vs 276 for Week 10)?",
         why_it_blocks="Availability base rates change with the denominator, and the base rate is the one "
                       "number the depth and pricing discussion leans on.",
         who_publishes_it="The league office publishes the report; the mirror's row set is a subset by "
                          "design (it drops rows without a status).",
         how_to_find_out="Diff the two lists player by player and check whether the extra 50 official rows "
                         "are all no-status rows. That is a one-hour job, and until it is done the rate "
                         "carries a caveat.",
         fallback_used="Both counts published per club in availability_source_diff.csv; the rate is "
                       "computed on the mirror's join-able subset and labelled as such.",
         state="OPEN"),
    dict(id="MK-Q-05", blocking="BLOCKING",
         question="Can a player-prop bet be graded from any source this project would call official?",
         why_it_blocks="The prop-combos division of the leaderboard, and the correlation between two "
                       "players' outputs, both need graded prop outcomes. Without them the division is "
                       "empty and the correlation is refused.",
         who_publishes_it="The NFL's own play-by-play statistics, which the repository does not currently "
                          "pin.",
         how_to_find_out="Pin a play-by-play asset with a digest, as the games/injuries/snap mirrors "
                         "already are, then re-run. Roughly an hour of setup, no new subscription.",
         fallback_used="Prop markets captured as observations in the store; the division published as "
                       "BLOCKED with this question as its reason.",
         state="OPEN"),
    dict(id="MK-Q-06", blocking="NON-BLOCKING",
         question="How does the operator handle a parlay leg that pushes: void, or reduce?",
         why_it_blocks="It changes parlay EV materially, but only for parlays containing a whole-number "
                       "line. The desk's parlay division excludes pushes as void, and says so.",
         who_publishes_it="The sportsbook's rules page - operator tier, not official NFL data.",
         how_to_find_out="Read the posted rules for the specific bet type before any parlay is graded "
                         "live; house rules differ between spreads and totals.",
         fallback_used="Push leg voids the parlay; stated in grade.py and on the leaderboard page.",
         state="OPEN"),
    dict(id="MK-Q-07", blocking="BLOCKING",
         question="Who is allowed to promote a strategy, and can the answer be the model?",
         why_it_blocks="The gate tables decide *whether* the evidence exists. Who acts on a yes is a "
                       "governance question this build cannot answer for the project.",
         who_publishes_it="Nobody external. This is the project's decision.",
         how_to_find_out="Name a person and a review cadence. If no name exists, the honest setting is "
                         "'no live betting, paper only', which is what the current gates already produce.",
         fallback_used="Promotion writes a recommendation, never a state change. No live staking exists.",
         state="OPEN - needs a name, not data"),
    dict(id="MK-Q-08", blocking="NON-BLOCKING",
         question="Is the 0.47-point measured home advantage (n=130, 95% CI -1.81 to +2.75) usable as a "
                  "model constant, or must the constant stay pre-registered?",
         why_it_blocks="It does not block the build; it blocks *tuning*. A constant estimated from the same "
                       "season being backtested on is a look-ahead in disguise.",
         who_publishes_it="Nobody publishes a true HFA; it is an estimate with an interval that contains "
                          "zero.",
         how_to_find_out="Widen the window: estimate HFA over 2021-2025 from the pinned mirror and compare "
                         "with the 2026 value. If they agree within the interval, a pre-registered constant "
                         "is defensible.",
         fallback_used="Model uses a pre-registered 1.4-point constant and publishes the measured 2026 "
                       "value beside it rather than substituting it.",
         state="OPEN"),
]

FLAGS = [
    dict(id="MK-F-01", severity="HIGH", kind="UPSTREAM DRIFT",
         item="Three pinned nflverse mirrors (games, injuries_2026, snap_counts_2026) now carry a "
              "different asset digest upstream than the copy this desk reads.",
         detail="Local copies match the digest their owning session recorded on 2026-11-12T16:52:39Z, so "
                "the desk's inputs are internally consistent and reproducible. The upstream release has "
                "been republished since. Every number in this build is therefore correct *for the pin*, "
                "and would move if the pin moved.",
         action="Re-pin deliberately or accept the pin. Do not silently refresh.",
         source="https://api.github.com/repos/nflverse/nflverse-data/releases/tags/schedules"),
    dict(id="MK-F-02", severity="MEDIUM", kind="DISPLAY CONVENTION",
         item="The aggregator odds page splits an opening price across two team rows (open spread on the "
              "favourite's row, open total prefixed o/u on the other).",
         detail="Which row a number sits on appears to carry meaning the page never states. The open total "
                "is recorded as displayed with the prefix kept in raw_display and is excluded from every "
                "computed move statistic.",
         action="Two-sample comparison (question MK-Q-03). Until then: no line-move claims.",
         source="https://www.espn.com/nfl/odds/_/date/20261115"),
    dict(id="MK-F-03", severity="MEDIUM", kind="SUSPECT PRICES",
         item="Four games show implausibly large open-to-current moves on a single page: MIA@IND 47.5 to "
              "37.5 total, LAR@ARI 47.5 to 39.5, JAX@TEN -2.5 to -10.5 side, and IND@HOU -5.5 to -10.0 "
              "five days out.",
         detail="Either the market moved on news this desk cannot see, or the page's open column is not an "
                "open. Both readings are recorded, neither is resolved; the numbers are kept verbatim in "
                "the store and excluded from any movement claim.",
         action="Second-source confirmation before any of these four games is used as an example.",
         source="https://www.espn.com/nfl/odds/_/date/20261115"),
    dict(id="MK-F-04", severity="LOW", kind="ABBREVIATION MISMATCH",
         item="The standings page renders the Rams as 'LA' and the Cardinals as 'AZ'; the schedule pages "
              "and this desk's keys use LAR and ARI.",
         detail="Mapped explicitly in pinned/capture.py (STANDINGS_PAGE_ABBREV) so a transcription is not "
                "silently keyed to a different club. The mirror uses LA for the Rams in its own team column.",
         action="None needed - the mapping is the fix. Any new source must be added to the same map.",
         source="https://www.nfl.com/standings/"),
    dict(id="MK-F-05", severity="LOW", kind="INFERRED STRUCTURE",
         item="The prop rows were captured from a page whose tab titles were not in the rendered text; "
              "the tab identity is inferred from render order.",
         detail="Prop rows are therefore labelled as observations and never graded or used in a "
                "correlation - which is also why the prop division is blocked (MK-Q-05).",
         action="Re-capture with the tab label in the transcription, or drop prop rows from the store.",
         source="https://www.espn.com/nfl/odds/_/gameId/401873064"),
    dict(id="MK-F-06", severity="MEDIUM", kind="SOURCE DISAGREEMENT",
         item="The official Week 10 injury report and the mirror's injury feed disagree on row counts for "
              "the same week: 326 vs 276.",
         detail="Official-only names include LAC Daiyan Henley, IND Grover Stewart, BAL Jaylinn Hawkins; "
                "the mirror adds rows the official page does not list on that date. Per-club counts are "
                "published in availability_source_diff.csv rather than reconciled by preference.",
         action="Answer MK-Q-04 before the availability base rate is quoted as a rate.",
         source="https://www.nfl.com/injuries/league/2026/reg10"),
    dict(id="MK-F-07", severity="MEDIUM", kind="VENDORED, NOT RE-FETCHED",
         item="Two inputs were vendored from another session's files rather than fetched from the source "
              "by this session: the Week 10 official injury report and the 31-club depth-chart "
              "transcription.",
         detail="Both are pinned by digest in pinned/vendor_manifest.json, and every row in the derived "
                "tables carries the *original* official URL, so a reviewer can check the upstream page "
                "directly. What this session did not do is re-read those pages itself.",
         action="A reviewer spot-checks three rows against the live official page; the manifest digest "
                 "then becomes a verified pin rather than a transcription claim.",
         source="https://www.nfl.com/injuries/league/2026/reg10"),
    dict(id="MK-F-08", severity="MEDIUM", kind="COVERAGE GAP",
         item="The results feed carries an official URL for every 2026 game in the vendored slate, but "
              "the score field for 137 of them was verified against the pinned mirror rather than against "
              "137 individually fetched official pages.",
         detail="Reading each game's own nfl.com page would be 137 fetches. The reconciliation is still "
                "three-way in effect (transcription vs mirror vs standings totals) and the standings "
                "reconciliation would fail loudly if any score were wrong - RF-02 checks W/L/T/PF/PA for "
                "all 32 clubs, which pins every score in aggregate.",
         action="Per-game official fetches in the CI job, one slate per run, until coverage reaches 100%.",
         source="https://www.nfl.com/schedules/2026/by-week/week-10"),
    dict(id="MK-F-09", severity="LOW", kind="TIER VIOLATION AVOIDED",
         item="The QB-vs-top-WR yards correlation (r=0.76) published by an earlier session is not "
              "reproduced in this desk's correlation table.",
         detail="It is computed from a third-party play-by-play dump, and requirement 7 restricts "
                "correlations to officially sourced numbers. The row is printed as NOT COMPUTED with that "
                "reason, so the absence is visible rather than looking like a zero.",
         action="Pin an official play-by-play asset (MK-Q-05) and the row becomes computable.",
         source="nfl-desk-864d5668/data/"),
    dict(id="MK-F-10", severity="LOW", kind="VENUE CLAIM NOT READ FROM SOURCE",
         item="The Munich neutral-site marker for NE@DET came from the vendored transcription, not from an "
              "official page this session read.",
         detail="Resolved in-build: the pinned mirror marks the game 'Neutral' with stadium 'FC Bayern "
                "Munich Stadium', and check RF-13 now reconciles all nine 2026 international rows against "
                "that column, so no neutral-site claim in this build is unverified.",
         action="None - kept in the register so the origin of the claim stays visible.",
         source="https://github.com/nflverse/nflverse-data/releases/tag/schedules"),
    dict(id="MK-F-11", severity="HIGH", kind="NO PROMOTABLE SIGNAL",
         item="No strategy clears the gates. The walk-forward model forecasts the margin at r=0.29 where "
              "the posted line forecasts it at r=0.45, and its total is worse still (r=0.055).",
         detail="This is not a build failure - it is the honest result of an honest test, and it is the "
                "reason nothing is promoted. The desk publishes a model that loses to the market rather "
                "than a model tuned until it wins.",
         action="Either improve the forecast (see suggestions MK-SG-02, MK-SG-08) or keep the desk "
                "paper-only. Tuning the gates until something passes is not an action.",
         source="nfl-desk-ce1f16ff/data/calibration.csv"),
    dict(id="MK-F-12", severity="MEDIUM", kind="EMPTY BY DESIGN",
         item="data/live_bets.csv ships with a header and no rows.",
         detail="The demotion gate reads it, and the gate is therefore 'armed, not passed'. Populating it "
                "with plausible-looking bets to demonstrate the machinery would have been the one truly "
                "unforgivable fabrication in this build.",
         action="None. If a live strategy ever exists, the ledger fills and the gate evaluates.",
         source="nfl-desk-ce1f16ff/data/live_bets.csv"),
]


def sources_table():
    """One register of everything this desk read, with its tier and its state.

    A source row answers three questions and no others: what was read, where, and
    whether the value taken from it was verified or merely transcribed. Anything
    the desk *did not* read is here too, marked as such, because a register with only
    the successes in it is a marketing document.
    """
    import inputs
    from pinned import capture as cap
    reg = {r["input_key"]: r for r in inputs.register()}
    rows = []
    for entry in cap.SOURCES:
        sid, publisher, what, url, tier, fields, state, stamp = entry
        rows.append(dict(id=sid, publisher=publisher, what_was_read=what, url=url, tier=tier,
                         fields_taken=fields, state=state, captured_utc=stamp,
                         digest="", note="transcription pinned verbatim in pinned/capture.py"))
    nv_tag = {"nflverse_games": "schedules", "injuries": "injuries", "snap": "snap_counts"}
    for key, r in reg.items():
        url = r["upstream_url"]
        if not url and key.startswith("nflverse_"):
            tag = next((v for k, v in nv_tag.items() if k in key), "schedules")
            url = f"https://github.com/nflverse/nflverse-data/releases/tag/{tag}"
        rows.append(dict(id=f"DIGEST:{key}", publisher="pinned input",
                         what_was_read=r["path"], url=url, tier=r["kind"],
                         fields_taken="-", state=r["pin_check"], captured_utc="",
                         digest=r["sha256_local"][:16],
                         note=(r["upstream_drift"] or "no known upstream change since the pin")))
    rows.append(dict(id="MK-SG-99", publisher="this build",
                     what_was_read="nfl-desk-ce1f16ff/data/* (every derived table)",
                     url="https://github.com/sassnarep3-star/Own5/tree/main/nfl-desk-ce1f16ff/data",
                     tier="DERIVED", fields_taken="all",
                     state="reproducible: verify.py rebuilds and compares", captured_utc="", digest="",
                     note="no derived number is a source; every one traces back through a row above"))
    return rows


def strategy_states():
    """Who is live, who is paper, and why - the file the demotion gate acts on.

    Promotion is the only thing that may change a state, and promotion is gated;
    demotion is not gated, it just reads this file and fires. Keeping the state in a
    table rather than in code means a reviewer can see, and disagree with, the
    decision to run something live without touching a line of Python.
    """
    sig_path = os.path.join(DATA, "leaderboard_signal.csv")
    prom_path = os.path.join(DATA, "promotion_status.csv")
    prom = {}
    if os.path.exists(prom_path):
        for r in csv.DictReader(open(prom_path, newline="", encoding="utf-8")):
            prom[r["strategy"]] = r
    rows = []
    if os.path.exists(sig_path):
        for r in csv.DictReader(open(sig_path, newline="", encoding="utf-8")):
            p = prom.get(r["strategy"], {})
            rows.append(dict(strategy=r["strategy"], division=r["division"], state="PAPER",
                             since="2026-11-14",
                             promotion_decision=p.get("promotion_decision", "BLOCKED"),
                             reason=(p.get("reasons", "no promotion record for this strategy")[:400]),
                             live_bets_allowed="no",
                             note="every strategy starts and stays on paper until its gates clear; the "
                                  "demotion gate reads this file, so a state change is an auditable event"))
    return rows


def write():
    os.makedirs(DATA, exist_ok=True)
    src = sources_table()
    st_rows = strategy_states()
    with open(os.path.join(DATA, "strategy_states.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(st_rows[0].keys())) if st_rows else None
        if w:
            w.writeheader()
            w.writerows(st_rows)
    with open(os.path.join(DATA, "sources.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(src[0].keys()))
        w.writeheader()
        w.writerows(src)
    with open(os.path.join(DATA, "suggestions.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(SUGGESTIONS[0].keys()))
        w.writeheader()
        w.writerows(SUGGESTIONS)
    with open(os.path.join(DATA, "questions.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(QUESTIONS[0].keys()))
        w.writeheader()
        w.writerows(QUESTIONS)
    with open(os.path.join(DATA, "flags.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(FLAGS[0].keys()))
        w.writeheader()
        w.writerows(FLAGS)
    return dict(suggestions=len(SUGGESTIONS), questions=len(QUESTIONS), flags=len(FLAGS),
                sources=len(src), strategy_states=len(st_rows))


if __name__ == "__main__":
    print(write())
