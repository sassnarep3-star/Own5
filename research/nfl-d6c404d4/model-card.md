# Model card — D6C-WEIGHTED-EFFICIENCY-v1

**Desk:** NFL verified line desk · session `d6c404d4`
**Registration:** `REG-D6C404D4-V1` (`nfl-line-audit/data/preregistration.json`, sha256 pinned by `verify.py`)
**Written:** 2026-11-19T07:05Z

## What the model is

An opponent-adjusted, recency-weighted points-per-drive model. Each club gets an offensive rate and a
defensive rate in points per drive. The fit is iterative: a club's offensive rate is measured against the
defensive rates of the clubs it actually played, and the defensive rates are simultaneously measured
against the offences they faced. Recency weighting uses a six-week half-life. Home advantage is estimated
on the same data and enters as a rate added to the home offence.

The model does not use win percentage, point differential, jersey numbers, salary, experience, or a
depth chart. Pace is a control (estimated drives per game, from recorded offensive snaps divided by 6.2),
not a signal.

## Frozen parameters

| Parameter | Value | Why |
|---|---|---|
| Half-life | 6 weeks | Chosen in the tune window only (2023-24); never re-tuned on 2025-26 |
| Iterations | 60 | Converges; more iterations change nothing at the published precision |
| Minimum history | 200 usable games | Below this the fit is unidentifiable, so the first season in the record is scored only once history exists |
| Drives proxy | offensive snaps / 6.2 | Measured from the pinned snap counts, not assumed per club |
| Margin dispersion | residual sd, recent 400 games | Measured, replacing an earlier 0.72x total fudge factor |
| Total dispersion | residual sd, recent 400 games | Same construction |

## Measured results (walk-forward, 744 games, 2023-2026)

| Measure | Value |
|---|---|
| Brier skill vs the de-vigged closing line | **-0.0782** |
| Brier, model | 0.2244 |
| Tune window 2023-24 | -0.1064 |
| Holdout 2025-26 | -0.0561 |
| Side MAE, model | 10.18-11.33 points by season |
| Side MAE, closing line | 9.49-10.59 points by season |
| Total MAE, model | 10.33-12.65 points by season |
| Total MAE, closing line | 9.73-10.60 points by season |
| Model closer to truth than the line (side) | 44.9-47.4% of games |

Every season, on every market, the closing line is closer to the result than the model. There is no
season in which this model would be deployed.

## Why it loses — decomposed, not excused

1. **The model is too flat.** Its forecast totals have a standard deviation across games of 5.96 points;
   the closing line's is 4.31. The model barely separates one matchup from another.
2. **It is less informative.** Correlation of forecast total with the realised total: 0.187 (model) versus
   0.318 (line).
3. **It is unbiased.** Mean residual (actual minus forecast) on totals: +0.41 points, cluster interval
   -0.56 to +1.29. The model is not systematically high or low; it is simply noisier.

Root-mean-square error on totals, the number that combines bias and spread: **13.83 points (model)** versus
**12.99 (closing line)**. The model's error is therefore mostly variance, not bias. That is the harder failure to fix with public
data, and the desk says so rather than reporting a tuned number.

## The one positive number, and its caveat

Betting every over at the closing total returns **+0.33%** per unit over 741 decided games. The cause is
visible: the closing total sits **1.26 points below** the total actually scored, with a week-clustered
interval of 0.40 to 2.05 over 49 clusters. That is a market-level effect, not a modelling edge.

A discovery screen looked at whether the effect is concentrated (by season, by total size). It is not: both
total buckets show the same rate. **Because the screen looked at the holdout, the holdout is no longer a
holdout for this hypothesis.** Any test must be pre-registered on 2026 games only, before kickoff, with the
threshold frozen and the commit published first. No threshold is proposed here.

## Ablations instead of fixed penalties

Personnel features (availability, usage rank) are **not** in the model. The registration forbids adding
them without a point-in-time join that is complete enough to survive a walk-forward test; the published
join rate is 60% for designations against playing time, so the feature would launder missingness. The
ablation table records the base model's score and states that no personnel variant is admitted.

## Known limitations, published

- The corpus is an aggregator dataset (nflverse), labelled `PINNED-DATASET` on every row; no row is described as official.
- Week 10 of 2026 was appended from the official nfl.com page because the pinned snapshot stops at week 9.
- The 136-game log in the repository cannot serve as a corpus: 16 rows have no score and 3 fixtures are absent.
- Closing prices for the backtest are the pinned dataset's closing fields; they are not operator reads taken by this desk.
- No inactives, no snap-count detail for week 10, no weather model.

## Reproduction

```
python3 nfl-line-audit/build_data.py     # ~33 s
python3 nfl-line-audit/build_registers.py
python3 nfl-line-audit/build_site.py
python3 nfl-line-audit/verify.py         # 80 checks
```
