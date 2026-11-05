# Executive Summary — Own5 NBA Research Hub

**Date:** 2026-11-05 UTC  
**Session:** 4c43d5e6  
**Status:** Exploratory retrospective research deliverable. No strategy is eligible for betting or rewards.

## Bottom line

The hub produces reproducible NBA research lines, descriptive player signals, correlation/joint-dependence estimates, and a fail-closed strategy competition. It does **not** establish a profitable betting edge. There are no verified sportsbook prices, final November 6 lineups, graded wagers, ROI, CLV, or funded prizes. All six candidate strategies are blocked by validation gates; the leaderboard is unranked and rewards are zero.

## What was directly checked

- All 30 current NBA team records and the completed 2025-26 team table were read from official NBA traditional statistics pages; W/L was cross-checked against official standings.
- 125 stored player-game rows (Luka Dončić 64, Anthony Edwards 61) were compared with re-opened official NBA tables. Per-game means reconcile to the official rounded leaders page.
- The nine November 6 games were read from the official NBA schedule.
- The November 5, 4:00 p.m. official injury report was read; most November 6 teams were not yet submitted, so final availability is blank/held.
- NBA Rule 5, the FanDuel NBA guide, NIST binomial/autocorrelation pages, and the deflated-Sharpe paper were used as rules/operator/method context, not edge proof.

## What was calculated

- **Research lines:** nine November 6 spreads/totals/scores from blended official current/prior team inputs. Primary prior strength K=20 and home adjustment 0; all nine sensitivity variants are disclosed. Market spread/total/odds/edge are blank.
- **Player forecasts:** 460 strictly walk-forward forecast rows at frozen analyst thresholds. Rolling means reduce descriptive MAE versus the last observed value, but **0 of 8** player×stat binary series pass the predictive gate: each has n<100 and no Holm-significant negative Brier difference.
- **Correlations:** same-game points–threes is positive and Holm-significant for both selected players (Dončić r=0.666, Edwards r=0.696; adjusted permutation p=0.004). Lag-1 non-significance is not independence proof.
- **Joint dependence:** Edwards points>25.5 + threes>2.5 has historical joint probability 0.525 versus independent product 0.419 (lift 1.251; Holm-adjusted Fisher p=0.007). Positive lift means multiplying marginals **understates** joint hits. These are research thresholds, not sportsbook props.
- **Luck/power:** at an arithmetic −110 break-even null (0.523810), distinguishing 55% win probability at one-sided α=0.05 and 80% power requires about 2,243 bets by normal approximation; exact binomial power at that n is 0.791890. A 54-test planning family raises the approximate requirement to 5,678. The 30-bet/20-win exact tail is 0.082242, not the inherited 0.17 example.

## Repository audit

- Pinned baseline inventory: 484 files and 67,618 physical lines hashed line by line (updated at final integration to include concurrent PR #40).
- Selected inherited field comparisons: 4,182; 3,490 match, 250 are stale current-season snapshots, 442 remain unverified with blank official values, and 0 unexpected mismatches.
- Inventory/link presence is **not** independent factual verification. Code is tested by behavior; most inherited factual claims remain manual-review.

## Blocking irregularities

High-severity flags include missing market quotes, unavailable final lineups, unverified jurisdiction-specific settlement rules, unmeasured cross-game parlay dependence, and no funded reward pool. Medium/low flags cover retrospective protocol timing, selected-sample limits, stale inherited snapshots, source-layout/access fragility, and inherited overclaims. All are published on the Flagged for Review page with links.

## Competition result

- Eligible strategies: **0 / 6**
- Genuine graded priced bets: **0**
- Rewards paid: **0**
- Monetary prize pool: **blank / unverified**

Future eligibility requires every gate to PASS or be explicitly N/A, genuine timestamped quotes and settlement rules, final availability, adequate clustered sample size, multiplicity-adjusted predictive and economic evidence, and reproducible risk controls. Luck cannot be literally removed; the hub quantifies uncertainty instead.
