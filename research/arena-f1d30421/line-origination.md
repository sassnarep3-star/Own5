# Line Origination Methodology (T2)

Status: done | Owner: session arena-f1d30421 | Verified: 2026-11-02

Goal: generate our own NFL numbers (spreads, totals, and player-prop projections) rather than
reacting to market lines. A market line is a *benchmark*, not an input: our line is built from
official data, and the difference between our line and the market is the candidate signal.

## 1. Data inputs (provenance-first)

| Input | Source | Status |
|---|---|---|
| Game results, PF/PA, W-L-T | Official NFL standings/schedules pages (nfl.com) | Verified — official |
| Historical scores + closing lines (1966–2025 wk5) | `tobycrabtree/spreadspoke` @ commit `1d309cb` ([file](https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv)) | Community dataset — flagged (no official public line archive exists) |
| Play-by-play 2002–2013 | `brianfoshee/nfl-play-by-play-data` @ commit `352c9c9` ([repo](https://github.com/brianfoshee/nfl-play-by-play-data)) | Community mirror — flagged |
| League rules/facts | [2025 NFL Record & Fact Book](https://static.clubs.nfl.com/image/upload/patriots/fvc6qgwyqlztq1muztpi.pdf) (official NFL CDN) | Verified — official |

Rule applied everywhere: values that cannot be confirmed from a listed source are left blank and
flagged (see site page "Flagged for Review"). No value is inferred.

## 2. Game-line model (transparent baseline)

Implemented in [`scripts/originate_lines.py`](../../scripts/originate_lines.py); produced
[`data/model_lines_2026_wk9.csv`](../../data/model_lines_2026_wk9.csv).

```
rating(team) = (PF - PA) / G                    # net points per game, from official standings
shrunk(team) = rating * G / (G + 4)             # empirical-Bayes shrinkage toward league average
model_margin = shrunk(home) - shrunk(away) + HFA
model_total  = (PPG_scored_h + PPG_allowed_a + PPG_scored_a + PPG_allowed_h) / 2
```

* **HFA = 2.0 points**, rounded from the computed 2002–2024 mean home margin of **2.22 pts**
  (`data/base_rates.csv`, `mean_home_margin_pts`, window `modern_2002_2024`; derived from the pinned
  dataset, re-computable via `scripts/compute_analysis.py`). Neutral-site games (e.g. Madrid) use HFA = 0.
* Shrinkage constant 4 (= games of league-average performance of "prior weight") is a documented
  modeling choice; sensitivity is a validation gate (G6, see validation-gates.md).
* Lines rounded to the nearest 0.5. Totals are team-points-based (no weather/pace adjustment in v1 —
  known limitation, see Limitations).

This v1 model is a *baseline*, deliberately simple so every number is auditable. Improvement path
(documented for the leaderboard competition): opponent-adjusted ratings (SRS-style iteration),
EPA-based efficiency components (nflverse/nflfastR expected-points model — see
[nflfastR docs](https://www.nflfastr.com/articles/nflfastR.html)), injury/inactive adjustments from
official reports ([NFL.com transactions/inactives](https://www.nfl.com/)), quarterback availability,
and weather from official game books.

## 3. From model line to bet signal

A bet is only a candidate when our line disagrees with the market by more than a threshold:

```
edge = model_margin - market_margin      (in points)
bet side = model side, when |edge| >= threshold AND price makes EV positive
```

* Threshold candidates (pre-registered, tested via gates): 1.0, 1.5, 2.0 points.
* EV must be computed with the *actual* price; break-even rates per price are in
  [`data/luck_skill.csv`](../../data/luck_skill.csv) (e.g. 52.38% at −110).
* **Market lines cannot currently be verified from an official source** — market columns in our
  line table are intentionally blank and flagged. Until a licensed/verifiable odds feed is connected,
  live edge computation is defined but not executed. This is policy, not a gap in the method.

## 4. Player-prop origination (framework)

1. Project usage (attempts/targets/carries) from team pace + game script expectations
   (script effects are quantified in `data/correlation_props.csv`: RB rush yards correlate +0.21 with
   team margin; QB pass yards +0.08 with margin — passing volume rises in negative scripts).
2. Convert usage to yards with per-player efficiency (season-to-date rates, shrunk — same
   G/(G+k) approach).
3. Compare to prop market line; require the same edge + validation gates as game lines.
4. **Same-game combinations must use empirical joint probabilities**, never naive multiplication —
   measured QB-pass-yards vs top-WR-yards correlation is **0.76** (n = 3,852 team-games,
   `data/correlation_props.csv`).

## 5. What the model produced this week (2026 Week 9)

Full table with per-row official schedule/standings links: [`data/model_lines_2026_wk9.csv`](../../data/model_lines_2026_wk9.csv)
(15 games). Market columns blank + flagged per policy.

## 6. Limitations (honest list)

1. Net-points ratings ignore opponent strength; early-season records with soft schedules are
   overrated until opponent adjustment lands (example tension visible in CLE@NO week-9 line).
2. HFA is a league-wide constant; team-specific HFA not modeled in v1.
3. Historical line data (1966–2025) is community-sourced; official verification possible only for
   game scores (spot-verified 2025 Week 1, 16/16 rows matched nfl.com — see `data/verified_official_results.csv`).
4. No injuries/news inputs in v1 — these are often the sharpest late signals (see Kaunitz et al.
   2017 on market movement, [arXiv:1710.02824](https://arxiv.org/abs/1710.02824)).
