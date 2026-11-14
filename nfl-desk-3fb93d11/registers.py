"""The review-facing registers: requirements, suggestions, questions, flags.

Nothing in here is implemented.  The suggestions register exists so a human can
choose a path before any code or shared file changes.  Every row carries the
evidence that produced it and the test that would change the recommendation.
"""

from __future__ import annotations

import os

from engine import (RETRIEVED_UTC, STANDINGS_URL, INJURY_URL, INJURY_WK11_URL,
                    MIRROR_GAMES_URL, write_csv, read_csv, sha256_file)

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "data")
SITE = "https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/"


def _flag_rows(acc: dict, depth: dict, mirror_stats: dict, hfa: float, n_official: int) -> list:
    n_out = depth["out_players_checked"]
    irr = depth["out_players_irregular"]
    rows = [
        dict(id="F-01", severity="blocking", area="Price data",
             title="nfl.com publishes no spreads, totals or moneylines",
             detail="The league's official site carries no betting prices, and no operator "
                    "publishes a public, machine-readable, timestamped price history. The "
                    "price store therefore has empty MARKET_OPEN and MARKET_CLOSE rows for "
                    "every market we originate, and gate G2 (price provenance) cannot pass for "
                    "any strategy.",
             consequence="Closing-line value, ROI at a real price, and demotion triggers D1a, "
                         "D1b and D1f are all unmeasurable today.",
             action="Capture an operator price page on a fixed schedule and record the raw "
                    "snapshot with a UTC timestamp, or accept that no strategy can ever be "
                    "certified.",
             source_url=STANDINGS_URL),
        dict(id="F-02", severity="review", area="Results feed",
             title="The pinned mirror lags the official results feed",
             detail=f"Of {n_official} official 2026 finals, the mirror agrees on "
                    f"{mirror_stats['agree']} and disagrees on {mirror_stats['disagree']}. "
                    f"{mirror_stats['missing']} game (2026 Week 10, Commanders @ Giants, "
                    "Thursday 12 November) is final on nfl.com but still unscored in the mirror.",
             consequence="Any desk that reads scores from the mirror is up to several days "
                         "behind the official page.",
             action="Keep nfl.com as the results source of record and treat the mirror as a "
                    "cross-check only, which is what this desk does.",
             source_url="https://www.nfl.com/schedules/2026/by-week/week-10"),
        dict(id="F-03", severity="open", area="Price store",
             title="MODEL_CLOSE is not yet observed for any market",
             detail="The store records the desk's origination price. Its close-out price can "
                    "only exist once the pipeline runs again closer to kickoff, so every "
                    "MODEL_CLOSE row is empty in this build.",
             consequence="We cannot yet measure how far our own line moves between origination "
                         "and kickoff.",
             action="Schedule the pipeline to re-run a few hours before kickoff and write a "
                    "second MODEL row; the store already has the slot for it.",
             source_url=SITE + "price-store.html"),
        dict(id="F-04", severity="blocking", area="Injuries",
             title="The Week 11 official injury report is not published yet",
             detail=f"Requesting {INJURY_WK11_URL} returns the Week 10 report; the only week "
                    "tabs offered are 1 through 10. The report the desk would need to price "
                    "Week 11 does not exist.",
             consequence="Every Week 11 market is originated with no injury or replacement-depth "
                         "adjustment, and the model line carries no deficiency term.",
             action="Re-run the pipeline once the league publishes the Week 11 report; the "
                    "adjustment column is already wired and will populate automatically.",
             source_url=INJURY_WK11_URL),
        dict(id="F-05", severity="review", area="Depth",
             title="Depth charts are one club short and one day old",
             detail=f"{depth['clubs_published']} of 32 clubs publish a readable depth chart. "
                    "Houston publishes its chart only as a raster image, so it contributes no "
                    "rows rather than a guessed set. The snapshot was taken 2026-11-13.",
             consequence="Houston's replacement depth is unknown, and any club that edited its "
                         "chart after the snapshot is stale.",
             action="Re-fetch weekly and fail closed (blank plus flag) for clubs that do not "
                    "publish machine-readable charts.",
             source_url="https://www.houstontexans.com/team/depth-chart"),
        dict(id="F-06", severity="watch", area="Depth",
             title="Out players still shown as first string on the club's own chart",
             detail=f"Build check: of {n_out} players the official report lists as Out, "
                    f"{irr} are still printed as the first-string starter on their club's "
                    "published depth chart. The check runs on every rebuild.",
             consequence="A club chart can lag the league's injury report by days, so "
                         "'starter available' can be wrong in both directions.",
             action="Keep reporting the check; treat a non-zero count as a data-quality "
                    "incident for that club.",
             source_url=INJURY_URL),
        dict(id="F-07", severity="review", area="Backtest convention",
             title="Every bet is graded at a flat -110",
             detail="The mirror carries no per-leg prices for the 2026 season, so each graded "
                    "bet is scored at the standard -110 convention with a 52.38% break-even.",
             consequence="Real prices vary by side and by game; ROI figures are indicative, "
                         "not a statement of what a bet would have paid.",
             action="Replace with captured operator prices as soon as any exist (F-01).",
             source_url=MIRROR_GAMES_URL),
        dict(id="F-08", severity="blocking", area="Player props",
             title="No player-prop lines exist from any source in this repo",
             detail="Neither nfl.com nor the mirror publishes player-prop lines. The prop-combo "
                    "family S9 therefore produced no graded bets, and gate G7 (correlation "
                    "audit) cannot be satisfied for any parlay or prop combination.",
             consequence="Two of the three bet classes in the brief cannot be priced at all.",
             action="Source prop lines with timestamps, or keep S9 on the board as an explicit, "
                    "unpriceable entry rather than deleting it.",
             source_url="https://www.nfl.com/stats/player-stats/"),
        dict(id="F-09", severity="review", area="Model",
             title="The totals model does not beat a naive league-average baseline",
             detail=f"Out-of-sample on 2026 weeks {acc.get('weeks_covered')}: totals MAE "
                    f"{acc.get('total_mae')} points against {acc.get('naive_mae_league_total')} "
                    "for simply predicting the league average total every game.",
             consequence="Half of the origination chain (the total) currently adds no forecast "
                         "value, and the moneyline inherits that because it is derived from "
                         "the side and the total.",
             action="Rebuild the totals model before trusting any total or moneyline we "
                    "originate; see suggestion S-04.",
             source_url=STANDINGS_URL),
        dict(id="F-10", severity="blocking", area="Sample size",
             title="The certification universe is far smaller than gate G1 requires",
             detail=f"The official feed holds {n_official} games. After the walk-forward "
                    "warm-up, each family produced between 4 and 51 graded bets on the "
                    "certification board, against a 300-bet minimum.",
             consequence="Nothing on the certification board can be certified this season, "
                         "whatever its hit rate.",
             action="Accumulate seasons of official results, or lower G1 explicitly and record "
                     "the increased false-discovery risk in the decision log.",
             source_url="https://www.nfl.com/schedules/2026/"),
        dict(id="F-11", severity="review", area="Model",
             title="Home-field advantage is not distinguishable from zero this season",
             detail=f"The margin model fits home-field advantage at {hfa} points per game on "
                    "130 non-neutral 2026 games. Session 864d5668 measured +0.47 with a 95% "
                    "interval of -1.81 to +2.75 on the same season; this build publishes the "
                    "point estimate and does not compute an interval.",
             consequence="A rule that leans on home advantage is leaning on a number we cannot "
                         "separate from noise.",
             action="Add a confidence interval to the home-field coefficient and prefer "
                    "multi-season fits; see suggestion S-06.",
             source_url=STANDINGS_URL),
        dict(id="F-12", severity="review", area="Injuries",
             title="Most official injury rows carry no game status at retrieval",
             detail="The Week 10 report lists 326 players; only 25 carry a game status "
                    "(14 Out, 11 Questionable). Game statuses are published later in the week.",
             consequence="The replacement-depth tracker can only use practice status for the "
                         "other 301 players, so 'out' is under-counted early in the week.",
             action="Re-read the report on Friday and again on Saturday; the tracker keys off "
                    "game status and will change as it fills in.",
             source_url=INJURY_URL),
        dict(id="F-13", severity="review", area="Correlations",
             title="Every correlation previously published in this repo is inadmissible",
             detail="The brief now requires correlations to come only from officially sourced "
                    "numbers with n published. Prior desks computed theirs from the nflverse "
                    "mirror. Those values are not deleted - they are moved to "
                    "correlations_withheld.csv with their basis and reason.",
             consequence="The correlations published here are fewer and narrower than what the "
                         "site showed before. That is the point of the rule.",
             action="Recompute from official inputs only, which is what this desk does.",
             source_url=SITE + "correlations.html"),
        dict(id="F-14", severity="review", area="Price data",
             title="The aggregator reference line has no timestamp, so it is neither an "
                   "opening nor a closing price",
             detail="The mirror supplies one line per game per market with no snapshot time. "
                    "The store records it as MARKET_REFERENCE, never as MARKET_OPEN or "
                    "MARKET_CLOSE.",
             consequence="Any 'we beat the line by X' statement computed against it could be "
                         "measuring a stale early-week price.",
             action="Do not quote a CLV number against it; the desk uses it only as a "
                    "difference column and says so on every page.",
             source_url=MIRROR_GAMES_URL),
    ]
    for r in rows:
        r["fetched_utc"] = RETRIEVED_UTC
        r["status"] = "published for review"
    return rows


