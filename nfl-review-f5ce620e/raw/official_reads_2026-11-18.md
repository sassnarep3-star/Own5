# Source-read notes — 2026-11-18 UTC

**Primary capture window:** fetcher reads made on 2026-11-18 between approximately 03:14Z and 03:21Z, using Arena's page fetcher. A follow-up official Houston Texans stadium-page read was made at approximately 03:27Z. The fetcher does not expose a server `Date` header or exact per-request UTC timestamp; the local UTC clock was read after batches. Times are therefore minute-level read windows, not server timestamps.

**Capture scope:** these are short source-response notes and table transcriptions, not complete HTTP/HTML archives. The local SHA-256 manifest covers this note file and the generated venue/result tables only; it does not hash or authenticate original live pages. No sportsbook odds values or Game Book player-level rows are copied into this file.

## Official NFL Week 11 injury endpoint

Requested: https://www.nfl.com/injuries/league/2026/reg11

The fetcher returned `url: https://www.nfl.com/injuries/league/2026/reg10`, with title `Official NFL Injury Report for Players - Week 10 of the 2026 Season | NFL.com` and heading `Injuries - WEEK 10`. This establishes the endpoint state observed in this read; it does **not** establish that club pages lacked Week 11 reports.

## Houston Texans Week 11 injury report (official club page)

https://www.houstontexans.com/news/week-11-injury-report-texans-vs-colts

The page title is `Injury Report | Week 11`; it says published Nov. 16, 2026 at 05:48 PM and updated Nov. 17 at 03:46 PM (the page does not state a timezone). It contains Houston Texans and Indianapolis Colts practice-status tables with MON and TUES columns. The table does not provide a final game-status column. Only the two clubs in this matchup are covered here; this is not a 32-club report.

## Official NFL Week 11 schedule and game centres

Schedule: https://www.nfl.com/schedules/2026/by-week/week-11

The schedule page lists Colts at Texans on Thursday, Nov. 19 at 8:15 PM. Each of the 13 scheduled Week 11 game-centre pages was opened during the primary read window. Their published `Game Info` location and stadium labels are transcribed in `../data/venues_week11.csv`, with one official NFL game-centre URL per fixture. No weather, roof, surface, or inferred home-field adjustment is added to that venue table.

## Official Houston Texans stadium naming (follow-up read, approximately 03:27Z)

https://www.houstontexans.com/stadium/

The official club page is titled `Reliant Stadium (Previously NRG Stadium) | Houston Texans` and calls Reliant Stadium the home of the Texans. It says the stadium used the NRG Stadium name from 2014 until August 2026, when the Reliant name returned. This corroborates the `RELIANT STADIUM` label returned by the Week 11 Colts–Texans Game Center as of the page read; it is not a stale-name discrepancy. Preserve the NFL Game Center's exact published label in the venue table.

## Official NFL result update — Week 10

Game centre: https://www.nfl.com/games/chargers-at-ravens-2026-reg-10

The page shows Los Angeles Chargers 23, Baltimore Ravens 20, `Final`, Week 10, Nov. 16. The Week 10 schedule page independently lists the same final. This is the one game missing as pending in the earlier 2026-11-17 result-feed capture; the source-linked delta is in `../data/results_increment_week10.csv`. This one-row delta is not a claim that the carried-forward full results feed or 32-club standings have been rebuilt and reconciled.

## Historical club-code join check (repository-derived, not a live source capture)

The read-only `nfl-desk-e46fb855/data/results_feed.csv` contains 145 game rows and 290 team appearances. Its 9 `LAR` and 9 `ARI` appearances do not match the `LA` and `AZ` codes in the prior desk's official standings transcription, so an exact team-code join misses 18 club-game appearances. The newer `nfl-desk-35a1feb2/data/results_feed_2026.csv` uses `LA`/`AZ` and its integrity register records a 32/32 club reconciliation at its earlier cutoff. That earlier result does not verify the full feed after the later Chargers–Ravens final; no full-feed rebuild was performed here. This is an audit of local code joins, not a new NFL field/value.

## NFL Game Book access and use notice

The official Week 10 Chargers–Ravens Game Center page exposes a `Download Game Book (PDF)` link to:

https://static.www.nfl.com/image/upload/v1794916121/gamecenter/ab78ad5a-4feb-11f1-abca-2c54536568a9.pdf

The PDF's own notice says it is for the express purpose of assisting media coverage and that any other use is prohibited without written permission. The PDF includes lineup, substitution, did-not-play and not-active sections. This review does not reproduce player-level Game Book rows or use them as model inputs. Obtain written permission or an expressly authorized feed before operational or public reuse. The NFL Operations Game Books landing page returned only a skip-navigation line in the parsed response; that response is not evidence that Game Books do not exist.

