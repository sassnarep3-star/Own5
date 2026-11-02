# Correlation Analysis (T5)

Status: done | Owner: session arena-f1d30421 | Verified: 2026-11-02

Correlation values decide (a) whether parlay payouts are fair, (b) whether "hedges" actually hedge,
and (c) how to price same-game combos (SGPs). **Every number on this page is computed** by
[`scripts/compute_analysis.py`](../../scripts/compute_analysis.py) (game level) and
[`scripts/compute_prop_correlations.py`](../../scripts/compute_prop_correlations.py) (player level) from
pinned datasets; outputs in [`data/correlation_bets.csv`](../../data/correlation_bets.csv),
[`data/correlation_parlays.csv`](../../data/correlation_parlays.csv),
[`data/correlation_props.csv`](../../data/correlation_props.csv). Derived values are labeled as such
(dataset sources are community datasets — see [flagged](flagged.md)).

## 1. Same-game bet-outcome correlations (1980–2024, n = 10,228 games)

| Pair | Correlation | Type | Interpretation |
|---|---|---|---|
| favorite covers vs over | 0.009 | phi | ≈ independent — spread & total legs can use product rule within ±0.01 error |
| favorite SU vs over | 0.002 | phi | ≈ independent |
| favorite covers vs favorite SU | **0.712** | phi | strongly redundant — parlaying ML + spread of the same side ≈ double-counting one outcome |
| home SU vs over | −0.005 | phi | ≈ independent |
| home-dog status vs over | 0.008 | phi | ≈ independent |
| home margin vs total points | 0.028 | pearson | blowouts don't reliably go over |
| ATS margin vs total deviation | 0.051 | pearson | weak positive — covering teams slightly inflate totals |
| fav covers vs over \| home favorite | 0.016 | phi | ≈ independent |
| fav covers vs over \| away favorite | −0.004 | phi | ≈ independent |

## 2. Parlay joint probabilities (why fixed parlays lose)

Full table: [`data/correlation_parlays.csv`](../../data/correlation_parlays.csv). Selected rows
(full window):

| Leg A | Leg B | P(A) | P(B) | P(both) measured | P(A)×P(B) | ratio |
|---|---|---|---|---|---|---|
| favorite covers | over | 0.480 | 0.491 | 0.238 | 0.236 | 1.009 |
| favorite covers | under | 0.480 | 0.509 | 0.243 | 0.245 | 0.991 |
| home underdog covers | over | 0.189 | 0.491 | 0.094 | 0.093 | 1.016 |
| fav covers (game i) | fav covers (game i+1, same week) | 0.479 | 0.478 | 0.225 | 0.229 | 0.984 |

Takeaways:

1. **Cross-game legs are independent in practice** (ratio 0.984) — safe to multiply, but a parlay
   cannot manufacture edge: with break-even legs (48% × 49% ≈ 23.6%) a 2-leg −110/−110 parlay
   (needs 27.47%) is solidly −EV. Parlays make sense only from gate-passing legs or with measured
   positive correlation priced in.
2. **Same-game legs at the game-line level are also ≈ independent** (ratios 1.00–1.02). Real SGP
   correlation lives in *player props* (below), which is why books price SGPs off player-level
   correlation, not game-line correlation.

## 3. Player-prop correlations (2002–2013 play-by-play, 6,186 team-games)

Full table: [`data/correlation_props.csv`](../../data/correlation_props.csv). Key rows:

| Pair | Pearson r | n | Why it matters |
|---|---|---|---|
| QB passing yards vs top-WR receiving yards | **0.760** | 3,852 | QB-over + WR-over legs are strongly correlated; naive parlay pricing is wrong. Use empirical joint probability. |
| QB passing yards vs game total | 0.347 | 3,852 | QB props and game totals share script information |
| QB passing yards vs team points | 0.299 | 3,852 | QB prop ↔ team total combos: moderate positive |
| top-WR receiving yards vs team points | 0.229 | 3,574 | moderate |
| top-RB rushing yards vs team margin | 0.207 | 4,415 | "winning script runs the ball" — RB overs correlate with favorite-side outcomes |
| top-RB rushing yards vs game total | 0.071 | 4,415 | weak |
| team passing vs team rushing yards | 0.125 | 6,186 | weak positive in aggregate (era-dependent) |
| team points vs opponent points | −0.035 | 6,186 | game-flow: slight negative |

Era caveat (flagged): the only play-by-play archive reachable from this environment covers
2002–2013; modern pass-volume correlations may differ. Values are labeled derived
(dataset [pin](https://github.com/brianfoshee/nfl-play-by-play-data/blob/352c9c9b0bce0ffa8ce85681cf9ed50c0398f462/)).

## 4. How the leaderboard uses correlation (gate G5)

* Cross-game parlays: independence allowed when |ratio − 1| ≤ 0.05 (measured 0.984 ✓).
* Same-game game-line combos: independence allowed at ±0.02 error band (measured 1.00–1.02 ✓).
* Any combo containing player-prop legs: **empirical joint pricing mandatory** (r up to 0.76).
* Hedge definitions require negative measured correlation; none of the tested game-line pairs
  qualifies (all ≈ 0), so "hedging" across spread/total is a myth at game level — documented here so
  the leaderboard rejects hedge-based variance claims.

## Sources

* Computed values: scripts + pinned datasets above (reproducible).
* Statistical definitions: standard Pearson/phi coefficients (no external source needed for the
  definitions; every *value* is ours, computed).
