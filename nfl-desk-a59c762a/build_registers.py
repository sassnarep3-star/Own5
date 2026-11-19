#!/usr/bin/env python3
"""Authored registers for the NFL Decision Console (session a59c762a).

These registers are written by hand, not computed. Each row states a
requirement taken from the reviewer's brief, the gate that blocks it, the
number that would clear it, what is observed now, and where the evidence
lives. Every factual cell carries a link; every cell that cannot be confirmed
is left blank and carries an explicit flag.

Run:  python3 nfl-desk-a59c762a/build_registers.py
"""
from __future__ import annotations

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BLOB = "https://github.com/sassnarep3-star/Own5/blob/main"
SELF = "nfl-desk-a59c762a"

STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
SCHED11 = "https://www.nfl.com/schedules/2026/by-week/week-11"
SCHED10 = "https://www.nfl.com/schedules/2026/by-week/week-10"
INJ11 = "https://www.nfl.com/injuries/league/2026/reg11"
INJ10 = "https://www.nfl.com/injuries/league/2026/reg10"
GAMECENTER = "https://www.nfl.com/games/colts-at-texans-2026-reg-11"
RELEASE = "https://www.nfl.com/nfl-schedule-release/"
GAMEBOOKS = "https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books"
GAMEBOOK_WASNYG = ("https://static.www.nfl.com/image/upload/v1794570519/gamecenter/"
                   "ab5828d9-4feb-11f1-abca-2c54536568a9.pdf")
NGS = "https://nextgenstats.nfl.com/glossary"
FLEX = "https://www.nfl.com/legal/flexible-scheduling-procedures"
RULEBOOK = "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"

REQUIREMENT_FIELDS = [
    "requirement_id", "category", "requirement", "status", "blocking_gate",
    "number_that_clears_it", "observed_now", "repo_evidence_url",
    "official_source_url", "verification", "flag",
]

