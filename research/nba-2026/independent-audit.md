# Independent NBA audit — 2026-11-03 UTC

## Decision

The existing NBA evidence refresh is reproducible and internally consistent. Its narrow data sample and correlations are correctly described as historical and exploratory; they do **not** constitute betting lines, probabilities of prop outcomes, evidence of market edge, or a skill-validated strategy. No independently originated numeric line is supportable from this evidence, and no strategy qualifies for the leaderboard.

This is a verification note, not a new model or recommendation. Scope was limited to the additive `nba-2026-lab/` deliverable. Existing `docs/` and shared site outputs were not edited.

## Source-by-source verification

| Check | Result | Official source |
|---|---|---|
| Player-game source and season filter | NBA.com player game log identifies the 2025–26 season and exposes 61 regular-season rows. The CSV contains the first ten rows displayed, in descending date order, as documented. | [Anthony Edwards 2025–26 box scores](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |
| Team-statistics source | NBA.com team traditional statistics page exposes the 2025–26 regular-season selector and 30 team rows. This is historical descriptive input, not a current market quote or model validation. | [NBA team traditional statistics](https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season) |
| Injury-report source | NBA Official states reports are continually updated and provides dated report links; the page does not itself establish that an injury signal has betting value. | [2026–27 injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) |

### Player-log transcription check

For each row below, I checked date, opponent, W/L, minutes, points, made threes, rebounds, assists and the game ID against the corresponding row in the official NBA.com player-log table. Each row links to the NBA game page; the player-log page is the cross-check for the player box-score values. Values are transcribed, not inferred.

| Game date | Opponent | W/L | MIN | PTS | 3PM | REB | AST | Official NBA game |
|---|---:|:---:|---:|---:|---:|---:|---:|---|
| 2026-04-10 | HOU | W | 27 | 22 | 3 | 2 | 3 | [0022501178](https://www.nba.com/game/0022501178/) |
| 2026-04-03 | PHI | L | 26 | 8 | 0 | 2 | 3 | [0022501121](https://www.nba.com/game/0022501121/) |
| 2026-03-30 | DAL | W | 23 | 17 | 2 | 2 | 4 | [0022501095](https://www.nba.com/game/0022501095/) |
| 2026-03-15 | OKC | L | 37 | 19 | 2 | 6 | 5 | [0022500976](https://www.nba.com/game/0022500976/) |
| 2026-03-13 | GSW | W | 37 | 42 | 4 | 8 | 5 | [0022500966](https://www.nba.com/game/0022500966/) |
| 2026-03-11 | LAC | L | 35 | 36 | 3 | 2 | 5 | [0022500952](https://www.nba.com/game/0022500952/) |
| 2026-03-10 | LAL | L | 31 | 14 | 1 | 2 | 4 | [0022500946](https://www.nba.com/game/0022500946/) |
| 2026-03-07 | ORL | L | 32 | 34 | 5 | 3 | 2 | [0022500915](https://www.nba.com/game/0022500915/) |
| 2026-03-05 | TOR | W | 34 | 22 | 5 | 4 | 3 | [0022500903](https://www.nba.com/game/0022500903/) |
| 2026-03-03 | MEM | W | 37 | 41 | 7 | 6 | 2 | [0022500890](https://www.nba.com/game/0022500890/) |

No transcription discrepancy was found in these ten rows. This check does not independently validate every other row in the 61-game source log, and the selected ten are not a random or league-representative sample.

## Recalculation and site checks

`nba-2026-lab/compute.py` was run from the checked-in CSV using its stated Pearson formula. Results exactly reproduce the published four-decimal values:

| Pair | r | n | Official outcome input |
|---|---:|---:|---|
| PTS × AST | -0.0239 | 10 | [NBA player game log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |
| PTS × REB | +0.5762 | 10 | [NBA player game log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |
| 3PM × PTS | +0.7974 | 10 | [NBA player game log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |
| PTS × W (1/0) | +0.2925 | 10 | [NBA player game log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |
| AST × REB | +0.2053 | 10 | [NBA player game log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |

These are game-outcome correlations for one selected player sample. They are **not** threshold-hit correlations for quoted props and do not estimate a parlay's fair price. 3PM is a component of PTS, so that pair has direct arithmetic dependence. No correction for selection, sampling uncertainty, or multiple testing is represented by the displayed descriptive coefficients.

Verification commands and results:

- `python3 -m unittest discover -s tests -q` — **56 tests passed**.
- `python3 nba-2026-lab/compute.py` — all five values above reproduced.
- `python3 nba-2026-lab/build.py` — **8 pages built**, 10 linked game rows, 5 exploratory coefficients; a second build left tracked generated files unchanged.
- `python3 nba-2026-lab/check.py` — all 8 pages passed structural/link checks; table row counts: Overview 4, Executive summary 5, Official game data 10, Correlations 5, Strategies 7, Validation gates 9, Leaderboard 3, Flagged for Review 8. Every table row has an official NBA/NBA Official link.

The page check verifies that rows contain links to the official domain and that local navigation resolves. It is not a guarantee that a dynamic source will remain unchanged or that all source links will be available indefinitely.

## Readiness and flags

- **Own lines:** no current independently estimated game or player prices are present. A historical average or Pearson correlation is not a line. Numeric fair prices remain absent rather than inferred.
- **Single bets / props / combinations:** candidate designs are hypotheses only; none passes validation.
- **Correlation:** five small-sample outcome coefficients are present; pairwise `r` is not the probability of a parlay/prop-combo joint event.
- **Skill versus luck:** prospective, time-stamped predictions and quotes, an untouched chronological holdout, settlement records, uncertainty and pre-registration are still absent. Luck cannot be removed; the gates can only reduce false attribution.
- **Rewards:** no qualifying entry or documented funded prize pool; no awards are represented.
- **Existing older NBA research:** the older `research/nba/` correlation taxonomy cites third-party qualitative guides. This audit did not verify those guides as evidence of numerical NBA correlations; the new ten-game sample does not retroactively validate them. The older site remains separate and its own review flags remain applicable.

No new error was identified in the checked refresh. The material limitation is scope: one player's selected ten games, no timestamped executable prices, no complete point-in-time features/availability join, and no prospective out-of-sample ledger. These are published limitations, not evidence that any market edge exists.
