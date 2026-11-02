# Methodology — line origination & validation (Own5)

All inputs are verified official NFL data (`data/`, source registry `data/sources.json`). Engine: `scripts/analyze.py` (pure stdlib, deterministic, no network). As-of 2026-11-02; 2026 data through Week 8 (120 final games; CHI@SEA W8 MNF pending, excluded — F05).

## 1. Team power rating (pooled, no lookahead)

For team *t*: `rating(t) = (PF − PA) / GP`, where PF/PA/GP pool the **2025 full verified season (GP=17)** with **all final 2026 games of the team played before the game being predicted**. When originating Week 9 lines, the 2026 pool is Weeks 1–8 only.

## 2. Originated spread (home perspective)

`model_margin = rating(home) − rating(away) + HFA`, where **HFA = empirical mean home margin over the prior completed 2026 games** (0 in Week 1; for Week 9 lines: mean over the 120 final 2026 games = **+0.72 pts**, home win rate 62/120 = 51.7% — assumption F09). The originated spread is the model margin rounded to the nearest 0.5-style display; the bet side is the team favored by the model.

## 3. Originated total

`expected(team) = (team PF/GP + opponent PA/GP) / 2`; `model_total = expected(home) + expected(away)`. Total direction pick (S3) compares model_total to a walk-forward league reference (2025 verified league mean total ≈ 46.0 for Week 1; thereafter the mean actual total of prior 2026 games).

## 4. Backtest protocol (walk-forward, 2026 Weeks 1–8, 120 games)

Each game is predicted using only 2025 aggregates + final 2026 games from **earlier weeks** — no lookahead. Recorded per game (`analysis/backtest_2026.json`): model margin/total, HFA used, own-line spread bet at −110 (F02), spread SU direction, own-line total bet at −110, total SU direction vs reference.

## 5. Strategies & validation gates

Strategies (`analysis/strategies.json`): S1 spread direction all games (SU); S2 spread direction selective |line| ≥ 6 (threshold documented a priori); S3 total direction vs league reference (SU); S4 same-game 2-leg parlay (S1 leg + S3 leg) priced as a 2-leg −110 parlay; S5 weekly top-2 |line| cross-game parlay; S6 negative control (own line at −110); S7 W9 QB prop lines (originated only — not backtested, unrated).

**Gates (all must pass for approval):** G1 ≥ 30 graded bets · G2 win rate ≥ breakeven (50% SU; 52.38% at −110; 27.44% for a 2-leg −110 parlay) · G3 one-sided binomial p < 0.05 vs breakeven (luck removed: SU legs are graded against a 50% null at even money) · G4 Weeks 7–8 holdout win rate ≥ breakeven · G5 max drawdown ≤ 15 units · G6 parlay correlation guard |same-game leg r| < 0.35 (computed values C4/C5 in `analysis/correlations.json`).

## 6. Correlations (all computed from verified data; `analysis/correlations.json`)

C1 2025 NET vs win% r=0.919 (n=32) · C2 2026 NET vs win% r=0.831 (n=32) · C3 model vs actual margin r=0.289 (n=120) · C4 same-game margin vs total r=−0.164 (n=120) · C5 same-game spread-leg vs total-leg result r=+0.087 (n=120) · C6 2025 differential vs 2026 win% r=0.397 (n=32) · C7 empirical HFA = +0.72 pts, home win rate 51.7% (n=120).

## 7. Leaderboard

Score = 100×ROI + 10×Sharpe + 50×(win rate − breakeven) — a **project-defined competition metric**, labeled as such (not an official NFL value). Rewards only for gate-approved strategies; approved strategies rank above non-approved. Result: S2, S4, S3, S1 approved (Gold); S5 not approved (G1, n=8); S6 negative control fails; S7 unrated/flagged.

## 8. Week 9 QB prop lines

`line = 0.65 × (2026 YDS / team GP) + 0.35 × (2025 YDS / 17)` (team GP as QB GP — assumption F03; weights documented a priori). Not backtested (no verified per-game logs fetched) → fails G1/G3 by construction → published as originated lines only, with blank cells where the starter or 2026 total is unverified (F06/F07).
