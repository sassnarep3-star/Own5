# Luck vs Skill

**Session `26d4cafb` - snapshot 2026-11-12 UTC - NFL 2026 Week 10**

> Generated directly from `nfl-desk-26d4cafb/data/` by `engine.py`. Every row links to the official source it was read from. Values that could not be confirmed from an official source are left blank and listed on the Flagged for Review page.

## Luck vs skill

| Strategy | n | Win rate | Null | Lift | p (exact) | Holm p | Significant | Brier | Brier null | Sharpe | DSR | Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BASE | 87 | 0.6437 | 0.5047 | 0.139 | 0.009621 | 0.025719 | YES | 0.2183 | 0.2583 | 0.2503 | 0.8356 | 6.273 |
| STR-01 | 35 | 0.7429 | 0.5141 | 0.2288 | 0.00643 | 0.025719 | YES | 0.2061 | 0.2539 | 0.5012 | 0.9138 | 2.091 |
| STR-04 | 26 | 0.8077 | 0.4964 | 0.3113 | 0.001372 | 0.006861 | YES | 0.2074 | 0.2563 | 0.7203 | 0.9478 | 1.091 |
| STR-05 | 36 | 0.3333 | 0.5078 | -0.1745 | 0.043682 | 0.043682 | YES | 0.25 | 0.2609 | -0.4041 | 0.0004 | 13.091 |
| STR-10 | 8 | 1.0 | 0.5 | 0.5 | 0.007742 | 0.025719 | YES | 0.0443 | 0.2506 | &mdash; | &mdash; | 0.0 |
| STR-07 (two-leg parlay) | 16 | 0.5 | 0.2648 | 0.2352 | 0.044088 | &mdash; | NOT IN FAMILY (single parlay construction) | 0.3073 | 0.3141 | 0.4512 | 0.7023 | 3.0 |

## Selectivity test

| Confidence tercile | n | Mean abs margin | Wins | Win rate | Null | Lift |
|---|---|---|---|---|---|---|
| 1 (lowest \|model margin\|) | 29 | 0.573 | 11 | 0.3793 | 0.5002 | -0.1209 |
| 2 (middle) | 29 | 2.387 | 24 | 0.8276 | 0.4953 | 0.3323 |
| 3 (highest \|model margin\|) | 29 | 6.193 | 21 | 0.7241 | 0.5186 | 0.2055 |

chi2 = 7.5173, p = 0.006111, monotone increasing: **NO**

NOT ESTABLISHED: either the ordering is not monotone or the trend test does not clear alpha=0.05. The observed spread is within what uniform luck produces, so no selectivity claim is made.

## Two-leg parlays

| Parlays | Pairing | Leg A | Leg B | phi | Hit rate | Null | Independence | Lift | Min | Max | Break-even | ROI/unit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16 | greedy, non-overlapping, within week | 0.75 | 0.75 | -0.3333 | 0.5 | 0.2648 | 0.5625 | 0.8889 | 0.5 | 0.75 | 0.2744 | 0.8223 |
