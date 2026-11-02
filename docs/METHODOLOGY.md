# Research protocol v0.1

## Objective and non-negotiable distinction

The project originates **independent research lines**, not sportsbook quotes. Official NFL facts, operator statements, and derived estimates are separate data classes. An official source can verify an input without endorsing a model output. Unsupported market values remain `null` and render as blank cells. No strategy is currently approved for real-money use.

Luck cannot be literally removed from a finite sample. The protocol instead separates predictive skill from short-run wagering results, controls selection bias, preserves uncertainty, and refuses qualification when evidence is missing.

## Frozen evidence in this release

- 32 official 2026 standings rows, retrieved 2026-11-02 before Week 9.
- 15 official Week 9 matchups, with venue-local times and the Madrid game flagged.
- 17 paired 2024 regular-season Burrow passing / Chase receiving observations.
- Official scoring, product, settlement, and signal-definition excerpts.
- Zero verified sportsbook quotes, current prop quotes, or out-of-sample betting records.

The standings are a snapshot, not a full game-level history. The player study is deliberately narrow and descriptive. Neither is sufficient to establish a league-wide betting edge.

## Independent line originator

For team `i`, let `n_i = wins + losses + ties`, `pf_i = PF/n_i`, and `pa_i = PA/n_i`. Let `mu` be total league PF divided by total team games. The denominator is team games, not matchups.

Use an explicitly declared empirical-Bayes-style shrinkage with `k = 8` pseudo-games:

```
attack_i  = (PF_i + k * mu) / (n_i + k)
defense_i = (PA_i + k * mu) / (n_i + k)
lambda_away = attack_away * defense_home / mu
lambda_home = attack_home * defense_away / mu
```

This is a transparent baseline, not a fitted or validated NFL model. `k` is a project assumption. Home advantage is **disabled**, not assigned an invented empirical value. The Madrid matchup is neutral-site flagged. Injury, weather, starter, rest, and coaching adjustments are blank until point-in-time evidence exists.

The score baseline uses independent Poisson distributions, truncated at 100 points per team with the remaining tail reported. It produces a research total, home fair spread, win/tie/loss probabilities, and fair American prices. A tie is a separate mass. Two-way moneyline probabilities condition on no tie; spread and total pushes remain explicit. The Poisson assumption is a known limitation for football scores and must beat stronger baselines out of sample.

**No current fair spread/total is a recommended wager.** A fair line is not an executable price, and a projected score is not an observed result.

## Predeclared strategy families

The registry is frozen before any holdout evaluation. Adding a variant increments the trial count; it does not reset the evidence standard.

| ID | Family | Signal and selection rule | Current disposition |
|---|---|---|---|
| ST01 | Points-rating singles | Shrunken PF/PA rating; require at least 3 percentage points of model-vs-market edge and 2.5 points of spread disagreement. | Research lines only; market gate blocked. |
| ST02 | Total-distribution singles | Compare the full score distribution with an operator total and both prices; require 4 percentage points of edge after push mass. | No verified totals or prices. |
| ST03 | Cross-game two-leg parlay | Two distinct games, no shared team; joint probability must include residual dependence or pass a narrow-dependence test. Require 5 points of joint edge. | No quotes or validated joint model. |
| ST04 | QB–WR same-game combo | Burrow passing yards ≥250 and Chase receiving yards ≥75 in the historical study; estimate joint hit rate directly, not as a product of marginals. | Descriptive only; no current prop market. |
| ST05 | Role-stability player props | Require verified targets, routes, snap share, opponent allowance and participation; use training-only shrinkage and a predeclared volume threshold. | Required tracking/role inputs unavailable. |
| ST06 | Market-disagreement filter | Independent model and de-vigged market must disagree by at least 4 points; reject stale quotes, thin limits and unexplained line moves. | No authorized market feed. |

Thresholds and `k` are **project design choices**, not official NFL values or empirically optimized claims. They must not be changed after looking at a holdout.

## Correlation and combination pricing

For continuous yards, report Pearson `r`, Spearman rank correlation, and a paired bootstrap interval. For binary legs `A` and `B`, report:

