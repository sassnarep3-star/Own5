# Executive summary — NFL decision review

**Review date:** 2026-11-17 (UTC date supplied by the workspace)
**Live Pages path:** [`nfl-review-3bba0722/`](https://sassnarep3-star.github.io/Own5/nfl-review-3bba0722/)
**Purpose:** independently re-check selected official sources, surface decision blockers, and give every proposal a review test before implementation. This is an additive audit; it does not overwrite another session's site or data.

## Executive finding

The repository contains a substantial amount of NFL research, but a user cannot reasonably treat all snapshots as current or wagering-ready. Several important facts are now verifiable from official sources; critical inputs remain missing, stale, restricted or incomplete. No prices, ROI, CLV, betting edge, snap share, replacement rank or player-availability probability are produced by this review. Unknown values are blank and flagged.

**Decision:** keep price-dependent rankings, injury-change features, replacement-depth claims and combination bets blocked until each source, timestamp, rights status and validation gate is satisfied. Suggestions are proposals awaiting review, not implementation approvals.

## What was verified directly

| Finding | Review result | Official source |
|---|---|---|
| Requested Week 12 injury URL | On 2026-11-17, the URL `https://www.nfl.com/injuries/league/2026/reg12` retrieved a page titled and headed Week 10. This does not prove whether the Week 12 report is unpublished or the route is unsupported; it proves only that this response did not contain verified Week 12 rows. | [NFL injury-report route requested for Week 12](https://www.nfl.com/injuries/league/2026/reg12) |
| NFL Game Book fields | One official Week 10 Game Book includes Lineups, Did Not Play, Not Active, final statistics and game-time weather/roof text. It is one sample, not a season-wide coverage test. | [Game Center](https://www.nfl.com/games/rams-at-cardinals-2026-reg-10) · [Game Book PDF](https://static.www.nfl.com/image/upload/v1794854921/gamecenter/ab78a133-4feb-11f1-abca-2c54536568a9.pdf) |
| Game Book reuse restriction | The PDF says its summary/play-by-play is for assisting media coverage and other use requires written NFL permission. That restriction must be reviewed before raw retention, model use or public display. This summary is not legal advice. | [Official Game Book PDF](https://static.www.nfl.com/image/upload/v1794854921/gamecenter/ab78a133-4feb-11f1-abca-2c54536568a9.pdf) |
| Club depth chart parsing | The Texans page labels its chart unofficial and exposes an image, not a structured text table in the retrieved content. The Packers table contains jersey-number-prefixed player cells and is labelled unofficial, dated Nov. 10, 2026. | [Houston Texans depth chart](https://www.houstontexans.com/team/depth-chart) · [Green Bay Packers depth chart](https://www.packers.com/team/depth-chart) |
| Reserve-list evidence | The NFL's November 2026 reserve list contains dated Reserve/Injured entries, including Malik Willis on Nov. 10. The earlier e46 capture was not rewritten or backfilled. | [NFL November 2026 reserve list](https://www.nfl.com/transactions/league/reserve-list/2026/11) |
| Official schedule/rule sources | The NFL schedule release is dated May 14, 2026; the 2026 rulebook lists Rule 6-1-6 as permitting a team to declare an onside kick at any time during the game. Rule presence is verified; predictive value is not. | [Dated schedule announcement](https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced) · [2026 NFL Rulebook](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook) |
| Weather source | NWS documents an API for forecasts, alerts and observations. A Game Book's postgame observation must not be substituted for an issued pregame forecast or 90-minute roof decision. | [National Weather Service API documentation](https://www.weather.gov/documentation/services-web-api) · [sample Game Book](https://static.www.nfl.com/image/upload/v1794854921/gamecenter/ab78a133-4feb-11f1-abca-2c54536568a9.pdf) |
| Detroit Week 10 designation check | In the specific e46 Week 10 capture checked here, Kerby Joseph, Cade Mays and D.J. Reed each have Game Status Out, matching the retrieved official Week 10 injury page. This does not certify other weeks or other copies of the table. | [NFL Week 10 injury report](https://www.nfl.com/injuries/league/2026/reg10) |

## Material blockers

1. **Price policy:** the reviewed price-snapshot table has blank market-open and market-close cells. NFL schedule/standings are not operator quotes. Do not publish a market residual, CLV or ROI without a permitted, timestamped operator/licensed source.
2. **Availability freshness:** the requested Week 12 injury URL returned Week 10. Wrong-week data is not current data; no injury level or change was inferred.
3. **Depth coverage:** only two club pages were re-checked here. The NFL directory identifies 32 club sites, but this review is not a 32/32 route certification. Houston needs an authorized structured source; no image-by-eye transcription. Packers raw strings must be retained when normalizing jersey numbers.
4. **Actual starters and inactives:** the Game Book sample shows that official per-game evidence exists, but the Game Book notice carries a written-permission restriction. Full-game coverage and reuse terms remain unresolved.
5. **Roster events:** a current official reserve-list route is now found, but older captures remain snapshots of what was known then. A later read must not silently rewrite the historical state.
6. **Snap counts:** one attempted NFL statistics URL returned 404. This is not proof that no official snap-count source exists; no snap share is published here.
7. **Strategy validation:** this review does not certify any strategy. The prior e46 signal table is a backtest snapshot; the proper-score gate cannot be treated as prospective skill. A preregistered singles shadow baseline, chronological train/validation/final holdout, controls, uncertainty, multiplicity and a price benchmark are needed.
8. **Parlays and prop combos:** keep them unranked until directly validated joint probabilities and the applicable operator/jurisdiction void/push rules are available. Do not multiply marginals under dependence.
9. **Existing citation quality:** several numerical claims on an earlier suggestions page cannot be reproduced from the official links displayed beside them. This hub intentionally does not repeat those numbers; publish the underlying data, code/version, sample, period and uncertainty or leave them blank.
10. **Terms and public/private separation:** official sources are not automatically permission to retain or republish raw content. Review rights source by source and keep restricted raw data private.

## Recommended order of work

1. Record terms for each source and decide the permitted private/public uses before ingestion.
2. Select an automated price source; if none clears rights and timestamp checks, keep price-dependent outputs blank. No manual data-entry fallback.
3. Schedule immutable official captures with UTC timestamp, raw hash, source identity, parser status and freshness/drift alarms. Fail closed when page week or required schema is wrong.
4. Complete a 32-club depth-route audit; preserve raw slot strings, grouped/empty slots and source dates. Separate expected depth from actual Game Book/inactive evidence.
5. Join official reserve/transaction events by effective time. Build the expected-versus-actual availability graph with conflicts and unknowns represented explicitly.
6. Verify an official snap-count source and its terms before modeling playing time; do not derive depth from jersey number, experience or salary.
7. Pre-register a singles-only shadow baseline with version hash and two-sided “what would change our mind” tests. Publish each forecast as probability plus exact inputs. Compare identical models with/without verified availability features on chronological holdouts and publish uncertainty.
8. Keep backtests out of the prospective leaderboard. Separate signal from staking, publish proper-score skill relative to controls with game-cluster uncertainty and multiplicity adjustment, and retain a removal-of-luck panel.
9. Hold parlays and prop combos behind a direct joint-probability and settlement-rule gate. Add venue, NWS forecast and roof/surface data only when each value has a time-matched official source.

## Site and audit

The review hub has separate [Questions & answers](../../nfl-review-3bba0722/questions.html), [Suggestions for review](../../nfl-review-3bba0722/suggestions.html), [Flagged for review](../../nfl-review-3bba0722/flagged.html) and [Sources](../../nfl-review-3bba0722/sources.html) pages. Every data table links to an official source or displays an explicit unverified state; repository evidence is identified separately. All suggestions remain **AWAITING REVIEW** and this session makes no changes to any existing model or shared navigation.

The exact UTC retrieval time was not exposed by the page retriever, so only the date is recorded. This session checked one NFL Game Book, two club depth pages, the requested injury route, the reserve-list route, the schedule/standings pages, the rulebook, one operator help page and NWS documentation. It did not perform the full 32-team or full-season audit.
