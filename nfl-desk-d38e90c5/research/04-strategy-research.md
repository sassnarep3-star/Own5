# Strategy research: single bets, parlays and player-prop combinations

Every strategy below states its selection rule, the price it is priced at, the measured result and
the gate status. The full gate table is in `data/gate_decisions.csv`; the leaderboards are in
`data/leaderboard_signal.csv` and `data/leaderboard_staking.csv`.

**Pricing rule for this desk.** No primary market price is available, so every strategy that can be
measured is priced at **the model's own fair price**. At a fair price the expected profit is exactly
zero, so the realised result of any of these strategies is *luck*, not skill. That is the reason the
two leaderboards are separate and the reason a staking run can never promote a strategy.

## S1 - Model spread favourite (single bet)

* **Rule:** take the side the model prefers when `|model margin| >= 3.5` points.
* **Price basis:** the model's own fair price for that side (cover probability from the model's
  margin distribution).
* **Measured:** 16 bets, 50.0% hit rate, -2.19 units realised, ROI -13.7% per bet at the model's own
  fair price.
* **Reads:** the loss is not luck - it is a *signal* defect, and the leaderboard exposes it. The
  model's cover probability is derived from the margin noise scale that was calibrated on win/loss
  outcomes, and it is overconfident for cover outcomes, where the model's margin error (MAE 10.24
  points) is large relative to a 3.5-point threshold. The honest use of this strategy is as a
  calibration exercise, not as a recommendation.

## S2 - Model moneyline favourite (single bet)

* **Rule:** back the model side when the calibrated win probability is at least 0.60.
* **Price basis:** model fair price.
* **Measured:** 37 bets, 70.3% hit rate, +0.12 units realised - a result that sits **inside** the
  95% luck band of +/-7.90 units, so it is indistinguishable from luck. That is exactly the case the
  gate is built to catch, and it is why the strategy stays in PAPER.

## S3 - Two-leg parlay of model favourites (parlay)

* **Rule:** in each week, pair the two most confident model sides into a two-leg parlay.
* **Price basis:** the combined model fair price (product of the leg probabilities).
* **Measured:** 17 parlays, 41.2% hit rate, -3.32 units realised, also inside the luck band.
* **Reads:** parlay construction adds variance without adding skill when the legs are priced at fair
  probabilities. The realised loss is larger than either single-bet strategy over a comparable
  number of bets because parlay outcomes are rare events.
* **Research note:** parlay construction adds variance without adding skill when the legs are priced
  at fair probabilities. A parlay only becomes interesting when the legs are priced *below* their
  model probabilities, which requires a real price feed. The repo's third-party price work
  (`nfl-desk-26d4cafb/data/oos_week9.csv`, labelled "ESPN/DraftKings -- THIRD PARTY") shows what that
  looks like, but those numbers are not official and are therefore not used here.

## S4 - Value versus the market line (single bet, blocked)

* **Rule:** bet where the model line differs from the market line by at least a point.
* **Status:** blocked. NFL.com publishes no market line, and no operator price feed was reachable from
  this environment. The market line, market price, difference, CLV and ROI columns are blank and
  flagged. This is the single highest-value unlock in the whole desk: it converts the pack from a
  model study into a betting record.

## S5 - Replacement-depth adjusted line (single bet, prospective)

* **Rule:** shift the model line when a starter is Out and the next in line at that position is a
  third- or fourth-string reserve.
* **Status:** paper track from Week 10. The official NFL injury report is a *current week* page -
  there is no official archive of historical Week 1-9 injury reports on nfl.com - so a
  walk-forward backtest of a depth adjustment is not possible with official inputs today.
* **What exists already:** 347 official injury rows, 32 official depth charts, and a per-player
  replacement tier for every row that the club charts cover. From Week 10 forward the desk can
  freeze each week's injury report and build the missing history (see discovery step D-04).
* **Interim evidence:** the Week 10 cross-section (C4, C5 in `data/correlations.csv`) shows no
  relationship between offensive starters out and season point differential (r = 0.034, n = 28) and a
  weak negative relationship for defensive starters out versus points allowed per game
  (r = -0.1587, n = 28). One week of injuries cannot separate injury effect from team quality.

## S6 - Player-prop combinations (player prop, blocked)

* **Rule:** combine player-level official box scores (passing, rushing, receiving yards) with the
  replacement-depth state, then look for prop lines that sit below the model probability.
* **Status:** blocked on two independent requirements:
  1. *Player-level official data*: the NFL Game Center exposes a **Game Book PDF** (for example the
     official Week 10 Washington-New York book at
     `https://static.www.nfl.com/image/upload/v1794570519/gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf`).
     Parsing that into a machine-readable player table is a defined discovery step (D-03), not a
     guess. The NFL.com team-stat pages were rejected as a source because their multi-value tiles
     cannot be paired with their labels without ambiguity - the values are left blank rather than
     inferred.
  2. *Prop prices*: no official prop line exists, so no prop edge can be computed.
* **Research note:** prop strategies also inherit the same luck problem. A prop bet at the model's
  own fair price has zero expected profit; only a price feed turns it into an edge.

## Validation gates (fail-closed)

Ten criteria per strategy, published row by row in `data/gate_decisions.csv`:

| # | Criterion | Type |
|---|---|---|
| 1 | Every input traces to an official NFL or official club source | provenance |
| 2 | No look-ahead: a prediction uses only earlier weeks | structural |
| 3 | Minimum out-of-sample sample size (n >= 30) | signal |
| 4 | Brier score at or better than the league base-rate baseline | signal |
| 5 | Log loss at or better than the league base-rate baseline | signal |
| 6 | Calibration slope inside the 0.8 - 1.2 band | signal |
| 7 | Realised staking result is separated from signal quality | luck control |
| 8 | Staking profit is never used alone to reward a strategy | luck control |
| 9 | Market ROI and closing-line value against a real price | market (not evaluable today) |
| 10 | Break-even hit rate at a real offered price | market (not evaluable today) |

**Decision rule.** Any `FAIL` -> `PAPER`. Any `NOT_EVALUABLE` -> `PAPER` (fail closed). Only a
strategy whose every live criterion is `PASS` may be `LIVE_ELIGIBLE`. A strategy that is already live
is moved back to `PAPER` by the same rule - that is the demotion gate, and it is exercised on every
build.

**Current outcome:** all six strategies are `PAPER`, because criteria 9 and 10 cannot be evaluated
without a price source, and S4/S5/S6 cannot even measure their signal yet. No strategy is promoted on
the strength of a staking run.