# id, category, requirement, status, gate, clears, observed, repo, official, verification, flag
REQUIREMENTS = [
    # ---------------------------------------------------------------- pricing
    ("R-01", "Pricing", "Add a price-snapshot store that records opening and closing numbers for every market we originate",
     "PARTIAL", "Price-data policy P-01 is an open decision and no operator or licensed price source has been admitted to this repository",
     "1 opening and 1 closing quote, each with a source and a capture timestamp, for 100% of originated markets",
     "39 Week-11 model-record snapshot rows exist; every opening and closing cell is blank and every row carries the price policy flag",
     BLOB + "/" + SELF + "/data/price_snapshots.csv", SCHED11,
     "Row count and blank cells checked by nfl-desk-a59c762a/verify_desk.py",
     "F-A59-02 market price cells are blank by policy P-01"),
    ("R-02", "Pricing", "Decide the price-data policy before any backtest is published",
     "OPEN_DECISION", "A single named, permitted price source with a timestamp, a jurisdiction and documented push/void rules must be chosen and recorded",
     "1 written policy naming the source, the licence terms, the capture cadence and the push/void rule set",
     "No policy is adopted. The decision is written up as suggestion SG-A59-01 with a two-sided what-would-change-our-mind field",
     BLOB + "/" + SELF + "/data/suggestions.csv", "",
     "Decision register only; no external source is cited for an internal policy choice",
     ""),
    ("R-03", "Pricing", "Price a line ourselves and publish the residual against the market, on a schedule, from day one",
     "BLOCKED", "R-01 and R-02 must clear before any residual can be computed",
     "A published model-minus-market residual for every originated market on every publication day",
     "Model lines are published for all 13 Week-11 games; the market line and the residual columns are blank and flagged",
     BLOB + "/" + SELF + "/data/originated_lines.csv", SCHED11,
     "39 line rows: 13 games x side, total, moneyline", "F-A59-02"),
    ("R-04", "Pricing", "Publish the model's fair line, the market line, and the difference as separate columns",
     "MET", "",
     "n/a - structure requirement",
     "originated_lines.csv carries model_fair_line, market_line and difference_vs_market as three separate columns for all 39 rows",
     BLOB + "/" + SELF + "/data/originated_lines.csv", SCHED11,
     "Column presence checked by the verifier", ""),
    ("R-05", "Pricing", "Vig-Free Market Consensus vs. Originated Fair-Line Decomposition View",
     "BLOCKED", "No admitted market price, so no vig can be removed and no consensus can be formed",
     "A vig-free consensus line from at least two admitted books and a decomposition of origination alpha against operator margin",
     "Not built. Depends entirely on R-01 and R-02",
     BLOB + "/" + SELF + "/data/requirements.csv", "",
     "Dependency recorded; nothing computed", "F-A59-02"),
    ("R-06", "Pricing", "Publish a weekly 'what changed' diff instead of a static snapshot",
     "PARTIAL", "Needs at least two dated publication cycles; the first was published 2026-11-19",
     "2 dated weekly snapshots of every table with a rendered diff column",
     "This desk is the first dated publication. The change column is wired into the availability and lines tables; a second cycle is required",
     BLOB + "/" + SELF + "/data/availability_delta.csv", INJ11,
     "Delta table published with a previous and a current read clock on every row", ""),
    # ------------------------------------------------------------- results
    ("R-07", "Results", "Add a verified results feed so backtests and ROI can be computed at all",
     "MET", "",
     "n/a - feed requirement",
     "150 games, weeks 1-10 of the 2026 regular season, every row carrying the official nfl.com source URL. Weeks 1-9 are carried forward from the repository feed; all 14 Week-10 finals were read first-hand on 2026-11-19",
     BLOB + "/" + SELF + "/data/results_2026.csv", SCHED10,
     "Reconciled against the first-hand official standings read: 32 clubs x W, L, T, points for, points against all agree; 0 mismatches",
     ""),
    ("R-08", "Results", "Turn the 136-game log into the pre-registered backtest corpus",
     "PARTIAL", "The pre-registration must name the corpus, the window and the gates before the corpus is scored",
     "A pre-registration record naming the corpus hash, the train, validation and holdout windows, and the gates",
     "The corpus is 150 games, not 136. The pre-registration below names the 150-game corpus, the week 1-8 train window, week 9 validation and week 10 final holdout",
     BLOB + "/" + SELF + "/data/pre_registration.csv", SCHED10,
     "Corpus row count reconciled to the standings sum: 149 wins + 2 ties gives 150 games", ""),
    ("R-09", "Results", "Split data into train, validation and final holdout seasons",
     "MET", "",
     "n/a - structure requirement",
     "Train: weeks 1-8 (121 games). Validation: week 9 (15 games). Final holdout: week 10 (14 games). The split is chronological, not random",
     BLOB + "/" + SELF + "/data/shadow_backtest.csv", SCHED10,
     "Split recorded on every backtest row and in the model card", ""),
    ("R-10", "Results", "Ingest game-level results to make the ratings opponent-aware",
     "MET", "",
     "n/a - implementation requirement",
     "Ratings are fitted by opponent-adjusted least squares on the 150-game corpus: margin = HFA + rating_home - rating_away, with the rating vector constrained to sum to zero",
     BLOB + "/" + SELF + "/data/model_ratings.csv", STANDINGS,
     "Model m1-2026-11-19-opponent-adjusted-ls; fitted on weeks 1-8 only", ""),
    ("R-11", "Results", "Fixture-context feature set built only from published schedule facts",
     "PARTIAL", "Venue, neutral site, kickoff and network are captured; the remaining published facts (weather from the official game book) exist for one game only",
     "A fixture table whose every column is a published schedule or game-book fact, for 100% of the slate",
     "Kickoff date, kickoff time, network and neutral-site venue are captured for all 13 Week-11 games. The Week-11 neutral game is confirmed from the Schedule Release page",
     BLOB + "/" + SELF + "/raw/schedule_wk11_2026-11-19.csv", RELEASE,
     "Read first-hand on 2026-11-19; the release page lists Week 11 Vikings at 49ers at Estadio Banorte",
     ""),
    # ------------------------------------------------------------- the model
    ("R-12", "Model", "Originate the side first, then the total, then the moneyline",
     "MET", "",
     "n/a - ordering requirement",
     "Every one of the 13 Week-11 games carries three rows in market_order 1 side, 2 total, 3 moneyline",
     BLOB + "/" + SELF + "/data/originated_lines.csv", SCHED11,
     "39 rows = 13 games x 3 markets, ordered", ""),
    ("R-13", "Model", "Publish every model total twice until one wins",
     "MET", "",
     "n/a - structure requirement",
     "The total row publishes estimator A (league mean total) and estimator B (shrunk offense plus shrunk opponent defense) and the gap between them. Neither is retired",
     BLOB + "/" + SELF + "/data/originated_lines.csv", STANDINGS,
     "Both estimators and the gap are in the inputs column of every total row", ""),
    ("R-14", "Model", "Store every model output as a probability plus its inputs, not just a pick",
     "MET", "",
     "n/a - structure requirement",
     "Every line row carries probability, probability_label, inputs and inputs_source_url",
     BLOB + "/" + SELF + "/data/originated_lines.csv", STANDINGS,
     "Field presence enforced by the verifier", ""),
    ("R-15", "Model", "Score injury-designation reliability before using it as a feature",
     "OPEN", "Requires several seasons of designations joined to the official inactive lists; only the 2026 season is captured and only one game book has been read",
     "A per-designation play rate with a confidence interval, computed from at least three seasons of official designations and official inactive lists",
     "Not computed. The join is specified as SG-A59-04 with its data prerequisites",
     BLOB + "/" + SELF + "/data/suggestions.csv", INJ11,
     "Prerequisite specified; not started", ""),
    ("R-16", "Model", "Make the injury signal a surprise, never a level",
     "PARTIAL", "Needs a dated multi-day series; only two dated reads of the same report exist (2026-11-18 partial, 2026-11-19 full)",
     "A model feature built from the change between consecutive dated reads, with no level term",
     "The availability delta table publishes change_type, previous_value and current_value for every row and carries both read clocks. No injury level is used as a feature anywhere in this desk",
     BLOB + "/" + SELF + "/data/availability_delta.csv", INJ11,
     "Verified: the model inputs column contains no injury term", ""),
    ("R-17", "Model", "Add injury and personnel ablations instead of fixed penalties",
     "OPEN", "Requires a verified availability feature and a second model fitted without it; no such feature exists yet because R-22 and R-29 are open",
     "Two otherwise identical models, fitted on a chronological holdout, differing only by the availability feature, with the difference and its uncertainty reported",
     "Not run. The current model has no injury term at all, so the ablation would be a no-op rather than a measurement. This is recorded rather than faked",
     BLOB + "/" + SELF + "/data/suggestions.csv", INJ11,
     "Reason recorded explicitly", ""),
    ("R-18", "Model", "Add injury/depth ablations, not fixed penalties",
     "OPEN", "Same prerequisite as R-17",
     "Same as R-17",
     "Not run, for the same reason as R-17",
     BLOB + "/" + SELF + "/data/suggestions.csv", INJ11,
     "Reason recorded explicitly", ""),
    ("R-19", "Model", "2026 Kickoff and Declared Onside-Kick Regime Priors Filter",
     "OPEN", "Needs the official per-game kickoff and onside-kick statistics for the 2026 season, which this repository does not hold",
     "An official per-game onside-kick rate and a declared-regime variable for every game in the corpus",
     "Not built. No official onside-kick or kickoff-regime dataset is present in the repository",
     BLOB + "/" + SELF + "/data/requirements.csv", RULEBOOK,
     "Rule context is cited; no statistics are claimed", ""),
    ("R-20", "Model", "Interactive Offense vs. Defense Matchup Deficiency Matrix (1st to 4th string)",
     "BLOCKED", "Needs a verified depth-order source for all 32 clubs and a captured play-time source; see R-22, R-29 and R-31",
     "A matrix of every offensive slot against every defensive slot with a verified string depth on both sides",
     "Not built. The depth source is verified for 31 of 32 clubs and play time is not captured at all",
     BLOB + "/" + SELF + "/data/depth_coverage.csv", "",
     "Coverage computed from the repository depth captures", "F-A59-05"),
    # -------------------------------------------------------- availability
    ("R-21", "Availability", "Build the availability graph as a first-class dataset (who was expected to start, who actually did)",
     "PARTIAL", "The official Game Book route is proven on one game; it has not been run across the league, and no official expected-starter file has been read",
     "Expected starters and actual starters linked per player per game for every game in the evaluation window",
     "One game is complete: Washington at New York, Week 10, with 22 expected starters, 22 actual starters, 6 Washington and 7 New York players Not Active, 3 and 1 Did Not Play",
     BLOB + "/" + SELF + "/raw/gamebook_was_nyg_reg10_2026-11-19.md", GAMEBOOK_WASNYG,
     "Read first-hand from the official PDF on 2026-11-19",
     "F-A59-06 the availability graph is one game, not a league dataset"),
    ("R-22", "Availability", "Use official NFL Game Books for actual starters and game-day status; do not infer depth rank or snaps",
     "PARTIAL", "Proven on one game; the league-wide capture job does not exist",
     "Every game in the evaluation window has its official Game Book read and stored",
     "The official Game Book publishes the starting lineups, the substitutions, the players who did not play, the Not Active list and the game-day weather and surface. It does not publish snap counts, so a snap proxy cannot come from this document",
     BLOB + "/" + SELF + "/raw/gamebook_was_nyg_reg10_2026-11-19.md", GAMEBOOKS,
     "Document contents checked by reading the official PDF",
     "F-A59-06"),
    ("R-23", "Availability", "Capture official inactive lists and snap counts",
     "PARTIAL", "Inactive lists are captured for one game. Snap counts are not in the Game Book and no official snap-count source has been verified in this session",
     "An official Not Active list per game for the whole window, plus a verified official source of per-player play counts",
     "Not Active captured for one game. The Next Gen Stats glossary read on 2026-11-19 publishes tracking metrics and does not document a public snap-count series, so route (b) for play time is not verified",
     BLOB + "/" + SELF + "/raw/gamebook_was_nyg_reg10_2026-11-19.md", NGS,
     "Glossary read first-hand on 2026-11-19",
     "F-A59-07 no official snap-count source verified in this session"),
    ("R-24", "Availability", "Do not model depth from jersey order; model it from playing time",
     "OPEN", "No verified play-time source exists (R-23)",
     "A depth feature built from verified play counts for every player",
     "No depth feature is built at all. Jersey number, experience and salary are explicitly rejected as depth proxies",
     BLOB + "/" + SELF + "/data/requirements.csv", "",
     "Rejection recorded as design rule, not as a finding", "F-A59-07"),
    ("R-25", "Availability", "Track the depth of the replacement, not just the fact of a replacement",
     "BLOCKED", "Needs R-22 (depth order verified for all 32 clubs) and a play-time source",
     "Every replacement named with its verified string depth",
     "Not computed. The replacement columns in the per-team view are blank and flagged",
     BLOB + "/" + SELF + "/data/team_availability.csv", "",
     "Blank and flagged, never inferred", "F-A59-05"),
    ("R-26", "Availability", "Add a per-team view: starters out, replacements named, net injury count",
     "PARTIAL", "Net injury count is computable and published; starters out and replacements named are not",
     "All three columns populated for every club in the slate",
     "Net injury count is published for all 32 clubs (26 in the slate, 6 on a bye). Starters out and replacements named are blank with an explicit flag",
     BLOB + "/" + SELF + "/data/team_availability.csv", INJ11,
     "253 official rows read on 2026-11-19 and counted per club",
     "F-A59-05"),
    ("R-27", "Availability", "Add an announced-starter evidence field (not an inferred replacement)",
     "OPEN", "Needs the official announced-starter articles to be read and stored per game",
     "An announced-starter record for every changed starter in the window, each with its own dated official article",
     "Not built. The official injury report publishes no announced-starter field, and no article-level capture job exists",
     BLOB + "/" + SELF + "/data/requirements.csv", INJ11,
     "Dependency recorded", ""),
    ("R-28", "Availability", "Add an official depth-chart register with date and source per row",
     "PARTIAL", "The register exists in the repository for 31 of 32 clubs; the date and source discipline is only complete for the captured rows",
     "A depth register in which every row carries a publication date and the club depth-chart URL",
     "890 rows across 32 clubs are captured in the repository. The Houston row is a single image-only placeholder. The Patriots rows are marked partial",
     BLOB + "/nfl-c98c6270/data/depth_slots.csv", "",
     "Club-by-club coverage recomputed in this session", "F-A59-05"),
    ("R-29", "Availability", "Resolve the depth-order source before building the backup-deficiency feature",
     "BLOCKED", "Route (a) fails for Houston because the club publishes depth as an image; route (b) has no verified official snap-count source",
     "One route verified for all 32 clubs, or a documented, authorised structured substitute for Houston",
     "Route (a) verified for 31 of 32 clubs. Route (b) not verified. The backup-deficiency feature is therefore not built, as instructed",
     BLOB + "/" + SELF + "/data/depth_coverage.csv", NGS,
     "Per-club status recomputed from the repository capture on 2026-11-19",
     "F-A59-05"),
    ("R-30", "Availability", "Fix the two depth-parsing failures before widening coverage",
     "PARTIAL", "The Packers row is recoverable by stripping jersey numbers; the Texans row needs an authorised structured source and is not fixed",
     "0 unparsed club depth pages",
     "The two failures are confirmed and located. The Packers failure is a documented, mechanical fix that has not been applied by the owning session. The Texans failure needs an authorised structured source; transcription by eye is rejected",
     BLOB + "/nfl-desk-e46fb855/data/depth_slots.csv", "",
     "Status strings read directly from the repository capture", "F-A59-05"),
    ("R-31", "Availability", "Model depth slots as groups, not a single starter",
     "PARTIAL", "The repository capture already records shared rank-1 and empty slots, but only for 31 clubs",
     "Every slot across all 32 clubs stored as a group with its full membership",
     "The repository capture records 14 shared rank-1 slots and 5 empty first strings out of 890 rows. Treating column 1 as a single starter is explicitly rejected",
     BLOB + "/nfl-c98c6270/data/depth_slots.csv", "",
     "Counts recomputed in this session on 2026-11-19", "F-A59-05"),
    ("R-32", "Availability", "Represent shared and empty depth slots faithfully",
     "PARTIAL", "Same as R-31",
     "Same as R-31",
     "Same evidence as R-31",
     BLOB + "/nfl-c98c6270/data/depth_slots.csv", "",
     "Counts recomputed in this session on 2026-11-19", "F-A59-05"),
    ("R-33", "Availability", "Flag stale depth rows against the official transactions log",
     "OPEN", "Needs a captured official transactions log to compare each depth row against",
     "Every depth row versioned against the last official roster event for that club",
     "Not built in this desk. The repository contains a transactions register for November 2026 that is capped by the publisher and needs pagination before it can be used as a baseline",
     BLOB + "/nfl-desk-35a1feb2/data/transactions_register.csv", "",
     "Repository evidence located, not re-verified in this session", ""),
    ("R-34", "Availability", "Treat roster turnover as a first-class data event",
     "OPEN", "Same as R-33",
     "A versioned availability record whose version moves on every official roster event",
     "Not built in this desk",
     BLOB + "/nfl-desk-35a1feb2/data/transactions_register.csv", "",
     "Repository evidence located", ""),
    ("R-35", "Availability", "Run the 32-team roster and IR sweep before any team-level model is trusted",
     "PARTIAL", "The sweep exists in the repository; it is not re-run here and the reserve-list capture is partial",
     "A dated 32-club roster and reserve-list sweep with the reserve list captured so that not-listed never means available",
     "The repository holds a 32-club roster sweep. This desk does not re-run it and does not claim it as its own verification",
     BLOB + "/nfl-market-desk/data/roster_sweep_32.csv", "",
     "Repository evidence located, not re-verified in this session", ""),
    ("R-36", "Availability", "Capture the reserve list so 'not listed' never means 'available'",
     "PARTIAL", "The official reserve list is captured for part of the season only",
     "A reserve-list capture covering every week of the evaluation window",
     "Not captured in this desk. The repository holds a reserve-list register for November 2026 and records that the monthly page is capped, so the capture job must paginate",
     BLOB + "/nfl-desk-35a1feb2/data/reserve_list_register.csv", "",
     "Repository evidence located", ""),
    ("R-37", "Availability", "Populate the three missing Lions game-status designations",
     "PARTIAL", "The designations existed for Week 10 and were published; the Week-11 columns for those three Lions are legitimately blank because the Sunday game has not reached its designation deadline",
     "A game-status cell for every named player on the official report",
     "Kerby Joseph, Cade Mays and D.J. Reed all appear on the official Week-11 report with a blank game-status cell. The report was read at 2026-11-19T06:45Z, and the Lions play on Sunday 22 November, so the Sunday game-status columns are not yet published. The repository holds the Week-10 record in which all three were listed Out",
     BLOB + "/" + SELF + "/data/availability_wk11.csv", INJ11,
     "253 rows read first-hand on 2026-11-19; the blank cells are the publisher's, not a parsing failure",
     "F-A59-08 the blank Lions cells are a publication-timing fact, not a defect"),
    ("R-38", "Availability", "Store every injury-hub read with its clock time and publish the delta, never the level",
     "MET", "",
     "n/a - storage requirement",
     "Every availability row carries read_at_utc and the source URL. The delta table carries the previous and the current read clock on every row and publishes change_type, previous_value and current_value",
     BLOB + "/" + SELF + "/data/availability_delta.csv", INJ11,
     "258 delta rows computed from the 2026-11-18T03:46Z preview and the 2026-11-19T06:45Z full read", ""),
    ("R-39", "Availability", "Snapshot the nfl.com injury report every Wed, Thu and Fri and keep a dated history",
     "PARTIAL", "A scheduled capture job is required; this session performed one read",
     "A dated capture on every Wednesday, Thursday and Friday of the evaluation window",
     "One capture, read 2026-11-19T06:45Z, 253 rows, 26 club tables. The capture log records the read clock and the SHA-256 of the stored extract",
     BLOB + "/" + SELF + "/data/captures.csv", INJ11,
     "Capture hash recomputed from the stored file by the verifier", ""),
    ("R-40", "Availability", "Treat the injury report as a timestamped series, not a weekly snapshot",
     "PARTIAL", "Needs at least three consecutive dated reads of the same report",
     "A delta between consecutive dated reads for the same week",
     "Two dated reads of the same Week-11 report exist: 2026-11-18T03:46Z (four rows per club from the game pages) and 2026-11-19T06:45Z (253 rows from the league report). The delta is published. Two of the earlier club-level statements are superseded: the Vikings and 49ers pages said they had no active injuries, and the league report now names 10 Minnesota rows and 15 San Francisco rows",
     BLOB + "/" + SELF + "/data/availability_delta.csv", INJ11,
     "Delta rows computed and printed by the build", "F-A59-04 the earlier read was a game-page sample, not a league report"),
    ("R-41", "Availability", "Automate immutable multi-day availability snapshots",
     "PARTIAL", "Needs a scheduled capture job writing immutable dated artefacts outside the static site",
     "A daily retained capture with a content hash and a timestamp that cannot be overwritten",
     "The storage layer is not built in this desk. The capture log with read clocks and SHA-256 extract hashes is published for the one capture made",
     BLOB + "/" + SELF + "/data/captures.csv", INJ11,
     "Capture log published; the scheduler and durable store are not", "F-A59-09"),
    ("R-42", "Availability", "Build immutable official availability snapshots",
     "PARTIAL", "Same as R-41",
     "Same as R-41",
     "Same as R-41",
     BLOB + "/" + SELF + "/data/captures.csv", INJ11,
     "Capture log published", "F-A59-09"),
    ("R-43", "Availability", "Point-in-Time Snapshot Ledger for Injuries, Depth Charts and Inactives",
     "PARTIAL", "The ledger needs to be reconstructable at the pre-kickoff instant of each game; only the Week-11 report read exists in this desk",
     "For every game, the exact availability state as it stood at its own kickoff",
     "One dated ledger entry exists, for the Week-11 report read at 2026-11-19T06:45Z, which is before the 2026-11-19 8:15 PM ET kickoff of Colts at Texans",
     BLOB + "/" + SELF + "/data/captures.csv", INJ11,
     "Read clock precedes the kickoff; verified against the schedule page", ""),
    ("R-44", "Availability", "Calibrate what Questionable means empirically instead of using old percentages",
     "OPEN", "Requires several seasons of designations joined to official inactive lists",
     "A per-designation play rate with a confidence interval over at least three seasons",
     "Not computed. No old percentage is used anywhere in this desk",
     BLOB + "/" + SELF + "/data/suggestions.csv", INJ11,
     "No percentage claimed", ""),
    ("R-45", "Availability", "Archive weekly injury reports for past seasons",
     "OPEN", "Requires back-filling the official weekly reports for several past seasons",
     "A dated archive of every weekly official injury report for at least three past seasons",
     "Not archived in this desk",
     BLOB + "/" + SELF + "/data/requirements.csv", INJ10,
     "Archive URL pattern identified from the 2026 report index", ""),
    ("R-46", "Availability", "Use snap counts as the starter proxy when the depth chart is unavailable",
     "BLOCKED", "No verified official snap-count source (R-23)",
     "A verified official source of per-player play counts",
     "Not used. The official Game Book was read and contains no snap counts; the Next Gen Stats glossary publishes tracking metrics and does not document a public snap series",
     BLOB + "/" + SELF + "/data/requirements.csv", NGS,
     "Both candidate sources checked on 2026-11-19", "F-A59-07"),
    # ----------------------------------------------------------- strategy
    ("R-47", "Strategy", "Pre-register every strategy; forbid backtest numbers from ever appearing on the leaderboard",
     "MET", "",
     "n/a - structural requirement",
     "Every strategy is registered in the pre-registration table with its rule text, its window and its gates. The leaderboard publishes only prospective scores. The shadow backtest is published on a separate page and is explicitly marked not-for-leaderboard",
     BLOB + "/" + SELF + "/data/leaderboard.csv", "",
     "The verifier fails if any leaderboard row carries a backtest-derived score", ""),
    ("R-48", "Strategy", "Pre-register each strategy (definition frozen before results are seen)",
     "MET", "",
     "n/a - structural requirement",
     "Three strategies and two control baselines are registered with a rule text frozen before the Week-11 kickoff. The git commit that freezes them is the registration",
     BLOB + "/" + SELF + "/data/pre_registration.csv", "",
     "Registration commit recorded on the pre-registration page", ""),
    ("R-49", "Strategy", "Freeze a rule before it sees data (pre-registration)",
     "MET", "",
     "n/a - structural requirement",
     "Same as R-48",
     BLOB + "/" + SELF + "/data/pre_registration.csv", "",
     "Registration commit recorded", ""),
    ("R-50", "Strategy", "Start with a singles-only shadow baseline",
     "MET", "",
     "n/a - structural requirement",
     "The baseline S-SHADOW-01 is singles-only: it bets the model moneyline on one game at a time. No parlay and no prop combo is registered",
     BLOB + "/" + SELF + "/data/pre_registration.csv", "",
     "Registration table lists no multi-leg strategy", ""),
    ("R-51", "Strategy", "Keep parlays and prop combos behind a joint-evidence gate",
     "MET", "",
     "n/a - structural requirement",
     "No parlay or prop combo is registered or ranked. The gate is recorded: a combo may be ranked only when a directly validated joint probability and the operator's void and push rules are both available",
     BLOB + "/" + SELF + "/data/gates.csv", "",
     "Gate G-JOINT recorded with its two prerequisites", ""),
    ("R-52", "Strategy", "Use proper-score leaderboard divisions",
     "PARTIAL", "Divisions exist but only the singles division can be scored, because the joint-evidence gate blocks the others",
     "Four live divisions: singles, game parlays, same-game parlays and prop combos",
     "Four divisions are registered. Only singles can receive a score. The other three are blocked by the joint-evidence gate and read as blocked, not as empty",
     BLOB + "/" + SELF + "/data/leaderboard.csv", "",
     "Division state checked by the verifier", ""),
    ("R-53", "Strategy", "Rank with proper scores and uncertainty, not win rate",
     "PARTIAL", "Uncertainty needs a prospective sample; the model has 29 out-of-sample games and zero prospective games",
     "A benchmark-relative Brier skill score with a game-cluster lower bound and a multiplicity adjustment, computed on the prospective window",
     "The shadow backtest reports Brier skill against a climatology baseline with n, an interval and a Bonferroni-adjusted alpha for 3 trials. The leaderboard itself is unscored because no prospective game has been played",
     BLOB + "/" + SELF + "/data/shadow_backtest.csv", "",
     "Brier, skill score, n and adjusted alpha all present", ""),
    ("R-54", "Strategy", "Two-Stage Skill Leaderboard (Proper-Score Qualification then Prospective CLV/ROI Escrow)",
     "BLOCKED", "Stage two needs a price source to escrow against",
     "Stage one qualification passed for a strategy, then a prospective CLV and ROI escrow over a multi-week window",
     "Stage one is registered and the scoring rule is published. Stage two is blocked by the price policy",
     BLOB + "/" + SELF + "/data/leaderboard.csv", "",
     "Two stages registered; stage two blocked and labelled", "F-A59-02"),
    ("R-55", "Strategy", "Separate signal from staking in the leaderboard so a lucky staking run cannot mask a bad signal",
     "MET", "",
     "n/a - structural requirement",
     "The leaderboard has separate signal_score and staking_return columns. Both are blank because no prospective game has been played and no price exists",
     BLOB + "/" + SELF + "/data/leaderboard.csv", "",
     "Column separation enforced by the verifier", ""),
    ("R-56", "Strategy", "Add a control baseline (random picks, favourites only) to every leaderboard run",
     "MET", "",
     "n/a - structural requirement",
     "Two control baselines are registered and are scored on every run: a random pick and a favourites-only pick. Both are shown on the removal-of-luck panel",
     BLOB + "/" + SELF + "/data/luck_panel.csv", "",
     "Control rows present on the panel", ""),
    ("R-57", "Strategy", "Define a demotion gate that sends a live strategy back to paper",
     "PARTIAL", "The gate rule can be written now; it can be exercised only once prospective scores exist",
     "1 demotion rule with an explicit trigger, an observation window and a review action",
     "The demotion rule is registered with its trigger and its review action. It has not been exercised because no strategy has been live",
     BLOB + "/" + SELF + "/data/gates.csv", "",
     "Gate G-DEMOTE registered", ""),
    ("R-58", "Strategy", "Add a two-sided what-would-change-our-mind field to every strategy entry",
     "MET", "",
     "n/a - structural requirement",
     "Every strategy entry and every suggestion carries a what_would_change_our_mind field with both a direction that would trigger a change and a direction that would confirm the current path",
     BLOB + "/" + SELF + "/data/pre_registration.csv", "",
     "Field presence enforced by the verifier", ""),
    ("R-59", "Strategy", "Compute and publish the removal of luck panel on the site dashboard",
     "MET", "",
     "n/a - publication requirement",
     "The removal-of-luck panel is on the dashboard with five rows: the model, the climatology control, the random control, the favourites-only control, and realised ROI, which is undefined without a price",
     BLOB + "/" + SELF + "/data/luck_panel.csv", "",
     "Rendered on the dashboard page and verified", "F-A59-02"),
    ("R-60", "Strategy", "Each strategy must pass validation gates",
     "PARTIAL", "The gates are written and applied, but no strategy can pass a gate that needs a price",
     "Every registered strategy passes every gate that does not depend on an admitted price source",
     "Three of the registered gates are currently blocked by the price policy and are labelled BLOCKED rather than failed",
     BLOB + "/" + SELF + "/data/gates.csv", "",
     "Gate states checked by the verifier", "F-A59-02"),
    ("R-61", "Strategy", "Determine correlation values",
     "MET", "",
     "n/a - computation requirement",
     "8 correlations are computed from officially sourced numbers only, each published with n, a 95% interval and a two-sided p-value",
     BLOB + "/" + SELF + "/data/correlations.csv", STANDINGS,
     "Recomputed by the build from the official standings and the results feed", ""),
    # ----------------------------------------------------------- site / ops
    ("R-62", "Site", "Put a decision-readiness table on the landing page: one row per requirement, with the gate that blocks it and the number that would clear it",
     "MET", "",
     "n/a - publication requirement",
     "The landing page carries the full requirement register, one row per brief requirement, each with the blocking gate and the clearing number",
     BLOB + "/" + SELF + "/index.html", "",
     "Row count equals the register row count; checked by the verifier", ""),
    ("R-63", "Site", "Make suggestions on how to improve the site to improve decision making, in a dedicated section for review before implementing changes",
     "MET", "",
     "n/a - publication requirement",
     "A dedicated suggestions page lists 8 suggestions, each with options, a recommended path, a two-sided what-would-change-our-mind field and a decision status. Nothing has been implemented on a suggestion",
     BLOB + "/" + SELF + "/suggestions.html", "",
     "Suggestion page rendered and verified", ""),
    ("R-64", "Site", "A clear list of questions, information and answers that need to be addressed before a decision can reasonably be made",
     "MET", "",
     "n/a - publication requirement",
     "A questions page lists 12 open questions, each with what is known from verified sources, what is missing, what is needed before a decision, and the clearing evidence",
     BLOB + "/" + SELF + "/questions.html", "",
     "Question page rendered and verified", ""),
    ("R-65", "Site", "Create a clean landing page and subpages organised by category, simple and easy to use, all entries in table form",
     "MET", "",
     "n/a - presentation requirement",
     "The desk has a landing page and 10 category subpages: requirements, availability, lines, leaderboard, gates, correlations, backtest, questions, suggestions, flagged, sources and executive summary",
     BLOB + "/" + SELF + "/index.html", "",
     "All pages linked from the navigation; the verifier checks every internal link", ""),
    ("R-66", "Site", "Verification: every table row must have a source link to an official site; if a value cannot be confirmed, leave it blank and flag it as unverified",
     "MET", "",
     "n/a - verification requirement",
     "The verifier fails closed on any row that carries a factual value without an https source link, and on any blank factual value that lacks an explicit flag",
     BLOB + "/" + SELF + "/verify_desk.py", "",
     "Negative-control tests cover a stripped source link, a filled blank and a deleted flag", ""),
    ("R-67", "Site", "Split the site into a public analysis layer and a private data layer",
     "OPEN", "Requires a legal decision on the terms of use before any raw row-level data is published",
     "A written terms review and a public surface that contains only derived analysis",
     "This desk publishes derived analysis and links to the official pages. No raw row-level commercial data is published. The terms review is raised as SG-A59-06",
     BLOB + "/" + SELF + "/data/suggestions.csv", "",
     "Current posture recorded", ""),
    ("R-68", "Site", "Stadium Roof/Surface and NWS Hourly Wind/Precipitation Overlay",
     "PARTIAL", "The official 90-minute roof designation comes from the official Game Book, which exists only after the game; the pre-game NWS grid must be captured separately",
     "A per-game overlay of the official roof and surface designation and the NWS hourly forecast grid, for every game in the window",
     "The official Game Book prints the game-day weather and the surface, for example Open Stadium on Field Turf for Washington at New York. Captured for one game. No NWS grid capture exists in this repository",
     BLOB + "/" + SELF + "/raw/gamebook_was_nyg_reg10_2026-11-19.md", GAMEBOOK_WASNYG,
     "Weather and surface line read from the official PDF", "F-A59-06"),
    ("R-69", "Site", "Add durable snapshot storage and alerts",
     "OPEN", "Needs a store outside the static site and a scheduler",
     "A durable, append-only store with a freshness monitor and an alert on source or schema change",
     "Not built in this desk",
     BLOB + "/" + SELF + "/data/captures.csv", "",
     "Requirement recorded", "F-A59-09"),
    ("R-70", "Site", "Add a drift alarm to every scraper",
     "OPEN", "Needs a pinned row count and a required-field list per capture job",
     "Every capture job pins its expected row count and required fields and fails the build loudly when a field disappears",
     "The capture log records the observed row count for the one capture. No alarm is wired to a scheduled job",
     BLOB + "/" + SELF + "/data/captures.csv", INJ11,
     "Observed row counts recorded", "F-A59-09"),
    ("R-71", "Site", "Transcribe the venue of every fixture from the official game centre and publish it",
     "PARTIAL", "The official game centre for one game was read; the other 12 Week-11 game centres were not read in this session",
     "A venue string for all 13 Week-11 fixtures, each from its own official game centre",
     "Colts at Texans: HOUSTON, TX, stadium RELIANT STADIUM, read from the official game centre. The Week-11 international game is Estadio Banorte from the Schedule Release page. The other 11 venues are blank",
     BLOB + "/" + SELF + "/raw/schedule_wk11_2026-11-19.csv", GAMECENTER,
     "Game centre read first-hand on 2026-11-19", "F-A59-10 the schedule page hotel link says NRG Stadium while the game centre says RELIANT STADIUM"),
    ("R-72", "Site", "Publish the league's dated schedule announcement beside the live schedule page",
     "PARTIAL", "The Schedule Release landing page does not print a publication date, so the announcement cannot be dated from the page itself",
     "A dated announcement record, with the date taken from an official dated source",
     "The 2026 Schedule Release landing page, its nine international games and its flexible-scheduling notice are linked. The release page itself prints no publication date, so the date cell is blank and flagged",
     BLOB + "/" + SELF + "/data/sources.csv", RELEASE,
     "Landing page read first-hand on 2026-11-19; no date printed", "F-A59-11 the release landing page carries no publication date"),
    ("R-73", "Site", "Create an executive summary outlining the important details",
     "MET", "",
     "n/a - publication requirement",
     "An executive summary page states what was verified, what was computed, what is blocked, and the three findings that matter most",
     BLOB + "/" + SELF + "/executive-summary.html", "",
     "Rendered and verified", ""),
    ("R-74", "Site", "Review the repository line by line, verify from official trusted sources, provide links for manual review and flag irregularities",
     "PARTIAL", "A full line-by-line review of every desk in the repository is beyond one session; this session reviewed the results feeds, the depth captures and the availability reads, which are the shared inputs",
     "Every published row in the repository traced to an official source, with every irregularity on a flagged page",
     "Three material findings: a stale Week-10 row in the primary results feed, five repository feeds that are shorter than the true corpus, and an unverified depth-order source for one club. All are on the flagged page with source links",
     BLOB + "/" + SELF + "/flagged.html", SCHED10,
     "Reconciliation recomputed in this session on 2026-11-19", "F-A59-01"),
    ("R-75", "Site", "Flag stale depth rows against the official transactions log",
     "OPEN", "Same as R-33",
     "Same as R-33",
     "Same as R-35",
     BLOB + "/" + SELF + "/data/requirements.csv", "",
     "Dependency recorded", ""),
    ("R-76", "Site", "Flagged for Review page for irregularities and unverified items, published with source links",
     "MET", "",
     "n/a - publication requirement",
     "A flagged page lists 11 items, each with severity, what was observed, the decision impact and the official source link",
     BLOB + "/" + SELF + "/flagged.html", "",
     "Rendered and verified", ""),
    ("R-77", "Site", "Coordinate parallel sessions through COORDINATION.md, with non-overlapping scopes and an explicit final integration session",
     "MET", "",
     "n/a - process requirement",
     "This desk claimed an additive namespace, pushed the claim before any build work, edited no file owned by another session, and logged the one cross-session defect as a request rather than an edit",
     BLOB + "/COORDINATION.md", "",
     "Claim commit pushed before the first data file was written", ""),
    ("R-78", "Site", "Create a pull request, merge it without waiting for approval, and confirm that GitHub Pages deploys",
     "IN_PROGRESS", "The merge and the Pages check happen after the desk verifies green",
     "1 merged pull request with a green check run and a confirmed live page fetch",
     "The branch is pushed and the verification runs locally green. The merge record is written on the coordination board after the merge",
     BLOB + "/COORDINATION.md", "",
     "Recorded in the coordination log", ""),
    ("R-79", "Site", "No manual input required; work autonomously to completion",
     "MET", "",
     "n/a - process requirement",
     "Every artefact in this desk was produced by the scripts in this folder from the dated raw captures, with no interactive input and no manual value entry",
     BLOB + "/" + SELF + "/build_data.py", "",
     "Deterministic rebuild check enforced by the verifier", ""),
    # --------------------------------------------------------- rejected
    ("R-80", "Rejected", "Reject deriving depth order from jersey number, experience or salary",
     "REJECTED_AS_DESIGNED", "",
     "n/a - a rejection, not a task",
     "No depth feature in this desk uses jersey number, experience or salary. The Packers jersey-number prefix is recorded as a parsing defect to be stripped, not as a ranking signal",
     BLOB + "/" + SELF + "/data/depth_coverage.csv", "",
     "Design rule recorded", ""),
    ("R-81", "Rejected", "Reject ranking strategies by season-long realised ROI as the ranking metric",
     "REJECTED_AS_DESIGNED", "",
     "n/a - a rejection, not a task",
     "The leaderboard ranks by benchmark-relative Brier skill with an uncertainty and a multiplicity adjustment. Realised ROI is published separately and only when a price source exists",
     BLOB + "/" + SELF + "/data/leaderboard.csv", "",
     "Design rule recorded", ""),
]

