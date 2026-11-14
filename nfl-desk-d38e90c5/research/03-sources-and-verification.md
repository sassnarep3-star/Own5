# Sources and verification

## Source register

The machine-readable register is `data/sources.csv` and the published page is *Sources*. Every
published table row links to one of these entries.

| Source | Publisher | What it supports |
|---|---|---|
| https://www.nfl.com/standings/league/2026/REG | NFL.com | official W-L-T, PCT, PF, PA and point difference for all 32 clubs |
| https://www.nfl.com/schedules/2026/by-week/week-1 ... week-9 | NFL.com | 137 official final scores with dates |
| https://www.nfl.com/schedules/2026/by-week/week-10 | NFL.com | Week 10 matchups, kickoff times, networks, the completed Thursday result |
| https://www.nfl.com/schedules/2026/by-week/week-11 | NFL.com | Week 11 matchups, kickoff times, networks, venues |
| https://www.nfl.com/injuries/ | NFL.com | the complete official Week 10 injury report (347 rows) |
| https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-14 | NFL.com | the league notes published with the injury report (IR moves, quarterback changes) |
| 32 club depth-chart pages (`data/sources.csv`, ids `D-<club>`) | each club's own site | replacement depth tiers, first to fourth string |

Each club depth chart carries the stamp the club printed (for example "Unofficial, Nov. 10, 2026",
"Updated as of 11/10/26", "As of 10/31/2026"). The stamp is published with the source so a reviewer
can see how current each chart is.

## How the facts were verified

1. **Standings against results.** The 137 transcribed final scores are summed per club and compared
   with the official standings. All 32 clubs match on W, L, T, PF and PA, and the aggregate points
   scored and allowed are both 6,291. One transcription error was found and corrected during this
   check (the Week 2 Vikings-at-Bears score was initially written MIN 3 - CHI 9 and is MIN 9 - CHI 3).
2. **Multi-chunk pages.** The official schedule and injury pages are paginated. Every chunk was
   fetched and compared, not just the first one, because a single-chunk read silently truncates the
   Chiefs' injury block. The truncation and the two-segment Titans assembly are recorded as flagged
   irregularities.
3. **Machine-readable depth rows.** 31 of 32 club charts publish text rows. Houston publishes a
   raster image, so every Texans depth value is blank rather than estimated, and the image URL is
   pinned for manual review.
4. **Name matching.** Injury rows are matched to depth charts on the normalised player name, with a
   small first-name alias table (Josh/Joshua, Matt/Matthew, and similar published variants). 61 rows
   have no chart entry and stay blank with a flag; nothing is inferred from another club's chart.

## What the verifier checks

`verify.py` runs 115 checks and fails the build on any of them:

| Group | Checks |
|---|---|
| 1. Inputs reconcile | 32 clubs, points for and allowed equal to the transcribed results, 137 games, no duplicated matchup |
| 2. Source coverage | every populated source cell in every published dataset points at an official domain |
| 3. Blank-value policy | every blank market field is registered in the flagged register; a blank depth value only appears on a row registered as "no depth-chart match" |
| 4. Correlations | every row publishes a usable `n` and names the source of both inputs |
| 5. Publication order | every game publishes spread (1), total (2), moneyline (3); only the three required markets exist |
| 6. Price snapshots | no duplicate keys, an opening and a closing record for every market, the JSONL store and the published table agree |
| 7. Demotion gate | one decision per strategy, a reason for each, and no strategy leaves PAPER while a required criterion is not evaluable |
| 8. Site integrity | every page exists, no broken internal link, every page links to the source register and the flagged register |
| 9. Determinism | content hashes recorded for every published data file, so CI can prove the committed artefacts match a fresh build |

## Reproducing the build

```
cd nfl-desk-d38e90c5
python3 pipeline.py     # transcribe -> data/*.csv, data/price_snapshots.jsonl
python3 build_site.py   # data -> index.html, pages/*.html, assets/style.css
python3 verify.py       # 115 checks, exit code 0 on success
```

The build is deterministic: the same official inputs always produce byte-identical data files and
pages, which is what lets CI run `git diff --exit-code` after a rebuild.

## What could not be verified

| Item | Why | Status |
|---|---|---|
| Market spreads, totals, moneylines and prices | NFL.com publishes none; `nfl.com/betting/` returns 404; operator pages are geolocation-gated | blank and flagged |
| Player-prop lines and player-level statistics | the NFL.com team-stat tiles cannot be paired with their labels without ambiguity; the official Game Book PDF has not been parsed | blank and flagged |
| Houston Texans depth tiers | published only as a raster image | blank and flagged |
| Chiefs' and Titans' full Week 10 injury blocks | page-chunk truncation and a two-segment assembly | flagged as irregular |
| Exact historical injury context for Weeks 1-9 | nfl.com publishes only the current week's report | discovery step D-04 |
