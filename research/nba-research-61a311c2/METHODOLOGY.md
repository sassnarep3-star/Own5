# Methodology — NBA Research Desk 61a311c2

## Data rule

Every empirical row must carry an official NBA source URL. Operator quotes/rules carry the operator's own official URL. Method rows carry primary scientific documentation or the author's paper. Project policy rows carry the official repository URL. Unconfirmed values are `null`/blank and flagged; they are never inferred. [NBA stats](https://www.nba.com/stats) · [FanDuel NBA](https://sportsbook.fanduel.com/navigation/nba) · [SciPy Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) · [Repo](https://github.com/sassnarep3-star/Own5)

## Line origination

For team `t`, shrink current official ratings toward the possession-weighted league mean with declared `K=10`:

`w = GP / (GP + K)`  
`Off*_t = w Off_t + (1-w) LeagueOff`  
`Def*_t = w Def_t + (1-w) LeagueDef`  
`Pace*_t = w Pace_t + (1-w) LeaguePace`

For home `h` vs away `a`:

`Pace_match = (Pace*_h + Pace*_a)/2`  
`HomePts = Pace_match (Off*_h + Def*_a - LeagueOff)/100 + HFA/2`  
`AwayPts = Pace_match (Off*_a + Def*_h - LeagueOff)/100 - HFA/2`  
`HomeSpread = -(HomePts - AwayPts)`  
`Total = HomePts + AwayPts`

`HFA=0` is used because no independently fitted home-advantage point estimate is asserted. Sensitivity columns show HFA ±2 and K=5/20 totals. Official PACE is used as published; PACE/POSS non-identity is flagged rather than silently recomputed. [NBA advanced](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) · [NBA glossary](https://www.nba.com/stats/help/glossary)

## Correlation and combinations

Pearson `r` is computed within each selected player, not pooled across players for pricing. Uncertainty uses a moving-block percentile bootstrap: block length 5, 2000 resamples, seed 610311, 2.5/97.5 percentiles. This preserves short local dependence but does not prove stationarity or remove selection bias. Threshold combinations use direct joint counts; independence products are shown only as diagnostics. Three-leg pricing cannot be reduced to pairwise phi. [SciPy Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) · [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/eda334.htm)

## Skill vs luck

The points replay is chronological: minimum 20 prior games; half-step expanding median; last-5 mean at least 2 points above/below median triggers OVER/UNDER, otherwise PASS. Exact binomial tails test against 50%; Wilson intervals and Bonferroni family-6 correction are reported. This is forecast accuracy, not betting ROI. True Deflated Sharpe requires a full trial ledger, trial variance and return moments; it remains blank. [Deflated Sharpe paper](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)

## Settlement and economics

FanDuel's NBA FAQ states results use the league governing body/official data supplier, DNP player props are void, and overtime counts unless stated otherwise. DraftKings rules define parlay/SGP reduction on void/push and are operator-specific; retrieved general rules explicitly govern Virginia. No global eligibility or executable edge is asserted. [FanDuel NBA FAQ](https://sportsbook.fanduel.com/navigation/nba) · [DraftKings market rules](https://sportsbook.draftkings.com/help/general-betting-rules/market-rules) · [DraftKings general rules](https://sportsbook.draftkings.com/help/general-betting-rules/general-rules)

## Fail-closed gates

G01–G12 must all be explicitly true before qualification. Missing evidence is not a pass. Current decision: `PAPER_RESEARCH_ONLY`, 0 qualified strategies. [Repo](https://github.com/sassnarep3-star/Own5)
