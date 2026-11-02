# Validation Gates (T3)

Every strategy must pass **all** gates, in order, before it can enter the leaderboard (see `leaderboard.md`). A strategy that fails any gate returns to candidate status. Gates are designed to remove luck, selection bias, and overfitting from the evaluation — a strategy should only survive if its edge is *skill* (information or modeling advantage), not variance.

| Gate | Name | Rule | Why / Source |
|---|---|---|---|
| G0 | Pre-registration | The full strategy spec (features, bet trigger, staking, markets) is committed to this repo **before** any evaluation data is scored. The spec is frozen; any change restarts the clock. | Writing the hypothesis before touching data is the first defense against overfitting. https://fortraders.com/blog/how-to-avoid-bias-in-backtesting |
| G1 | Parameter budget | ≤ 5 free parameters; ≥ 30 observations per free parameter. | Trades-per-parameter heuristic; more parameters = more freedom to fit noise. https://backtrex.com/en/blog/overfitting-backtesting-detect-prevent ; https://fortraders.com/blog/how-to-avoid-bias-in-backtesting |
| G2 | Walk-forward out-of-sample | Optimize on rolling in-sample windows, test unchanged on the following window, across all available seasons. Holdout season opened **once**. In-sample vs. out-of-sample degradation > 30–40% ⇒ fail. | Walk-forward analysis reduces curve-fitting; divergence beyond ~30–40% indicates overfit. https://backtrex.com/en/blog/overfitting-backtesting-detect-prevent ; https://fortraders.com/blog/how-to-avoid-bias-in-backtesting ; https://wagerproof.ghost.io/walk-forward-vs-backtesting-key-differences/ |
| G3 | CLV gate (the luck remover) | Over ≥ 200 logged bets, mean **de-vigged** CLV must be positive with a bootstrap 95% CI excluding 0. CLV% = (de-vigged closing odds / bet odds) − 1, benchmarked to the sharpest available close. | CLV separates skill from variance far faster than ROI (≈200–500 bets vs. thousands). INDUSTRY convention — exact thresholds flagged for review. https://www.pinnacleoddsdropper.com/blog/closing-line-value ; https://www.sportsbettingoddscalculator.com/guides/closing-line-value ; https://pikkit.com/blog/how-to-track-closing-line-value-clv-in-sports-betting |
| G4 | Multiple-testing control | Report number of strategy variants ever tried. Compute Deflated Sharpe Ratio (DSR) / Probability of Backtest Overfitting (PBO) via CSCV; require PBO < 10% and a selection-aware t-statistic ≳ 3. | Bailey & López de Prado: PBO/DSR correct for selection bias across trials; Harvey–Liu–Zhu propose t > 3 for newly discovered effects. PRIMARY. https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf |
| G5 | Monte Carlo null | Strategy's backtest metric must exceed the 95th percentile of the same metric computed on outcome-shuffled (null) data. | Permutation testing against randomness. https://backtrex.com/en/blog/overfitting-backtesting-detect-prevent |
| G6 | Economic realism | Backtests must use prices actually available at bet time (timestamped), include full vig, and respect realistic limits. No closing-price fills for a strategy that claims to beat the close. | Many "edges" vanish once friction is modeled. https://fortraders.com/blog/how-to-avoid-bias-in-backtesting |
| G7 | Correlation audit (parlays/SGP only) | Joint probability of legs must be computed from a fitted joint distribution — never by multiplying marginals. Negative-correlation leg pairs are prohibited. Parlay EV must be positive **after** the book's correlation tax. | Independence pricing of correlated legs is wrong in both directions. https://nba-prop-bets.com/articles/nba-same/ ; https://oddsindex.com/guides/nba-same-game-parlay-tips |
| G8 | Risk & staking | Fractional Kelly only (≤ ½ Kelly; ¼ Kelly when edge uncertainty is high or positions are correlated). f* = (bp − q)/b per Kelly (1956). Max-drawdown kill-switch pre-committed. | Full Kelly is too volatile when the edge is estimated; half Kelly ≈ 75% of growth at ~25% of the variance. PRIMARY (Kelly 1956, Bell System Technical Journal) + INDUSTRY. https://oddscipher.com/the-codex/kelly/ ; https://marketmath.io/blog/kelly-criterion-guide ; https://expectedvalue.co.uk/blog/kelly-criterion-optimal-bet-sizing/ |

## Gate order and lifecycle

```
Candidate → G0 pre-register → G1–G2 backtest hygiene → G5 null test → G4 multiplicity
          → paper-trade live (timestamped) → G3 CLV over ≥200 bets → G6 realism audit
          → (parlays: G7) → G8 staking plan → LEADERBOARD-ELIGIBLE
```

## Hard rules

1. **No strategy is ever graded on W/L record alone.** Win rate needs 1,000–3,000 bets to mean anything and is heavily luck-contaminated; CLV is the primary grade. (https://www.sportsbettingoddscalculator.com/guides/closing-line-value)
2. **Every logged bet records:** timestamp, market, line & price at bet, de-vigged fair close, stake, and the strategy version hash that produced it.
3. **Unverifiable inputs are blank, never guessed.** If an input (injury status, lineup) can't be confirmed from the official source at bet time, the bet is not placed.