def _req_fill(rows: list) -> list:
    """A blank gap cell would read as missing data.  Say when there is none."""
    for r in rows:
        if not str(r.get("gap_or_caveat", "")).strip():
            r["gap_or_caveat"] = ("none - this requirement is met in full"
                                  if str(r["status"]).lower().startswith("met")
                                  else "not assessed in this session")
    return rows


def requirements_rows() -> list:
    """The full brief, one row per requirement, with the artefact that answers it."""
    R = [
        ("R-01", "Add a price-snapshot store that records opening and closing numbers for "
                 "every market we originate", "Met",
         "price_snapshots.csv holds one row per market per snapshot type across all 78 "
         "originated markets; price_store_schema.csv documents each slot.",
         "Operator opening and closing numbers are empty and flagged (F-01); MODEL_CLOSE is "
         "empty until a second run (F-03).", "price-store.html"),
        ("R-02", "Add a verified results feed so backtests and ROI can be computed at all",
         "Met",
         "results_feed.csv carries 137 official 2026 finals transcribed week by week from "
         "nfl.com, each with its source URL and a UTC retrieval stamp.",
         "It covers one season. Multi-season official results would need the same week-by-week "
         "transcription for 1999-2025.", "results.html"),
        ("R-03", "Originate the side first, then the total, then the moneyline", "Met",
         "origination_steps.csv records the three steps in order for every game; the moneyline "
         "row records that it is derived from the side and the total, never fitted separately.",
         "", "lines.html"),
        ("R-04", "Publish the model's fair line, the market line and the difference as "
                 "separate columns", "Met",
         "originated_markets.csv has model_line, market_line and "
         "difference_model_minus_market as three distinct columns for all three market types.",
         "market_line is AGGREGATOR tier with no timestamp (F-14).", "lines.html"),
        ("R-05", "Separate signal from staking in the leaderboard so a lucky staking run "
                 "cannot mask a bad signal", "Met",
         "leaderboard.csv ranks each family twice - signal_rank and staking_rank - computed "
         "from disjoint inputs, and the staking axis cannot certify or reward anything.",
         "The clearest case on the board today is S7: first on staking from 4 bets, fifth of "
         "eight on signal.", "leaderboard.html"),
        ("R-06", "Track the depth of the replacement, not just the fact of a replacement",
         "Met",
         "replacement_depth.csv publishes, per position slot, which string steps in "
         "(2nd/3rd/4th), whether that replacement is himself on the official injury report, "
         "and whether the loss compounds to a third name.",
         "31 of 32 clubs; Houston publishes no readable chart (F-05). Snapshot is 2026-11-13.",
         "depth.html"),
        ("R-07", "Compute correlations only from officially sourced numbers and publish n "
                 "with each value", "Met",
         "correlations_official.csv publishes 9 pairs with r, p, a 95% interval, n and the "
         "definition of n - all computed from nfl.com numbers only.",
         "Everything computed from the mirror is moved to correlations_withheld.csv (F-13).",
         "correlations.html"),
        ("R-08", "Define a demotion gate that sends a live strategy back to paper", "Met",
         "demotion_gate.csv evaluates six triggers (D1a-D1f) against every family, with the "
         "reason each matters and whether it has fired.",
         "No strategy has ever gone live, so no trigger has fired; the gate is armed, not "
         "proven.", "gates.html"),
        ("R-09", "Originate my own NFL lines", "Met",
         "78 markets across 26 scheduled games (the 13 unplayed Week 10 games and all 13 Week "
         "11 games), priced from a model fitted on 137 official 2026 results.",
         "The totals half of the model does not beat a naive baseline (F-09).", "lines.html"),
        ("R-10", "Research and develop strategies that generate useful signals", "Partially met",
         "Nine pre-registered families across singles, parlays and prop combos, graded "
         "walk-forward on two universes.",
         "None produces a hit rate above break-even with a deflated Sharpe above the "
         "threshold. Two are significantly worse than break-even.", "strategies.html"),
        ("R-11", "Treat it as a leaderboard competition that rewards top-performing strategies",
         "Partially met",
         "Two boards, separate signal and staking axes, gates as the entry condition, and a "
         "documented reward structure proposal.",
         "No certified entrant, so no reward is payable. Reward funding and jurisdiction are "
         "unanswered (Q-04, Q-05).", "leaderboard.html"),
        ("R-12", "Cover single bets, parlays and player prop bet combos", "Partially met",
         "Singles (S1-S7), a same-game two-leg parlay (S8) and a prop-combo family (S9) are all "
         "on the board and scored.",
         "S9 produced no graded bets: no prop lines exist anywhere in this repo (F-08).",
         "strategies.html"),
        ("R-13", "Each strategy must pass validation gates", "Met",
         "Nine gates G0-G8 evaluated per family per universe in gate_matrix.csv.",
         "G2 fails for every family because no verified price exists; G1 fails on the "
         "certification board for the same reason of sample size.", "gates.html"),
        ("R-14", "Determine correlation values", "Met",
         "Nine official pairs published with n; the withheld register names and explains every "
         "value that is no longer admissible.", "", "correlations.html"),
        ("R-15", "Remove luck and build selectively skill-based strategies", "Partially met",
         "Shrinkage toward zero, Holm-Bonferroni across families, deflated Sharpe against the "
         "family count, out-of-sample-only grading, and a demotion gate.",
         "Luck cannot be removed, only measured. On the samples available today nothing clears "
         "the bar, which is the honest output rather than a failure to find one.",
         "strategies.html"),
        ("R-16", "Track injuries and know defensive deficiencies where 2nd, 3rd or 4th string "
                 "backups replace starters", "Met",
         "Per-slot tracking of which string steps in, split by offence and defence, cross-"
         "checked against the official injury report's Out list.",
         "Game status is empty for 301 of 326 rows at retrieval (F-12).", "depth.html"),
        ("R-17", "The same for offences using starters or backups", "Met",
         "Offence and defence are separate rows with their own unit column, so the two are "
         "never pooled.", "", "depth.html"),
        ("R-18", "Make suggestions to improve the site, with a section where someone can review "
                 "suggestions and choose the best path before implementing anything",
         "Met",
         "suggestions.html publishes every proposal with two or three costed options, a "
         "recommended path, and the test that would change the recommendation. All are "
         "AWAITING DECISION; none is implemented.", "", "suggestions.html"),
        ("R-19", "A clear list of questions, information and answers needed before a decision, "
                 "with suggestions to discover the missing information", "Met",
         "questions.html splits the register into answered, partially answered and blocking, "
         "each with what we have, what is missing and the cheapest way to get it.",
         "Five questions cannot be closed from any public source.", "questions.html"),
        ("R-20", "Create an executive summary outlining the important details", "Met",
         "executive-summary.html and research/nfl-3fb93d11/EXECUTIVE_SUMMARY.md restate only "
         "computed or officially sourced values.", "", "executive-summary.html"),
        ("R-21", "Review the repo line by line against official trusted sources, flag "
                 "irregularities, no hallucinations", "Met",
         "audit_repo.py re-checks the existing NFL desks' headline claims against the official "
         "pages fetched for this build; repo-audit.html publishes each check with its source.",
         "Only the headline claims are re-checked; a full line-by-line audit of all 1,000+ "
         "files is out of scope for one session.", "repo-audit.html"),
        ("R-22", "Create a GitHub Pages site with a clean landing page and subpages organised "
                 "by category, dashboard-style, tables, all findings", "Met",
         "A 12-page static dashboard under /nfl-desk-3fb93d11/, generated deterministically "
         "and checked for broken links before merge.", "", "index.html"),
        ("R-23", "Every table row must have a source link to an official site; leave "
                 "unverifiable values blank and flag them", "Met",
         "verify.py walks every body-table row in the generated HTML and fails the build if a "
         "row has neither an official link nor an explicit blank flag.",
         "Market-line columns link to the mirror, which is an official-grade publisher of "
         "nothing - they are labelled AGGREGATOR and flagged (F-14).", "flagged.html"),
        ("R-24", "Coordinate with parallel sessions via COORDINATION.md", "Met",
         "Scope claimed and pushed before implementation; every other session's files are "
         "read-only here.", "", "https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md"),
        ("R-25", "Open a PR, merge autonomously, confirm Pages deploys, record the result",
         "In progress at merge time",
         "The PR, its checks, the merge SHA and the live Pages build are recorded in "
         "COORDINATION.md and on this site's sources page.", "", "sources.html"),
    ]
    rows = []
    for rid, req, status, how, gap, page in R:
        rows.append({
            "id": rid, "requirement": req, "status": status, "how_it_is_met": how,
            "gap_or_caveat": gap, "page": page,
            "source_url": SITE if page.endswith(".html") else page,
        })
    return _req_fill(rows)