```
phi = (P(A∩B) - P(A)P(B)) / sqrt(P(A)(1-P(A))P(B)(1-P(B)))
lift = P(A∩B) / (P(A)P(B))
```

The empirical joint frequency, marginal frequencies, independence product, and their difference are all retained. Zero denominators produce blank values, not fabricated correlations. The 17-game interval is uncertainty, not proof of causation or transportability to another season.

For a two-leg ticket with decimal prices `d1,d2`, fair independent decimal pricing is `d1*d2` only when the legs really are independent and void rules are compatible. Same-game legs generally are not independent. A shared pace, script, target share, or quarterback can induce positive or negative dependence. Pearson correlation alone does not identify a joint betting distribution.

The engine includes exact binary joint bounds, joint-price sensitivity, de-vigging, push-aware expected value, and settlement-aware parlay returns. It does **not** invent an SGP copula from one correlation. Operator-specific void/reprice rules must be supplied before a ticket can be evaluated.

## Validation gates — all must pass

Unknown is not pass. A failed or unavailable gate blocks qualification and rewards.

| Gate | Requirement |
|---|---|
| G00 Provenance | Every input has an official-source URL, evidence excerpt, retrieval time, and reconciliation status. Missing values stay missing. |
| G01 Point-in-time | Forecast and quote timestamps precede kickoff; features use earlier games only; no retroactive injury/roster information. |
| G02 Settlement | Exact operator, jurisdiction, rule version, push/void/reprice treatment, and official settlement result are recorded. |
| G03 Sample | At least 500 settled selections, 100 distinct season-week clusters, and 3 completed seasons. These are conservative project minima, not a power calculation. |
| G04 Walk-forward | At least 3 expanding-window folds, a one-week embargo, and a final untouched holdout. No random split of plays from the same game. |
| G05 Forecast skill | Brier and log-loss improvements over a frozen baseline have positive multiplicity-adjusted lower bounds; calibration error ≤0.03. |
| G06 Economic skill | Net ROI lower bound >0.5% and mean CLV lower bound >0.2%, after prices, pushes, voids and costs. Flat stakes are used for qualification. |
| G07 Multiplicity | One-sided family alpha 0.05 across all 6 registered families; Bonferroni per-test alpha 0.05/6. All abandoned trials count. |
| G08 Dependence | Joint events are calibrated out of sample; uncertainty resamples whole season-weeks. Same-game independence is never assumed by default. |
| G09 Robustness | At least 70% of evaluated seasons have positive net ROI; flat-stake maximum drawdown ≤20 units; declared sensitivity settings do not reverse the conclusion. |
| G10 Reproducibility | Locked configuration, deterministic outputs, passing tests, source audit, internal-link check and successful static build. |

CLV compares the decimal price obtained with the de-vigged closing price for the same selection: `decimal_taken / fair_decimal_close - 1`. It is a diagnostic, not a substitute for realized out-of-sample expected value. A strategy can have positive CLV and still lose money.

The bootstrap implementation resamples season-week clusters, keeping all legs and tickets in a week together. A stationary block variant is provided for ordered weeks. Confidence bounds are research diagnostics; they do not eliminate regime change, selection bias, or model misspecification.

## Leaderboard and rewards

Only strategies passing every gate enter the performance leaderboard. Rank by net ROI lower confidence bound, then CLV lower bound, then Brier skill. Raw profit and hit rate do not determine eligibility.

The competition awards **non-cash research points**: 100 to first, 60 to second, 40 to third. No points are issued for an empty qualified field. Ties share the same rank. This release has no qualified entries and therefore no performance ranking or reward allocation. Synthetic unit tests are never leaderboard results.

## Future data contract

`nfl_model.contracts` defines the required market, forecast and settlement fields. A future authorized collector must preserve raw responses and official source links, normalize team/player identifiers, and append immutable snapshots. It must never turn an unavailable price into a consensus estimate. The current release does not claim to have such a feed.

## Responsible scope

This is research software, not betting execution, a guarantee, or personalized financial advice. Do not use nonpublic information. NFL personnel and other restricted persons must follow their applicable policies. No wager is placed by this project.
