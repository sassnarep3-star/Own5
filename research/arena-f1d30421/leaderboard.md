# Leaderboard Competition Design (T7)

Status: done | Owner: session arena-f1d30421 | Verified: 2026-11-02

The project is run as a strategy competition: strategies (not bettors) accumulate score, pass
validation gates, and earn rewards. Reward *amounts* below are **proposals** (design values, not
verifiable facts — flagged as such on the site).

## 1. Entries

* An entry = one strategy: market(s), signal rule, sizing rule, correlation plan, and the gates it
  claims. Entries are immutable once registered (amendments create new entry IDs) — this keeps the
  multiple-testing accounting honest (k counts every variant ever registered).
* Entry classes: `Single`, `Parlay`, `Prop-combo`. All three compete on one board with
  class-specific difficulty multipliers (parlays/prop combos need stricter G5 evidence).

## 2. Scoring (deflated, luck-resistant)

```
Score = 100 × [ 0.40 × CLV_index + 0.30 × DSR_index + 0.20 × Sample_discipline + 0.10 × Calibration ]
```

| Component | Definition | Luck control |
|---|---|---|
| CLV_index | share of picks beating the closing number, shrunk toward 50% by sample size (Beta prior) | converges fast; hard to fake (G3) |
| DSR_index | Deflated Sharpe-style probability that true edge > 0 given n, returns skew/kurtosis, and number of registered variants (Bailey & López de Prado 2014) | explicitly subtracts the expected best-of-luck score |
| Sample_discipline | min(n/500, 1) × stake-consistency factor | rewards flat, pre-registered staking |
| Calibration | accuracy of the entry's own stated probabilities vs outcomes (Brier skill) | punishes overconfidence |

Tie-breakers: (1) higher CLV_index, (2) longer live record, (3) fewer registered variants.

## 3. Seasons & phases

| Phase | Duration | Scoring window | Gate set |
|---|---|---|---|
| Open Research | ongoing | rolling | G0 only (publication required) |
| Qualification | one full NFL season (weeks 1–18) | season | G0, G1, G4 |
| Finals (live) | next NFL season | forward-only | G0–G7, G3 measured live |
| Roll-forward | continuous | trailing 2 seasons | all gates re-checked quarterly |

Backtest scores never outrank live scores; a backtest-only entry caps at Qualification tier.

## 4. Rewards (PROPOSAL — design values, not verified facts)

| Rank (after Finals) | Proposed reward | Notes |
|---|---|---|
| 1st | 40% of reward pool | must be `Validated` |
| 2nd | 25% | must be `Validated` |
| 3rd | 15% | must be `Validated` |
| 4th–10th | 2% each | `Candidate` or better |
| Participation | 0.25% per gate-passing season entry | encourages publishing losers |
| Anti-luck clawback | rewards vest 50% at Finals win, 50% after next-season G3 pass | a lucky Finals run cannot cash out fully |

Reward pool size, funding source and payout currency are owner decisions — left blank pending
instruction (flagged). The mechanics above are what "rewards for top performing strategies" means
structurally: **rewards pay for demonstrated, gate-passing, luck-adjusted skill**.

## 5. Current board (initial standings, 2026-11-02)

| Rank | Entry | Class | Gates | State | Score |
|---|---|---|---|---|---|
| 1 | S2 home dog ≥7 | Single | G1 ✓, G2 ✗ (p=0.0134), G4 ✓ | Candidate | (scored at Finals) |
| 2 | S1 home underdog | Single | G1 ✓, G2 ✗, G4 ✓ | Candidate | (scored at Finals) |
| 3 | S5 high-total under | Single | G1 ✓, G2 ✗, G4 ✓ | Research | (scored at Finals) |
| — | S3, S4, S6, S7 | Single | G4 ✗ | Research | published outcomes |
| — | P1/P2 parlay framework | Parlay | framework | Research | no qualifying legs yet |
| — | X1–X3 prop combos | Prop-combo | framework (G5 measured) | Research | awaiting verifiable prop lines |

Scores render only once the Finals phase begins (live picks with closing-line capture); until then
rank is by gate progress — no lucky backtest ROI is displayed as a rank. This is a deliberate
anti-luck design, not missing functionality.

## 6. Integrity rules

1. All picks timestamped before kickoff; closing lines recorded at kickoff (G3 input).
2. Entry withdrawal after seeing results = forfeit (prevents survivorship on the board).
3. Every number on the board links to its computation source (G0).
4. Irregularities are published on the Flagged for Review page and do not block the season.
