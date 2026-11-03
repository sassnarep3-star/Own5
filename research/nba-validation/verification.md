# NBA validation desk — evidence review, 2026-11-03 UTC

## Scope and claim discipline

This is an additive review, not a claim to have independently verified every historical NFL/NBA statement in this multi-session repository. Existing outputs are preserved. The new desk links all earlier category sites and records their verification limitations. A URL-presence test is not factual verification.

## Official source checks performed in this session

1. https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26 — fetched chunks 0 and 1. Compared each of the ten existing CSV rows with the displayed Match Up, W/L, MIN, PTS, 3PM, REB and AST fields. Dates, opponents, game IDs and all listed fields match. Displayed minutes are integer minutes, not reconstructed seconds. Source page was season-filtered; the profile header's current PPG was not used.
2. https://official.nba.com/nba-injury-report-2026-27-season/ — fetched chunk 0. Verified 5 p.m. local day-before reporting deadline except second back-to-back games; 1 p.m. local same-day deadline for second back-to-back games; continual updates. No individual injury PDF or player status asserted.
3. https://www.nba.com/stats/help/glossary — fetched chunk 0. Verified %3PA is percentage of team three-point attempts while on court and %AST is percentage of team assists while on court. This supports feature definitions only, not predictive value.

## Row-level sample checks

Columns checked for every row: game_id, date, opponent, result, minutes, points, threes, rebounds, assists. Official source is the season-filtered player log above; game-specific official links are retained in the CSV and rendered data table.

- 0022501178: 2026-04-10 HOU W 27 22 3 2 3 — match
- 0022501121: 2026-04-03 PHI L 26 8 0 2 3 — match
- 0022501095: 2026-03-30 DAL W 23 17 2 2 4 — match
- 0022500976: 2026-03-15 OKC L 37 19 2 6 5 — match
- 0022500966: 2026-03-13 GSW W 37 42 4 8 5 — match
- 0022500952: 2026-03-11 LAC L 35 36 3 2 5 — match
- 0022500946: 2026-03-10 LAL L 31 14 1 2 4 — match
- 0022500915: 2026-03-07 ORL L 32 34 5 3 2 — match
- 0022500903: 2026-03-05 TOR W 34 22 5 4 3 — match
- 0022500890: 2026-03-03 MEM W 37 41 7 6 2 — match

## Irregularities

- Root landing page is NFL-oriented; standalone NBA landing page avoids overwriting shared outputs.
- COORDINATION contains stale date and an older in-progress task alongside later publication records. Treat appended dated records as scoped history, not a universal verified status.
- Ten selected games for one player cannot establish a deployable NBA strategy. No random-sample confidence claim is made.
- Historical source-link checks alone do not certify every old factual statement. Older NFL numerical claims and third-party material are not re-certified here.
- No timestamped bookmaker quote/settlement dataset or prospective ledger is available in the reviewed NBA scope. Current lines, ROI, CLV, phi and reward amounts remain blank.
- Research methods and reward rules are project proposals, not NBA-endorsed facts. Official links on those rows indicate the relevant input source only.

## Reproducibility

New build imports the existing sample computation without changing its scope. Pearson values are derived from independently rechecked inputs, not officially published correlation estimates. Unit tests use synthetic values solely to test mathematics, never as evidence of NBA performance. Structural audit checks every generated table body row for an official NBA URL and resolves local links. External source verification is limited to the fetched pages above; a local link check does not assert every external deep link returns HTTP 200.
