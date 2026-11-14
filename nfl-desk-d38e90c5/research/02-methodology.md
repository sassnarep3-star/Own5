# Methodology: how the desk originates its own lines

Source code: `model.py` (engine), `pipeline.py` (datasets), `raw_inputs.py`, `injuries_raw.py`,
`depth_raw.py` (transcribed official inputs).

## 1. Inputs (all official)

| Input | Content | Source |
|---|---|---|
| Official standings | W, L, T, PCT, PF, PA, point difference for all 32 clubs | https://www.nfl.com/standings/league/2026/REG |
| Official results | 137 completed games with date, away, home, final score, week | https://www.nfl.com/schedules/2026/by-week/week-1 ... week-10 |
| Official slate | 26 upcoming Week 10 and Week 11 games with kickoff, network, venue | https://www.nfl.com/schedules/2026/by-week/week-10 , week-11 |
| Official injury report | 347 Week 10 rows: player, position, injury, practice status, game status | https://www.nfl.com/injuries/ |
| Official club depth charts | 32 club pages, 31 transcribed | each club's own site, listed in `data/sources.csv` |

The transcription reconciles: all 32 clubs match the official W-L-T, PF and PA exactly, and the
aggregate points scored and allowed both equal 6,291 over 137 games.

## 2. Ratings

Ratings are estimated by alternating least squares on the official final scores, with the home-field
term held fixed:

```
expected_home = L + HFA/2 + off_home - def_away
expected_away = L - HFA/2 + off_away - def_home
```

* `L` = league points per team per game, computed from the official results (22.9599 for the current
  sample).
* `off_t` = points scored above the league mean; `def_t` = points conceded above the league mean.
  Both are re-centred after every sweep so their weighted league mean is exactly zero.
* `HFA` = 2.0 points. **This is a model assumption, not an official statistic**, and it is the only
  non-official number inside the line engine. It is flagged, and the published lines move one point
  for each half-point of HFA.
* Shrinkage: `w(t) = G(t) / (G(t) + 6)`, applied to both ratings, so a club with four games is pulled
  towards the league mean and a club with nine games is trusted more.

## 3. Probability calibration

* Primary estimator: `p(home) = logistic(a + b * margin)`, with `a` and `b` fitted by Newton-Raphson
  on the model's **own earlier out-of-sample predictions**. Current fit: `a = -0.8297`,
  `b = 0.2211`, trained on 73 predictions.
* Fallback (used only until 20 out-of-sample predictions exist): `p(home) = Phi(margin / SD)` where SD
  is the standard deviation of official final margins in the training window (13.2251 points).
* Margin noise scale for the total market: the residual standard deviation of walk-forward total
  predictions, 13.9602 points over 73 predictions.

## 4. Lines and publication order

| Market | Model line | Probability | Fair price |
|---|---|---|---|
| Side / spread | home line = `-round_half(margin)` | `p(home wins)` | American odds from that probability |
| Total | `round_half(expected_home + expected_away)` | `P(total > line)` | American odds from that probability |
| Moneyline | home selection | `p(home wins)` | American odds from that probability |

Publication order is fixed by `model.MARKET_ORDER = ("spread", "total", "moneyline")` and carried in
the `publish_seq` column of every published line row.

## 5. Backtest discipline

Every backtest number is walk-forward. For week *w* the engine rebuilds ratings from games played in
weeks < *w* and rebuilds the calibration from predictions made in weeks < *w*. No result can inform
its own prediction. The walk-forward starts in Week 5 (the first week with a usable amount of team
history), which yields **73 out-of-sample predictions**.

Measured on those 73 predictions:

| Metric | Model | Reference | n |
|---|---|---|---|
| Mean absolute error of the margin | 10.24 points | - | 73 |
| Root mean squared error | 12.96 points | - | 73 |
| Brier score | 0.2291 | 0.2443 (base-rate) | 73 |
| Log loss | 0.6480 | 0.6818 (base-rate) | 73 |
| Winner hit rate | 60.3% | 42.5% (home base rate) | 73 |
| Calibration slope | 0.869 | 1.0 (ideal) | 73 |
| Correlation of model margin with actual margin | r = 0.3517 | - | 73 |

The model is a **transparent baseline**: it beats the base-rate references on the probability metrics
but explains only a modest share of margin variation. It is not claimed to be a proven edge.

## 6. Replacement depth

Each official injury row is matched to the club's official depth chart by normalised player name
(a small first-name alias table handles Josh/Joshua, Matt/Matthew and similar published variants).
The row then carries:

* the unit (Offense, Defense, Special Teams) and the club's own position label;
* the depth slot (1 = first string) and the depth tier (1st / 2nd / 3rd / 4th string);
* the named player who would step in, and that player's depth tier;
* a **depth deficiency** flag when a starter is Out and the next in line is a third- or
  fourth-string reserve.

61 of 347 injury rows have no entry on the club's published chart (16 of them Houston, whose chart is
image-only). Those rows keep a blank depth tier and are flagged rather than guessed.

## 7. Known sensitivities (read before using a published line)

* **Schedule adjustment is the loudest input.** The ratings compare each club with the average
  strength of the opponents it actually faced, so a club that played several strong offenses is
  credited with a better defense than its raw points-against number shows (Minnesota, for example,
  allows only 14.5 points per game yet is rated as the league's weakest defense because of the
  opponents it faced). With only eight or nine games in the sample, that adjustment is noisy and it
  can produce lines that look aggressive - Jacksonville is published as a 10.5-point favourite at
  Tennessee in Week 10 for exactly this reason. Shrinkage (`SHRINKAGE_K`) was compared over
  K = 4, 6, 8, 10 and 14 on the walk-forward sample and barely moves the result (Brier 0.2291 to
  0.2302), so the published lines are not an artefact of the shrinkage constant; they are the
  honest output of a transparent schedule-adjusted model on a short sample.
* **Home-field advantage is an assumption.** 2.0 points is not an official statistic. The published
  spread moves one full point for every half-point of HFA, and the moneyline moves with it.
* **The sample is short.** 73 out-of-sample predictions is enough to show the model is not worse
  than a base-rate guess on the probability metrics, and far too short to call it an edge. The
  weekly build keeps adding to the sample (discovery step D-02).

## 8. Price snapshots and results

* `data/price_snapshots.jsonl` is append-only: one `opening` and one `closing` record for every
  originated market, keyed by `game_id|market|phase`. A rebuild never rewrites an existing record.
* `data/results_verified.csv` holds the 137 official final scores with the official schedule page as
  the source of each row, and is the feed that settlement and ROI would use.

## 9. Fail-closed rules

1. No official price source -> market line, market price, difference, CLV and market ROI are blank
   and registered on the Flagged for Review page.
2. A gate criterion that cannot be evaluated is `NOT_EVALUABLE`; any strategy with a
   `NOT_EVALUABLE` live criterion is `PAPER`, never `LIVE`.
3. An injury row with a blank game-status cell is recorded as "No designation published" and is never
   treated as healthy.
4. A depth value that cannot be read from a machine-readable official chart stays blank.