QUESTION_FIELDS = [
    "question_id", "question", "known_from_verified_sources", "missing_information",
    "answer_needed_before_decision", "clearing_evidence", "official_source_urls",
    "repo_evidence_urls", "status",
]

QUESTIONS = [
    ("Q-A59-01", "Which book and which quote is the market line we are trying to beat, and at what time?",
     "Nothing in this repository holds an operator price. The Week-11 price store holds 39 model-record rows with every opening and closing cell blank",
     "Provider, jurisdiction, permission, quote timestamp, opening and closing number, and the push and void rule set",
     "Without an admitted price there is no market residual, no closing-line value and no real-price return, so no strategy can be staked or ranked on money",
     "One named permitted source with immutable timestamped open and close observations and a documented rule set",
     "", BLOB + "/" + SELF + "/data/price_snapshots.csv", "OPEN"),
    ("Q-A59-02", "How do we treat a player who is absent from the weekly report because he is on injured reserve rather than because he is healthy?",
     "The official report lists only players with an injury. A club statement on a game page can say a club has no active injuries while a player is on reserve",
     "A reserve-list capture and a join key that links the injury report to the reserve list",
     "Until the join exists, absence from the report cannot be read as availability, and any availability feature built on the report alone will overstate availability",
     "A dated reserve-list capture with pagination for the whole window, joined to the report",
     "", BLOB + "/nfl-desk-35a1feb2/data/reserve_list_register.csv", "OPEN"),
    ("Q-A59-03", "What does Questionable actually mean for a game's scoring margin?",
     "The official report publishes the word and no percentage. In the Week-11 read there are 7 Questionable rows and 9 Out rows out of 253",
     "Several seasons of designations joined to the official inactive lists, so that the play rate of each designation can be estimated",
     "Whether Questionable belongs in a personnel feature at all, and with what weight",
     "A per-designation play rate with a confidence interval over at least three seasons",
     INJ11, BLOB + "/" + SELF + "/data/availability_wk11.csv", "OPEN"),
    ("Q-A59-04", "Who is the replacement for each starter who is out, and at what string?",
     "The repository holds 890 depth rows across 32 clubs. Houston is a single image-only row. The Patriots rows are marked partial",
     "A verified depth order for Houston, a complete Patriots capture, and an official play-time source",
     "Any backup-deficiency feature, any off-versus-defence matchup matrix, and any starter-out count",
     "One depth route verified for all 32 clubs, and an authorised structured source for the Houston page",
     "", BLOB + "/" + SELF + "/data/depth_coverage.csv", "OPEN"),
    ("Q-A59-05", "Which official source publishes per-player play counts?",
     "The official Game Book for Washington at New York was read in full. It publishes the lineups, the substitutions, the players who did not play, the Not Active list and the weather, and no snap counts. The Next Gen Stats glossary publishes tracking metrics and does not document a public snap series",
     "A named official endpoint or document that publishes per-player play counts for the season",
     "Whether route (b) for depth exists at all, which decides whether the backup-deficiency feature can be built for Houston",
     "An official source read first-hand that publishes play counts",
     NGS + "|" + GAMEBOOK_WASNYG, BLOB + "/" + SELF + "/raw/gamebook_was_nyg_reg10_2026-11-19.md", "OPEN"),
    ("Q-A59-06", "Was the Sunday game-status column published for the Lions on the official Week-11 report?",
     "No. Kerby Joseph, Cade Mays and D.J. Reed appear on the official Week-11 report with a blank game-status cell, read at 2026-11-19T06:45Z. The Lions play Sunday 22 November. The Week-10 record in the repository lists all three as Out",
     "Nothing: this is a publication-timing fact, not a missing measurement",
     "Nothing. The cells are correct as published and must stay blank until the publisher fills them",
     "A later dated read of the same Week-11 report, published after the Sunday designation deadline",
     INJ11 + "|" + INJ10, BLOB + "/" + SELF + "/data/availability_wk11.csv", "ANSWERED_IN_REGISTRY"),
    ("Q-A59-07", "Did the earlier club statements that no club had active injuries survive the full league report?",
     "No. The 2026-11-18T03:46Z game-page read carried a club statement for Minnesota and for San Francisco saying there were no active injuries. The 2026-11-19T06:45Z league report names 10 Minnesota rows and 15 San Francisco rows, including Jordan Addison who did not participate",
     "Nothing further for this pair; the delta is published",
     "Nothing. It establishes that a game page is not an availability source and that only the league report carries the full row set",
     "The published delta table with both read clocks",
     INJ11, BLOB + "/" + SELF + "/data/availability_delta.csv", "ANSWERED_IN_REGISTRY"),
    ("Q-A59-08", "Is the model's Week-10 holdout performance skill or luck?",
     "On 29 out-of-sample games in weeks 9 and 10 the model has a Brier skill score of 0.0188 against a climatology baseline on the final holdout week, while the validation week alone gave 0.4357. The favourites-only control won 79.3% of the same 29 games while the model itself won 71.4%",
     "A longer prospective window, and a price source so that the return can be separated from the forecast",
     "Any claim of skill, any staking decision and any reward",
     "A prospective window large enough to separate the two, with an interval on the skill score",
     SCHED10, BLOB + "/" + SELF + "/data/shadow_backtest.csv", "OPEN"),
    ("Q-A59-09", "Is the home-field estimate of 1.49 points stable?",
     "The opponent-adjusted fit on weeks 1 to 8 estimates home field at 1.488 points with a residual standard deviation of 14.079 points",
     "A longer season and a proper interval on the home-field term",
     "Whether the spread model is precise enough to price a half point",
     "An interval on the home-field coefficient from a full-season fit",
     STANDINGS, BLOB + "/" + SELF + "/data/model_ratings.csv", "OPEN"),
    ("Q-A59-10", "What is the correct venue string for the Colts at Texans game?",
     "The official game centre prints HOUSTON, TX and RELIANT STADIUM. The schedule page hotel link for the same fixture says NRG Stadium. The official Schedule Release page lists the Week-11 international game at Estadio Banorte, Mexico City",
     "A ruling on which official string is canonical, so that the venue field is not inconsistent across rows",
     "The venue field, and any stadium roof or surface feature that keys off it",
     "A documented convention agreed once and applied to every venue cell",
     GAMECENTER + "|" + SCHED11 + "|" + RELEASE, BLOB + "/" + SELF + "/raw/schedule_wk11_2026-11-19.csv", "OPEN"),
    ("Q-A59-11", "On what date was the 2026 schedule announced?",
     "The official Schedule Release landing page was read on 2026-11-19. It publishes the 2026 schedule, the nine international games and the flexible-scheduling notice, and it prints no publication date",
     "A dated official announcement, for example a dated league article or a dated league media release",
     "The dated announcement requirement, which asks for the announcement beside the live schedule",
     "An official dated page that states the announcement date",
     RELEASE, BLOB + "/" + SELF + "/data/sources.csv", "OPEN"),
    ("Q-A59-12", "Can the primary repository results feed be used for a backtest as it stands?",
     "No. The 150-row feed in nfl-desk-35a1feb2 leaves the Week-10 Los Angeles Chargers at Baltimore Ravens row blank and marked as not kicked off. The official week-10 page, read on 2026-11-19, shows the game finished, Chargers 23, Ravens 20, on Monday 16 November. The official standings include the game, which is why a per-club reconciliation fails for exactly two clubs",
     "A corrected row in the owning session's feed",
     "Any backtest that uses the stale feed will mis-state the Week-10 result for two clubs and therefore mis-state the ratings",
     "The owning session updates the row, and the reconciliation against the standings returns 0 mismatches for all 32 clubs",
     SCHED10 + "|" + STANDINGS, BLOB + "/nfl-desk-35a1feb2/data/results_feed_2026.csv", "CROSS_SESSION_REQUEST_RAISED"),
]

