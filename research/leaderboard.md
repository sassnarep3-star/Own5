# Leaderboard Competition Design (T6)

A standing competition that rewards **repeatable, skill-based origination** — not hot streaks.

## Entry

1. Strategy spec pre-registered in this repo (Gate G0) with a version hash.
2. Passed Gates G1–G8 (see `validation-gates.md`).
3. All bets logged pre-game with timestamp, market, line/price at bet, stake, and strategy hash. Late or retroactive entries are void — no cherry-picking by construction.

## Scoring (anti-luck by design)

| Component | Weight | Definition |
|---|---|---|
| **Shrunken CLV score** | 70% | Mean de-vigged CLV (bps), empirical-Bayes shrunk toward 0 by sample size. Primary skill metric — see `skill-vs-luck.md`. |
| **Flat-stake yield** | 20% | 1-unit ROI, reported with bootstrap 95% CI. Informational; cannot rescue a negative-CLV record. |
| **Process score** | 10% | Gate-compliance audit: timestamp integrity, spec adherence, falsification criteria honored. |

**Minimums:** 200 graded bets to appear on the board; 500 to be reward-eligible (CLV sample-size guidance: https://www.sportsbettingoddscalculator.com/guides/closing-line-value — convention, flagged).

## Divisions

- **Singles** (sides/totals/ML)
- **Player props** (single-leg props)
- **Parlays & SGP/prop combos** (must additionally pass Gate G7 correlation audit; scored on parlay-level CLV vs. the book's correlated price)

## Rewards

| Tier | Requirement | Reward |
|---|---|---|
| Gold | #1 shrunken-CLV in division, ≥500 bets, PBO < 5% | Full prize share + spec published as reference strategy |
| Silver | Top 3, ≥500 bets | Partial prize share |
| Bronze | Positive shrunken CLV, ≥200 bets, all gates passed | Recognition + priority data access |

(Reward *amounts* are an operator decision; nothing here implies a funded prize pool exists today.)

## Anti-gaming rules

1. **No result-based ranking.** Profit alone never moves rank — only shrunken CLV and process.
2. **All variants count.** Every tried variant must be registered; the multiplicity count feeds Gate G4 (DSR/PBO). Hiding failed variants = disqualification. (PRIMARY: https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
3. **Stake caps.** Max 2% bankroll nominal per bet; fractional Kelly enforced (Gate G8).
4. **Decay.** Scores computed on a rolling 2-season window so retired edges age off the board.
5. **Audit trail.** Any bet whose line/price can't be verified from the captured odds snapshot is excluded and listed on the Flagged for Review page.

## Current standings

**EMPTY — by design.** No strategy has passed the gates yet; publishing a fake leaderboard would violate the project's no-fabrication rule. The board populates only from logged, gate-passing records.
