# Decision-readiness questions

The machine-readable [`decision_questions.csv`](../../nfl-b34253a1/data/decision_questions.csv) contains 16 questions with known evidence, missing information, answer needed before decision, discovery steps, status, and source links. The [interactive-readable Questions page](../../nfl-b34253a1/questions.html) renders the full matrix.

## Short answers

- **Intended use?** The current artifact is a static research snapshot. It does not place bets, issue picks, or establish a licensed/compliant wagering service. A project owner still needs to approve the public use boundary.
- **Can the Week 10 quote be treated as live/executable?** No. The records are dated 2026-11-12; exact UTC capture time, jurisdiction, accepted price, limits, and closing price are not retained.
- **Are the own lines calibrated probabilities or fair prices?** No. They are symmetric score-line baselines (team PF/G and opponent PA/G), with zero HFA and no injury adjustment.
- **Is the model evidence of skill?** No. Week 2–9 one-season walk-forward metrics are descriptive, not a bet ledger or net return test.
- **How many points does a second/third/fourth string replacement cost?** Unknown. No validated position/player-specific point coefficient is available; adjusted lines are blank.
- **Are player props or parlays priced?** No. The paired player-game outcomes, precise offered lines, joint settlement data, and/or combined prices are missing; the affected correlation rows are blank.
- **Are any strategies ranked or rewarded?** No. G0 passes; G1–G10 are blocked, no strategy has graded bets, and no reward is funded.
- **Are all NFL teams injury-cleared?** No. 76 selected observations cover 17 teams; the tracker is not exhaustive. Four Week 10 bye-team chart pages were added for source coverage, not injury conclusions.
- **Should the site be integrated into existing dashboards?** Awaiting reviewer choice among isolated-only, a shared navigation link, or consolidation. No shared root/dashboard was edited.

## Required before any stronger claim

1. Define jurisdiction, intended use, and user eligibility with appropriate review.
2. Establish a lawful, time-stamped market quote archive with jurisdiction, event/market IDs, prices, and closing prices.
3. Record pre-event predictions/features, model hash, lineup cutoffs, exact price, settlement/push/void, and all attempted strategies in an append-only ledger.
4. Obtain paired player-game and prop data with exact lines and settlement definitions for joint outcomes.
5. Pre-register a useful effect size, power/sample design, clustering unit, multiplicity family, and independent time-based holdout before new outcome review.
6. Resolve competition funding, scoring, eligibility, audit and dispute rules before offering any reward.

All project thresholds are proposals, not NFL standards. The absence of a value is not treated as zero, a pass, or an affirmative answer.
