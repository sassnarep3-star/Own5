# Flagged for Review

**Session `26d4cafb` - snapshot 2026-11-12 UTC - NFL 2026 Week 10**

> Generated directly from `nfl-desk-26d4cafb/data/` by `engine.py`. Every row links to the official source it was read from. Values that could not be confirmed from an official source are left blank and listed on the Flagged for Review page.

## Flagged for review

| # | Severity | Category | Item | Issue | Value left blank | Discovery | Status |
|---|---|---|---|---|---|---|---|
| FLG-01 | high | Market data | Sportsbook spreads, totals, moneylines | nfl.com publishes no sportsbook prices; the repo's market numbers are an ESPN/DraftKings scrape. | market_spread, market_total, market_ml, edge, CLV on every Week 10 line | DISC-01 | open |
| FLG-02 | medium | Market data | Player-prop lines | No official player-prop lines exist; only official player statistics are published. | prop line, prop edge, prop price | DISC-01 | open |
| FLG-03 | high | Injuries | Week 10 official game statuses for the 12 Sunday/Monday games | Final game-status designations are not issued until Friday/Saturday; the 2026-11-12 snapshot publishes them only for TNF and the early Munich game. | official_game_status on all DNP rows for W10-03..W10-14 (except confirmed IR/Out) | DISC-02 | open |
| FLG-04 | medium | Injuries | Per-player snap-weighted EPA / WAR replacement value | No official NFL source publishes individual snap-weighted value; only team-level PF/PA are official. | snap_epa_official on all 46 injury/depth rows | DISC-04 | open |
| FLG-05 | medium | Depth charts | Blank 2nd-string depth-chart cells | 49ers (LCB2, NB2), Steelers (LOLB2 behind Watt, DT2 behind Heyward), Dolphins (QB2 behind McCord, K), Colts (CB2 behind Gardner), Browns (RG2, WILL2) publish no backup in that slot. | backup_2nd / backup_3rd / backup_4th on the affected rows | DISC-03 | open |
| FLG-06 | high | Injuries | LAC@BAL Monday-night injury table shows 'No Injuries Reported' | The official Week 10 table is in its pre-Thursday window and excludes IR players, so it reads as if BAL is healthy while QB1 Jackson and QB2 Huntley are both on IR. | n/a - contradiction documented, not filled in | DISC-02 | open |
| FLG-07 | low | Position mapping | Ben Brown listed as C on nfl.com but LG1 and C2 on patriots.com | The official league injury report and the official club depth chart disagree on the position label. | single canonical position label | DISC-03 | open |
| FLG-08 | low | Props | Rashee Rice played only 5 of 8 KC games | Partial-season availability makes the KC QB-to-target correlation sample smaller than the team's game count. | n/a - sample size disclosed instead | DISC-05 | open |
| FLG-09 | medium | Depth charts | Houston Texans depth chart is a raster image with zero HTML rows | houstontexans.com/team/depth-chart embeds only a static image, so no depth row can be read programmatically. | all HOU 2nd/3rd/4th string cells | DISC-03 | open |
| FLG-10 | low | Roster lag | Kirk Cousins trade not yet reflected on vikings.com depth chart | The official club page lags a confirmed transaction by several days. | affected MIN backup cells | DISC-03 | open |
| FLG-11 | low | Roster lag | Micah Parsons listed LP on nfl.com but absent from the Nov 10 packers.com table | The league injury report and the club depth chart disagree on a starter's presence. | affected GB depth cells | DISC-03 | open |
| FLG-12 | medium | Neutral sites | W4 IND@WSH and W6 HOU@JAX show a 9:30 AM ET international window with no confirmed venue | The official schedule page does not state the venue, so neutral-site status cannot be confirmed. | neutral flag for those two games; sensitivity reported both ways | DISC-06 | open |
| FLG-13 | low | Rewards | Leaderboard prize pool | No funded prize pool or written payout rule exists; prior reward tiers carried no performance data. | pool_size, payout_rule on every leaderboard row | DISC-09 | open |
| FLG-14 | low | Weather | Weather, travel distance and altitude | nfl.com publishes no official weather or travel dataset for Week 10, including the Munich neutral-site game. | weather_adjustment on every Week 10 line | DISC-07 | open |
| FLG-15 | low | Rules | 2026 kickoff/onside outcome rates | The 2026 rulebook changed dynamic-kickoff and onside rules, but no official 2026 outcome rates are published yet. | kickoff_environment_adjustment | DISC-08 | open |
| FLG-16 | medium | Sample size | Player-prop correlation sample covers 6 teams / 50 team-games | The official player-log pull covers CIN, DET, DAL, BUF, GB and KC, not all 32 teams. | league-wide prop correlation matrix | DISC-05 | open |
