# NBA Own Lines — executive summary

**Snapshot:** 2026-11-03T23:39:30Z · **Season:** 2026–27 · **Session:** 636a7712  
**Live dashboard:** https://sassnarep3-star.github.io/Own5/nba-own-lines/ · **Integration:** [PR #27](https://github.com/sassnarep3-star/Own5/pull/27), merged 2026-11-03T23:47:32Z

## Decision

The desk originates **16 transparent NBA game-line baselines** for the official November 4–5 slate. It releases **zero betting signals**: **0 of 7 strategies qualify**, no entrant is ranked, and current rewards are **0 research points**. This is a fail-closed validation result, not a claim that the lines have no value.

No sportsbook spread, total, moneyline, parlay payout, ROI, CLV, playable prop, joint-hit probability or monetary prize has been inferred. Those fields are blank in `data/derived.json` and on the site.

## Material findings

| Finding | Evidence | Consequence | Official review |
|---|---|---|---|
| 30 teams / 16 games / 26 player-games | All team records reconcile across the advanced table and schedule cards; player game counts and rounded averages reconcile | Sufficient for reproducible descriptive calculations, not predictive certification | [NBA team stats](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) · [NBA games](https://www.nba.com/games) |
| Own lines calculated | Shrunk OffRtg/DefRtg/PACE; 10-game prior; zero HFA; no overtime adjustment; logistic scale 6 | Research spread/total/fair-price baselines only | [NBA glossary](https://www.nba.com/stats/help/glossary) |
| Team NetRtg × Win% r = +0.9163 | n = 30 current-season teams; OffRtg × Win% = +0.7333; DefRtg × Win% = −0.7715 | Contemporaneous association, not out-of-sample skill | [NBA team stats](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) |
| PACE adds no demonstrated signal here | PACE × OffRtg r = −0.0541; PACE × Win% r = −0.3667 | Descriptive only; no totals or side strategy qualifies | [NBA team stats](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) |
| 0/16 player correlation tests survives Holm p < 0.05 | Luka PTS×3PM r = 0.9230, raw exact p = 0.00476, Holm p = 0.07143; Shai PTS×AST r = 0.9104, raw p = 0.00357, Holm p = 0.05714 | Strong raw associations can plausibly be luck after multiplicity control; no prop-combo claim | [Luka log](https://www.nba.com/stats/player/1629029/boxscores?Season=2026-27&SeasonType=Regular%20Season) · [Shai log](https://www.nba.com/stats/player/1628983/boxscores?Season=2026-27&SeasonType=Regular%20Season) |
| Anthony Edwards Out | Official 6:15 PM ET report: Injury/Illness — Right Knee Arthroscopy | His playable line and PC04 are suppressed | [Official injury PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-03_06_15PM.pdf) |
| Availability incomplete | LAL/SAC and other teams were NOT YET SUBMITTED in the snapshot; absence from a report is not inferred as Available | All other selected prop references remain held; team lines are not injury-adjusted | [Official injury PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-03_06_15PM.pdf) |

## Competition and skill-versus-luck conclusion

Seven registered hypotheses cover moneyline/spread/total singles, cross-game and same-game parlays, and same-player/cross-game player-prop combinations. G00–G09 require official provenance, frozen specifications, availability, market/settlement evidence, a prospective ledger, at least 100 out-of-sample forecasts, baseline-beating predictive metrics, luck screening, combination dependence where applicable, and risk/leakage controls.

Only provenance, specification and written risk policy currently pass. There is no prospective graded ledger or price history. **Luck cannot be removed from NBA outcomes**; it can only be evaluated with preregistered tests and uncertainty. Exact permutation tests, Holm multiplicity correction and a tested binomial upper-tail function are implemented. No performance claim is made without outcomes.

The future leaderboard policy offers only non-cash recognition of 100/60/40 research points to the top three *eligible* strategies. It is inactive while zero strategies qualify; no reward is funded or promised.

## Publication and review

The additive 11-page dashboard contains 199 body-table rows, each with an official NBA source/context link, and 454 checked links. Automated checks cover deterministic output, internal links, source hosts, schedule/record agreement, player-average reconciliation, model invariants and fail-closed gates. Eleven nonblocking publication flags are on `review.html`; high-severity evidence gaps continue to block strategy qualification.

Other sessions' existing NFL/NBA sites are preserved. Their historical source values were not independently re-transcribed in this session; that scope limitation is F10 rather than an unverified claim of repository-wide certification.
