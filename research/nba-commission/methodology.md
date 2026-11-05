# Methodology — NBA Line Commission (session arena-a46d621e)

Snapshot 2026-11-05. This document is the contract for every number on the site: what is official,
what is computed, what is assumed, and what is deliberately left blank.

## 1. Data provenance

- Only **official nba.com** pages supply data: `/standings`, `/stats/teams/traditional`,
  `/schedule`, and `/stats/player/<id>/boxscores` / `/game/<id>/`.
- Every row of every CSV carries a `source_url` column. `verify.py` fails the build if a row lacks one.
- Values were transcribed by hand into `nba-commission/data/*.csv` after fetching through the platform
  page fetcher (the sandbox cannot reach nba.com over curl; outbound TLS is restricted to GitHub hosts).
- Fetches happen once, on 2026-11-05 (UTC). The snapshot date is displayed on every page. A later
  reader must assume the live pages have moved on.

## 2. Verification protocol (all executed by `compute.py`, re-executed by `verify.py`)

**X01** W-L agreement across two independent official renderings (standings vs team traditional): 30/30.
**X02** `GP = W + L` on every team row: 30/30.
**X03** HOME + ROAD + NEUTRAL wins/losses sum to the team record: 30/30.
**X04** Σ(net points/game × GP) over 30 teams is within ±2 of zero (1-decimal rounding): 0.7.
**X05** PTS and REB identities on every game-log row: 137/137.
**X06** Per-player averages recomputed from the logs equal the official nba.com headline averages,
using round-half-up (33.25 → 33.3, which Python's `round()` would turn into 33.2).
**X07** No duplicate `(player_id, game_id)` across the two log files: 0 duplicates.
**X08** The inherited 2025-26 prior table is internally consistent (GP = W + L; Σ(net × GP) = −16.4,
consistent with 1-decimal row rounding — recorded as flag F12 rather than silently fixed).
**X09** Slate integrity: 11 unique game ids, every team present in the standings table.
**X10** Six 2025 (Nov 19, 17, 15, 14, 10, 09) Edwards rows re-fetched independently: 6/6 exact match.
**X11** The earlier board's published PTS × 3PM correlation recomputes exactly (0.6893).
**X12** Staleness reconciliation: the 2026-11-03 snapshot plus the 14 official 2026-11-04 games equals
the 2026-11-05 standings for all 30 teams, with zero unexplained differences.

## 3. Own game lines

Definitions, per team *i*, using official per-game values:

```
off_i   = PTS/g_i  − lg_avg          (points scored above league average)
def_i   = PA/g_i   − lg_avg          (points allowed above league average)
PA/g_i  = PTS/g_i  − net_i           (exact up to the page's 1-decimal rounding)
est_x   = w · x_current + (1 − w) · x_prior,   w = GP_i / (GP_i + K)
home_pts = lg_avg + (est_off_home + est_def_away)/2 + HFA/2
away_pts = lg_avg + (est_off_away + est_def_home)/2 − HFA/2
spread   = home_pts − away_pts        total = home_pts + away_pts
```

`lg_avg` = 113.43 points (GP-weighted across the 30 official 2026-27 rows); the 2025-26 prior league
average is 115.61. Both are printed on the site rather than left implicit.

**Parameters are choices, not measurements** and are named as such everywhere:

- `K_BLEND = 20` — shrinkage constant. With 9 games played, w ≈ 0.31, i.e. the prior season carries
  about 69% of the weight. Sensitivity at K = 10 and 40 is published per game.
- `HFA = 2.5` points (split ±1.25 per side) — an assumption (F02). The 2026-27 home/road split
  (62–59, p = 0.856) does not pin the size of the home edge. A 0.0 run is published too.
- Publication rounding: spread and total are rounded to the nearest 0.5. The unrounded values are also
  published so a reader can verify the arithmetic.

**No market input touches the model.** Market columns exist in the schema and are blank.

## 4. Player props

```
own_line = round_to_half( (K_PROP · mean_2025-26 + n_2026-27 · mean_2026-27) / (K_PROP + n_2026-27) )
K_PROP   = 20
```

Empirical `over` and `push` rates are the share of the player's 137 pooled games strictly above / exactly
on the published line. They are descriptive statistics of the sample, not probabilities of a bet winning:
they ignore opponent, usage, rest and availability, and the sample is two players.

## 5. Correlations

- Pearson r, computed in-repo; 95% intervals via Fisher z with se = 1/√(n−3).
- Team level: n = 30 team rows (2026-27).
- Player pairs: n = 137 pooled game rows, plus a same-pair re-test inside each season (125 and 12 rows).
  The 2026-27 column is a genuine out-of-sample check of the 2025-26 value.
- Prop combos: 2×2 joint tables at fixed thresholds; φ for dependence; lift = P(both) / (P(A)·P(B));
  "fair odds if independent" = 1/(P(A)·P(B)); "fair odds, empirical" = 1/P(both). The gap between them is
  the mispricing a marginal-multiplying parlay would create.
- Serial independence: lag-1 correlation of each player's own points across date-ordered games.

Correlation is not causation, and a near-zero lag-1 value does not prove independence — it fails to
detect dependence at this sample size.

## 6. Luck vs skill

- Break-even rate for a single −110 price: 110/210 = 0.523809… (arithmetic, not an NBA statistic).
- Power: smallest n for which a **one-sided exact binomial test** of the break-even rate rejects at
  α = 0.05 with probability ≥ 0.80 (and ≥ 0.90) when the true rate is p₁. The normal approximation
  locates the answer; the exact binomial tail is then scanned in a narrow window around it. The
  approximation is printed alongside so the difference is visible (55%: exact 2,248 vs normal 2,242).
- Two-sided exact binomial p-values use the probability-ordering definition (sum of all outcomes at
  least as unlikely as the observed one).
- Family-wise error: Bonferroni α = 0.05/m and Šidák 1 − (1 − α)^(1/m) for m = 8 pre-registered strategies.
- Deflation: `deflated_rate = (wins + K·p₀)/(n + K)` with K = 25 and p₀ = break-even. A 55–45 record
  deflates to 0.5448. No raw win rate is ever displayed on the leaderboard.
- No Sharpe-ratio statistic is computed, because no return series exists. The Deflated Sharpe Ratio is
  cited as the framework that would be required once a return series exists — implementing it on a
  nonexistent series would be theatre.

## 7. Gates and certification

A strategy is certified only when **every** applicable gate passes. `FAIL`, `BLOCKED` and `PENDING`
all count as not passed. At this snapshot: 4 PASS, 1 PARTIAL, 2 BLOCKED, 2 PENDING, 3 FAIL/other —
and therefore 0 of 8 strategies certified. Gate definitions are project policy anchored in published
method (multiple-testing corrections, deflation for selection bias, market-efficiency limits).

## 8. What is deliberately absent

- Odds, de-vigged probabilities, edge, CLV, ROI, bankroll, staking advice (F01).
- Moneyline win probabilities (F08).
- Injury/availability state (F04, F11) and operator settlement rules for props (F10).
- Any claim that a line is "better" than the market: no market is in evidence.

## 9. Reproduction

```
python3 nba-commission/compute.py    # rebuild outputs.json, run X01–X09 and the arithmetic checks
python3 nba-commission/build.py      # regenerate 14 pages deterministically
python3 nba-commission/verify.py     # provenance + link + render + idempotency audit
python3 -m unittest discover -s nba-commission/checks
```

`compute.py` is deterministic: rerunning it produces a byte-identical `outputs.json`, which `verify.py`
asserts.
