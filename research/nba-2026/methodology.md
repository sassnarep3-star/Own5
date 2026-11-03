# NBA 2026 evidence and competition method

**Checked 2026-11-03 UTC.** Only the new `nba-2026-lab/` is governed by this record. Its official inputs are [NBA Anthony Edwards 2025–26 regular-season game log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26), [NBA team statistics](https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season), and [NBA 2026–27 injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/). Game rows carry the official per-game links published in the log. The log default view contains 61 rows; exactly its first ten displayed were transcribed, not all 61. Date, opponent, result, minutes, points, made threes, rebounds, assists checked against NBA column order. 2025–26 is historical; these are not 2026–27 projections. `compute.py` calculates Pearson r directly from these ten rows. It does not estimate correlations between *bet legs* at specified thresholds; those cells remain blank.

## Originate, don't mirror

1. At a timestamp before tip, archive official game, rosters, injury release, team/player history and source version. Train only on observations preceding that timestamp.
2. Fit calibrated distributions for team scores/win, individual minutes and role-dependent per-minute counting stats. Create a *joint* simulated outcome for same-game combinations and compare joint hit probability with the actual executable operator payout. These are proposals, not established profitable models.
3. Log all strategies and variants before their chronological untouched evaluation. Do not reuse test games for model fitting or cherry-pick correlation pairs after observing outcomes. Archive actual market quotes, withdrawal rules, limits, fees, grading and close at the time each would have been available. No such quote archive exists in this checkout.
4. Score prospective predictions by calibration and proper scoring rules, compare de-vigged close and net yield, report uncertainty and multiple-test adjustment. Apply G0–G8. When any required input is missing, mark blocked rather than claim an edge. Correlated legs require *joint* payoff calculations: pairwise r is not joint threshold-hit probability. A positive coefficient does not itself imply value.
5. Leaderboard divisions: singles, player props, and combinations. Allow entry only after every gate passes. Reward amounts and recipients stay blank until funded rules and eligibility are documented. Random outcomes cannot be eliminated; uncertainty intervals and prospective testing control attribution of skill, not chance itself.

## Checks / caveats

- Ten selected, non-random player games; small sample, one player, no holdout and no confidence interval. Correlations are descriptive and may be unstable or mechanically related. In particular made threes contribute three points to total points.
- The official injury-report page says reports are continually updated and supplies release timestamps; a policy statement does *not* establish a tradable injury edge.
- Source links identify source *inputs* for candidate strategies and proposed gates, not official NBA endorsement of betting methods.
- No operator price snapshot or payout, even for singles; fair bet lines, closing-line value, net yield and rewards all intentionally blank. See `nba-2026-lab/review.html`.
