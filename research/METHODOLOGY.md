# NFL line origination and evidence standard

As of 2026-11-02. **Research specification, not a fitted model or betting advice.** No historical predictions, empirical correlations, profits or funded rewards exist in this repository. Unknown empirical fields are JSON `null` and render as empty cells with an accessible “Unverified” label. Official source definitions do not establish profitable signals.

## Executive summary

The repository began with only `README.md` containing `# Own5`. The deliverable is a static, source-linked research dashboard, an eight-candidate strategy registry across singles, player props, parlays and prop combinations, seven mandatory validation gates, a correlation research plan, proposed competition governance, a tested mathematical utility module, and an explicit evidence-gap register. There are zero fitted or eligible strategies. No bet is recommended and no money is placed.

The immediate bottleneck is a licensed/authorized historical official-source dataset joining game/player outcomes, pre-decision features, market snapshots, and exact settlement rules. Public current-season tables are not an as-of history. No missing values are inferred. Availability of public pages does not establish permission to bulk collect or redistribute data.

NFL outcomes contain irreducible randomness. The objective is reproducible evidence of incremental predictive skill and positive risk-adjusted expected value, not removal of luck. Confidence intervals and significance tests cannot guarantee future returns. Gate thresholds are **project policy**, not officially endorsed requirements.

## Source verification and scope

See [the machine-readable source register](../data/research.json) for URLs, review date, checked finding and limitation. Each dashboard table row links the relevant primary publisher. For proposed methods/policies the link is a methodological reference, **not independent verification of that policy or strategy**. Local code, inventory counts and project status are repository observations. Source review involved reading the relevant text excerpts; it was not an audit of every line of each external website. The source register distinguishes these scopes.

## Data contracts and automatic abstention

Required game records: `event_id`, season, week, kickoff_utc, home/away team IDs, final scores, result_source_url, result_capture_utc, rule version. Player outcomes also require stable player ID, team, participation, statistic definition and official game-level source. Feature rows require `event_id`, `feature_name`, `value`, `published_at_utc`, `captured_at_utc`, official source URL and immutable raw snapshot hash. Historical aggregates must use only rows known at the prediction cutoff; no end-of-season summaries for earlier games.

Market records: operator, jurisdiction, event_id, player_id (if applicable), market/period, selection, threshold, decimal odds, captured_at_utc, official source URL, rule snapshot, actual quote acceptance/limits if available. Combo records require leg IDs, quoted combined decimal price and a state-dependent settlement function. A closing quote is an evaluation label, never an input to an earlier prediction.

Prediction ledger: strategy version/code hash, model/training-window hash, feature cutoff, prediction timestamp, game kickoff, marginal probabilities, push/void probabilities, joint distribution if applicable, offered price, selection/abstention reason and evidence links. Append-only records must precede kickoff. Unsupported timestamps, unmatched IDs, ambiguous definitions, no quote or incomplete rules produce **ABSTAIN**, not defaults. This session has no authorized complete dataset; `predictions` is empty. No claim of a working continuous data importer or trained forecasting service is made.

## Model research roadmap

1. Build team strength from lagged official game outcomes with regularization and opponent adjustment. Fit a joint discrete home/away scoring model with training-only hyperparameter selection. Examine overtime/rule-regime drift. Compare with a simple lagged average and no-vig market when prices exist.
2. Add possession/pace and official pregame availability only when historical release/capture timestamps exist. Treat unknown availability as uncertainty; do not invent injury-to-performance coefficients. Compare frozen ablations on identical folds.
3. Model props hierarchically: opportunity/volume, then conditional efficiency. Use the NFL Next Gen Stats glossary for feature meaning, not as evidence of predictive efficacy. Lag all inputs and account for role changes; injury designation alone is not a probability of playing.
4. For same-game combinations, share latent game scenarios across legs and price the full settlement distribution. Check simulation convergence, marginal calibration, joint-hit calibration and impossible outcome constraints. Pairwise correlations do not identify a multivariate distribution. A copula or simulation family requires held-out checking, not assumed dependence.
5. Price only after the exact market, line and settlement rule are known. Raw score means are insufficient to quote cover probabilities at key integer thresholds. All proposed strategies remain blocked until trained and evaluated.

