# Research design and validation policy

## What the study actually contains

This is a retrospective research demonstration, not a live wagering service. The [NFL Football Operations game file](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv) contains 91 games in the first six weeks of 2017. Its designated-home label includes games outside a team's usual home venue. Do not interpret it as proof of home-field advantage. The two player-pair samples are manually transcribed from the four [NFL.com logs in the source register](SOURCES.md). No missing QB row is converted to zero.

Every game row is a direct copy of fields in a pinned official NFL file. Player rows are checked transcriptions of the official NFL pages. Correlations, model probabilities, fair-price conversions and backtest statistics are **our calculations**, not NFL-published statistics. The samples were known before this analysis; model definitions and thresholds were not independently registered in 2017. Thus the rolling results are retrospective and not a genuinely untouched, prospective test.

## Model definitions

For each game week, generate all forecasts before updating anything with that week's outcomes. Weeks 1–3 establish history; evaluate 2017 Weeks 4–6 (44 games). In Week 5, Week 4's games are prior data; likewise for Week 6. Thus this is a sequential/rolling evaluation, not one fixed training set. No games in the source sample ended tied. The code excludes ties from the binary scoring if present and uses a half-result for the Elo update.

1. **50/50 reference:** home win probability `0.5` for every decisive game.
2. **Weekly Elo:** every team starts at 1500; with home/visitor ratings `Rh`, `Ra`, `p_home = 1/(1+10^((Ra-Rh)/400))`. Each week's results update both teams after all forecasts, using `K=20`; no venue or neutral-site adjustment. These constants are simple research choices, not officially verified facts.
3. **Prior margin:** each team's prior-season-to-date points scored minus conceded, divided by its number of prior games, gives its mean margin. `p_home = logistic((home_mean_margin − away_mean_margin)/14)`. The scale 14 is a fixed demonstration parameter, not a fitted or verified universal effect.
4. **Score blend:** projected home points = half of (home prior scoring average + visitor prior points-allowed average), and conversely for the visitor. The estimated total is their sum, and the home spread projection is visitor minus home projected points. Compare total MAE against the mean total from all previous weeks. Neither projection provides the complete distribution needed to price a spread or total; these are not offered market lines.

Elo probabilities are interpreted only for an illustrative two-outcome, tie-void contract. A hypothetical no-vig decimal price is `1/p` and American odds are `-100*p/(1-p)` for `p >= 0.5`, or `100*(1-p)/p` for `p < 0.5`. The displayed odds are rounded only for presentation; the source is the model calculation, not a bookmaker. No tie probability, sportsbook quote, availability, vig or current edge is asserted. Different house rules may settle a tie differently; consult the relevant operator's rules, as explained by the [UK Gambling Commission](https://www.gamblingcommission.gov.uk/licensees-and-businesses/lccp/condition/4-2-6-display-of-rules-betting).

## Scoring and correlation

