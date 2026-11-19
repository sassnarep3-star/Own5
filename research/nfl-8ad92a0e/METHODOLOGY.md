# Methodology — session 8ad92a0e

## Model (frozen before Week-11 kickoff): `m8-2026-11-19-walkforward-v1`

| Parameter | Value | How chosen | Disclosure |
|---|---|---|---|
| Shrinkage k | 8 games | fixed constant, registered in `model_spec.json` | assumption (small-sample protection) |
| League scoring mean L | 23.077 pts/team/game | computed from official finals (PF=PA identity) | measured |
| Home-field advantage | −0.98 pts | mean home margin, 150 official finals | measured; **negative in 2026** (F8-03) |
| Margin σ | 13.49 pts | sd of home margins, 150 finals | measured |
| Total σ | 18.95 pts | sd of totals, 150 finals | measured |

**Side.** For clubs with prior games: shrunk scoring rates
`pf = (PF + L·k)/(gp + k)`, `pa = (PA + L·k)/(gp + k)`. Expected points:
`exp_home = (pf_home + pa_away)/2`, `exp_away = (pf_away + pa_home)/2`.
Expected home margin `m = (exp_home − exp_away) + HFA`. Fair side line published in operator style
(negative = home favoured) **and** as expected home margin (positive = home favoured) — both columns,
no sign ambiguity. `p_home = Φ(m/σ)` (normal CDF); ties observed 1/150 in-window and treated as push
by rule (Q8-06 open).

**Total.** `total = exp_home + exp_away` (HFA cancels). Published with `p_over at fair line = 0.5000`
by construction — stated explicitly so the probability column is not mistaken for a market number.

**Moneyline.** `p_home`, `p_away = 1 − p_home` published as the fair price; fair decimal odds are the
reciprocal. Order per game is always side → total → moneyline (verified by `verify.py` V5).

**Inputs.** Every row carries `inputs_sha256` over the fixture, records, k, HFA, σ and L — model output
is a probability **plus its inputs**, per brief.

## Walk-forward luck panel (no lookahead)

Games sorted by date (feed order within a date). For each game the forecast uses **only prior games**:
expanding league mean, shrunk rates, expanding HFA (mean of prior margins), expanding σ (sd of prior
margins; falls back to 14.0 until two margins exist — F8-14). After the forecast the game is ingested.
Ties are excluded from scoring (n=149 of 150). Baselines: p=0.5 and the expanding prior home-win rate.
Skill = 1 − Brier_model/Brier_baseline; 95% CI via week-cluster bootstrap (10 clusters, 1,000 resamples,
seed 8,920,611). Reported with n on every row.

## Correlations

Pearson r computed in-repo from official numbers only: 8 pairs from the standings (n=32), 1 pair
(away points × home points) from the finals feed (n=150). Fisher-z 95% CI published with each value.
No third-party data enters any correlation (brief rule).

## Origination order and separation of concerns

1. Side first, then total, then moneyline (registration order in `lines_wk11.csv`).
2. Model fair line / market line / difference are three separate columns; the last two stay BLANK
   until a licensed price source is onboarded (policy **P-8AD-01**, decided **before** any backtest
   number was published — brief's price-data-policy rule).
3. Leaderboard separates **signal** (proper-score columns) from **staking** (return column, structurally
   blank until Q8-03 is decided). Backtest numbers are forbidden on the leaderboard (G8-11, enforced).
4. Controls (random, favourites-only) are registered on every run (G8-09).
5. Demotion gate (G8-07): a live strategy whose rolling-100 skill CI lower bound ≤ 0 returns to paper.

## Availability rules

- Injury levels are never model inputs; only future **deltas** (surprise) may enter — rule adopted (R8-35).
- Depth order is never inferred from jersey number, experience or salary (rejected, R8-57).
- Replacement depth, expected/actual starters, inactives and snap counts stay BLANK until a verified
  depth source exists for all 32 clubs (Q8-04, F8-02/F8-16).

## Pre-registration

Strategies S8-B01…S8-B06 and this model were frozen in the claim commit
`75752e50f01df5e0741ff31a498242da3ce6c990` (git hash = registration) before Week-11 kickoffs.
Each strategy carries a two-sided "what would change our mind" field and a demotion rule.

## Adoption rules (results feed)

The 150-game feed is accepted only if: (a) every week-9 and week-10 row matches a direct official
read taken 2026-11-19; (b) per-club W-L-T/PF/PA reproduce the official standings 32/32 exactly.
Both tests are re-run on every verify (V3) and published on `results.html`.