## Pricing mathematics (derived identities, not observed NFL values)

For unit stake, win probability `w`, push probability `u` and decimal offered odds `d`, assuming no void/partial settlement: net EV = `w*(d−1) − (1−w−u)` = `w*d + u − 1`. Setting EV to zero gives fair decimal `d* = (1−u)/w` for `w > 0`. With no push, `d*=1/w`. Void or partial-parlay settlement requires explicit outcome states; never reuse this formula without the matching assumptions.

American to decimal: positive A => `1 + A/100`; negative A => `1 + 100/abs(A)`. Conventional American quotes have absolute magnitude at least 100. Decimal odds include stake. No empirical odds are provided in this release.

For a complete, mutually exclusive no-push market, proportional de-vig gives `q_i=(1/d_i)/Σ_j(1/d_j)`. This is a declared normalization convention, not the true event probability, and may be inappropriate for asymmetric margins. Missing sides, mixed periods or mismatched timestamps block the comparison. Closing-line value compares prices only at identical market definitions and thresholds; a better closing price is not proof of profit or skill.

For two Bernoulli leg indicators, the phi/Pearson correlation may be computed from matched observations at the **frozen thresholds**. For two events, joint probability is bounded by `max(0,pA+pB−1) ≤ pAB ≤ min(pA,pB)`. These bounds are not an estimate. For general combos use `EV = Σ P(state) × net_return(state)` including repriced pushes/voids, not product of marginal probabilities. `scripts/analytics.py` implements small input-checked utilities; it is not an end-to-end sportsbook or trainer.

## Correlation estimation plan

All C01–C06 empirical cells are blank. Acquire matched game-level records, log pair construction, date window, missingness and selection rules. Report paired n and number of independent game/week clusters separately, Pearson for continuous outcomes, rank sensitivity for nonlinear/outlier effects, and phi for binary leg wins. Constant inputs are undefined, never zero. Estimate uncertainty by resampling games/weeks as blocks so shared players and overlapping bets stay together; ordinary iid intervals can overstate precision. Compare raw and training-only residualized associations controlling for pregame opportunity, opponent and roster. Check windows/roles and shrink unstable estimates using training data only. A zero linear coefficient does not prove independence. Never assume the sign from a football narrative.

## Validation and competition

G01–G07 in the dashboard are sequential, mandatory project policies. Preregister chronological train/validation/test windows, grouping by game/week and a gap suitable to feature lookbacks; irregularly spaced game rows require custom splits (the official TimeSeriesSplit docs warn about equal-spacing assumptions). Fit transformations, residual models and probability calibrators only on training folds. Retain an untouched final holdout and then a nonoverlapping prospective paper window.

Measure Brier, log loss, reliability diagrams, subgroup errors, net unit return, drawdown, turnover and coverage/abstention. Score the same available opportunities and decision times; do not cherry-pick only winning placed bets. Market and naive baselines require equivalent settlement and costs. Test skill using preregistered game/week-block resampling, a 95% return interval with lower bound above zero, and valid Holm-adjusted p-values ≤ 0.05 for all tried strategies. Holm is the default because testing many selected strategies creates false discoveries; invalid null designs are not cured by adjustment. Use an independent-cluster power analysis for a preregistered minimum economically relevant effect. No universal sample count proves skill.

Rank only eligible candidates within the same division and fixed prospective evaluation period by lower clustered return bound, tie-breaking with log loss then drawdown. Each eligible strategy needs independent reproducibility review. Compare strategy-return correlations to limit duplicate exposures. Proposed badges are non-cash; monetary rewards are disabled. There is no sponsor, prize budget, payout system, or active contest. Stop or abstain when data provenance fails, rules change or preregistered risk constraints are exceeded. Do not optimize real-money stakes in this release.

## Boundaries

No user account, API key, manual upload, funds, personal data or betting authorization was requested. The dashboard runs without a backend and never transmits bets. Operator rules retrieved were Virginia-specific; legality and eligibility in any jurisdiction are not determined here. Flagged items are published, nonblocking research limitations rather than fabricated completions.
