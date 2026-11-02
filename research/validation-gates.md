# Validation Gates — Removing Luck from the Equation (T5)

Every strategy, signal, and leaderboard entry must pass these gates before it is trusted. Gates G01–G08 and G12 are in-repo rules (no external factual claim). Gates G09–G11 are enforced by official operator rules. Gate G04 is defined but **cannot be passed from official sources** (flag F01) — it stays "flagged", not "passed".

<!-- TABLE:validation-gates.csv -->

## Why these gates remove luck

- **G01/G02 (sample size + confidence interval):** a 5-1 start is not skill; requiring n≥30 and a 95% CI above break-even makes luck statistically unable to masquerade as edge.
- **G03 (walk-forward):** the last 25% of bets are held out; a strategy that only works in-sample is overfit, i.e., luck fitted to noise.
- **G05 (correlation cap):** two strategies that win and lose together are one bet, not two; capping |r|<0.50 keeps parlay/combo books honest.
- **G06/G07 (drawdown + quarter-Kelly):** variance control so a run of bad luck cannot compound into ruin.
- **G08 (official sources only):** no hallucinated inputs; every row in every table carries a source link or is blank+flagged.
- **G09–G11 (operator rules):** parlays with unpermitted correlated legs can be voided; grading follows official operator rules (OT included, pushes refunded, postponements void, inactive-player props void).
- **G12 (responsible gambling):** standing gate — legal age only, never bet more than you can afford to lose; help 24/7 at **1-800-GAMBLER** ([NCPG](https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/)).
