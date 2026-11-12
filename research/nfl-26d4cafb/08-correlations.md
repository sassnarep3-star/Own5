# Correlations and Prop Combos

**Session `26d4cafb` - snapshot 2026-11-12 UTC - NFL 2026 Week 10**

> Generated directly from `nfl-desk-26d4cafb/data/` by `engine.py`. Every row links to the official source it was read from. Values that could not be confirmed from an official source are left blank and listed on the Flagged for Review page.

## Team level (n=32)

| # | Metric X | Metric Y | n | r | r^2 | t | p | Status |
|---|---|---|---|---|---|---|---|---|
| CORR-T01 | points for per game (PF/G) | winning percentage (PCT) | 32 | 0.6938 | 0.4814 | 5.2772 | 0.0 | verified inputs (nfl.com); value computed in-repo |
| CORR-T02 | points allowed per game (PA/G) | winning percentage (PCT) | 32 | -0.6662 | 0.4438 | -4.8925 | 1e-06 | verified inputs (nfl.com); value computed in-repo |
| CORR-T03 | net points per game (PF/G - PA/G) | winning percentage (PCT) | 32 | 0.8758 | 0.7671 | 9.9398 | 0.0 | verified inputs (nfl.com); value computed in-repo |
| CORR-T04 | points for per game (PF/G) | points allowed per game (PA/G) | 32 | -0.2061 | 0.0425 | -1.1535 | 0.248702 | verified inputs (nfl.com); value computed in-repo |
| CORR-T05 | net points (PF - PA) | wins (W) | 32 | 0.8463 | 0.7162 | 8.7001 | 0.0 | verified inputs (nfl.com); value computed in-repo |
| CORR-T06 | points for per game (PF/G) | wins (W) | 32 | 0.6712 | 0.4505 | 4.9589 | 1e-06 | verified inputs (nfl.com); value computed in-repo |
| CORR-T07 | points allowed per game (PA/G) | wins (W) | 32 | -0.6518 | 0.4248 | -4.7068 | 3e-06 | verified inputs (nfl.com); value computed in-repo |

## Player props (same-game pairs)

| # | Metric X | Metric Y | n | r | r^2 | t | p |
|---|---|---|---|---|---|---|---|
| CORR-P01 | QB passing yards | primary target receiving yards | 50 | 0.2685 | 0.0721 | 1.9314 | 0.053429 |
| CORR-P02 | QB passing yards | lead RB rushing yards | 36 | -0.4586 | 0.2103 | -3.0093 | 0.002618 |
| CORR-P03 | primary target receiving yards | lead RB rushing yards | 36 | -0.0064 | 0.0 | -0.0374 | 0.970176 |
| CORR-P04 | QB passing yards | team points scored | 50 | 0.2545 | 0.0648 | 1.8232 | 0.068279 |
| CORR-P05 | QB pass attempts | QB passing yards | 50 | 0.6215 | 0.3863 | 5.4963 | 0.0 |
| CORR-P06 | target receptions | target receiving yards | 50 | 0.8274 | 0.6846 | 10.2061 | 0.0 |
| CORR-P07 | RB rushing attempts | RB rushing yards | 36 | 0.8114 | 0.6584 | 8.0957 | 0.0 |
| CORR-P08 | team points scored | lead RB rushing yards | 36 | 0.1317 | 0.0173 | 0.7745 | 0.438645 |
| CORR-P09 | team margin (pts - opp pts) | lead RB rushing yards | 36 | 0.2324 | 0.054 | 1.3934 | 0.163511 |
| CORR-P10 | team margin (pts - opp pts) | QB passing yards | 50 | -0.1019 | 0.0104 | -0.7098 | 0.477824 |
| CORR-P11 | team points scored | primary target receiving yards | 50 | 0.2316 | 0.0536 | 1.6495 | 0.099044 |

## Prop combos: joints, lift, Frechet-Hoeffding bounds

