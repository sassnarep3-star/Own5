# Correlation Analysis (T5)

## Method

Correlation values are **computed in-repo** by `tools/compute_correlations.py` (Pearson r) from the official standings snapshot `data/standings-2026-wk8.csv`, which was captured from [nfl.com/standings](https://www.nfl.com/standings/) on 2026-11-02 (2026 season through Week 8, all 32 teams). The script first asserts internal consistency of the official data (NET = PF − PA for every team; PCT = (W + 0.5·T)/GP; total wins = total losses) — all checks pass. Input source for every row: [https://www.nfl.com/standings/](https://www.nfl.com/standings/).

## Results (n = 32 teams)

<!-- TABLE:correlations.csv -->

## Interpretation

- **Net points per game vs. winning percentage, r = 0.839** — the strongest verified single-team predictor; the backbone of STR02 (net-points mismatch).
- Offense and defense are essentially independent (PF/G vs. PA/G, r = −0.012): build **separate** offensive and defensive signals rather than one blended rating.
- **Betting-leg correlations:** same-game parlay leg correlations (e.g., QB passing yards vs. team total) are **not published by any official source** — numeric cells are left blank and flagged (F03). Policy instead: correlated legs are only combined inside sportsbook-offered SGPs (house rules, [FanDuel](https://www.fanduel.com/fanduel-sportsbook-house-rules-on)), with reduced stakes (STR06/STR07), and cross-strategy outcome correlation is capped at |r| < 0.50 by gate G05.

## Input data (official, 2026-11-02 snapshot)

<!-- TABLE:standings-2026-wk8.csv -->
