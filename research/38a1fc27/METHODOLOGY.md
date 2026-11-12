# Methodology

Every number on the site is produced by `tools/decision_desk/build_all.py` from inputs pinned in
`data/decision-desk/raw/`. This document states the definitions, the assumptions and the failure
modes.

## 1. Data tiers

- **OFFICIAL** — published by the league or a club (nfl.com injury report, schedule, standings).
- **AGGREGATOR** — a third-party project re-publishing data derived from official sources
  (nflverse releases: injuries, snap counts, weekly stats, schedules/results; spreadspoke results).
- Official pages are parsed row-by-row (`parse_official.py`). Aggregator data is used where the
  official page is not machine-readable at scale (snap counts, historical lines).
- **Dual-source assertion:** where both exist, they must agree row-for-row. Current state: standings
  32/32, Week 10 injury report 276/276.

## 2. Depth and lineup deficiency

1. **Unit snap share.** For each player and season, the mean of his offence (or defence) percentage
   across the games he played, using only weeks *before* the week being evaluated (no leakage).
2. **Depth string.** Players are ranked by snap share inside (team, unit, position group).
   Rank 1 = 1st string, 2 = 2nd string, and so on. Starter = share ≥ 0.50.
3. **Availability weight.** Out 1.00, Doubtful 0.75, Questionable 0.50. When the game status is not
   yet published: DNP 0.50, Limited 0.25, Full 0.00. "Not injury related" absences are excluded.
4. **Replacement drop.** `weight × max(0, player_share − next_man_up_share)` at the same position
   group. Summed by unit → offence and defence deficiency in percentage points of unit snaps.

The weights in (3) are **assumptions**, published here, in `injury_signal.json` and on the site.
They are not official probabilities. Suggestion S07 replaces them with fitted activation rates.

## 3. Market sign convention (critical)

`nflverse.games.spread_line` is the **expected home margin** (positive = home team expected to win
by that many points). Therefore:

- home ATS margin = `actual_home_margin − spread_line`
- model edge = `model_margin − spread_line`

The first pass of this session used `margin + spread`, which manufactured a false edge. See
`VERIFICATION.md` §3 and flag F11. Any future feed must be checked with the fixture test in S02.

## 4. Line model

- **Ratings:** ridge least squares, `margin = rating_home − rating_away + hfa`, λ = 4.0, fitted on
  games strictly before the week being priced, restricted to the prior two seasons.
- **Totals:** ridge two-way points model, `points = μ + offence_team − defence_opponent`, λ = 8.0.
- **Neutral sites:** home-field advantage set to zero (documented assumption, F17).
- **Injury adjustment:** coefficient from a regression of margin on the deficiency gap controlling
  for prior scoring margin, estimated only on games where both clubs have an injury report.
- **Walk-forward backtest:** every regular-season game 1999–2026 priced pre-kickoff with the same
  procedure; bets taken only when the model disagrees with the line by 2, 3 or 4 points.

## 5. Validation gates

Thirteen gates (G0–G12), defined in `validation-gates.md`. Hard requirements include an exact
two-sided binomial test against the 52.38% break-even implied by −110 pricing, Bonferroni over the
number of variants actually tested, a chronological holdout, drawdown limits and a verified price
source. G2 additionally requires the strategy to be **above** break-even: a statistically
significant losing strategy is not a pass.

## 6. Correlation

- **Prop pairs:** Pearson r on the underlying statistics (not bet outcomes), with Fisher 95%
  intervals. Team-games are the unit of observation; a team's QB is the player with the most
  passing yards in that game, and WR1 is the team-season leader in receiving yards.
- **Parlay legs:** phi coefficient on 2×2 cover/over outcomes over 2010–2026 completed games.
- **SGP pricing:** for two equal-probability legs, joint probability = 0.25 + arcsin(r)/(2π), which
  is the bivariate normal result for zero thresholds. Fair price keeps a 9.09% hold so it can be
  compared with a two-leg −110 parlay paying +264.

## 7. What the method cannot do

- It cannot certify skill without a verified closing price (no public source).
- It cannot evaluate prop economics without prop lines (no public source).
- It cannot resolve depth beyond snap-share inference (no machine-readable official depth chart).
- It cannot remove luck entirely: it bounds the probability that a result is luck, which is the
  most any methodology can do.
