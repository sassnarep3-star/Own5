# Executive Summary — Evidence-First NBA Line-Origination Desk

**Session:** `61a311c2` · **Snapshot:** 2026-11-05 · **Dashboard:** `nba-research-61a311c2/index.html` · **Repo:** [sassnarep3-star/Own5](https://github.com/sassnarep3-star/Own5)

## Objective

Origin independent NBA lines, identify useful signals across singles, parlays and player-prop combinations, measure dependence instead of assuming it, separate skill from luck as far as the evidence allows, impose mandatory validation gates, and organize strategies as a reward-based leaderboard. Publish a clean GitHub Pages dashboard with official-source links on every table row and a nonblocking **Flagged for Review** page.

## What is actually verified

- **241 canonical rows** carry row-level evidence: 125 historical player-game rows, 29 current player-game rows, 30 prior-season team rows, 30 current team rows, 11 schedule rows, 12 operator quote rows and 4 availability rows. **237 rows have verified values; 4 availability rows are intentionally blank and flagged.** [NBA stats](https://www.nba.com/stats) · [NBA schedule](https://www.nba.com/schedule?date=2026-11-06) · [FanDuel NBA](https://sportsbook.fanduel.com/navigation/nba) · [NBA injury report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf)
- **434 baseline repository files** were inventoried and hashed at commit `54e8dee`. This is an identity/coverage audit, not a claim that every legacy NFL/NBA assertion was re-certified. [Baseline tree](https://github.com/sassnarep3-star/Own5/tree/54e8dee596d49731c3da535a1f77b01cd0c295d5)
- The historical Edwards/Dončić logs were compared field-by-field against official NBA tables: 61 + 64 = 125 rows match. [Edwards log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) · [Dončić log](https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26&SeasonType=Regular%20Season)

## What the desk can do now

- Originate **11 model-only spreads/totals** for Nov 5–6 from verified team pace/efficiency inputs. Home spread uses betting convention: negative = home favorite. Shrinkage `K=10` and `HFA=0` are declared model choices, not fitted NBA constants. [Current advanced table](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) · [NBA glossary](https://www.nba.com/stats/help/glossary)
- Compare two Nov 5 games with a **dynamic FanDuel snapshot**. Example: ORL@PHX model total 229.37 vs market 222.5; MIA@GSW model total 232.70 vs market 236.5. These are line differences, **not executable edges**. [FanDuel NBA](https://sportsbook.fanduel.com/navigation/nba)
- Measure **12 within-player correlations** and **10 threshold-combination frequencies** with moving-block 95% CIs. The strongest selected-player linear associations are PTS×3PM (Dončić 0.666; Edwards 0.696) and PTS×MIN (0.552; 0.596). PTS×AST is near zero in this sample. [Pearson method](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) · [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/eda334.htm)
- Run a chronological exploratory points replay: **47 forecasts, 23 hits / 24 misses, hit rate 0.4894, exact p vs 50% = 0.614567, Bonferroni family-6 p = 1.0**. This provides **no evidence of betting skill**. [Deflated Sharpe / selection-bias method](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)

## What remains blocked

- No closing-line archive, no calibrated win/prop probabilities, no confirmed Nov 6 availability for the selected players, and no measured cross-game parlay dependence. Moneyline probabilities, fair odds, EV, ROI, rank and monetary rewards stay blank. [FanDuel settlement FAQ](https://sportsbook.fanduel.com/navigation/nba) · [NBA injury policy](https://official.nba.com/nba-injury-report-2026-27-season/)
- **0 / 6 strategies qualify.** Gates G01–G12 are fail-closed; current action is `PAPER_RESEARCH_ONLY`. [Project repo](https://github.com/sassnarep3-star/Own5)
- Rewards are **unfunded**. Research reward points are zero until qualification; monetary amounts are blank. [Project repo](https://github.com/sassnarep3-star/Own5)

## Key irregularities flagged

Legacy spread-sign ambiguity, an invalid legacy claim that within-player lag-1 proves cross-game independence, a mislabeled “DSR-style” shrinkage, a non-ASCII duplicate-looking CSV header, partially re-verified legacy 22-game sample, NFL/NBA scope mix, dynamic-source drift, FanDuel/NBA tip-time display mismatch, and official PACE/POSS non-identity. All are published on **Flagged for Review** with source links. [Flagged page](../../nba-research-61a311c2/review.html) · [Baseline repo](https://github.com/sassnarep3-star/Own5/tree/54e8dee596d49731c3da535a1f77b01cd0c295d5)

## Recommended next steps

1. Capture timestamped bet-time and closing quotes for the same official game IDs; do not infer missing prices. [FanDuel NBA](https://sportsbook.fanduel.com/navigation/nba)
2. Refresh the official injury report after Nov 6 submissions; keep blank statuses blank until confirmed. [NBA injury report](https://official.nba.com/nba-injury-report-2026-27-season/)
3. Build a matched cross-game leg sample before pricing parlays; never substitute within-player lag-1 for cross-game independence. [Pearson method](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)
4. Accumulate a prospective paper ledger with all trials registered, then apply exact tests, block-bootstrap bounds and multiplicity control before any leaderboard rank or reward. [Deflated Sharpe method](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
