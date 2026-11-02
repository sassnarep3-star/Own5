# Executive summary · OWN5 NFL Research

**Reviewed:** November 2, 2026 UTC
**Decision:** publish the research framework; abstain from betting and performance claims.

## What has been delivered

A clean GitHub Pages dashboard with eight category pages: Overview, Strategy Lab, Line Origination, Correlations, Validation Gates, Leaderboard, Sources & Findings, and Flagged for Review. Tables are searchable and exportable; they retain official source links and render without JavaScript. Unknown empirical values are blank, never invented.

The research register contains **13 checked primary sources, 11 sourced definitions, 8 candidate strategies, 7 validation gates, 6 correlation research questions, 5 pricing frameworks, 5 competition policies and 10 review items**. These counts describe repository contents, not a statistical sample.

## Origination strategy

Develop joint team-score distributions for moneylines, spreads and totals; separate player opportunity from efficiency for props; and use joint game scenarios for parlays and prop combinations. Price the exact selection and threshold, preserving push/void states. Compare against timestamped executable operator prices only after calibration and settlement checks. Code includes tested pricing, de-vig, correlation, Brier and Holm-adjustment utilities—not a trained forecasting service.

Candidate signals include opponent-adjusted team strength, pace, pregame official availability, receiving opportunity, rushing workload, cross-game value baskets, quarterback–receiver combinations and game-script combinations. **None has demonstrated an edge.** Official definitions establish what a feature means, not whether it predicts a profitable outcome.

## Skill standard and competition

Every strategy must pass provenance, as-of integrity, preregistered walk-forward evaluation, predictive quality, dependence/payout, skill evidence, and forward replication/risk gates. Use naive and available no-vig market baselines, reliability diagrams, game/week-clustered uncertainty and multiple-testing correction. The proposed 95% interval and 0.05 adjusted-significance thresholds are project policies, not NFL standards or guarantees.

Only eligible strategies may be ranked within their market division. Rank by the lower clustered net-return bound over a common frozen evaluation window, with log loss and drawdown as tie-breakers. Proposed rewards are non-cash research badges. **No sponsor, funded cash prize, payout system or active cash contest is verified.**

## Key findings and blockers

- **Zero validated strategies and zero recommendations.** No historical prediction ledger or empirical gate evaluation exists.
- **No measured correlations.** Coefficients, sample counts, joint win rates and confidence intervals stay blank pending matched held-out data.
- **No verified EV or ROI.** A timestamped official-source odds archive and complete as-of outcome/feature history were not obtained.
- **Settlement matters.** General rules retrieved were Virginia-specific. Exact prop/combination participation and void rules remain unverified; jurisdiction eligibility is not established.
- **Luck cannot be removed.** Reproducible held-out evidence can reduce false confidence, not eliminate outcome randomness or guarantee future profit.

## Evidence and review

Each dashboard table row links a primary publisher. NFL Football Operations supplies rule context; NFL.com supplies schedule, injury and statistical-page scope; NFL Next Gen Stats supplies feature definitions; DraftKings supplies scoped market rules; official scikit-learn, SciPy and statsmodels documentation supplies methodological references. Proposed methods are explicitly labeled project designs.

See [methodology and data contracts](METHODOLOGY.md), [source verification record](VERIFICATION.md), and the published **Flagged for Review** page for evidence limitations. Initial repository audit found only a six-byte README, with no existing implementation or dataset to validate. Site build, tests, PR and deployment outcomes are documented in the root coordination board.