Binary Brier score is `mean((p-y)^2)` and log loss is `−mean(y log(p)+(1−y) log(1−p))`; both are lower-is-better. See [NOAA's verification definitions](https://vlab.ncep.noaa.gov/web/mdl/ndfd-verification-score-definitions). Brier skill versus the 50/50 reference is `1−Brier/0.25`. This checks probability accuracy against a weak reference, **not** profitability or superiority to a sportsbook. Total-point MAE is measured in points.

Pearson r follows the [NIST definition](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/correlat.htm); applied to two binary indicators, it is phi. The player examples pair the QB's total passing yards and the receiver's total receiving yards from the same listed game. They do not prove all of the receiver's yards came from that QB. The examples `QB >249.5` and `receiver >49.5`, and `home win + game total >44.5`, are **hypothetical fixed thresholds**, not observed sportsbook quotes. For each pair calculate the observed joint fraction `n11/n` and the independence product `(n1./n)*(n.1/n)` on the same sample. Correlation of continuous yardage is not the correlation of thresholded prop outcomes. These figures are unconditional and retrospective: they are not matchup-specific conditional forecasts, do not establish causality, do not account for changing roles/injuries or market selection, and should not be used as parlay prices. The studies have only 6, 17, and 14 game-week blocks respectively; reliable multi-season, dependence-aware uncertainty bounds are unavailable and remain blank.

For two binary events with marginals `pA`, `pB`, their joint satisfies `p11 = pA*pB + phi*sqrt(pA*(1-pA)*pB*(1-pB))` only when the phi and marginals refer to **the same distribution and exact events** and the resulting joint obeys feasible probability bounds. Do not transfer these retrospective phi values to future lines. More than two legs generally requires a full joint model or a valid conditional chain; pairwise correlation alone is insufficient.

## Competition and validation gates

This project proposes a simulated **non-cash research-credit** competition, not a paid contest or a promise of a payout. Rank only strategies making probabilities for the same event set, by lower Brier score; the 50/50 reference is not reward-eligible. Ties at exactly equal full-precision Brier share the same competition rank, with subsequent ranks skipped. After **all** gates pass, ranks 1/2/3 receive 100/60/30 research credits respectively; any later rank receives zero credits. Currently no strategy qualifies and no credits are awarded. The leaderboard's descriptive order is not a qualified ranking.

Gates are conservative project policy choices, not requirements published by the NFL or NOAA and not a guarantee of skill:

- **Provenance:** every relevant input must be sourced, complete and verified; reject conflicting, missing and duplicate records. For the game study, compare all 91 rows to the pinned source and retain the source revision and hash. Player logs require separately documented source checks.
- **Chronology:** lock definitions before a genuinely prospective test, prevent feature leakage, and make each forecast before the outcome. This implementation enforces end-of-prior-week snapshots and has an alteration test; the historical research itself was not preregistered.
- **Sample:** at least 200 matched held-out events across at least three seasons and 10 season/week blocks. These minimums are policy, not proof of adequacy or independence.
- **Calibration:** use fixed probability bins `[0,.2), [.2,.4), [.4,.6), [.6,.8), [.8,1]`; every populated bin must have at least 20 outcomes and absolute forecast/frequency gap at most 0.10. A pass is only a coarse diagnostic, not proof of calibration; empty bins do not pass on their own.
- **Skill and selection:** Brier improvement over the same-event 50/50 reference must be positive, and its lower confidence bound must be positive under a prespecified paired season/week-block bootstrap with family-wise adjustment across all tried candidates. Specify and document the adjustment and block structure before testing. No such defensible interval exists here; a negative point improvement is a fail even before that check.
- **Market and settlement:** require timestamped, executable, correctly identified, official operator prices, selection/limits, fees, terms, and actual push/void/tie/settlement outcomes. Compare to a properly specified market reference; a no-vig estimate is itself a modeling choice. No verified market archive or settlements were obtained, so edge, ROI and closing-line value are unverified.
- **Forward test:** log forecasts and model version before the game and measure on an untouched forward period. Nothing here was actually locked before 2017 or the 2024/25 games. This gate is unverified. For parlays/prop combos, also require event-specific, out-of-sample joint-probability calibration, consistent settlements, and leg-level timestamped data before any ranking.

An estimated win probability `p` and a decimal quote `d` do not alone cover all settlement cases. With no fees, expected net return per unit stake is `P(win)*(d−1)−P(loss)`; pushes/voids return the stake under the assumed rules and contribute zero. Without verified probabilities and quotes, no expected return is reported. Betting can lose money and can be addictive ([FTC](https://www.ftc.gov/news-events/news/press-releases/2002/06/ftc-warns-consumers-about-online-gambling-children)); follow local law and operator rules. Chance cannot be eliminated. Sample splitting, precommitment, uncertainty and controls can only reduce the risk of mistaking luck or leakage for skill.

## Reproduction

From the repository root, with Python 3.10+:

```sh
python scripts/verify_sources.py --online
python scripts/analyze.py
python -m unittest discover -s tests -v
```

`--online` compares all game rows byte-for-byte and field-by-field with the pinned NFL source through the GitHub API. The player-log checks were performed against NFL.com pages on 2026-11-02; the script does not claim to re-check those pages online. `data/derived/report.json` is generated deterministically from the checked source files. External data can change and the study is not an automatically updating feed.
