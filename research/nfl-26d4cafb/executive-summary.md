# Executive Summary

**Session `26d4cafb` - snapshot 2026-11-12 UTC - NFL 2026 Week 10**

> Generated directly from `nfl-desk-26d4cafb/data/` by `engine.py`. Every row links to the official source it was read from. Values that could not be confirmed from an official source are left blank and listed on the Flagged for Review page.

## Headline numbers

| Metric | Value |
|---|---|
| Completed games in official ledger | 136 |
| Games re-fetched after the repo's 2026-11-02 freeze | 16 |
| Standings reconciliation | 32/32 teams, 0 mismatches |
| Empirical home-field advantage | -0.054 pts (n=130, p=0.963127) |
| Home / away records | 64 home W / 71 away W / 1 T |
| Week 10 lines originated | 14 |
| Injury / depth rows tracked | 46 |
| Player game logs | 50 |
| QB season checksums verified | 6, 0 mismatches |
| Strategies passing all 10 gates | 2 of 10 |
| Open flagged items | 16 |

## Findings that should change decisions

1. **The repository's NFL boards are 16 games stale.** Four boards (root `index.html`, `own5-desk/`, `line-lab/`, `nfl-strategy-lab/`) are frozen at 2026-11-02 and are missing Week 8 Monday Night Football and all 15 Week 9 games. All 16 were re-fetched verbatim from NFL.com and merged; the resulting 136-game ledger reconciles **32/32** teams to [nfl.com/standings](https://www.nfl.com/standings/) with zero mismatches.
2. **2026 home-field advantage is statistically indistinguishable from zero.** The empirical value on 130 non-neutral games is -0.054 points (95% CI [-2.3367, 2.2291], p=0.963127). Prior boards assumed +2.0; on the matched sample that assumption produced a margin bias of **5.346 points**.
3. **Baltimore is starting its third-string quarterback on Monday night**, while the official Week 10 injury table still reads "No Injuries Reported" for that game because IR players are excluded and the report is in its pre-Thursday window (FLG-06).
4. **Two of ten strategies clear all ten validation gates** after Holm-Bonferroni family-wise control and the Deflated Sharpe Ratio. The other eight are explicitly blocked or marked not evaluable, not silently dropped.
5. **Selective skill is NOT established.** Accuracy across confidence terciles is 0.3793 / 0.8276 / 0.7241, which is not monotone, so the highest-confidence bucket does not beat the middle one. The engine reports this rather than claiming selectivity.
6. **No official market or player-prop lines exist.** NFL.com publishes none, so every market, price, edge and CLV column is deliberately left blank and flagged (FLG-01, FLG-02) rather than sourced from a third-party scrape.

## Requirements coverage