SUGGESTION_FIELDS = [
    "suggestion_id", "priority", "topic", "options", "recommended_path",
    "what_would_change_our_mind", "official_source_urls", "related_evidence_urls",
    "decision_status",
]

SUGGESTIONS = [
    ("SG-A59-01", "high", "Price-data policy, the single gate that blocks most of the plan",
     "A: adopt an official operator feed that the NFL publishes for partners; "
     "B: adopt a licensed commercial feed and store only derived, non-redistributable features; "
     "C: keep the price store empty and run the project as a pure forecasting desk with no staking or ROI claim.",
     "C for now, with B as the target. The empty store is honest and already implemented, and the model can be judged on forecast quality alone until a feed is licensed. Choose B before any backtest with a money outcome is published.",
     "What would change this: a written, signed permission for a named feed with a quote timestamp, a jurisdiction and a push and void rule set. What would keep it: the model still cannot be scored on money without that document.",
     "", BLOB + "/" + SELF + "/data/price_snapshots.csv", "PROPOSED_NOT_IMPLEMENTED"),
    ("SG-A59-02", "high", "Depth-order source for the Houston Texans",
     "A: find an official structured source for the Texans depth page, for example a feed or a printable page rather than the image; "
     "B: use the official Game Book across a season to build actual-starter history and treat it as the depth proxy; "
     "C: keep Houston out of every depth-based feature and label it as missing.",
     "B plus C now, A as the goal. The Game Book route is already proven on one game and it is the only official source that publishes who actually started, which is the quantity the feature actually needs.",
     "What would change this: an official structured Texans source would remove the exception entirely. What would keep it: no such source appears on the club site, and the brief forbids transcription by eye.",
     "", BLOB + "/" + SELF + "/data/depth_coverage.csv", "PROPOSED_NOT_IMPLEMENTED"),
    ("SG-A59-03", "high", "Whether the pre-registered shadow baseline should stay published",
     "A: keep publishing it with the shadow label and the train, validation and holdout split visible on every row; "
     "B: withdraw all backtest numbers and publish only prospective scores; "
     "C: keep publishing it but add a second untouched holdout.",
     "A now, C before any strategy is staked. The published numbers show exactly why the label matters: the validation week gave a Brier skill of 0.44 and the final holdout gave 0.02. Removing the numbers would hide that lesson.",
     "What would change this: a second holdout season that the model has never seen would let the number stand on its own. What would keep it: nothing in the numbers themselves changes; the label and the split do the work.",
     SCHED10, BLOB + "/" + SELF + "/data/shadow_backtest.csv", "PROPOSED_NOT_IMPLEMENTED"),
    ("SG-A59-04", "medium", "Scoring the injury designation empirically",
     "A: join designations to official inactive lists across three past seasons and estimate a play rate per designation; "
     "B: use the designation only as a filter, never as a weight; "
     "C: do not use designations at all until the archive exists.",
     "A, with C as the interim. The archive of past weekly reports is a public, dated source, so the join is achievable; until then the designation is a filter and never a number in a model.",
     "What would change this: a season of joins that produces a tight interval on the Questionable play rate. What would keep it: wide intervals or a designation that predicts nothing.",
     INJ11, BLOB + "/" + SELF + "/data/suggestions.csv", "PROPOSED_NOT_IMPLEMENTED"),
    ("SG-A59-05", "medium", "Two estimators for the model total, and when one may be retired",
     "A: publish both estimators and their gap indefinitely; "
     "B: retire the weaker estimator after a chronological walk-forward comparison; "
     "C: replace both with a single point estimate and publish the interval instead.",
     "B with A until then. The walk-forward rule must be written before the comparison is run, so that the retirement is not chosen after seeing which one wins.",
     "What would change this: a pre-written walk-forward rule that names the estimator, the window and the decision threshold before the run. What would keep it: the gap column stays until that rule has fired.",
     STANDINGS, BLOB + "/" + SELF + "/data/originated_lines.csv", "PROPOSED_NOT_IMPLEMENTED"),
    ("SG-A59-06", "medium", "Public analysis layer versus private data layer",
     "A: publish everything including raw rows; "
     "B: publish only derived indices, ratios and model output, and link to the official page; "
     "C: publish nothing but links.",
     "B. It is already the posture of this desk: derived analysis in public, and a link to the official page for every fact. It also removes the terms question from the critical path.",
     "What would change this: a written terms review that permits raw row-level republication. What would keep it: the review is not complete, so the conservative layer stays.",
     "", BLOB + "/" + SELF + "/data/suggestions.csv", "PROPOSED_NOT_IMPLEMENTED"),
    ("SG-A59-07", "low", "The price store, the results feed and the standings: one canonical file or many",
     "A: one canonical results feed with every desk reading it; "
     "B: keep the per-desk feeds and publish a reconciliation report; "
     "C: rebuild the feeds from the official pages on a schedule and drop the carried-forward rows.",
     "C for the corpus, because a carried-forward row is only as good as the capture that produced it, and one stale row has already been found. Until the scheduled rebuild exists, B keeps the reconciliation visible.",
     "What would change this: a scheduled rebuild that reproduces the corpus from the official pages with 0 mismatches against the standings. What would keep it: the reconciliation report is the only thing that currently catches a stale row.",
     SCHED10, BLOB + "/" + SELF + "/data/results_2026.csv", "PROPOSED_NOT_IMPLEMENTED"),
    ("SG-A59-08", "low", "What counts as a fair comparison for the removal-of-luck panel",
     "A: compare against the climatology baseline only; "
     "B: compare against the climatology baseline and both controls, as this desk does; "
     "C: compare against a second independent model.",
     "B. With three trials the Bonferroni-adjusted significance level is 0.0167, and a panel that shows only the model can hide a lucky run.",
     "What would change this: a second independently specified model whose forecasts are registered before the window opens. What would keep it: the controls are free, reproducible and already published.",
     "", BLOB + "/" + SELF + "/data/luck_panel.csv", "PROPOSED_NOT_IMPLEMENTED"),
]