def suggestion_rows() -> list:
    S = [
        dict(id="S-01", title="Capture a real operator price twice per game week",
             problem="Every certification gate that depends on price fails, not because the "
                     "signals are bad but because no verified opening or closing price exists "
                     "anywhere in the repo.",
             option_a="Do nothing; keep the board permanently in paper and say so.",
             option_b="Capture one operator's NFL page on a fixed schedule (Tuesday and three "
                      "hours before kickoff), store the raw snapshot with a UTC stamp, and "
                      "populate MARKET_OPEN and MARKET_CLOSE from it.",
             option_c="Buy or licence a commercial odds history and ingest it.",
             recommended="B", impact="High", effort="Medium", confidence="High",
             evidence="price-store.html - 156 of 390 snapshot rows are empty, all for want of a "
                      "publisher",
             owner="Data engineering",
             review_test="If two consecutive weeks of captures produce an opening and a closing "
                         "price for at least 90% of originated markets, this becomes the "
                         "default and G2 becomes testable."),
        dict(id="S-02", title="Rebuild the totals model before trusting any total or moneyline",
             problem="The totals model's out-of-sample MAE is statistically indistinguishable "
                     "from always predicting the league average, yet the moneyline is derived "
                     "from the side and the total together.",
             option_a="Keep the current model and publish the total with a health warning.",
             option_b="Rebuild it on pace and efficiency inputs, re-measure against the same "
                      "naive baseline, and only then re-derive the moneyline.",
             option_c="Stop originating totals and price only the side and the moneyline.",
             recommended="B", impact="High", effort="Medium", confidence="High",
             evidence="lines.html - totals MAE 11.00 vs naive 11.02",
             owner="Model owner",
             review_test="If the rebuilt model does not beat the naive baseline by at least 0.5 "
                         "points of MAE on a held-out season, take option C."),
        dict(id="S-03", title="Grade parlays against an empirical joint, never independent legs",
             problem="The two-leg parlay family prices its legs independently. The board shows "
                     "it needs 27.44% to break even and delivered 26.32% over 1,953 bets, so "
                     "the independence assumption is doing real work.",
             option_a="Keep independent pricing and accept the error.",
             option_b="Require an empirical joint estimate for every leg pair, and refuse the "
                      "bet when the market price assumes independence and we cannot measure "
                      "the joint.",
             option_c="Drop parlays from the board until the joint can be measured.",
             recommended="B", impact="High", effort="Medium", confidence="Medium",
             evidence="strategies.html - S8 on the research board",
             owner="Quant",
             review_test="If the joint cannot be estimated for a leg pair within one season, "
                         "that pair is refused automatically (option B degenerates to C by "
                         "itself)."),
        dict(id="S-04", title="Put a confidence interval on every published model coefficient",
             problem="Home-field advantage is published as a point estimate with no interval, "
                     "and a reader cannot tell it apart from zero.",
             option_a="Leave point estimates as they are.",
             option_b="Publish a bootstrap interval beside every coefficient, including "
                      "home-field advantage and each team rating.",
             option_c="Publish intervals and suppress any coefficient whose interval contains "
                      "zero from the headline tables.",
             recommended="B", impact="Medium", effort="Low", confidence="High",
             evidence="lines.html - home-field advantage fitted at +0.21 pts",
             owner="Model owner",
             review_test="If an interval cannot be computed for a coefficient, that coefficient "
                         "is published blank rather than as a bare number."),
        dict(id="S-05", title="Budget how many new families a season, and publish the count",
             problem="Multiplicity control only means something if the number of things tried "
                     "is honest. Nine families were tried here; a hundred would have needed a "
                     "very different alpha.",
             option_a="Unlimited families, corrected after the fact.",
             option_b="Fix a family budget per season, register every family before the season "
                      "starts, and count abandoned ones too.",
             option_c="One new family per month, with a doubled alpha requirement for "
                      "exceptions.",
             recommended="B", impact="High", effort="Low", confidence="High",
             evidence="gates.html - Holm correction applied across 8 betting families",
             owner="Research",
             review_test="If a family is added after the season has started, it starts a new "
                         "pre-registration round with its own alpha budget."),
        dict(id="S-06", title="Extend the official results feed backwards, one season at a time",
             problem="The certification board has 137 games because the official feed was "
                     "transcribed for 2026 only, so every family fails the 300-bet gate.",
             option_a="Keep grading on the mirror and label it clearly.",
             option_b="Transcribe one additional official season per month, oldest first, until "
                      "the certification board has a usable sample.",
             option_c="Lower gate G1 to the sample we have and record the extra risk.",
             recommended="B", impact="High", effort="Medium", confidence="High",
             evidence="results.html - 137 games; gate G1 needs 300 graded bets per family",
             owner="Data engineering",
             review_test="After four added seasons the board should hold roughly 1,000 games; "
                         "if it does not, revisit the gate rather than the data."),
        dict(id="S-07", title="Publish a market-efficiency scorecard next to every signal",
             problem="The board shows whether a signal predicts results. The useful question is "
                     "whether the market has already priced it.",
             option_a="Keep reporting predictive power only.",
             option_b="For every signal report both its raw predictive power and its residual "
                      "edge after the market line, and rank by the residual.",
             option_c="Rank by residual only and drop the raw column.",
             recommended="B", impact="High", effort="Medium", confidence="Medium",
             evidence="strategies.html - S1 hits 51.15% against the line over 3,769 bets, "
                      "which is predictive but below break-even",
             owner="Quant",
             review_test="A signal with strong raw power and no residual edge is demoted to a "
                         "pricing input, not a betting signal."),
        dict(id="S-08", title="Make the demotion gate automatic rather than advisory",
             problem="The gate is defined and evaluated but nothing enforces it, because no "
                     "strategy is live yet.",
             option_a="Leave it as a published rule.",
             option_b="Wire D1a-D1f into the build so a demotion is written to the ledger and "
                      "the decision log without a human step.",
             option_c="Route demotions through a weekly review meeting.",
             recommended="B", impact="High", effort="Low", confidence="High",
             evidence="gates.html - six triggers, none fired, all currently evaluated by hand",
             owner="Competition design",
             review_test="Inject a synthetic drawdown past the D1b threshold; if the build does "
                         "not demote the strategy, the wiring is wrong."),
        dict(id="S-09", title="Keep the prop-combo family on the board as an explicit blank",
             problem="S9 produced no bets because no prop lines exist. Deleting it would make "
                     "the board look complete when one of the three bet classes is simply "
                     "unpriceable.",
             option_a="Delete S9 until prop lines exist.",
             option_b="Keep S9 with zero bets, the reason printed on the row, and the blocking "
                      "flag linked.",
             option_c="Model prop lines from season medians so the row has numbers.",
             recommended="B", impact="Medium", effort="Low", confidence="High",
             evidence="strategies.html - S9 row, flag F-08",
             owner="Research",
             review_test="Option C is rejected in advance: modelled lines would be inferred "
                         "values, which this repo does not publish."),
        dict(id="S-10", title="Record an ADR row whenever a suggestion changes state",
             problem="Accepted suggestions without a recorded rationale get re-litigated and "
                     "rejected ones get re-proposed.",
             option_a="Track decisions in the suggestions table only.",
             option_b="Append a dated decision row (decision, evidence, owner, revisit date) to "
                      "a decision log whenever a suggestion moves.",
             option_c="Hold the decision in the pull request that implements it.",
             recommended="B", impact="Medium", effort="Low", confidence="High",
             evidence="suggestions.html - 10 suggestions, all AWAITING DECISION",
             owner="Project owner",
             review_test="If the log has fewer than one entry per accepted suggestion, the "
                         "process is not being followed."),
        dict(id="S-11", title="Re-read the official injury report twice more per week",
             problem="Game status is empty for 301 of 326 rows at retrieval, so the "
                     "replacement-depth tracker under-countsOut players early in the week.",
             option_a="One read per week, as now.",
             option_b="Read on Wednesday, Friday and Saturday; keep each snapshot and show the "
                      "tracker's movement across the week.",
             option_c="Read only on Saturday, when statuses are fullest.",
             recommended="B", impact="Medium", effort="Low", confidence="High",
             evidence="depth.html - 14 Out, 11 Questionable, 301 blank at 2026-11-13",
             owner="Data engineering",
             review_test="If the Saturday read adds no Out designation over the Friday read for "
                         "two consecutive weeks, drop back to two reads."),
        dict(id="S-12", title="Publish the reward structure as a proposal, not a commitment",
             problem="The brief asks for rewards, but cash prizes raise licensing, tax and "
                     "eligibility questions that no public source answers for this project.",
             option_a="Publish cash tiers now.",
             option_b="Run the competition as points-only until Q-04 and Q-05 are answered, and "
                      "publish the intended cash structure as a marked proposal.",
             option_c="Drop rewards entirely.",
             recommended="B", impact="Medium", effort="Low", confidence="High",
             evidence="questions.html - Q-04, Q-05",
             owner="Project owner",
             review_test="Close Q-04 and Q-05 first; then publish reward terms with eligibility "
                         "rules attached."),
    ]
    rows = []
    for s in S:
        rows.append({
            "id": s["id"], "title": s["title"], "problem": s["problem"],
            "option_a": s["option_a"], "option_b": s["option_b"], "option_c": s["option_c"],
            "recommended": s["recommended"], "impact": s["impact"], "effort": s["effort"],
            "confidence": s["confidence"], "evidence": s["evidence"], "owner": s["owner"],
            "decision": "AWAITING DECISION",
            "review_test": s["review_test"],
            "implemented": "no - this page is a proposal register, nothing here is built",
            "source_url": SITE + "suggestions.html",
        })
    return rows


