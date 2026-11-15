# Flagged for review — Own5 NFL Decision-Readiness & Verification Desk

Non-blocking register of irregularities, data gaps and unverified blanks. Every item is published with
its source link so it can be reviewed. None of these blocks the site: they are labelled rather than
silently corrected or filled.

| ID | Severity | Area | Title | Detail | Action | Source |
|---|---|---|---|---|---|---|
| F-01 | blocking | Price data | nfl.com publishes no spreads, totals or moneylines | No official price exists; gate G2 cannot pass for any strategy; CLV, real-price ROI and demotion triggers are unmeasurable. | Capture an operator price page on a fixed schedule, or accept that no strategy can ever be certified. | https://www.nfl.com/standings/league/2026/REG |
| F-02 | review | Results feed | The pinned mirror lags the official results feed | Of 137 official 2026 finals, the mirror agrees on 136 and disagrees on 0; 1 game is final on nfl.com but unscored in the mirror. | Keep nfl.com as the source of record; treat the mirror as a cross-check only. | https://www.nfl.com/schedules/2026/by-week/ |
| F-03 | open | Price store | MODEL_CLOSE is not yet observed for any market | The close-out price can only exist once the pipeline re-runs closer to kickoff. | Schedule the pipeline to re-run a few hours before kickoff. | https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/price-store.html |
| F-04 | blocking | Injuries | The Week 11 official injury report is not published yet | The Week 11 URL serves the Week 10 report; every Week 11 market is originated with no injury adjustment. | Re-run the pipeline once the league publishes the Week 11 report. | https://www.nfl.com/injuries/league/2026/reg11 |
| F-05 | review | Depth | Depth charts are one club short and one day old | 31 of 32 clubs publish a readable chart; Houston publishes only a raster image. | Re-fetch weekly and fail closed for clubs without machine-readable charts. | https://www.nfl.com/teams/ |
| F-08 | blocking | Player props | No player-prop lines exist from any source in this repo | Neither nfl.com nor the mirror publishes prop lines; the prop-combo family produced no graded bets and gate G7 cannot pass. | Source prop lines with timestamps, or keep the family as an explicit unpriceable entry. | https://www.nfl.com/stats/player-stats/ |
| F-09 | review | Model | The totals model does not beat a naive league-average baseline | Out-of-sample totals MAE 11.0038 vs 11.0235 for predicting the league average every game. | Rebuild the totals model before trusting any total or moneyline. | https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/lines.html |
| F-10 | blocking | Sample size | The certification universe is far smaller than gate G1 requires | Each family produced 4–51 graded bets against a 300-bet minimum. | Accumulate seasons of official results, or lower G1 explicitly and record the risk. | https://www.nfl.com/schedules/2026/ |
| F-11 | review | Model | Home-field advantage is not distinguishable from zero this season | Fitted at ~0.21 pts/game on 130 non-neutral 2026 games; another desk measured +0.47 with a 95% interval of −1.81 to +2.75. | Add a confidence interval and prefer multi-season fits. | https://www.nfl.com/standings/league/2026/REG |
| F-12 | review | Injuries | Most official injury rows carry no game status at retrieval | The Week 10 report lists 326 players; only 25 carry a game status. | Re-read the report on Friday and Saturday; the tracker keys off game status. | https://www.nfl.com/injuries/league/2026/reg10 |
| F-13 | review | Correlations | Every correlation previously published in this repo is inadmissible | Prior desks computed correlations from the nflverse mirror; those values are moved to a withheld register. | Recompute from official inputs only. | https://www.nfl.com/standings/league/2026/REG |
| F-14 | review | Price data | The aggregator reference line has no timestamp | The mirror supplies one line per game per market with no snapshot time; it is neither an open nor a close. | Do not quote a CLV against it; use it only as a difference column. | https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz |

## Unverified blanks in the decision-readiness table

A requirement whose `observed today` value cannot be computed from a verified source is published with a
blank `observed today` cell and an `UNVERIFIED` badge (42 rows). These are requirements whose current
count is not derivable from any official source the desk can read — for example, "how many clubs have a
machine-readable depth chart" for a requirement that has not been swept, or a policy count that is an
owner decision. They are left blank deliberately, not filled.
