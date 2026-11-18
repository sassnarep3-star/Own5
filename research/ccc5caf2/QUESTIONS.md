# Questions / information / answers — OWN5 NFL Line Originator

**Session:** `ccc5caf2` · **Date:** 2026-11-18 · **Desk:** `nfl-desk-ccc5caf2/questions.html`

What must be answered before any decision can reasonably be made, plus suggestions for discovering missing information.

## Blocking questions (cannot be closed from public data)

| ID | Question | What we have | What is missing | Blocks |
|---|---|---|---|---|
| Q01 | Which price is the benchmark for 'beating the market'? | Single aggregator line per game, unknown timestamp | Timestamped operator price history | Gate G4, certification, any skill claim |
| Q02 | Are aggregator lines closing lines, for which operator? | nflverse games.csv, no documented source/time | Provenance and timestamp | Every market comparison in the repo |
| Q04 | Are rewards cash, points, or nothing? | Reward tiers proposed, no funding decision | Owner decision + jurisdiction review | Competition launch |
| Q05 | Which jurisdiction and operator rules govern the bets? | Operator house-rule pages cited | Confirmed jurisdiction + that operator's terms | G9–G12, any live betting |
| Q18 | Is there budget for a paid odds feed? | No paid feed; aggregator lines only | Owner budget decision | Certification of skill (G4), prop backtests |

## Also blocking certification

| ID | Question | Blocks |
|---|---|---|
| Q03 | What bankroll, staking rule and maximum drawdown are acceptable? | G6/G7 evaluation, reward sizing |

## Partially answered

| ID | Question | State |
|---|---|---|
| Q07 | What defines a 'starter' — depth chart or snap share? | Snap-share inference, labelled (F05) |
| Q08 | How many points is a missing player worth? | −0.039 pts per pp of deficiency (estimate) |
| Q09 | Should practice status be a probability weight? | Judgement weights applied, provisional (F14) |
| Q10 | Do Questionable players belong in the deficiency score? | 0.5 weight applied, disclosed |
| Q14 | Is home-field really zero at a neutral site? | HFA = 0 for Mexico City; assumption unmeasured |

## Answered (policy decision recorded)

Q11 (300-bet minimum), Q12 (Bonferroni strict / exploratory 0.10), Q13 (freeze after Wednesday report), Q15 (regular season only), Q16 (fail closed on mismatch), Q17 (provenance file, tag releases per season).

## Suggestions to discover missing information

- Q01/Q02: capture operator page twice weekly (S01) or accept certification stays blocked.
- Q04/Q05: owner states jurisdiction and reward preference; publish reward terms only after (S16).
- Q06: commercial odds archive, or forward-collect prop lines from today.
- Q07: cross-check snap-share inference against club-published depth charts.
- Q08/Q09/Q10: fit per-position coefficients and activation probabilities on 2023–2026 reports.
- Q18: document the cost of the paid-odds-feed gap either way.

Full table: `nfl-desk-ccc5caf2/questions.html`.
