# Pre-registration — session 35a1feb2 (frozen before the sample opens)

This file is the registration instrument the brief asks for: *commit the rule text, the sample window and
the gates to git before the evaluation window opens. The commit hash is the registration.*

- Frozen at: 2026-11-17T01:05Z
- Evaluation window opens: 2026-11-19T20:15Z (the first Week 11 kickoff, IND at HOU)
- Evaluation window closes: 2026-11-23T23:59Z (after CIN at WAS)
- Registering commit: recorded in `data/registration_proof.csv` (the commit that carries this file)
- Scope: singles only. No parlay, no same-game parlay, no prop combo is registered in this window
  (joint-evidence gate, REQ-36).

## The one registered model

`ridge-scoring v1` — a single team-strength rating per club plus one fitted home term.

- Objective: least squares on the game margin, `margin = hfa + strength(home) − strength(away)`, L2 penalty
  λ = 1.0 on team ratings only, no penalty on the home term.
- Training data: the 149 games completed and verified before the recorded forecast time, from the official
  week pages. No game in the prediction set appears in the training set.
- Inputs allowed: W, L, T, PF, PA from the league standings page and the game-by-game record. Nothing else.
- Explicitly excluded: injury designations, depth, snap counts, weather, market prices, and every
  third-party column. Each exclusion has a named gate on the gates page; none was excluded for convenience.
- Fixed constants: none. The home term is estimated, not assumed. The record's measured mean home margin is
  −0.51 points (−0.26 excluding the eight neutral-site games) and the fitted value is −0.46, so a
  conventional +2.5 anchor would be a documented error rather than a small one.

## The three registered market stages, in order

1. **Side.** Fair home margin in points, plus the fair spread rounded to the nearest half point.
2. **Total.** Two estimators, both published, with the gap between them as its own column. Estimator A is
   an opponent-averaged points expectation; estimator B is a league base rate plus net differentials.
   Neither retires on the current walk-forward (A wins weeks 5, 7 and 9; B wins 6, 8 and 10), so both stay
   published — and the naive league-average total beat both in weeks 7 and 9. That is reported, not buried.
3. **Moneyline.** Derived from the recorded probability of the registered margin distribution, no-vig.
   It is a fair price, never a quote.

## Scoring rules, fixed now

- Signal: Brier score per forecast, benchmarked against the league-average probability; skill is
  `1 − Brier_model / Brier_benchmark`, with a game-cluster bootstrap lower bound over four settled weeks.
- The leaderboard shows no backtest number of any kind, ever, in any column, in any division.
- Staking is a separate table. A staking run cannot raise a strategy's signal rank and a losing run cannot
  lower it, because the two tables are computed from the same probabilities with different stake rules.
- Controls run in the same window: a deterministic alternating-side coin flip, a best-differential-only pick,
  and the league-average total. A strategy that does not beat all three is reported as not beating them.
- Calibration requires 200 recorded forecasts before a slope is published; 39 are registered now, so the
  calibration column stays blank.

## What voids this registration

Any edit to a forecast row after kickoff voids the week's scores and the week is republished with the diff
visible. `verify.py` re-derives every table from the committed inputs, and the manifest hash of the raw read
is the check that a published number was not quietly improved after the fact.

## What this registration does *not* claim

It claims no edge. It does not say the model is any good. It fixes in advance what will be measured, so
that whatever Week 11 produces cannot be re-described afterwards into something that worked.
