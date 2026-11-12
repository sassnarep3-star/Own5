# Sources and provenance register

**Checked/retrieved:** 2026-11-12 (UTC date only unless a page explicitly states otherwise). The canonical row-level registry is [`sources_registry.csv`](../../nfl-b34253a1/data/sources_registry.csv) and the 32-team chart coverage register is [`depth_chart_coverage_2026_w10.csv`](../../nfl-b34253a1/data/depth_chart_coverage_2026_w10.csv).

## Primary official sources

- [NFL 2026 regular-season standings](https://www.nfl.com/standings/league/2026/REG): 32 team W-L-T / points for / points against entering Week 10; used for reconciliation and per-game standings metrics.
- [NFL schedules by week](https://www.nfl.com/schedules/2026/by-week/week-10) and NFL game pages: 2026 Weeks 1–9 finals and Week 10 matchups, times, venues, and bye rows. Each game in the current final log links to its NFL game page; historical rows were also reconciled to standings.
- NFL team statistics: [offense passing](https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all), [offense rushing](https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all), [defense passing](https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all), [defense rushing](https://www.nfl.com/stats/team-stats/defense/rushing/2026/reg/all). The team-stat CSV keeps a source URL for each category.
- [NFL injury index](https://www.nfl.com/injuries/) and [Week 10 injury report](https://www.nfl.com/news/nfl-week-10-injury-report-2026-season): selected practice/game statuses, body-part text, matchups, kickoff times, and venues. The row-level data is selective; it is not a full 32-team final inactive list.
- [NFL Nov. 11 news roundup](https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11): selected starter announcements, IR and injury-related context. The article is dynamic and is not treated as a complete injury feed.
- NFL Operations: [AT spotter role](https://operations.nfl.com/gameday/behind-the-scenes/at-spotters/), [health and safety](https://operations.nfl.com/game-operations-logistics/preparation-safety/health-safety), and [game/stadium preparation](https://operations.nfl.com/game-operations-logistics/preparation-safety/game-and-stadium-prep). These pages explain process only; no individual injury diagnosis or score adjustment was inferred.
- NFL player passing, rushing, and receiving leader pages were used only as discovery references: [passing](https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc), [rushing](https://www.nfl.com/stats/player-stats/category/rushing/2026/reg/all/rushingyards/desc), and [receiving](https://www.nfl.com/stats/player-stats/category/receiving/2026/reg/all/receivingreceptions/desc). No paired player-game/prop dataset is claimed.

## Sportsbook snapshot sources

- [DraftKings public NFL board](https://sportsbook.draftkings.com/leagues/football/nfl?category=games&subcategory=game-lines&nav_1=all-games)
- [FanDuel public NFL board](https://sportsbook.fanduel.com/navigation/nfl)

The 28 row-level quotes (14 games × two books) retain individual operator/event URLs and board URLs. These are operator snapshots, not NFL-published odds. A book's quote may differ from another book without either being erroneous. On the retrieved pages, exact UTC capture time and jurisdiction were not preserved, and a public listing is not evidence of account-level executability or an accepted bet.

## Club chart coverage

The data register lists all 32 official club-site chart URLs. Twenty-eight teams played in Week 10 and have the previously checked chart pages; CHI, DEN, PHI, and TB were Week 10 byes, and their chart pages were checked in this continuation to complete source coverage. Their chart sources are not used to create Week 10 injury observations or score adjustments.

Special cases recorded in the register: Chicago's page displays an as-of date of 2026-10-31; Denver's current chart page did not display an update date (a separate archived chart is marked unofficial and dated 2026-09-22); Philadelphia explicitly labels its chart unofficial and says it is compiled by the communications department; Tampa Bay's retrieved page did not display an update date. Houston's chart was image-only in the retrieval, so its string assignments remain unverified. Individual club chart pages may be marked unofficial; a chart is an order/reference, not proof of active status, replacement participation, or snaps.

## Provenance constraints

The sources are dynamic web pages; retrieved content is not a durable raw-page archive. The CSV snapshot preserves transcribed fields, source URLs, and available dates, not a cryptographic capture of the external page. Prior repo inputs that cited ESPN, Spreadspoke, nflverse, Kaggle, or other secondary datasets were not promoted to official evidence; they remain visible in the repository audit as legacy/flagged material and are not used for current lines or leaderboard claims. Team-code mappings (including NFL `AZ`/`LA` versus local `ARI`/`LAR`) remain documented in local fields instead of being silently relabelled.

For source-by-source titles, dates, scope, caveats, and all chart URLs, use the downloadable CSVs on the [Sources page](../../nfl-b34253a1/sources.html).