| Combo | Leg A | Leg B | n | P(A) | P(B) | P(A and B) | P(A)P(B) | Lift | phi | Min | Max | In bounds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| STR-08 QB over + primary target over | Dak Prescott | CeeDee Lamb | 9 | 0.5556 | 0.4444 | 0.4444 | 0.2469 | 1.8 | 0.8 | 0.0 | 0.4444 | YES |
| STR-08 QB over + primary target over | Jared Goff | Amon-Ra St. Brown | 8 | 0.625 | 0.375 | 0.25 | 0.2344 | 1.0667 | 0.0667 | 0.0 | 0.375 | YES |
| STR-08 QB over + primary target over | Joe Burrow | Ja'Marr Chase | 8 | 0.375 | 0.375 | 0.125 | 0.1406 | 0.8889 | -0.0667 | 0.0 | 0.375 | YES |
| STR-08 QB over + primary target over | Jordan Love | Tucker Kraft | 9 | 0.4444 | 0.5556 | 0.2222 | 0.2469 | 0.9 | -0.1 | 0.0 | 0.4444 | YES |
| STR-08 QB over + primary target over | Josh Allen | Khalil Shakir | 8 | 0.5 | 0.5 | 0.25 | 0.25 | 1.0 | 0.0 | 0.0 | 0.5 | YES |
| STR-08 QB over + primary target over | Patrick Mahomes | Travis Kelce | 8 | 0.375 | 0.5 | 0.25 | 0.1875 | 1.3333 | 0.2582 | 0.0 | 0.375 | YES |
| STR-09 QB over + lead RB over | Dak Prescott | Javonte Williams | 9 | 0.5556 | 0.4444 | 0.3333 | 0.2469 | 1.35 | 0.35 | 0.0 | 0.4444 | YES |
| STR-09 QB over + lead RB over | Jared Goff | Jahmyr Gibbs | 8 | 0.625 | 0.5 | 0.25 | 0.3125 | 0.8 | -0.2582 | 0.125 | 0.5 | YES |
| STR-09 QB over + lead RB over | Joe Burrow | Chase Brown | 8 | 0.375 | 0.625 | 0.125 | 0.2344 | 0.5333 | -0.4667 | 0.0 | 0.375 | YES |
| STR-09 QB over + lead RB over | Jordan Love | Josh Jacobs | 3 | 0.3333 | 0.6667 | 0.0 | 0.2222 | 0.0 | -1.0 | 0.0 | 0.3333 | YES |
| STR-09 QB over + lead RB over | Josh Allen | James Cook | 8 | 0.5 | 0.5 | 0.0 | 0.25 | 0.0 | -1.0 | 0.0 | 0.5 | YES |
| POOLED QB over + primary target over | ALL | ALL | 50 | 0.48 | 0.46 | 0.26 | 0.2208 | 1.1775 | 0.1574 | 0.0 | 0.46 | YES |
| POOLED QB over + lead RB over | ALL | ALL | 36 | 0.5 | 0.5278 | 0.1667 | 0.2639 | 0.6316 | -0.3895 | 0.0278 | 0.5 | YES |

> Reference line is each player's own shrunk season median - a synthetic fair reference, not an official prop line (FLG-01, FLG-02).

## Quarterback checksums

| QB | Team | Games | Official | Sum of logs | Check | Mean | SD | r vs target |
|---|---|---|---|---|---|---|---|---|
| Dak Prescott | DAL | 9 | 2381 | 2381 | MATCH | 264.6 | 59.8 | 0.5937 |
| Jared Goff | DET | 8 | 2134 | 2134 | MATCH | 266.8 | 82.2 | 0.3361 |
| Joe Burrow | CIN | 8 | 2386 | 2386 | MATCH | 298.2 | 97.6 | 0.1371 |
| Jordan Love | GB | 9 | 2618 | 2618 | MATCH | 290.9 | 81.1 | 0.2907 |
| Josh Allen | BUF | 8 | 2027 | 2027 | MATCH | 253.4 | 42.3 | 0.1655 |
| Patrick Mahomes | KC | 8 | 2037 | 2037 | MATCH | 254.6 | 70.8 | 0.6019 |