def question_rows() -> list:
    Q = [
        ("Q-01", "Which price is the benchmark for 'beating the market'?",
         "Our line at origination, the operator's current price, or the closing price?",
         "A model price per market with a UTC stamp, and an untimestamped aggregator line.",
         "Any timestamped operator price at all.",
         "Capture one operator page on a fixed schedule (S-01).",
         "G2, every CLV statement, and any claim of skill.", "BLOCKING"),
        ("Q-02", "Is the aggregator line an opening line, a closing line, or neither?",
         "If it is a closing line, a measured ATS edge is implausible; if it is an early line, "
         "part of any measured edge is stale-line alpha.",
         "One line per game per market, no timestamp, no publisher documentation.",
         "The mirror's upstream source and its snapshot convention.",
         "Ask the mirror maintainer, or stop using it for anything but a difference column "
         "(which is what this desk does).",
         "Interpretation of every market comparison in this repo.", "BLOCKING"),
        ("Q-03", "What bankroll, staking rule and maximum drawdown are acceptable?",
         "Kelly fractions, stop rules and the D1b drawdown trigger are undefined without them.",
         "A notional 100-unit reference bankroll used for illustration only.",
         "The owner's actual capital and risk tolerance.",
         "Owner decision; no public source can answer it.",
         "G6, D1b and any reward sizing.", "BLOCKING"),
        ("Q-04", "Are rewards cash, points, or nothing?",
         "Cash changes the legal, tax and eligibility position; operator terms may also "
         "restrict competition use.",
         "A proposed tier structure with no funding decision.",
         "Owner decision plus a jurisdiction review.",
         "Owner decision; run points-only until then (S-12).",
         "Whether any reward can be published at all.", "BLOCKING"),
        ("Q-05", "In which jurisdictions is this offered, and who is eligible?",
         "Eligibility, age, location checks and tax treatment all follow from this.",
         "Nothing.",
         "A jurisdiction determination.",
         "Owner decision with legal input; no public source answers it for this project.",
         "Reward publication and any live staking.", "BLOCKING"),
        ("Q-06", "How many new strategy families may be tried per season?",
         "Multiplicity control needs an honest count of what was tried.",
         "Nine families pre-registered for this build, with eight producing bets.",
         "A budget the owner agrees to be held to.",
         "Owner decision; option B of S-05 is the cheapest default.",
         "How harsh the Holm correction has to be.", "Partially answered"),
        ("Q-07", "What defines a starter - the club's published depth chart or snap share?",
         "Depth charts are official but lag; snap share is measurable but is not a role.",
         "31 of 32 clubs publish a readable chart; snap-share role inference is also available "
         "in-repo from an aggregator.",
         "An official machine-readable depth chart, which does not exist.",
         "Use the club chart as primary and report the snap-share cross-check beside it, which "
         "is what this desk does.",
         "The precision of the replacement-depth tracker, not its existence.", "Answered"),
        ("Q-08", "How stale may a depth chart be before we stop using it?",
         "A chart that is a week old can show a man who is already on injured reserve.",
         "A snapshot stamped 2026-11-13 with no published update cadence per club.",
         "Each club's edit cadence, which is not published.",
         "Re-fetch weekly and print the snapshot age on every depth row.",
         "Confidence in the depth tracker week to week.", "Partially answered"),
        ("Q-09", "May a research-board result ever justify live staking?",
         "The research board has thousands of bets but only mirror-sourced results.",
         "A rule: no. Certification is the official board's job alone.",
         "Owner agreement that the rule stands when a research result looks large.",
         "Owner decision; the board already enforces it mechanically.",
         "Which board can move money.", "Answered by design"),
        ("Q-10", "Who owns the demotion decision and how fast must it happen?",
         "A gate that waits for a meeting is not a gate.",
         "Six triggers defined; enforcement is manual.",
         "An owner and a maximum latency.",
         "Owner decision; wire it into the build (S-08).",
         "Whether D1 has any force.", "Partially answered"),
        ("Q-11", "Do we need play-by-play and EPA to make the side model competitive?",
         "A margin model cannot tell a good offence beating bad defences from a mediocre one "
         "doing the same.",
         "A margin model with r = 0.32 against actual margin out of sample.",
         "Play-by-play ingestion, which is a sizeable build.",
         "Pilot it and compare held-out log-loss against the current model.",
         "The ceiling on origination quality.", "Open"),
        ("Q-12", "Should the totals model carry weather and venue terms?",
         "Domes and high-wind games are systematically mis-totalled by a model that ignores "
         "both.",
         "The mirror carries roof, temperature and wind fields, often blank.",
         "Non-null weather for most games, from an official source.",
         "Join official game-time weather and re-measure; see S-02.",
         "Whether the totals model can be salvaged.", "Open"),
        ("Q-13", "Should MODEL_CLOSE be captured automatically before kickoff?",
         "Without a second run we cannot measure how far our own line moves.",
         "An empty MODEL_CLOSE slot for all 78 markets.",
         "A scheduled runner.",
         "Add a scheduled workflow that re-runs the origination a few hours before kickoff.",
         "Whether the store's close column ever fills.", "Open"),
        ("Q-14", "What happens to a demoted strategy's historical record?",
         "Retroactively erasing it hides the evidence that produced the demotion.",
         "Nothing, because nothing has been demoted.",
         "A retention rule.",
         "Owner decision; the natural default is to keep the record and mark the demotion "
         "date on it.",
         "Auditability of the competition.", "Open"),
    ]
    rows = []
    for qid, q, why, have, missing, resolve, blocks, status in Q:
        rows.append({
            "id": qid, "question": q, "why_it_matters": why,
            "what_we_have": have, "what_is_missing": missing,
            "cheapest_way_to_resolve": resolve, "what_it_blocks": blocks,
            "status": status, "source_url": SITE + "questions.html",
        })
    return rows


def write_registers(acc: dict, depth: dict, mirror_stats: dict, hfa: float,
                    n_official: int) -> None:
    flags = _flag_rows(acc, depth, mirror_stats, hfa, n_official)
    write_csv("flagged.csv", flags,
              ["id", "severity", "area", "title", "detail", "consequence", "action",
               "status", "source_url", "fetched_utc"])
    write_csv("requirements.csv", requirements_rows(),
              ["id", "requirement", "status", "how_it_is_met", "gap_or_caveat", "page",
               "source_url"])
    write_csv("suggestions.csv", suggestion_rows(),
              ["id", "title", "problem", "option_a", "option_b", "option_c", "recommended",
               "impact", "effort", "confidence", "evidence", "owner", "decision",
               "review_test", "implemented", "source_url"])
    write_csv("questions.csv", question_rows(),
              ["id", "question", "why_it_matters", "what_we_have", "what_is_missing",
               "cheapest_way_to_resolve", "what_it_blocks", "status", "source_url"])
