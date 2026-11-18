# Verification log — session 4078a9ad, read 2026-11-18 (UTC)

One line per check. "Read" means the page was retrieved in this session with the sandbox fetch
tool and its text read. Times are the read stamps recorded in `nfl-command-desk/data/sources.csv`.
nfl.com is **not** reachable by direct HTTPS from the sandbox (`curl` returns an SSL error); the
fetch tool is the retrieval path, and it returns processed text, not server bytes. That
limitation is recorded on the site (sources page) and in every row that cites a page.

## A. Pages read

| # | Page | Read (UTC) | What was taken from it | Chunks |
|---|---|---|---|---|
| 1 | https://www.nfl.com/schedules/2026/by-week/week-11 | 03:47 | 13 fixtures, 6 byes, networks, dates, hotel-link venues | 3 of 3 |
| 2 | https://www.nfl.com/injuries/league/2026/reg11 | 03:45 | **resolved to reg10**; title "Week 10 of the 2026 Season"; 44 rows for WAS/NYG/NE/DET | 1 of 8 |
| 3 | https://www.nfl.com/schedules/2026/by-week/week-10 | 03:50 | 14 finals with scores, 4 byes, one "Weather Clear" note | 2 of 2 |
| 4 | https://www.nfl.com/standings/league/2026/REG | 03:52 | 32 rows: W-L-T, PCT, PF, PA, NET, records, streak | 2 of 2 |
| 5 | https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1 | 03:55 | spot check: NE 10, SEA 13, Lumen Field, Game Book PDF link | 1 of 1 |
| 6 | https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced | 03:58 | dated announcement 2026-05-14; 18 weeks, 272 games, 17+3, nine international games, Week 11 in Mexico City | 1 of 2 |
| 7 | https://api.github.com/repos/sassnarep3-star/Own5/pages | 03:41 | Pages served from `main` at `/`, status `built` | API |

## B. Line-by-line checks performed

| Check | Method | Result |
|---|---|---|
| Corpus arithmetic | PF and PA recomputed from 150 rows | 32/32 clubs match; league PF = league PA |
| Corpus row count | pinned in the verifier | 150 (136 adopted + 14 added) |
| Reconcile negative control | planted a 1-point error and a flipped result | both correctly fail |
| Week 11 internal consistency | 13 games x 2 clubs + 6 byes | 32 distinct clubs, each once |
| Week 11 vs announcement | 6 comparable facts | 6/6 agree |
| Week 11 venue | hotel link destination per row | 13/13 sourced, method stated per row |
| Standings page consistency | recomputed PCT from W-L-T | 32/32 to 3 dp |
| Standings arithmetic | (W+L+T) equals games played implied by PF/PA blocks | consistent |
| Injury re-read | 44 rows compared cell by cell with the 2026-11-12 copy | 27 identical, 17 stale |
| Lions trio (brief) | Joseph, Mays, Reed | all three now OUT with an injury and DNP |
| Registration commit | `git cat-file -t f85bb0b` | exists, type `commit` |
| Site links | regex over 11 pages | 0 internal misses, 0 external non-official |
| Forbidden claims | regex for "certified", "ROI of", "guaranteed" | 0 hits |
| Drift alarms | pinned counts for 18 CSVs | 18/18 exact |

## C. Irregularities found (published on the Flagged page)

1. **FLAG-A1 — two club-code sets.** The standings page prints `AZ` and `LA`; the Week 11 page
   prints `LAR` in the bye block. The corpus uses `ARI`/`LAR`/`WSH` from earlier desks. Normalised
   for reconciliation only; the mapping is published.
2. **FLAG-A4 — the Week 11 report was not published.** A request for `reg11` served `reg10`. The
   resolved URL and the page title are both recorded. This is the second week running that a desk
   has logged this (sessions 3cb7800c, 98a211b8), which is corroboration, not a new finding.
3. **Stale availability capture.** 17 of the 44 re-read rows differ from the repository copy,
   including the three Lions cells the brief flagged. The repository copy is not wrong about
   what it saw on 2026-11-12; it is simply a single point in time and has since moved.
4. **Home-field assumption.** 2.0 points is assumed; the 2026 observed home margin is −0.98 over
   150 games (95% CI −3.07 to +1.13). The assumption is registered and flagged, not fitted.
5. **Week 1 date label.** The NFL.com game page for Patriots at Seahawks heads the game "Sunday
   Night Football, September 9th" while dating it Wednesday, September 9. The corpus keeps the
   earlier desk's note rather than resolving it; the schedule announcement independently says
   "Wednesday night, September 9".
6. **Only 1 of 8 chunks read.** The Week 10 injury page was read to chunk 0 only, so the 44 rows
   cover four clubs and the full-page row count is unknown. Quoted as unknown, not estimated.
7. **Root index is stale.** `index.html` is stamped "Reviewed 2026-11-02" and does not link this
   desk. It is generator-locked by `verify.yml` and was not edited (FLAG-S2).

## D. What this session did **not** verify

* Any market price, for any market, on any date (FLAG-P1).
* Any snap count, playing-time split or game-day inactive list (FLAG-A2).
* Any club depth chart, for any of the 32 clubs (FLAG-D1).
* Any player-level statistic; none was read, so none is published (Q11).
* Any Week 11 availability value (the report did not exist at read time).
* Any stadium roof or surface designation and any NWS forecast (FLAG-W1).
* Any correlation between two legs (FLAG-C1).
* The venue or kickoff of the 136 adopted rows; only their scores are reconciled.

## E. Reproduction

```
python3 nfl-command-desk/generate.py && python3 nfl-command-desk/build.py
python3 nfl-command-desk/verify.py            # 46 passed, 0 failed
python3 -m unittest discover -s nfl-command-desk/tests   # 24 tests, OK
```
