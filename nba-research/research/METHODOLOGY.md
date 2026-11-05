# Methodology

## 1. Evidence boundary

The frozen snapshot is dated 2026-11-05. Raw factual rows carry official NBA or official-operator URLs. Derived rows carry the official input URL and are labeled as calculations. Model constants and competition thresholds are **analyst policy choices**, not NBA facts. Unknown values are empty and appear in the review register.

The page fetcher returns rendered text rather than response headers or byte-for-byte HTML. We record source URLs and retrieval dates, not invented response hashes. CI rebuilds frozen inputs; it does not claim to re-fetch dynamic NBA or sportsbook pages. See [DATA_NOTES.md](DATA_NOTES.md).

## 2. Team line origination

For team statistic `x ∈ {OffRtg, DefRtg, PACE}`:

1. Compute possession-weighted league centers in the current and prior seasons.
2. Center each team against its season center.
3. Blend with current weight `w = GP / (GP + 20)` and prior weight `1-w`.
4. Add the current league center back.

`K=20` is a disclosed shrinkage policy, not a fitted or official estimate. Current samples are only 6–9 games; roster/coach changes are not adjusted.

For a matchup:

- `expected_pace = (home_pace + away_pace) / 2`
- `home_points = ((home_OffRtg + away_DefRtg) / 2) × expected_pace / 100`
- `away_points = ((away_OffRtg + home_DefRtg) / 2) × expected_pace / 100`
- `fair_total = home_points + away_points`
- `fair_home_spread = away_points − home_points`

The division by two is essential: each rating is points per 100 possessions for one team, so offense and opponent defense are averaged before applying pace. A unit test pins this identity.

Home advantage is **zero** in the baseline because no verified point estimate was collected. Sensitivity scenarios are −2, 0 and +2 margin points, split symmetrically across teams so the total is unchanged. These are scenarios, not estimates. No calibrated margin distribution was collected, so moneyline probability and expected value remain blank.

Market comparison uses the archived FanDuel snapshot. No-vig probabilities normalize the two implied American-price probabilities. Spread/total model differences are reported in points only. They are not EV, recommendations or executable edges.

## 3. Correlation and prop combinations

The sample is 64 Dončić and 61 Edwards games. It is not league-wide and not the top two scorers: official 2025–26 leaders rank Dončić first, Gilgeous-Alexander second and Edwards third.

We report:

- raw pooled Pearson correlations, labeled descriptive;
- per-player Pearson correlations;
- player-centered pooled correlations, which subtract each player’s mean to expose aggregation effects;
- conditional 95% moving-block bootstrap intervals (1,000 replicates, block length 5, seed 20261105), stratified by player;
- exact joint hit counts for fixed exploratory thresholds, the independence product, lift and two-leg phi;
- Clopper–Pearson intervals for per-player joint events, explicitly conditional on independent games within that player;
- adjacent logged-game points lag-1 only as a serial diagnostic.

Centered pooled intervals are omitted rather than treating centered values as raw observations in a bootstrap. With only two selected players, no interval is population-generalizable. Lag-1 scoring association does **not** establish independence of actual parlay legs. Shared games, slate effects, overlapping legs, pushes and voids require an exact-leg joint model or empirical joint outcomes. Gate G05 stays blocked.

For positive dependence, `P(A∩B) > P(A)P(B)`: multiplying marginals **understates** the joint hit probability. That correction still does not produce a market price without the offered combo odds and settlement terms.

## 4. Skill versus luck

The implementation includes:

- exact binomial upper tails and critical values;
- exact minimum sample size for a stated alternative and power (normal approximation is only a starting point);
- Clopper–Pearson confidence bounds by bisection;
- Holm step-down adjusted p-values;
- Deflated Sharpe Ratio with skewness, Pearson kurtosis and the expected maximum over the declared trial family;
- combinatorially symmetric cross-validation PBO for an aligned trial-return matrix.

At a hypothetical −110 price, break-even is `110/210 = 0.52381`. Exact 80% power for a true 55% hit rate requires 2,248 independent bets at one-sided α=0.05, or 4,055 at α=0.05/8. These are power calculations, not observed results. Dependence reduces effective sample size; the independent-bet figures are lower bounds on the evidence burden.

DSR requires the full comparable trial family and an externally justified effective trial count/effective-N. PBO requires a complete aligned trial-return matrix. Neither can repair undisclosed searching. With no settled/prospective ledger, ROI, CLV, DSR, PBO and skill claims remain blank.

## 5. Fail-closed gates and leaderboard

Eight candidates were registered before any settled-bet evaluation. The registry hash is in `data/preregistration.json`. Any later parameter search must be registered before outcomes and increases the family.

All ten gates must pass: official provenance/schema; frozen pre-registration; point-in-time leakage audit; power/effective sample; exact-leg dependence; out-of-sample market calibration; net economics/uncertainty; selection-bias control; prospective replication/execution; reproducible fail-closed release. Missing evidence is `BLOCKED`, never an optimistic default or a zero score.

Only certified strategies can rank. The current leaderboard has zero rows. Rewards are non-cash badges under a disclosed policy; no funded cash prize or payout mechanism is verified. See [LEADERBOARD.md](LEADERBOARD.md).

## 6. Repository audit scope

`audit_repo.py` scans every file at baseline `54e8dee596d49731c3da535a1f77b01cd0c295d5`: UTF-8 decode, line count, SHA-256, Python AST, JSON parse, Node syntax where available, CSV schema/header/row-source coverage, HTML links/ids/placeholders. It records exact GitHub review links. This is a structural/provenance audit, not a claim that every historical sports fact in every inherited file was independently re-fetched. The new snapshot and reused player sample have the separate official re-review scope documented in DATA_NOTES.md.
