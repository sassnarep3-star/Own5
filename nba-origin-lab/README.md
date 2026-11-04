# Own5 NBA Origin Lab — executive summary and audit

**As of 2026-11-03 UTC.** Static, additive GitHub Pages site: `https://sassnarep3-star.github.io/Own5/nba-origin-lab/`. Generate with `python3 nba-origin-lab/build.py`; test with `python3 -m unittest discover -s nba-origin-lab -p 'test_*.py' -v`. This namespace does not change other sessions' NFL or NBA outputs.

## Executive decision

No qualified strategy, current fair line, or prize can be responsibly published. Ten **selected historical** Anthony Edwards player-games are sufficient for illustrative descriptive calculations, not a prospective, priced edge. A sample median of **22 points** and in-sample absolute error of **9.5 points** are calculated on the *same* ten games, not predictive accuracy. Correlations on the sample are illustrative continuous-statistics associations, not prop-hit correlations. The site keeps current price, profitability and prize fields empty. It presents proposed hypotheses for singles, cross-game parlays and same-game props and fail-closed gates for provenance, availability, leakage, calibration, execution, selection and risk. Luck cannot be eliminated; prospective evidence can only distinguish skill from random variation with quantified uncertainty.

## Line-by-line provenance / scope

| Item | Checked on 2026-11-03 UTC | Official source | Limitation |
|---|---|---|---|
| Ten player-game rows (date, matchup, result, minutes, points, 3PM, rebounds, assists, game ID) | Manually compared each displayed record with the first ten rows of the official Anthony Edwards 2025–26 box-score log; all ten match. | [NBA player box-score log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) and each row's linked NBA game URL | Official page is dynamic; no immutable official extraction retained. Sample is selected, not exhaustive. |
| Game and results navigation | Opened official game page and schedule; official schedule is dynamic. | [NBA Games](https://www.nba.com/games) | No frozen as-of pregame schedule in this extension. |
| Definitions of pace, usage, rating | Checked official glossary. | [NBA glossary](https://www.nba.com/stats/help/glossary) | Definitions do not prove predictive value. |
| Injury reporting | Checked official 2026–27 injury page and its continuous-update description. | [Official NBA injury reports](https://official.nba.com/nba-injury-report-2026-27-season/) | No game-specific snapshot joined to a forecast. |
| Sample median, in-sample MAE and Pearson coefficients | Recomputed by `build.py` from the ten prior-lab CSV rows; structural tests pass. | [NBA log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) | Derived arithmetic, not NBA-issued ratings or validation. |

The site links official material on **every body table row**. For hypothesis, gate and contest-policy rows, that link supports an input definition or context **only**, not an endorsement of the proposed policy or any odds. No sportsbook price, SGP payout, jurisdiction, settlement or reward terms were independently verified; these values are intentionally empty and flagged.

## Requirements coverage

| Requirement | Location | Status |
|---|---|---|
| Repo audit and coordination | `COORDINATION.md`, this audit | Done in isolated namespace; prior NBA and NFL sites retained |
| Executive summary and category pages | `index.html`, `sources.html`, `lines.html`, `strategies.html`, `correlations.html`, `gates.html`, `leaderboard.html`, `review.html` | Built |
| Own lines | `lines.html` | Framework only; **current lines blank**, G0–G7 not met |
| Singles / parlays / player prop combos | `strategies.html` | Hypotheses, not bets |
| Correlation values | `correlations.html` | Four historical Pearson estimates; actual joint-hit values blank |
| Skill-versus-luck gates | `gates.html`, `leaderboard.html` | Proposed fail-closed protocol; zero certified entrants |
| Source link per row; unverified blanks and flags | All tables; `review.html` | Structural audit automated; external official source checked for the four cited evidence locations |
| GitHub Pages publication | GitHub Pages static folder | Pending PR/merge/deployment verification until recorded in `COORDINATION.md` |

**Review flags R01–R08 are nonblocking.** In particular, neither the absence of a quote nor an NBA schedule link verifies a missing bookmaker field. Source links in these rows provide review context only. No monetary reward is funded or promised.
