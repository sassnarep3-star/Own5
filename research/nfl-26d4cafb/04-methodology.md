# Methodology

**Session `26d4cafb` - snapshot 2026-11-12 UTC - NFL 2026 Week 10**

> Generated directly from `nfl-desk-26d4cafb/data/` by `engine.py`. Every row links to the official source it was read from. Values that could not be confirmed from an official source are left blank and listed on the Flagged for Review page.

## Declared model

- Team offence: shrunk, opponent-adjusted points per game above league mean.
- Team defence: shrunk, opponent-adjusted points allowed per game above league mean.
- Expected points: `pts_A = league_mean + off_A + def_B`, with the empirical home-field advantage split half to each side and zeroed for confirmed neutral-site games.
- Score distribution: independent Poisson on the two expected point totals; win, loss and tie probabilities, the fair spread and the fair total come from direct enumeration.
- Injury/depth toll: itemised per team per unit, weighted by the official availability tier. These are bounded model priors, never official statistics.

## Declared hyper-parameters

| Parameter | Value |
|---|---|
| assumed_price | -110 |
| correlation_cap | 0.6 |
| graded_from_week | 4 |
| max_drawdown_units | 10.0 |
| opp_adjust_iters | 2 |
| rest_edge_days | 3 |
| selectivity_threshold | 3.0 |
| shrink_k | 6.0 |

## Home-field advantage

| n | Mean | SD | SE | CI low | CI high | t | p | Home W | Away W | T | Incl. unconfirmed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 130 | -0.0538 | 13.2801 | 1.1647 | -2.3367 | 2.2291 | -0.0462 | 0.963127 | 63 | 66 | 1 | -0.2045 |

> Two 2026 games (Week 4 IND@WSH, Week 6 HOU@JAX) show a 9:30 AM ET international kickoff window but no venue on the official schedule page, so their neutral-site status is unconfirmed; they are excluded from the main estimate and reported as a sensitivity (FLG-12).

## Shrinkage sensitivity

| k | n | MAE | RMSE | Bias | Declared |
|---|---|---|---|---|---|
| 3 | 88 | 9.422 | 12.394 | 1.963 | &mdash; |
| 6 | 88 | 9.301 | 12.287 | 1.91 | YES (used for all reported results) |
| 9 | 88 | 9.406 | 12.331 | 1.882 | &mdash; |
| 12 | 88 | 9.544 | 12.398 | 1.865 | &mdash; |
| 16 | 88 | 9.7 | 12.483 | 1.851 | &mdash; |
| 24 | 88 | 9.906 | 12.612 | 1.834 | &mdash; |

## Zero-look-ahead protocol

- Walk-forward: a bet graded in week *w* is produced by a model fitted only on weeks < *w*.
- The null probability for each pick also comes only from weeks < *w*.
- Each pick is scored against its **own** null (the pre-week home win rate), then tested with an exact **Poisson-binomial**, not a plain binomial with a constant p.
- No official injury register exists for Weeks 1-9, so no injury-based strategy is backtested; those entries are marked not evaluable rather than graded on invented data.