GATE_FIELDS = ["gate_id", "gate", "rule", "threshold", "current_result", "evidence",
               "source_url", "flag"]

GATES = [
    ("G-A59-01", "Provenance", "Every published factual row carries a link to an official source, or is blank and explicitly flagged",
     "0 rows with a value and no source link", "PASS",
     "Enforced by nfl-desk-a59c762a/verify_desk.py; negative-control tests cover a stripped link, a filled blank and a deleted flag",
     BLOB + "/" + SELF + "/verify_desk.py", ""),
    ("G-A59-02", "Leakage", "No model input may carry information dated after the kickoff of the game it predicts",
     "0 inputs dated after the predicted game's kickoff", "PASS",
     "Every Week-11 line row records recorded_at_utc 2026-11-19T07:05:00Z, before the first Week-11 kickoff at 8:15 PM ET on 2026-11-19",
     SCHED11, ""),
    ("G-A59-03", "Holdout", "Train, validation and final holdout windows are chronological and disjoint",
     "3 disjoint chronological windows, final holdout never touched during fitting", "PASS",
     "Train weeks 1-8 (121 games), validation week 9 (15), final holdout week 10 (14). The model is fitted on the train window only",
     SCHED10, ""),
    ("G-A59-04", "Pre-registration", "Every strategy and every rule is frozen before the evaluation window opens",
     "1 registered rule per strategy with a commit hash", "PASS",
     "3 strategies and 2 controls registered in data/pre_registration.csv before the first Week-11 kickoff",
     BLOB + "/" + SELF + "/data/pre_registration.csv", ""),
    ("G-A59-05", "No backtest on the leaderboard", "No leaderboard cell may contain a backtest-derived number",
     "0 leaderboard cells with a backtest-derived value", "PASS",
     "The leaderboard holds prospective columns only. The verifier fails if any of them is filled from the shadow backtest",
     BLOB + "/" + SELF + "/data/leaderboard.csv", ""),
    ("G-A59-06", "Signal separated from staking", "Signal and staking are separate columns and a staking return may never be shown without a signal score",
     "2 separate column groups on every leaderboard row", "PASS",
     "leaderboard.csv carries signal_score and staking_return as distinct columns",
     BLOB + "/" + SELF + "/data/leaderboard.csv", ""),
    ("G-A59-07", "Control baselines", "Every scoring run includes a random control and a favourites-only control",
     "2 controls scored on every run", "PASS",
     "Both controls appear on the removal-of-luck panel with their own n",
     BLOB + "/" + SELF + "/data/luck_panel.csv", ""),
    ("G-A59-08", "Multiplicity", "The number of trials is declared and the significance threshold is adjusted",
     "adjusted alpha = 0.05 / trials", "PASS",
     "3 trials are declared on the removal-of-luck panel, so the adjusted alpha is 0.01667",
     BLOB + "/" + SELF + "/data/luck_panel.csv", ""),
    ("G-A59-09", "Proper score", "Ranking uses a benchmark-relative proper score with an uncertainty, never win rate",
     "a benchmark-relative Brier skill score with n and an interval", "PARTIAL",
     "The shadow backtest reports Brier skill against climatology with n and a Fisher interval. The leaderboard is unscored because no prospective game has been played",
     BLOB + "/" + SELF + "/data/shadow_backtest.csv", "F-A59-12 no prospective sample yet"),
    ("G-A59-10", "Joint evidence", "A parlay or a prop combo may be ranked only when a directly validated joint probability and the operator's void and push rules are both available",
     "2 prerequisites per combo", "BLOCKED",
     "No combo is registered. Both prerequisites are absent: no validated joint probability and no admitted operator rule set",
     BLOB + "/" + SELF + "/data/gates.csv", "F-A59-02"),
    ("G-A59-11", "Price source", "A market residual, a closing-line value or a realised return requires an admitted, timestamped price source",
     "1 admitted source with a quote timestamp per market", "BLOCKED",
     "No admitted source exists. All 39 price-snapshot rows are blank and flagged",
     BLOB + "/" + SELF + "/data/price_snapshots.csv", "F-A59-02"),
    ("G-A59-12", "Depth source", "A depth-based feature requires a verified depth order for all 32 clubs or a verified official play-time source",
     "32 of 32 clubs verified on one route", "BLOCKED",
     "Route (a) is verified for 31 clubs. Route (b) has no verified official source. The backup-deficiency feature is therefore not built",
     BLOB + "/" + SELF + "/data/depth_coverage.csv", "F-A59-05"),
    ("G-A59-13", "Demotion", "A live strategy that loses its skill evidence is returned to paper",
     "a demotion rule with a trigger, a window and a review action", "REGISTERED_NOT_EXERCISED",
     "The rule is registered. It has not been exercised because no strategy has been live and no prospective score exists",
     BLOB + "/" + SELF + "/data/gates.csv", "F-A59-12"),
    ("G-A59-14", "Availability timing", "An availability read may only be used if its clock time precedes the kickoff it informs",
     "read_at_utc earlier than the kickoff of every game it informs", "PASS",
     "The Week-11 injury report was read at 2026-11-19T06:45Z, before the 8:15 PM ET kickoff",
     SCHED11, ""),
]

