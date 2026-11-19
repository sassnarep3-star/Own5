# Methodology — NFL Origin Desk (session 2b6d55c1)

## Origination model (specification, not a fitted forecast)

Inputs (official standings, read 2026-11-19):
- team offense  = PF / games_played
- team defense  = PA / games_played

Assumptions (labeled, not fitted):
- HFA = 2.0 points (flag FZ-02)
- logistic scale = 13.7 points (flag FZ-03)

For each Week-11 game (home H, away A):
- home_exp = (H.off + A.def) / 2 + HFA / 2
- away_exp = (A.off + H.def) / 2 - HFA / 2
- fair spread (home − away) = home_exp − away_exp  (+ = home favoured)
- fair total = home_exp + away_exp
- home win probability = logistic((home_exp − away_exp) / scale)
- fair moneyline (American, home side) derived from home win probability

Order of origination: side first, then total, then moneyline. Model fair line / market line /
difference are separate columns. Market columns blank+flagged (no verified operator price source,
policy P-01, flag FZ-04).

Every row stores probability + inputs + inputs SHA-256 hash (no pick without its inputs).

## Price-snapshot store

Immutable opening snapshot per originated market at 2026-11-19T08:00:00Z. Closing line blank+pending
by price-data policy. Each snapshot carries inputs_sha256.

## Correlations

Pearson product-moment computed in-repo from official standings (n=32). Fisher-z 95% CI published.
n published on every row. Only officially sourced numbers are used.

## Leaderboard

Signal separated from staking. Every strategy pre-registered (registration hash frozen in git).
Backtest numbers forbidden from ever appearing on the leaderboard (G03). Control baselines (random
picks; favorites only) listed but not ranked for skill. 0 certified strategies (pre-season).

## Availability / injury

Deltas never levels. Injury signal treated as a surprise (change), never a level. 10 of 32 clubs
read from Week-11 injury report; rest NOT READ (blank+flagged, never inferred).