| # | Area | Requirement | Deliverable | Status |
|---|---|---|---|---|
| REQ-01 | Repo review | Review the repository line by line, verifying against official trusted sources, providing links for manual review. | Repo Audit page (RA-01..RA-12) with an official source link on every finding. | done |
| REQ-02 | Irregularities | Flag any irregularities discovered during the review. | Flagged for Review page (FLG-01..FLG-16) + data/flagged.csv. | done |
| REQ-03 | Suggestions | Dedicated Suggestions section with improvement proposals and selectable paths, so a reviewer chooses the path BEFORE any change is implemented. | Suggestions page (SUG-01..SUG-12) + Decision Paths (PATH-A..PATH-D); zero site-wide changes implemented. | done |
| REQ-04 | Pre-decision questions | Clear list of questions, known information, missing information and answers required before a decision is reasonable. | Pre-Decision page (Q-01..Q-14). | done |
| REQ-05 | Discovery | Suggestions to discover the missing information. | Discovery Actions (DISC-01..DISC-10) grouped against each open question. | done |
| REQ-06 | Line origination | Originate independent NFL lines (spread, total, moneyline) for the current Week 10 board. | 14 originated W10 lines with full derivation columns. | done |
| REQ-07 | Signals | Research and develop strategies for generating useful signals. | Signal register (SIG-01..SIG-14) with provenance and verification status. | done |
| REQ-08 | Leaderboard competition | Treat signal strategies as a leaderboard competition that rewards top performers across single bets, parlays and player-prop combos. | Walk-forward OOS leaderboard with reward tiers. | done |
| REQ-09 | Validation gates | Each strategy must pass validation gates before it is ranked or rewarded. | 10 fail-closed gates (G-01..G-10) evaluated per strategy. | done |
| REQ-10 | Correlation values | Determine correlation values, including player-prop combos and joint probability bounds. | Team-level and player-prop Pearson r matrix + combo lift + Frechet-Hoeffding bounds. | done |
| REQ-11 | Luck vs skill | Remove luck from the equation and build selectively skill-based strategies. | Exact Poisson-binomial p-values against per-pick nulls, Brier skill score, Deflated Sharpe Ratio, Holm-Bonferroni family-wise control, selectivity trend test. | done |
| REQ-12 | Injury & depth | Track injuries and identify offensive and defensive lineup deficiencies where 2nd, 3rd or 4th string backups replace starters. | 46-row Offense/Defense starter-to-backup register (INJ-01..INJ-46) with active-string tier. | done |
| REQ-13 | Executive summary + site | Executive summary and a clean dashboard-style live GitHub Pages site with a landing page and category subpages, all findings in readable tables. | 18-page dashboard site under /nfl-desk-26d4cafb/ + research/nfl-26d4cafb/*.md dossier. | done |
| REQ-14 | Verification & coordination | Verify every table row against an official source; leave unconfirmed values blank and flagged. Coordinate via COORDINATION.md, open a PR, merge without waiting, confirm deployment. | verify.py line-by-line checker, COORDINATION.md log, PR + merge + live Pages confirmation. | done |

## What is still missing

| # | Severity | Category | Item | Value left blank | Discovery | Status |
|---|---|---|---|---|---|---|
| FLG-01 | high | Market data | Sportsbook spreads, totals, moneylines | market_spread, market_total, market_ml, edge, CLV on every Week 10 line | DISC-01 | open |
| FLG-02 | medium | Market data | Player-prop lines | prop line, prop edge, prop price | DISC-01 | open |
| FLG-03 | high | Injuries | Week 10 official game statuses for the 12 Sunday/Monday games | official_game_status on all DNP rows for W10-03..W10-14 (except confirmed IR/Out) | DISC-02 | open |
| FLG-04 | medium | Injuries | Per-player snap-weighted EPA / WAR replacement value | snap_epa_official on all 46 injury/depth rows | DISC-04 | open |
| FLG-05 | medium | Depth charts | Blank 2nd-string depth-chart cells | backup_2nd / backup_3rd / backup_4th on the affected rows | DISC-03 | open |
| FLG-06 | high | Injuries | LAC@BAL Monday-night injury table shows 'No Injuries Reported' | n/a - contradiction documented, not filled in | DISC-02 | open |
| FLG-07 | low | Position mapping | Ben Brown listed as C on nfl.com but LG1 and C2 on patriots.com | single canonical position label | DISC-03 | open |
| FLG-08 | low | Props | Rashee Rice played only 5 of 8 KC games | n/a - sample size disclosed instead | DISC-05 | open |
| FLG-09 | medium | Depth charts | Houston Texans depth chart is a raster image with zero HTML rows | all HOU 2nd/3rd/4th string cells | DISC-03 | open |
| FLG-10 | low | Roster lag | Kirk Cousins trade not yet reflected on vikings.com depth chart | affected MIN backup cells | DISC-03 | open |
| FLG-11 | low | Roster lag | Micah Parsons listed LP on nfl.com but absent from the Nov 10 packers.com table | affected GB depth cells | DISC-03 | open |
| FLG-12 | medium | Neutral sites | W4 IND@WSH and W6 HOU@JAX show a 9:30 AM ET international window with no confirmed venue | neutral flag for those two games; sensitivity reported both ways | DISC-06 | open |
| FLG-13 | low | Rewards | Leaderboard prize pool | pool_size, payout_rule on every leaderboard row | DISC-09 | open |
| FLG-14 | low | Weather | Weather, travel distance and altitude | weather_adjustment on every Week 10 line | DISC-07 | open |
| FLG-15 | low | Rules | 2026 kickoff/onside outcome rates | kickoff_environment_adjustment | DISC-08 | open |
| FLG-16 | medium | Sample size | Player-prop correlation sample covers 6 teams / 50 team-games | league-wide prop correlation matrix | DISC-05 | open |