LEADERBOARD_FIELDS = [
    "entry_id", "division", "strategy_id", "strategy", "market_scope", "stake_policy",
    "registered_utc", "registration_commit", "n_prospective", "signal_score",
    "signal_score_metric", "signal_ci_low", "signal_ci_high", "skill_vs_benchmark",
    "staking_return", "staking_n", "eligibility", "block_reason", "source_url",
]

LEADERBOARD = [
    dict(zip(LEADERBOARD_FIELDS, ("LB-A59-01", "singles", "S-SHADOW-01",
     "Team-strength model, one game at a time, model moneyline",
     "single game moneyline", "stake nothing; paper only until the price gate clears",
     "2026-11-19T07:05:00Z", "see data/pre_registration.csv", 0, "",
     "Brier skill vs climatology", "", "", "", "", 0, "REGISTERED_NOT_SCORED",
     "No prospective game has been played and no price source is admitted, so neither a signal "
     "score nor a return can be published", SCHED11))),
    dict(zip(LEADERBOARD_FIELDS, ("LB-A59-02", "singles", "CTRL-RANDOM", "Control: random pick",
     "single game moneyline", "stake nothing", "2026-11-19T07:05:00Z",
     "see data/pre_registration.csv", 0, "", "Brier skill vs climatology", "", "", "", "", 0,
     "CONTROL_REGISTERED_NOT_SCORED",
     "Control baseline; scored automatically on every run once a prospective window exists",
     SCHED11))),
    dict(zip(LEADERBOARD_FIELDS, ("LB-A59-03", "singles", "CTRL-FAVE",
     "Control: favourites only, the higher-rated team", "single game moneyline", "stake nothing",
     "2026-11-19T07:05:00Z", "see data/pre_registration.csv", 0, "", "Brier skill vs climatology",
     "", "", "", "", 0, "CONTROL_REGISTERED_NOT_SCORED",
     "Control baseline; scored automatically on every run once a prospective window exists",
     SCHED11))),
    dict(zip(LEADERBOARD_FIELDS, ("LB-A59-04", "game parlay", "", "Division reserved: multi-game parlay",
     "two to six game parlay", "stake nothing", "2026-11-19T07:05:00Z",
     "see data/pre_registration.csv", 0, "", "", "", "", "", "", 0, "BLOCKED",
     "Joint-evidence gate G-A59-10: a directly validated joint probability and the operator's "
     "void and push rules are both required, and neither is available", SCHED11))),
    dict(zip(LEADERBOARD_FIELDS, ("LB-A59-05", "same-game parlay", "",
     "Division reserved: same-game parlay", "two or more legs from one game", "stake nothing",
     "2026-11-19T07:05:00Z", "see data/pre_registration.csv", 0, "", "", "", "", "", "", 0,
     "BLOCKED", "Joint-evidence gate G-A59-10: same prerequisite as the game parlay division",
     SCHED11))),
    dict(zip(LEADERBOARD_FIELDS, ("LB-A59-06", "prop combo", "",
     "Division reserved: player prop combo", "two or more player props", "stake nothing",
     "2026-11-19T07:05:00Z", "see data/pre_registration.csv", 0, "", "", "", "", "", "", 0,
     "BLOCKED", "Joint-evidence gate G-A59-10: same prerequisite as the game parlay division",
     SCHED11))),
]

PREREG_FIELDS = ["strategy_id", "strategy", "scope", "rule_text", "window",
                 "evaluation_metric", "gates", "frozen_utc", "frozen_commit",
                 "what_would_change_our_mind_a", "what_would_change_our_mind_b",
                 "source_url"]

