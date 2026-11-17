# Verification log

**Date checked:** 2026-11-17 (UTC date). Exact retrieval time was not exposed by the page retriever, so it is not recorded. A page's successful retrieval is not treated as evidence for fields it does not contain.

| Source ID | Official URL | Check result | Used for |
|---|---|---|---|
| NFL-WEEK12-SCHEDULE | https://www.nfl.com/schedules/2026/by-week/week-12 | Retrieved; page rendered the 2026 Week 12 schedule. No full fixture transcription in this session. | Current schedule route; context only, not prices. |
| NFL-WEEK9-SCHEDULE | https://www.nfl.com/schedules/2026/by-week/week-9 | Retrieved; page shows Week 9 fixtures/results and Game Center links. | Citation check for an existing suggestion; schedule is not a regression/coefficient source. |
| NFL-STANDINGS-2026 | https://www.nfl.com/standings/league/2026/REG | Retrieved; page rendered the 2026 league standings. | Official result/standing source; no team numbers copied into this hub. |
| NFL-INJURY-WEEK10 | https://www.nfl.com/injuries/league/2026/reg10 | Retrieved; Week 10 report visible. The retrieved section lists Kerby Joseph, Cade Mays and D.J. Reed as Out. | Recheck of the specific Detroit designation claim for Week 10 only. |
| NFL-INJURY-REQUESTED-WEEK12 | https://www.nfl.com/injuries/league/2026/reg12 | The retrieved page title/body identify Week 10, not Week 12. | Flag wrong-week response; no Week 12 values accepted. |
| NFL-GAMECENTER-RAMS-CARDINALS-W10 | https://www.nfl.com/games/rams-at-cardinals-2026-reg-10 | Retrieved; page shows a final score, location/stadium and Game Book PDF link. | Identify official per-game source route. |
| NFL-GAMEBOOK-RAMS-CARDINALS-W10 | https://static.www.nfl.com/image/upload/v1794854921/gamecenter/ab78a133-4feb-11f1-abca-2c54536568a9.pdf | Retrieved and parsed as PDF. Includes Lineups, Did Not Play, Not Active, final statistics and game-time conditions; contains a written-permission use notice for other use of the summary/play-by-play. | Actual starter/status source candidate; rights gate and postgame-weather distinction. |
| NFL-TEAMS-32 | https://www.nfl.com/teams/ | Retrieved; page title identifies official sites of all 32 teams. | Define the 32-club coverage requirement; not proof of chart format. |
| TEXANS-DEPTH-CHART | https://www.houstontexans.com/team/depth-chart | Retrieved; page labels chart “Unofficial Depth Chart” and renders the chart as an image. | Flag image-only source; no visual transcription. |
| PACKERS-DEPTH-CHART | https://www.packers.com/team/depth-chart | Retrieved; HTML table includes jersey-number-prefixed player cells and date “Unofficial, Nov. 10, 2026.” | Parser/raw-string test example; no rank inferred. |
| NFL-TRANSACTIONS-INDEX | https://www.nfl.com/transactions/ | Retrieved; official index exposes transaction categories. | Find official transaction source path. |
| NFL-TRANSACTIONS-RESERVE-NOV2026 | https://www.nfl.com/transactions/league/reserve-list/2026/11 | Retrieved; November reserve-list table includes dated Reserve/Injured entries, including Malik Willis on 11/10. | Demonstrate a dated reserve-list source; older captures remain unchanged. |
| NFL-SCHEDULE-ANNOUNCEMENT-2026 | https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced | Retrieved; release title and page state May 14, 2026. | Locate dated announcement to sit beside live schedule. |
| NFL-RULEBOOK-2026 | https://operations.nfl.com/rules-officiating/2026-nfl-rulebook | Retrieved; 2026 change table lists Rule 6-1-6 on onside kicks. | Version rule-regime inputs; no predictive claim. |
| FANDUEL-FOOTBALL-RULES | https://support.fanduel.com/s/article/Betting-football-with-FanDuel | Retrieved; operator help describes possible markets, location/game availability and settlement rules. | Example operator settlement context only; not odds or a local availability claim. |
| NWS-API-DOCUMENTATION | https://www.weather.gov/documentation/services-web-api | Retrieved; describes forecasts, alerts and observations via the API. | Candidate official forecast source; no fixture forecast was collected. |
| NFL-SNAP-COUNT-ATTEMPT | https://www.nfl.com/stats/player-stats/category/defense/2026/REG/all/defensivesnaps/desc | This particular route returned 404. | Record the failed route without claiming no official snap-count source exists. |

## Reproducible local checks

- `nfl-desk-e46fb855/data/price_snapshots.csv`: checked snapshot types and populated cells; its market-open and market-close quote cells are blank. This is repository evidence, not an official odds record.
- `nfl-desk-e46fb855/data/leaderboard_signal.csv`: checked stored certified/proper-score fields; no family in that snapshot is marked certified and proper-score status is non-computable without a benchmark price. This does not constitute a new backtest.
- `nfl-desk-e46fb855/data/injuries.csv`: checked the three Detroit names against the official Week 10 report; their game-status values are Out in the cited snapshot.
- Generated review pages are rebuilt from JSON. `verify.py` checks source-domain allowlists, source IDs, table-row links, internal links and determinism. Unit tests do not make a network claim.

## Limitations

This log does not claim a full 32-team depth sweep, a complete game-book archive, current Week 12 injury coverage, official snap-count coverage, current operator odds, source reuse permission, full-season fixture venue transcription, a multi-season injury calibration, or any strategy skill. All remain blank/blocked in the public review hub.
