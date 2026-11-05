# Mandatory Validation Gates — 61a311c2

A strategy qualifies only when every gate is explicitly true. Missing evidence fails closed. Current action: `PAPER_RESEARCH_ONLY`.

| Gate | Requirement | Current state | Source |
|---|---|---|---|
| G01 | Official source integrity | pass | [NBA glossary](https://www.nba.com/stats/help/glossary) |
| G02 | Schedule identity | pass | [NBA schedule](https://www.nba.com/schedule?date=2026-11-06) |
| G03 | Availability confirmed | blocked | [NBA injury PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf) |
| G04 | Timestamped bet/close quotes | blocked | [FanDuel NBA](https://sportsbook.fanduel.com/navigation/nba) |
| G05 | Operator settlement rules | pass, operator-specific | [FanDuel FAQ](https://sportsbook.fanduel.com/navigation/nba) |
| G06 | Chronological replay | pass, exploratory | [NBA log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |
| G07 | Sample size / exact evidence | blocked | [Deflated Sharpe method](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) |
| G08 | Multiple-testing policy | pass, policy only | [Deflated Sharpe method](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) |
| G09 | Dependence audit | blocked: cross-game blank | [Pearson method](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |
| G10 | Calibrated probabilities | blocked | [NBA glossary](https://www.nba.com/stats/help/glossary) |
| G11 | Economic realism / CLV | blocked | [DraftKings market rules](https://sportsbook.draftkings.com/help/general-betting-rules/market-rules) |
| G12 | Reward funding | blocked | [Repo](https://github.com/sassnarep3-star/Own5) |

Exact binomial, Wilson interval, Holm/Bonferroni and moving-block bootstrap utilities are implemented and unit-tested. True DSR and CLV remain blank because the required trial/quote ledgers do not exist. [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/eda334.htm) · [Deflated Sharpe](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