PREREG = [
    ("S-SHADOW-01", "Team-strength model, singles only", "single game moneyline",
     "For each Week-11 game, predict the margin as HFA + rating_home - rating_away, where the "
     "ratings are the opponent-adjusted least-squares fit on weeks 1 to 8 only, and convert it "
     "to a home-win probability with the training-window residual standard deviation. Bet the "
     "model moneyline on one game at a time. No parlay, no prop, no market price.",
     "Week 11, 2026, 13 games, kickoff from 2026-11-19 8:15 PM ET",
     "Brier skill score against the climatology baseline, with n, a Fisher interval and a "
     "Bonferroni adjustment for the number of trials",
     "G-A59-01 provenance; G-A59-02 leakage; G-A59-03 holdout; G-A59-05 no backtest on the "
     "leaderboard; G-A59-07 controls; G-A59-08 multiplicity; G-A59-09 proper score; "
     "G-A59-14 availability timing",
     "2026-11-19T07:05:00Z", "recorded in data/pre_registration.csv on the branch that merged this desk",
     "What would change this: a prospective Brier skill below zero with an interval that excludes "
     "zero, or a calibration failure on the reliability curve.",
     "What would keep it: a prospective Brier skill above zero with an interval that excludes zero, "
     "and a calibration curve close to the diagonal.",
     SCHED11),
    ("CTRL-RANDOM", "Control: random pick", "single game moneyline",
     "For each Week-11 game, flip a fair coin and take the home team if heads. Scored with the "
     "same metric as S-SHADOW-01 so that skill can be separated from luck.",
     "Week 11, 2026, 13 games", "Brier skill score against the climatology baseline",
     "G-A59-07 controls", "2026-11-19T07:05:00Z",
     "recorded in data/pre_registration.csv on the branch that merged this desk",
     "What would change this: nothing; a control has no hypothesis.",
     "What would keep it: nothing; a control has no hypothesis.",
     SCHED11),
    ("CTRL-FAVE", "Control: favourites only", "single game moneyline",
     "For each Week-11 game, take the team with the higher fitted rating, regardless of the "
     "market. Scored with the same metric as S-SHADOW-01.",
     "Week 11, 2026, 13 games", "Brier skill score against the climatology baseline",
     "G-A59-07 controls", "2026-11-19T07:05:00Z",
     "recorded in data/pre_registration.csv on the branch that merged this desk",
     "What would change this: nothing; a control has no hypothesis.",
     "What would keep it: nothing; a control has no hypothesis.",
     SCHED11),
]

FLAG_FIELDS = ["flag_id", "severity", "item", "observation", "decision_impact",
               "action", "official_source_urls", "repo_evidence_urls", "status"]

FLAGS = [
    ("F-A59-01", "critical",
     "The repository's primary 2026 results feed has a stale Week-10 row",
     "nfl-desk-35a1feb2/data/results_feed_2026.csv holds 150 rows; the row for the Los Angeles "
     "Chargers at Baltimore Ravens, game id 2026_10_LAC_BAL, has blank scores and the status "
     "SCHEDULED - NOT KICKED OFF AT READ TIME. The official nfl.com Week-10 schedule page, read "
     "on 2026-11-19, shows that game as FINAL on Monday 16 November, Chargers 23, Ravens 20. "
     "The official league standings include the game. A per-club reconciliation of the feed "
     "against the standings therefore fails for exactly two clubs: Baltimore reads 4 wins and 6 "
     "losses in the standings against 4 and 5 in the feed, and Los Angeles Chargers reads 1 and 8 "
     "against 0 and 8. Every other club, and all 13 other Week-10 finals, agree exactly.",
     "Any backtest, rating fit or availability join that reads this feed will mis-state the "
     "Week-10 result for two clubs, and therefore mis-state the ratings and the two clubs' "
     "season records.",
     "A cross-session request has been logged on COORDINATION.md for the owning session. This "
     "desk publishes a corrected 150-game feed in its own namespace, reconciled to the standings "
     "with 0 mismatches, and does not edit the owning session's file.",
     SCHED10 + "|" + STANDINGS,
     BLOB + "/nfl-desk-35a1feb2/data/results_feed_2026.csv", "CROSS_SESSION_REQUEST_RAISED"),
    ("F-A59-02", "blocking",
     "No market price source is admitted, so no market line, residual, closing-line value or return exists",
     "The price store holds 39 model-record rows with every opening and closing cell blank. The "
     "leaderboard's staking column cannot be filled, the real-price return is undefined, and the "
     "joint-evidence gate cannot be satisfied because the operator's void and push rules are "
     "unknown.",
     "Nothing about money can be computed or ranked. Every money-related cell is blank and "
     "labelled, and the gates that depend on it are marked BLOCKED rather than failed.",
     "Decide the price-data policy first. See SG-A59-01, which states the options, the "
     "recommendation and what would change it.",
     "", BLOB + "/" + SELF + "/data/price_snapshots.csv", "OPEN_DECISION"),
    ("F-A59-03", "review",
     "Four other repository results feeds are shorter than the true 2026 corpus",
     "nfl-market-desk and nfl-desk-e46fb855 hold 145 games each and are missing five of the "
     "fourteen Week-10 games; nfl-c98c6270 holds 150 rows but leaves the Los Angeles Rams at "
     "Arizona Cardinals row out entirely and leaves the Chargers at Ravens row as NOT FINAL; "
     "nfl-command-desk holds 150 rows but is missing the Rams at Cardinals row; "
     "nfl-price-results-853c0074 holds 136 games and is missing all fourteen Week-10 games.",
     "Any desk that reads one of these shorter feeds will compute on an incomplete corpus. The "
     "number of games in the corpus is verifiable: the official standings sum to 149 wins and 2 "
     "ties, which is 150 games.",
     "Logged as a cross-session request. The canonical corpus used by this desk is its own "
     "150-row feed, reconciled against the standings with 0 mismatches.",
     STANDINGS, BLOB + "/nfl-market-desk/data/results_feed.csv", "CROSS_SESSION_REQUEST_RAISED"),
    ("F-A59-04", "review",
     "The earlier Week-11 availability read in the repository is a game-page sample, not a league report",
     "data/nfl-desk-f2e20e96/availability_wk11_preview.csv holds 10 rows read at "
     "2026-11-18T03:46Z from two game pages, which expose four rows per club. It carries club "
     "statements that Minnesota and San Francisco have no active injuries. The full league "
     "report, read at 2026-11-19T06:45Z, names 10 Minnesota rows and 15 San Francisco rows, "
     "including Minnesota receiver Jordan Addison, who did not participate.",
     "A game page is not an availability source. The delta between the two reads is published in "
     "this desk so the change is visible rather than the level.",
     "The delta table is published with both read clocks on every row.",
     INJ11, BLOB + "/data/nfl-desk-f2e20e96/availability_wk11_preview.csv", "PUBLISHED"),
    ("F-A59-05", "blocking",
     "The depth-order source is verified for 31 of 32 clubs only",
     "nfl-desk-e46fb855/data/depth_slots.csv records 702 rows across 32 clubs. Thirty clubs are "
     "marked parsed. Houston is a single row marked NOT PARSED because the club publishes the "
     "depth chart as an image with no text table. The Patriots carry 19 parsed rows and 7 rows "
     "marked as a partial capture. A second capture in nfl-c98c6270 holds 890 rows across 32 "
     "clubs with Houston as a single image_only row, 14 shared rank-1 slots and 5 empty first "
     "strings.",
     "The backup-deficiency feature, the off-versus-defence matchup matrix and the starters-out "
     "count all depend on a complete depth order, and are therefore blocked and left blank.",
     "Route (b), the official Game Book, is proven on one game and is the better long-term "
     "source because it publishes who actually started. See SG-A59-02.",
     "", BLOB + "/nfl-desk-e46fb855/data/depth_slots.csv", "OPEN"),
    ("F-A59-06", "review",
     "The availability graph covers one game, not a league dataset",
     "The official NFL Game Book for Washington at New York, Week 10, was read in full on "
     "2026-11-19. It publishes the starting lineups, the substitutions, the players who did not "
     "play, the Not Active list and the game-day weather and surface line. No capture job exists "
     "to run it across the league.",
     "The expected-versus-actual starter comparison cannot be treated as a dataset until the "
     "Game Book route is run over the whole evaluation window.",
     "The single game is published as a proof of route, with every line source-linked.",
     GAMEBOOK_WASNYG, BLOB + "/" + SELF + "/raw/gamebook_was_nyg_reg10_2026-11-19.md", "PUBLISHED"),
    ("F-A59-07", "review",
     "No official snap-count source was verified, so route (b) for depth is unproven",
     "The official Game Book was read in full and contains no snap count. The official Next Gen "
     "Stats glossary was read on 2026-11-19 and publishes tracking metrics, including time to "
     "throw, completion probability and separation, and does not document a public per-player "
     "snap series.",
     "The brief requires that depth be modelled from playing time. Until an official play-time "
     "source is verified, the depth feature stays unbuilt rather than approximated.",
     "Recorded as the open prerequisite for the depth-order decision.",
     NGS + "|" + GAMEBOOK_WASNYG, BLOB + "/" + SELF + "/data/depth_coverage.csv", "OPEN"),
    ("F-A59-08", "resolved",
     "The three blank Lions game-status cells are a publication-timing fact, not a parsing failure",
     "Kerby Joseph, Cade Mays and D.J. Reed appear on the official Week-11 injury report with a "
     "blank game-status cell, read at 2026-11-19T06:45Z. The Lions play at Tampa Bay on Sunday 22 "
     "November. The same three players were listed Out on the official Week-10 report. The "
     "Sunday game-status columns are simply not yet published at the time of this read.",
     "Nothing. Filling those cells would be inference, and the brief forbids it.",
     "The cells stay blank and are flagged as the publisher's timing, not a defect.",
     INJ11 + "|" + INJ10, BLOB + "/" + SELF + "/data/availability_wk11.csv", "RESOLVED"),
    ("F-A59-09", "review",
     "No durable snapshot store, scheduler, freshness monitor or drift alarm exists",
     "The capture log records a read clock and the SHA-256 of the stored extract for one "
     "capture, but there is no append-only store outside the static site, no scheduled job and "
     "no alarm on a source or schema change.",
     "The multi-day availability series cannot be replayed as it was known, so a point-in-time "
     "backtest of availability is not yet possible.",
     "Raised as SG-A59-06 in the suggestions register and recorded against the affected "
     "requirements.",
     "", BLOB + "/" + SELF + "/data/captures.csv", "OPEN"),
    ("F-A59-10", "review",
     "Two official venue strings differ for the same fixture",
     "The official game centre for the Colts at Texans prints HOUSTON, TX and RELIANT STADIUM. "
     "The schedule page for the same fixture links a hotel at NRG Stadium. Both are official "
     "NFL strings for the same building.",
     "A venue key that is not consistent across rows will break any stadium or weather feature "
     "joined on the venue name.",
     "The game-centre string is used, and the conflict is published rather than silently "
     "resolved. See question Q-A59-10.",
     GAMECENTER + "|" + SCHED11, BLOB + "/" + SELF + "/raw/schedule_wk11_2026-11-19.csv", "OPEN"),
    ("F-A59-11", "review",
     "The official schedule-release landing page carries no publication date",
     "The 2026 NFL Schedule Release page was read on 2026-11-19. It publishes the schedule, the "
     "nine international games with their venues and dates, and the flexible-scheduling notice "
     "for Weeks 16, 17 and 18. It prints no announcement date, and the page carries no visible "
     "date stamp.",
     "The dated announcement requirement cannot be satisfied from this page alone, so the date "
     "cell is left blank rather than guessed.",
     "Raised as question Q-A59-11, which asks for a dated official source.",
     RELEASE, BLOB + "/" + SELF + "/data/sources.csv", "OPEN"),
]

