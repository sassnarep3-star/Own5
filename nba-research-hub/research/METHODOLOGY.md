# NBA Research Hub — frozen exploratory methodology (2026-11-05)

## Status and honesty boundary

This protocol was written **after** the historical player logs had been inspected. It is a frozen, reproducible **retrospective** analysis plan, not prospective preregistration and not evidence that the analyst avoided outcome-guided design. Gate G02 therefore fails for every actionable strategy. No strategy is eligible for a reward until all gates pass on genuine, timestamped, graded, priced evidence.

The project separates three kinds of statements:

1. **Official observation** — a value directly read from NBA.com, the NBA injury report, or NBA Official rules and linked in the row.
2. **Derived calculation** — a deterministic transformation of linked inputs, with formula and code path. It is not an official observation.
3. **Analyst policy / context** — a chosen threshold, model assumption, operator definition, or research citation. It is not proof of a betting edge.

Unconfirmed values are empty and flagged. They are never imputed from a model, a prior repository claim, or a plausible guess.

## Evidence scope

- Team snapshots: all 30 NBA teams, 2025-26 completed regular season and 2026-27 through the November 5 refresh. Fields: GP, W, L, win%, points/game, plus-minus/game. W/L cross-checked against official standings.
- Player logs: Luka Dončić (64 games) and Anthony Edwards (61 games), 2025-26 regular season. All stored fields were compared with re-opened official tables on 2026-11-05. This is a selected two-player sample, not a league-wide random sample.
- Schedule: the nine official November 6, 2026 games. Times are Eastern as listed by NBA.com.
- Availability: the official November 5, 2026 4:00 p.m. injury report. Most November 6 teams were not yet submitted; this is not final availability.
- No verified sportsbook quote, closing line, graded wager, payout, or funded prize pool was obtained.

## Team line origination

For team t, let `off_t = PTS/G`, `def_t = PTS/G − PLUS/MINUS/G`. The allowed-points value is **derived**, not separately observed. Blend current and prior season:

`w = current_GP / (current_GP + K)`, `rating_t = w*current_t + (1-w)*prior_t`, with frozen `K=20`.

Expected points:

- `home_pts = (home_off + away_def)/2 + HFA/2`
- `away_pts = (away_off + home_def)/2 − HFA/2`
- `margin = home_pts − away_pts`; `total = home_pts + away_pts`.

Primary `HFA=0` because no current home-court effect was estimated from a verified game ledger. Research lines are half-points: `floor(x) + 0.5` (v1.1 specification correction; always ends in `.5`). Home spread is `−margin`. Win probability is `1/(1+exp(−margin/6))`, an **uncalibrated heuristic**. Sensitivity grid: K∈{10,20,40}, HFA∈{−1,0,+1}; all nine variants are disclosed, not cherry-picked. No injury or minutes adjustment is applied because final availability is unknown. These are team-strength research lines, not actionable picks.

## Player forecasts and skill diagnostics

For each player and stat (points, rebounds, assists, three-pointers made), use only earlier games. Warm-up: first five games. Candidate continuous forecast: mean of up to ten prior games. Binary candidate probability at a frozen half-point threshold: normal survival function using trailing mean and sample SD (ddof=1). Binary baseline: expanding hit rate with Beta(1,1) smoothing. Continuous baselines: last value and expanding mean.

Report MAE/RMSE for continuous forecasts and Brier/log loss for binary forecasts. For each of eight player×stat series, resample **dates** with replacement (2,000 replicates, seed 20261105), preserving same-date cross-player dependence. Test candidate-minus-baseline Brier loss with a two-sided bootstrap-null p-value and 95% percentile CI; apply Holm across the eight series. A series needs at least 100 observations, adjusted p<0.05, and CI upper bound <0 to pass the predictive gate. The current series are shorter; no certification follows.

## Correlation and joint dependence

Same-game stat pairs: six unordered pairs per player. Lag-1 pairs: points/rebounds/assists/threes per player. Pearson r is descriptive. Same-game null: permute one stat vector within player (5,000 permutations). Lag-1 null: permute the next-game vector. Holm is applied across the 20 correlation tests. Game-level exchangeability is an assumption; serial dependence, role changes, and selection limit inference.

Two-prop combinations: all six unordered pairs of the four frozen thresholds per player. Report marginal hits, joint hits, product-of-marginals probability, empirical joint probability, lift, phi, and a two-sided Fisher exact p-value. Holm is applied across the 12 joint-hit tests. Three-prop combinations (four per player) are descriptive only. These are **historical research thresholds**, not sportsbook props. Positive dependence means multiplying marginals **understates** joint-hit probability; negative dependence means it overstates it. The direction is not assumed.

Cross-game parlay dependence is not estimated from two selected players. A non-significant lag-1 test does not prove independence. Cross-game joint probabilities and prices remain blank.

## Luck, power, and multiple testing

Luck cannot be literally removed. The project quantifies uncertainty and the probability of results under explicit nulls. For an American −110 example, break-even win probability is `110/210 = 0.523809…`; this is arithmetic, not an observed quote. Planning compares p0=0.523809… with p1=0.55 at one-sided α=0.05 and 80% power, using a normal approximation and reporting exact binomial power at that n. A 54-test planning family (9 model variants × 6 strategies) uses Bonferroni α=0.05/54. These are sample-size illustrations, not a promise that collecting n bets proves skill.

No real returns exist, so ROI, CLV, drawdown, deflated performance, and monetary rewards are blank. The future leaderboard ranking rule is frozen: eligible strategies only; rank by the lower 95% date-cluster bootstrap bound of mean net profit per unit stake; tie-break by more graded bets, then lower max drawdown. Rewards are badges; the funded pool is unverified.

## Validation gates

G01 provenance; G02 prospective registration; G03 chronological leakage control; G04 final availability; G05 timestamped market quotes; G06 jurisdiction-specific settlement rules; G07 dependence validation; G08 effective sample/power; G09 predictive skill vs baseline; G10 economic edge after costs; G11 multiplicity/luck diagnostics on real returns; G12 reproducibility/risk controls. UNKNOWN or FAIL blocks eligibility. N/A is allowed only with an explicit reason (e.g., joint dependence for a single). No synthetic or prospective-only ledger can pass an economic gate.

## Repository audit boundary

The line inventory hashes every physical line of every baseline tracked file and links to the pinned repository line. That is **content inventory**, not independent factual verification. Code lines are assessed by tests and behavior, not by NBA sources. Selected NBA fields receive direct official comparison; all other inherited factual claims remain unverified/manual-review. Link presence alone never upgrades a row to verified.
