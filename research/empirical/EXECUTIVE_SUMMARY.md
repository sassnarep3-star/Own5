# Executive Summary — OWN5 NFL Line Origination

**Date:** 2026-11-02 · **Scope:** NFL regular season, 2006–2025 backtest, 2026 live board
**Status:** research complete; **0 of 7 strategies validated**

## Bottom line

We built a complete line-origination and validation pipeline, then used it to test whether we could beat
the NFL closing market. **We could not.** Our model prices 4,991 games walk-forward and
learns real team strength (correlation 0.814 with the market spread), but the
closing line is more accurate on every metric we measured. All seven strategies failed at least one of ten
hard validation gates. No reward tier is awarded and no profitable edge is claimed.

One robust, actionable finding did survive: **same-game player props are materially correlated**, and naive
parlay pricing gets that combination wrong.

## What was built

| Component | Result |
|---|---|
| Games priced walk-forward | 4,991 (2006–2025) |
| Own lines originated | spread, total, moneyline + team power ratings |
| Strategies graded | 7 (singles, cross-game parlays, same-game combos) |
| Correlation pairs measured | 12 with week-clustered bootstrap CIs |
| Official score verification | 80/80 exact matches vs NFL.com |
| Hard validation gates | 10, all required |
| Strategies passing all gates | **0** |

## Model vs market

| Metric | Ours | Market | Better |
|---|---|---|---|
| Spread RMSE | 13.6276 | 13.1988 | Market |
| Total RMSE | 13.6244 | 13.3006 | Market |
| Win-prob Brier | 0.22232 | 0.21009 | Market |

The standard two-way hold at −110/−110 is 4.76%. A strategy must beat that
before any question of skill arises. None did.

## The positive finding: correlated player props

A quarterback's passing-yards over and his top receiver's receiving-yards over are **not independent**:

- φ = **0.249**
- Joint hit rate exceeds the naive product by **6.1 percentage points**
- Independence is rejected by the bootstrap interval
- The lift persists out-of-sample in **every** season tested (2016–2021), mean theoretical EV
  **+0.332** units per unit against a naively-priced book

**Critical caveat:** real sportsbooks already shade correlated same-game legs. This measures the size of the
pricing error, not a price we can necessarily obtain. No prop ROI is claimed, because no official prop lines
exist to grade against.

Cross-game legs, by contrast, tested close to independent — multiplying probabilities there is defensible.

## Removing luck

Six independent checks were applied: break-even computed from actual prices, exact binomial tests,
week-clustered bootstrap CIs, Benjamini–Hochberg false-discovery control, deflated Sharpe ratio against a
best-of-N noise hurdle, and chronological era splits.
The best point estimate was S4_division_dog at +0.66% ROI — inside its confidence interval of zero and not significant.

## Integrity position

- Historical inputs are **third-party**, not official. 80 games were re-verified
  line-by-line against NFL.com with a 100% exact-match rate; that is a sample, not a census, so gate G9
  blocks promotion for every strategy.
- **No official source publishes betting lines.** All prices are third-party consensus, declared throughout.
- **No player-prop prices were invented.** Prop lines are originated in-repo as trailing medians.
- 12 flagged items are published on the Flagged for Review page with source links.

## Recommended next steps

1. Expand official verification toward a census of the backtest universe (unblocks G9).
2. Add injury, quarterback and weather features — the clearest gap in model accuracy.
3. Extend player data past 2021 and re-test whether the prop correlation still holds.
4. Obtain timestamped prop prices to test whether the correlation gap is actually capturable.
5. Pre-register any new strategy before grading it, to keep FDR control meaningful.

---
*Research output, not betting advice. Luck cannot be removed from outcomes; it can only be bounded.*
