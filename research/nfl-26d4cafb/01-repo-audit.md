# Repository Audit

**Session `26d4cafb` - snapshot 2026-11-12 UTC - NFL 2026 Week 10**

> Generated directly from `nfl-desk-26d4cafb/data/` by `engine.py`. Every row links to the official source it was read from. Values that could not be confirmed from an official source are left blank and listed on the Flagged for Review page.

## Findings

| # | Severity | Area | Path | Finding | Impact | Recommendation | Status |
|---|---|---|---|---|---|---|---|
| RA-01 | high | Root index | index.html, EXECUTIVE_SUMMARY.md | Root index.html is NFL-dated 2026-11-02 while root EXECUTIVE_SUMMARY.md is NBA-dated 2026-11-11, across 20+ mixed-domain subsites (nba-*, sf-rent-*, nfl-*). | A reviewer landing on the root page sees two different sports and two different dates with no domain separation. | SUG-07 (PATH-B) | verified |
| RA-02 | high | Data freshness | index.html, own5-desk/, line-lab/, nfl-strategy-lab/ | All four NFL boards are frozen at 2026-11-02 and are missing 16 completed games (Week 8 MNF CHI@SEA plus all 15 Week 9 games). | Every line, rating and leaderboard on those boards is computed on a stale ledger. | SUG-01 (PATH-A) | verified |
| RA-03 | medium | Documentation accuracy | README.md, data/games_2026.json | README.md describes line-lab as a 'W1-9 game log' whereas games_2026.json holds 120 completed finals (Weeks 1-8) plus 16 unplayed 0-0 'scheduled' records. | A reviewer trusting the README will over-count nine weeks of results. | SUG-02 (PATH-A) | verified |
| RA-04 | high | Backtest provenance | data/backtest_results.csv, data/correlation_*.csv, data/luck_skill.csv | Backtest, correlation and luck/skill tables rely on third-party GitHub datasets (tobycrabtree/spreadspoke assuming a flat -110 price; brianfoshee/nfl-play-by-play-data). | Leaderboard ROI and correlation values are not reproducible from any official source. | SUG-05 (PATH-A) | flagged |
| RA-05 | high | Ingestion correctness | data/standings_2026.json, data/lines_upcoming_2026.json, data/futures_superbowl_2026.json | ESPN/DraftKings ingestion dropped ties (NYG 4-2 and WSH 2-4 instead of 5-2-1 and 2-5-1), produced 3 malformed open-spread tokens, and truncated Super Bowl futures at 16 of 32 teams. | Standings cannot reconcile to nfl.com; futures coverage is half the league. | SUG-03, SUG-10 (PATH-B/PATH-A) | flagged |
| RA-06 | high | Model specification | data/model_lines_2026_wk9.csv, data/own5_desk/derived_lines.json | Prior Week 9 originators disagreed on HFA (+2.0 vs 0.0 with k=8 shrinkage vs Pythagorean) and omitted starter injury/IR adjustments entirely, pricing BAL as healthy with Lamar Jackson on IR; JAX won 33-10. | Two different spreads for the same game, and the largest single-game error class is unmodelled. | SUG-04 (PATH-A) | verified |
| RA-07 | medium | Injury data | nfl.com/injuries/league/2026/reg10 | The official Week 10 injury table displays 'No Injuries Reported' for the Monday-night LAC@BAL game, because the report is in its pre-Thursday window and IR players are excluded from it. | A naive reader concludes BAL is fully healthy; both BAL QB1 and QB2 are in fact on IR. | SUG-04 (PATH-A) | verified |
| RA-08 | medium | Depth charts | Official club /team/depth-chart pages | Club depth charts carry 'unofficial' disclaimers, one is raster-only, several leave backup cells blank and several lag transactions. | 2nd/3rd/4th-string identification cannot be fully automated or fully trusted from club pages alone. | SUG-04 (PATH-A) | verified |
| RA-09 | low | Broken citation | nfl-decision-desk/ (sibling session) | The cited operations.nfl.com 2017 injury-report policy URL returns HTTP 404. | The claimed governance source cannot be opened by a reviewer. | SUG-11 (PATH-B) | verified |
| RA-10 | medium | Coverage gap | index.html, own5-desk/, line-lab/, nfl-strategy-lab/ | No Nov-2 subsite has a dedicated Suggestions/Paths section, a Pre-Decision Questions/Discovery section, or Offense/Defense 2nd-4th string depth tracking. | A reviewer has no structured place to choose an implementation path or see what is missing. | SUG-03, SUG-04 (PATH-B/PATH-A) | verified |
| RA-11 | high | Market data availability | All NFL boards | nfl.com publishes no spreads, totals, moneylines or player-prop lines, so no market column can be verified against an official source. | Edge and CLV are unverifiable; any market number is third-party. | SUG-03 (PATH-B) | flagged |
| RA-12 | medium | Parallel sessions | nfl-decision-desk/** | Sessions d0343637, 38a1fc27 and e413f933 all claimed overlapping scope on nfl-decision-desk/**. | Risk of silently overwritten or duplicated work. | SUG-12 (PATH-D) | verified |

## Verification performed

- Recomputed all 32 teams' W/L/T/PF/PA from the merged 136-game ledger and compared to [nfl.com/standings](https://www.nfl.com/standings/): 0 mismatches.
- Re-fetched Week 8 MNF and all 15 Week 9 finals from [nfl.com/schedules/2026/by-week/week-9](https://www.nfl.com/schedules/2026/by-week/week-9) and merged them into the ledger.
- Verified 6 quarterbacks' game-by-game passing yards against the official season totals on [nfl.com/stats/player-stats](https://www.nfl.com/stats/player-stats/): 0 mismatches.
