# Reward leaderboard design

## Current state

- Registered candidates: 8 across Singles, Cross-game parlays and Player-prop combinations.
- Certified entries: 0.
- Leaderboard rows: 0. Ranks, scores and rewards are empty, not zero-filled.
- Settled/prospective bets: 0. No performance is invented.

## Entry rule

A strategy enters the leaderboard only when **all ten gates** in `data/gates.csv` are `PASS` and the release checks pass. Missing evidence is `BLOCKED`. A blocked strategy is not ranked last with a fabricated score; it is absent from the ranking.

The ten gates cover provenance/schema, frozen pre-registration and trial count, point-in-time leakage, power/effective sample size, exact-leg dependence/joint pricing, out-of-sample market calibration, net economics/uncertainty, selection-bias control, prospective replication/execution, and reproducible fail-closed release.

## Scoring

1. **Primary:** Deflated Sharpe Ratio, using the full effective comparable trial family and the same return frequency. Require DSR ≥ 0.95.
2. **Tie-breaks:** lower uncertainty bound on net ROI after vig/fees/voids, then CLV. Unresolved ties share rank.
3. **Diagnostics:** CSCV/PBO ≤ 0.50 when a valid aligned trial-return matrix exists; calibration versus the applicable no-vig market; exact joint settlement handling.

These thresholds are analyst competition policy informed by the cited primary methods, not NBA or sportsbook rules. CLV is a benchmark diagnostic, not a substitute for settled net economics.

## Divisions

- Singles: spread, total and calibrated moneyline candidates.
- Cross-game parlays: two- and three-distinct-game candidates with validated joint pricing.
- Player-prop combinations: same-game multi-stat combos and distinct-game player props.

A strategy may compete in only its declared division. Cross-division comparison uses the same risk-adjusted score but does not merge settlement rules.

## Rewards

| Tier | Eligibility | Reward |
|---|---|---|
| Gold | Rank 1; at least one certified entry | Non-cash digital badge |
| Silver | Rank 2; at least two certified entries | Non-cash digital badge |
| Bronze | Rank 3; at least three certified entries | Non-cash digital badge |
| Cash pool | Verified funding and payout mechanism required | **Blank — unverified; not offered** |

No badge is awarded in this snapshot because no strategy is certified. No cash prize, payout processor, winner or reward balance is verified. Funding and payout details remain blank and flagged (R09).

## Anti-gaming rules

- Register rules, thresholds and the complete trial family before looking at outcomes; hash the registry.
- Any later parameter search increases the family and must be registered before evaluation.
- No selective deletion, retroactive rule changes, survivor substitution or fabricated settlement.
- Preserve pushes/voids and the exact operator/jurisdiction rules for every leg.
- Require auditable timestamped quotes and decision logs; archived dynamic renders are not execution records.
- Replicate in a predeclared prospective window before certification.

## Primary references

- Bailey & López de Prado, *The Deflated Sharpe Ratio*: https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf
- Bailey, Borwein, López de Prado & Zhu, *The Probability of Backtest Overfitting*: https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf
- Official operator market definitions: https://sportsbook.draftkings.com/page/nba-player-props