## Official club depth-chart pages

Houston: https://www.houstontexans.com/team/depth-chart

The official Texans page labels its chart `Unofficial Depth Chart` and presents the chart as an image; the fetcher exposed no structured player rows. No transcription by eye was attempted.

Green Bay: https://www.packers.com/team/depth-chart

The official Packers page says `Unofficial, Nov. 10, 2026`. Player strings include jersey numbers (for example, `9 Christian Watson`); this is a formatting observation, not a basis for assigning depth rank. Preserve the raw string and group/empty columns if this source is ever parsed.

## Current official reserve-list page

https://www.nfl.com/transactions/league/reserve-list/2026/11

The current page read shows entries dated Nov. 17, 2026. The earlier in-repository capture was read at 2026-11-17T00:46Z and its newest official date was Nov. 16. Re-capture and compare the full paginated history before making any absence-based roster claim; a later page update does not make the earlier timestamped capture false.

## Inherited official transaction reads (prior desk; not re-read in this batch)

The prior desk's raw transcript, `../../nfl-desk-35a1feb2/raw/official_reads_2026-11-17.txt`, records an NFL November reserve-list read at 2026-11-17T00:46Z and a November trades read at 2026-11-17T00:43:30Z. The reserve table stored by that desk contains 25 November rows dated Nov. 7–16 and 25 October rows dated Oct. 24–31; the only stored Baltimore reserve row is Tavius Robinson, dated Oct. 24. Its reserve schema has no player-position column. The recorded November trades include Jacoby Brissett from Arizona to Baltimore on Nov. 6; the trade table also has no position field. The transcript explicitly limits those reads to the rows returned and does not claim a complete historical or paginated transaction search. These are inherited source notes, not a fresh 2026-11-18 transaction recapture.

## Official club inactive list example

https://www.houstontexans.com/news/texans-inactives-week-10-vs-cleveland-browns

The page is dated Nov. 15, 2026 at 10:30 AM and has a dated `Texans Inactives` section for the Week 10 game. This demonstrates a club-level inactive-list source route; an inactive list does not by itself identify all actual starters or snap shares.

## Official operator market page (values withheld)

https://sportsbook.draftkings.com/leagues/football/nfl

The first-party sportsbook page returned upcoming NFL game markets with `Spread`, `Total`, and `Moneyline` categories. It also displayed a server-time label without a timezone. Some embedded team-image request URLs contained `x-pe-loc=US-RI`; this is not proof of the user's jurisdiction or of Georgia availability. Exact odds were observed in the tool response but intentionally were not copied into the repository or public site: source terms, redistribution rights, the local market context, and a historical opening/closing feed have not been established. The observed page is a source route, not a verified open/close archive and not CLV evidence.

## Official sportsbook combo-rule reference

https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet

The guide describes parlays, same-game parlays and round robins; its void-leg section says a voided leg is removed and the remaining parlay legs are recalculated. This is operator-specific settlement information; it does not validate multiplying marginal probabilities or establish another operator's rules. The page was fetched in two chunks.

## Third-party NFL data (not official NFL data)

https://github.com/nflverse/nflverse-data

The existing repository's `data/decision-desk/raw/games.csv.gz` is an nflverse release asset, not an NFL-published data file. A local schema/count check in this review reproduced 7,548 rows; 7,439 rows have both a spread and total, 5,458 have both home and away moneylines, and the 2026 subset has 272 rows, of which 163 have a spread and total. These are counts of the committed third-party file, not official NFL market facts. The file contains one game-level line set, not an opening/closing pair with quote timestamps. The prior desk asset register labels this asset third-party and `official=no`; the data-license/use decision remains open.

## Official NFL standings

https://www.nfl.com/standings/league/2026/REG

The standings page returned a partial official league table in this read. It is useful for standings context, but this review did not rebuild and reconcile the full result feed against all 32 clubs after the Week 10 Chargers–Ravens final.

## Scope and verification boundary

The source URLs are live review routes and may change after capture. Hashes in `data/manifest.json` cover this note plus the two local CSV tables only. They prove that those local files have not changed since their hashes were generated; they do not prove which bytes a source server returned. There are no saved full HTTP responses, response headers, exact per-request fetch timestamps, or original sportsbook quote values in this dossier. The findings therefore distinguish source facts from capture limits, and keep unconfirmed values blank or flagged.
