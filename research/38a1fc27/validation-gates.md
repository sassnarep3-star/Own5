# Validation gates

A strategy is **CERTIFIED** only when every hard gate passes. The gate set, thresholds and
multiplicity count are published before results are inspected (pre-registration, G0).

| Gate | Requirement | Threshold | Why |
|---|---|---|---|
| **G0** | Pre-registration | Rule, threshold and window committed before results | Stops post-hoc threshold selection |
| **G1** | Minimum sample | n ≥ 300 graded bets to list; power check to certify | At 80% power, distinguishing 55% from 52.38% needs ≈ 2,241 bets |
| **G2** | Significance vs multiplicity | Exact two-sided binomial p < 0.05/k **and** win rate above break-even | Bounds false discoveries; a significant *loss* is not a pass |
| **G3** | Chronological holdout | Final 30% of bets clears break-even on its own | Guards against fitting the past |
| **G4** | Closing-line value | Mean CLV ≥ 0 against a verified close | Industry skill metric; needs a price history |
| **G5** | Correlation cap | \|r\| < 0.50 with every live strategy on overlapping bets | Prevents duplicate exposure |
| **G6** | Drawdown | Max drawdown < 20 units per 100-unit bankroll | Risk control |
| **G7** | Staking | ≤ quarter Kelly, ≤ 2% bankroll per bet | Caps variance |
| **G8** | Market integrity | Every price traceable to a verified operator/official source | Aggregator prices do not qualify |
| **G9** | Parlay correlation | No correlated legs without the operator's same-game price | Independently-priced correlated legs are a guaranteed loss |
| **G10** | Grading integrity | Official final scores; pushes void; inactive players void props | Stops mis-graded results |
| **G11** | Liquidity | Stake within posted limits | Operational |
| **G12** | Responsible gambling | Adults, legal jurisdiction, 1-800-GAMBLER | Applies always |

## Current gate ledger

- Variants tested: **7** → Bonferroni α = 0.05/7 = **0.00714**
- Best pass count: **7 of 12** evaluated (G5 is not scored for strategies with no overlapping
  bet history; G8/G4 fail by construction).
- **Certified strategies: 0.**

## Why G4 and G8 cannot pass

No official NFL or operator source publishes historical closing lines with timestamps, and the only
market line available to this repo is an aggregator value of unknown timing. Until S01 is
implemented, the honest statement is "no strategy is certified", regardless of how good a backtest
looks.
