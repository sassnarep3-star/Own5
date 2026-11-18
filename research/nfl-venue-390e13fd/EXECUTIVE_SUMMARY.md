# Executive Summary — NFL Venue & Schedule-Announcement Desk (session 390e13fd)

**Session:** `arena/390e13fd-own5` · **Desk:** `nfl-venue-390e13fd/` · **Date of read:** 2026-11-18T03:43:57Z
**Mandate (user brief):** "Transcribe the venue of every fixture from the official
game centre and publish it" and "Publish the league's dated schedule announcement
beside the live schedule page."

## Deliverables

1. **Venue transcription — 13/13 Week 11 fixtures verified.** Each fixture's
   official NFL.com game-centre page was read; its *Game Info* block prints a
   location and a stadium, both transcribed verbatim into
   `data/venues.csv` as separate columns. Every row links to the official game
   centre; the venue-bearing extract of each page is committed under `raw/`.
2. **The Mexico City question is resolved.** Session 3cb7800c's Week 11 schedule
   desk left the Vikings at 49ers venue blank (flag F-03, REVIEW). The official
   game centre for that fixture states **Location: MEXICO CITY**,
   **Stadium: ESTADIO BANORTE**. The resolution is recorded on this desk's
   Flagged for Review page; 3cb7800c's own register was not edited (cross-session
   rule) — the resolution is logged in COORDINATION.md as a cross-session note.
3. **Dated schedule announcement published beside the live schedule page.**
   - Announcement article: "2026 NFL schedule powered by AWS to be released
     Thursday, May 14", **dated May 8, 2026** — records the release of the 2026
     NFL Schedule on **Thursday, May 14, 2026 at 8 p.m. ET**, and lists 2026
     International Markets including **Mexico City, Mexico (Estadio Banorte)**.
   - Schedule-release hub: **2026 NFL Schedule Release** page, dated
     **Thursday, May 14, 2026** — publishes the full schedule and the
     international slate (Week 11 international game at Estadio Banorte).
   - Live schedule page: the official Week 11 by-week schedule
     (13 games, read 2026-11-18T03:43:57Z), linked beside both.
4. **Site.** Clean dashboard (`index.html`) plus subpages: Schedule & Venues,
   Schedule Announcement, Sources, Flagged for Review, Executive Summary.
   Deterministic builder (`tools/build_site.py`), fail-closed verifier
   (`verify.py`), 12 unit tests, and a scoped CI workflow.

## Verified values (all from official NFL.com pages)

| Fixture | Location (as printed) | Stadium (as printed) | Source |
|---|---|---|---|
| Colts at Texans (Thu 11-19, PRIME) | HOUSTON, TX | RELIANT STADIUM | nfl.com game centre |
| Dolphins at Bills (Sun 11-22, CBS) | ORCHARD PARK, NY | HIGHMARK STADIUM | nfl.com game centre |
| Ravens at Panthers (Sun 11-22, FOX) | CHARLOTTE, NC | BANK OF AMERICA STADIUM | nfl.com game centre |
| Saints at Bears (Sun 11-22, FOX) | CHICAGO, IL | SOLDIER FIELD | nfl.com game centre |
| Titans at Cowboys (Sun 11-22, FOX) | ARLINGTON, TX | AT&T STADIUM | nfl.com game centre |
| Buccaneers at Lions (Sun 11-22, FOX) | DETROIT, MI | FORD FIELD | nfl.com game centre |
| Cardinals at Chiefs (Sun 11-22, CBS) | KANSAS CITY, MO | ARROWHEAD STADIUM | nfl.com game centre |
| Steelers at Eagles (Sun 11-22, CBS) | PHILADELPHIA, PA | LINCOLN FINANCIAL FIELD | nfl.com game centre |
| Jets at Chargers (Sun 11-22, FOX) | INGLEWOOD, CA | SOFI STADIUM | nfl.com game centre |
| Jaguars at Giants (Sun 11-22, CBS) | EAST RUTHERFORD, NJ | METLIFE STADIUM | nfl.com game centre |
| Raiders at Broncos (Sun 11-22, CBS) | DENVER, CO | EMPOWER FIELD AT MILE HIGH | nfl.com game centre |
| Vikings at 49ers (Sun 11-22, NBC) | MEXICO CITY | ESTADIO BANORTE | nfl.com game centre |
| Bengals at Commanders (Mon 11-23, ESPN) | LANDOVER, MD | NORTHWEST STADIUM | nfl.com game centre |

Byes (Week 11): Falcons, Browns, Packers, Rams, Patriots, Seahawks — from the
official by-week schedule page.

## Irregularities / flags

- **VF-01 (INFO, RESOLVED-HERE):** the open venue flag F-03 from session
  3cb7800c, resolved from the official game centre (see above).
- **VF-02 (INFO, OPEN):** the official game centre prints the Vikings at 49ers
  location as the city name only (`MEXICO CITY`), without a state/country
  suffix. Published as printed; no suffix added.
- **No unverified values.** No venue cell is blank; no value was inferred.

## Limitations

- Venue values are a point-in-time transcription of the official pages as read
  on 2026-11-18T03:43:57Z; the official pages remain the authority if any
  fixture's venue changes.
- The announcement dates (May 8, 2026 and May 14, 2026) are the dates printed
  on the official NFL.com pages.
