# Executive summary — Own5 NFL research desk

**Decision:** release the research infrastructure and frozen evidence snapshot. **Do not treat any strategy as a validated betting edge.** No strategy currently qualifies for the performance leaderboard or rewards.

## What was delivered

- A clean static dashboard with 13 pages: overview, independent lines, strategies, parlays/combos, player props, correlations, validation gates, leaderboard, official data, sources, methodology and Flagged for Review.
- A reproducible, standard-library-only modeling and validation engine.
- 15 independent Week 9 research lines derived from official standings and schedule inputs.
- Six predeclared strategy families spanning single bets, cross-game parlays, same-game player-prop combos and player props.
- Eleven fail-closed validation gates, an eligibility-first non-cash leaderboard, and 29 passing unit tests.
- A source register, frozen evidence excerpts, line-by-line fact table and explicit missing-value policy.

## Evidence base

The 2026-11-02 snapshot contains 17 primary/official sources and 78 verified fact rows: 32 team standings rows, 15 Week 9 matchups, 17 paired 2024 player-game rows and 14 quoted rule/product facts. League points reconcile at 5,528 PF = 5,528 PA. Burrow’s 2024 passing log sums to 4,918 yards; Chase’s receiving log sums to 1,708 yards and 127 receptions, matching official career controls.

Official inputs: [NFL standings](https://www.nfl.com/standings/league/2026/REG), [NFL Week 9 schedule](https://www.nfl.com/schedules/2026/by-week/week-9), [Burrow log](https://www.nfl.com/players/joe-burrow/stats/logs/2024/), [Chase log](https://www.nfl.com/players/ja-marr-chase/stats/logs/2024/).

## Most important findings

1. **The historical QB–WR pair moves together strongly in this selected sample.** Burrow passing yards and Chase receiving yards have Pearson r = +0.752 (95% paired bootstrap interval +0.524 to +0.920) across 17 games. This is descriptive, not a current-season or league-wide signal.
2. **Independence would misdescribe the historical combo.** At research thresholds of ≥250 passing yards and ≥75 receiving yards, the joint event hit 10/17 games (58.8%), versus a 45.7% marginal product. The observed lift is 1.288. The historical fair joint decimal is 1.70; it is **not** an executable or current SGP price.
3. **No economic edge is established.** There are zero verified sportsbook quotes, zero current prop quotes and zero untouched out-of-sample betting records. Net ROI, CLV and market edge remain blank.
4. **All six strategies are blocked.** Missing market history, participation/settlement evidence, broader samples and holdout validation prevent qualification. The leaderboard correctly has no ranked entries and awards zero research points.
5. **The line originator is transparent but unvalidated.** It uses shrunken PF/PA ratings, an independent-Poisson score baseline, eight pseudo-games of shrinkage and no home-advantage adjustment. Injury, weather and starter adjustments are blank rather than invented.

## Principal risks

- One selected QB–receiver pair and one season create severe selection and transportability limits.
- Poisson independence is a simplification of football scoring.
- Official standings are not a point-in-time game-level training archive.
- Operator void/push/reprice rules differ; a universal SGP settlement rule is not verified.
- Dynamic official pages can change; the release preserves dated evidence rather than claiming live freshness.
- Finite-sample luck cannot be eliminated. The gates reduce avoidable bias and quantify uncertainty; they do not guarantee future profit.

## What must happen before any strategy is trusted

Acquire authorized, timestamped operator quotes and settlement rules; expand official game/player logs; verify point-in-time participation; run the locked expanding-window protocol with whole-week uncertainty resampling; calibrate joint events out of sample; and keep the final holdout untouched. Only then can the leaderboard rank strategies by net ROI lower bound, CLV lower bound and forecast skill.

## Review queue

Thirteen items are published on Flagged for Review, including missing market inputs, current prop/participation gaps, correlation scope, model assumptions, an NFL Support title/content mismatch, a rejected player slug, GSIS access limits and rule-version control. These flags do not block the site release; they do block unsupported values and strategy qualification.

**Publication:** the final PR, merge and GitHub Pages verification result are recorded in `COORDINATION.md` and `docs/VERIFICATION_REPORT.md`.
