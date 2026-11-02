# Source and repository audit

Audit date: **2026-11-02 UTC**. Evidence is frozen in `research/evidence/`; the source register records the official URL, publisher, access method and SHA-256 of each excerpt.

## Starting repository

The checkout and `origin/main` contained exactly one file, `README.md`, with one line: `# Own5`. There was no application, dataset, test suite, workflow, coordination board, or prior claim to review. The initial claim was committed and pushed before implementation. The platform-required branch is `arena/e0e66278-own5`; the requested `session-*` branch convention is recorded as a platform exception in `COORDINATION.md`.

## Verification procedure

1. Read the rendered official page, not a third-party summary.
2. Save only the relevant official rows/quotations, with the source URL and retrieval date.
3. Parse each row into typed fields. Do not replace blank source cells with zero.
4. Check identifiers, row counts, duplicate keys, date/opponent/result agreement, and arithmetic reconciliation.
5. Link every published fact row to its official source. Link derived rows to their official inputs and label them **derived**, not official.
6. Put unavailable values and source irregularities on Flagged for Review.

The automated audit rechecks the saved evidence and arithmetic. It does not claim to continuously monitor upstream pages. A successful internal-link check is not a claim that every external site permits automated requests.

## Reconciliation controls

| Check | Result | Official control |
|---|---|---|
| Standings coverage | 32 unique teams | [NFL standings](https://www.nfl.com/standings/league/2026/REG) |
| League points | PF sum equals PA sum; both computed as 5,528 from the saved rows | [NFL standings](https://www.nfl.com/standings/league/2026/REG) |
| Week 9 coverage | 15 matchups; 30 participating teams plus PIT and TEN on bye | [NFL Week 9](https://www.nfl.com/schedules/2026/by-week/week-9) |
| Burrow log | 17 regular-season rows; passing yards sum to 4,918 | [NFL log](https://www.nfl.com/players/joe-burrow/stats/logs/2024/) · [NFL career control](https://www.nfl.com/players/joe-burrow/stats/career) |
| Chase log | 17 regular-season rows; 1,708 receiving yards and 127 receptions | [NFL log](https://www.nfl.com/players/ja-marr-chase/stats/logs/2024/) · [NFL career control](https://www.nfl.com/players/ja-marr-chase/stats/career) |
| Pair alignment | All 17 week/date/opponent/result tuples match; bye week 12 excluded | [Burrow log](https://www.nfl.com/players/joe-burrow/stats/logs/2024/) · [Chase log](https://www.nfl.com/players/ja-marr-chase/stats/logs/2024/) |

Computed sums are derived checks, not separately published official totals. The career controls independently agree with the log sums.

## Irregularities and exclusions

- The NFL Support URL named “What is the point spread?” returned a moneyline explanation. It is used only for the moneyline statements it actually contains.
- A guessed `jamarr-chase` slug returned a `player.DisplayName` placeholder. It was rejected. The canonical `ja-marr-chase` page returned the named player and complete log.
- A search-index excerpt of Chase’s career page was older than the rendered page. The rendered 2024 row, not the stale snippet, is used.
- The GSIS help page is public, but its schedule entry redirected to a login/error page. No bulk or authenticated GSIS feed is claimed.
- The 2026 scoring quotation comes from the official NFL PDF. The explicitly extracted overtime change is labeled 2025; rule versions must remain season-specific.
- No sportsbook price archive, current prop quote, current participation report, or out-of-sample wager ledger was verified. Those fields remain blank.
- FanDuel’s help is an official **operator** source, not a universal rule for all sportsbooks.
- Community mirrors and scrapers were inspected only to understand public document discovery. They are not used as factual sources in the dataset.

All review items, including the official links needed to inspect them, are in `data/own5_desk/review_items.json` and on the site’s Flagged for Review page.
