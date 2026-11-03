# Source and repository audit

**Audit time:** 2026-11-03 UTC · **Scope:** new `nba-own-lines/` and `research/nba-own-lines/` namespaces plus this session's coordination record.

## Official evidence reviewed

| ID | Official source | Values used | Verification |
|---|---|---|---|
| S01 | [NBA Games](https://www.nba.com/games) and individual NBA game pages | 16 matchups, dates, ET tip times, pregame records, game IDs for November 4–5 | Schedule markup transcribed; each CSV row retains its game slug/ID; 32 team-game records automatically match S02 |
| S02 | [NBA 2026–27 advanced team stats](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) | 30 rows: GP/W/L/MIN/OffRtg/DefRtg/NetRtg/PACE/POSS | Both table chunks reviewed; GP=W+L and NetRtg rounding tolerance checked |
| S03 | [NBA standings](https://www.nba.com/standings) | Independent W–L review | All 30 records manually compared; no discrepancy found |
| S04 | [NBA player per-game stats](https://www.nba.com/stats/players/traditional?Season=2026-27&SeasonType=Regular%20Season&PerMode=PerGame) | Selected GP/PTS/REB/AST/3PM | 16 mean checks reconcile game logs to displayed rounded averages |
| S05 | [Anthony Edwards game log](https://www.nba.com/stats/player/1630162/boxscores?Season=2026-27&SeasonType=Regular%20Season) | Complete 4-row current-season log | Dates/IDs/matchups/results/MIN/PTS/REB/AST/3PM transcribed |
| S06 | [Luka Dončić game log](https://www.nba.com/stats/player/1629029/boxscores?Season=2026-27&SeasonType=Regular%20Season) | Complete 7-row current-season log | Both chunks reviewed; same fields transcribed |
| S07 | [Tyrese Maxey game log](https://www.nba.com/stats/player/1630178/boxscores?Season=2026-27&SeasonType=Regular%20Season) | Complete 8-row current-season log | Both chunks reviewed; same fields transcribed |
| S08 | [Shai Gilgeous-Alexander game log](https://www.nba.com/stats/player/1628983/boxscores?Season=2026-27&SeasonType=Regular%20Season) | Complete 7-row current-season log | Both chunks reviewed; same fields transcribed |
| S09 | [Official injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) | Reporting policy and dated PDF links | Point-in-time nature and continuing updates reviewed |
| S10 | [Official 2026-11-03 6:15 PM ET injury PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-03_06_15PM.pdf) | Edwards Out; incomplete team submissions; selected-player review | Both PDF chunks reviewed; non-listing is not inferred as Available |
| S11 | [NBA statistics glossary](https://www.nba.com/stats/help/glossary) | OffRtg/DefRtg/PACE definitions | Model units and formulas documented separately from official definitions |
| S12 | [2026–27 Official NBA Playing Rules](https://ak-static.cms.nba.com/wp-content/uploads/sites/4/2026/10/2026-27-Official-NBA-Playing-Rules.pdf) | Timing/overtime context | Official PDF reviewed; no overtime estimate inferred |

## Line-by-line automated reconciliation

- 30 unique teams and IDs; `GP = W + L`; minutes are at least 48 × GP; NetRtg agrees with OffRtg−DefRtg within displayed-rounding tolerance.
- 16 unique upcoming game IDs with the `00226` season prefix; every slug contains its ID; every record equals S02; all 30 teams appear in the 16-game slate.
- 26 player-game rows equal official GP totals (7 + 4 + 8 + 7); every row links its official `www.nba.com/game/<id>/` page.
- For four players × four statistics, arithmetic means rounded half-up to one decimal equal official per-game values. This includes Maxey AST 42/8 = 5.25 → 5.3 and Edwards PTS 133/4 = 33.25 → 33.3.
- Every source URL is HTTPS on `www.nba.com`, `official.nba.com`, or `ak-static.cms.nba.com`. Every one of the 199 generated body-table rows has an official source/context link.
- Derived lines have probabilities summing to one, symmetric spreads, null market/edge fields and no qualified release. All playable player lines and all combo joint/payout values are null.

## Repository review and preservation

The session read the shared coordination board, repository README, CI workflows, root tests and prior NBA requirements before claiming work. The branch was synchronized with `origin/main`; concurrent NBA audits and dashboards were retained. Only the claimed namespaces and appended `COORDINATION.md` section are changed. CI-locked root `index.html`, `pages/`, `data/research.json`, `scripts/seed.py`, `scripts/build.py`, existing tests and other sessions' labs are untouched.

Existing root tests: **56 passed**. New namespace tests: **16 passed**. Site checker: **11 pages / 199 sourced table rows / 454 links / 16 lines / 0 qualified**. This certifies the new snapshot and generated outputs, not every historical claim in other sessions. F10 explicitly flags that older NFL/NBA source rows were not independently re-transcribed here.

## Irregularities

F01–F11 are published on `nba-own-lines/review.html`: dynamic sources, incomplete availability, Edwards Out, absent market data, small team/player samples, no prospective validation, model assumptions, unresolved combo dependence, limited historical-repo audit scope, and no funded rewards. They are nonblocking for static publication but blocking for strategy qualification.