SOURCE_FIELDS = ["source_id", "publisher", "title", "url", "read_at_utc", "what_it_establishes",
                 "scope_limit"]

SOURCES = [
    ("S-A59-01", "NFL.com", "2026 NFL league standings", STANDINGS, "2026-11-19T06:38:00Z",
     "Win, loss, tie, points for and points against for all 32 clubs through Week 10, read first-hand",
     "Season to date through Week 10. The page is updated live, so a later read will differ."),
    ("S-A59-02", "NFL.com", "Official NFL injury report, Week 11 of the 2026 season", INJ11,
     "2026-11-19T06:45:00Z",
     "253 named player rows across 24 clubs with practice status and game status, and a "
     "no-injuries-reported line for the Cincinnati Bengals and the Washington Commanders",
     "A Thursday edition. The Sunday game-status columns are not yet published at this read."),
    ("S-A59-03", "NFL.com", "NFL Week 11 schedule", SCHED11, "2026-11-19T06:41:00Z",
     "13 fixtures with date, kickoff time and network for Week 11",
     "The hotel links name venues informally and disagree with the game centre for one fixture."),
    ("S-A59-04", "NFL.com", "NFL Week 10 schedule with final scores", SCHED10,
     "2026-11-19T06:44:00Z",
     "All 14 Week-10 finals with scores, plus the four clubs on a bye",
     "One week only. It is the source of the corrected Chargers at Ravens row."),
    ("S-A59-05", "NFL.com", "Indianapolis Colts at Houston Texans game centre, Week 11",
     GAMECENTER, "2026-11-19T06:50:00Z",
     "The venue string HOUSTON, TX and RELIANT STADIUM, the team comparison, and the four "
     "injury rows per club that the game page exposes",
     "The game page exposes only four injury rows per club, which is why the league injury "
     "report is the availability source and not this page."),
    ("S-A59-06", "NFL.com", "2026 NFL Schedule Release", RELEASE, "2026-11-19T06:49:00Z",
     "The nine international games with their dates and venues, including Week 11 Vikings at "
     "49ers at Estadio Banorte, and the flexible-scheduling notice for Weeks 16, 17 and 18",
     "The landing page prints no publication date."),
    ("S-A59-07", "NFL.com", "Official NFL Game Book, Washington Commanders at New York Giants, Week 10",
     GAMEBOOK_WASNYG, "2026-11-19T06:47:00Z",
     "The actual starting lineups, the substitutions, the players who did not play, the official "
     "Not Active list, the game-day weather and surface, the officials and the final score",
     "One game. It publishes no snap counts."),
    ("S-A59-08", "NFL.com support", "NFL Game Books index", GAMEBOOKS, "2026-11-19T06:47:00Z",
     "The official location of the NFL Game Book documents",
     "An index page. It does not itself carry game data."),
    ("S-A59-09", "NFL Next Gen Stats", "Metric glossary", NGS, "2026-11-19T06:52:00Z",
     "The official set of published tracking metrics, used to check whether an official "
     "per-player play-count series is documented",
     "A glossary of tracking metrics. It does not document a public snap-count series."),
    ("S-A59-10", "NFL Operations", "2026 NFL Rulebook", RULEBOOK, "not read in this session",
     "Cited as the rule context for the onside-kick and kickoff-regime requirement",
     "Not read in this session. Cited as context only; no rule is interpreted here."),
    ("S-A59-11", "NFL.com legal", "Flexible scheduling procedures", FLEX, "not read in this session",
     "Cited as the rule context for the late-season schedule notice reproduced on the schedule page",
     "Not read in this session. The schedule page reproduces the relevant text."),
    ("S-A59-12", "Own5 repository", "Repository results feeds and depth captures reviewed for consistency",
     BLOB + "/nfl-desk-35a1feb2/data/results_feed_2026.csv", "2026-11-19T06:55:00Z",
     "The five results feeds and the two depth captures compared against the official reads of "
     "this session, which produced F-A59-01, F-A59-03 and F-A59-05",
     "Repository artefacts, not official sources. They are reviewed against official pages, not "
     "quoted as fact."),
]

DESK_FIELDS = ["desk_id", "desk_name", "entry_page", "repo_url", "what_it_holds",
               "official_source_links", "flagged_count", "read_only_for_this_session"]

DESKS = [
    ("nfl-desk-a59c762a", "NFL Decision Console (this desk)", "nfl-desk-a59c762a/index.html", BLOB + "/" + "nfl-desk-a59c762a/index.html", 
     "The master requirements register, the dated Week-11 availability capture and its delta, "
     "the opponent-adjusted model and its out-of-sample shadow backtest, the removal-of-luck "
     "panel, the correlations, the leaderboard with signal separated from staking, the "
     "questions and suggestions registers, and the flagged page",
     STANDINGS + "|" + INJ11 + "|" + SCHED11 + "|" + SCHED10 + "|" + GAMEBOOK_WASNYG + "|" + RELEASE,
     11, "no"),
    ("nfl-integration-a620f5a5", "NFL integration hub", "nfl-integration-a620f5a5/index.html", BLOB + "/" + "nfl-integration-a620f5a5/index.html", 
     "The repository-wide hub: the audit register, the questions register, the suggestions "
     "register and the sources register",
     STANDINGS, 14, "yes"),
    ("nfl-market-desk", "NFL market desk", "nfl-market-desk/index.html", BLOB + "/" + "nfl-market-desk/index.html", 
     "The price store and policy, the decision-readiness register, the depth coverage and order "
     "tests, the demotion rules, the control baselines, the personnel ablation and the venues "
     "and schedule announcements",
     STANDINGS, 35, "yes"),
    ("nfl-desk-35a1feb2", "NFL read-and-decide desk", "nfl-desk-35a1feb2/index.html", BLOB + "/" + "nfl-desk-35a1feb2/index.html", 
     "The 150-row 2026 results feed, the requirements master, the injury read delta, the "
     "transactions and reserve-list registers and the Week-11 origination",
     SCHED10, 18, "yes"),
    ("nfl-c98c6270", "NFL depth and availability desk", "nfl-c98c6270/index.html", BLOB + "/" + "nfl-c98c6270/index.html", 
     "The 890-row depth-slot capture with shared and empty slots recorded faithfully, the depth "
     "delta and the replacement depth cross-check",
     "", 14, "yes"),
    ("nfl-desk-e46fb855", "NFL decision-readiness desk", "nfl-desk-e46fb855/index.html", BLOB + "/" + "nfl-desk-e46fb855/index.html", 
     "The 72-row requirements register, the 702-row depth capture including the Houston "
     "not-parsed row and the Patriots partial capture, the price snapshots and the results feed",
     "", 21, "yes"),
    ("nfl-desk-3cb7800c", "NFL decision console", "nfl-desk-3cb7800c/index.html", BLOB + "/" + "nfl-desk-3cb7800c/index.html", 
     "The Week-11 registration capture metadata and the repo check register",
     INJ11, 9, "yes"),
    ("nfl-desk-6cbf25fa", "NFL price and ledger desk", "nfl-desk-6cbf25fa/index.html", BLOB + "/" + "nfl-desk-6cbf25fa/index.html", 
     "The price-snapshot store, the Week-11 origination, the injury point-in-time ledger and the "
     "CI takeover fix",
     SCHED11, 12, "yes"),
    ("nfl-desk-f2e20e96", "NFL decision desk", "nfl-desk-f2e20e96/index.html", BLOB + "/" + "nfl-desk-f2e20e96/index.html", 
     "The Week-10 verified feed, the Week-11 preview read, the pre-registered leaderboard and the "
     "readiness, questions and suggestions registers",
     SCHED10, 12, "yes"),
    ("nfl-desk-38430fe3", "NFL injury review desk", "nfl-desk-38430fe3/index.html", BLOB + "/" + "nfl-desk-38430fe3/index.html", 
     "The first-hand re-read of the official Week-10 injury report, the brief claim checks and "
     "the requirement readiness table",
     INJ10, 11, "yes"),
    ("repo-review", "Repository review", "repo-review/index.html",
     BLOB + "/repo-review/index.html",
     "The desk inventory, the verifier sweep and the irregularity register",
     "", 20, "yes"),
    ("nfl-desk-5c5f4aaf", "NFL desk directory", "nfl-desk-5c5f4aaf/index.html", BLOB + "/" + "nfl-desk-5c5f4aaf/index.html", 
     "The index of every NFL desk folder with its entry page and its flagged-item count",
     "", 2, "yes"),
]


def main():
    os.makedirs(DATA, exist_ok=True)
    tables = [
        ("requirements.csv", REQUIREMENT_FIELDS, REQUIREMENTS),
        ("questions.csv", QUESTION_FIELDS, QUESTIONS),
        ("suggestions.csv", SUGGESTION_FIELDS, SUGGESTIONS),
        ("gates.csv", GATE_FIELDS, GATES),
        ("leaderboard.csv", LEADERBOARD_FIELDS, LEADERBOARD),
        ("pre_registration.csv", PREREG_FIELDS, PREREG),
        ("flagged.csv", FLAG_FIELDS, FLAGS),
        ("sources.csv", SOURCE_FIELDS, SOURCES),
        ("desk_index.csv", DESK_FIELDS, DESKS),
    ]
    for name, fields, rows in tables:
        with open(os.path.join(DATA, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            for r in rows:
                if isinstance(r, dict):
                    rec = r
                else:
                    if len(r) != len(fields):
                        raise SystemExit("%s: row %r has %d fields, expected %d"
                                         % (name, r[:2], len(r), len(fields)))
                    rec = dict(zip(fields, r))
                missing = set(fields) - set(rec)
                extra = set(rec) - set(fields)
                if missing or extra:
                    raise SystemExit("%s: field mismatch %s %s" % (name, missing, extra))
                w.writerow(rec)
        print("%-24s %3d rows" % (name, len(rows)))


if __name__ == "__main__":
    main()
