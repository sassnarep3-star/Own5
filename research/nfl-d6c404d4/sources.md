# Sources — every external read, with its stamp and its class

Classes:
- **OFFICIAL** — published by the league or a club. Used for fixtures, results, standings and designations.
- **OPERATOR** — a named licensed sportsbook. Used only for prices we quote, with the operator named.
- **AGGREGATOR** — an independent research dataset (nflverse). Never described as official; labelled
  `PINNED-DATASET` on every row.
- **REPO** — a committed artifact in this repository, including committed byte captures.

| ID | Source | Class | Read (UTC) | Supports |
|---|---|---|---|---|
| SRC01 | https://www.nfl.com/standings/league/2026/REG | OFFICIAL | 2026-11-19T06:50:00Z | W-L-T, PCT, PF, PA for 32 clubs; the reconciliation target |
| SRC02 | https://www.nfl.com/schedules/2026/by-week/week-11 | OFFICIAL | 2026-11-19T06:49:00Z | The 13 Week 11 fixtures, kickoff times as printed, networks, byes |
| SRC03 | https://www.nfl.com/schedules/2026/by-week/week-10 | OFFICIAL | 2026-11-19T06:52:00Z | 14 Week 10 finals, all marked FINAL |
| SRC04 | https://www.nfl.com/injuries/league/2026/reg11 | OFFICIAL | 2026-11-19T06:53:00Z | 253 designation rows, 24 clubs; game status on 16 rows (IND/HOU) |
| SRC05 | https://sportsbook.draftkings.com/leagues/football/nfl | OPERATOR | 2026-11-19T07:00:00Z | DraftKings Week 11 spreads, totals, moneylines |
| SRC06 | https://sportsbook.fanduel.com/navigation/nfl | OPERATOR | 2026-11-19T07:01:00Z | FanDuel Week 11 spreads, totals, moneylines |
| SRC07 | https://www.nfl.com/legal/terms/ | OFFICIAL | 2026-11-19T07:04:00Z | Basis for data policy P-01 (no row-level republication) |
| SRC08 | nflverse `games.csv.gz` (release asset) | AGGREGATOR | pinned sha256 in `data/decision-desk/raw/provenance.json` | 7,117-game corpus, closing spread/total/ML fields |
| SRC09 | nflverse `injuries_2023..2026.csv.gz` | AGGREGATOR | pinned sha256 | Designation reliability study (4 seasons) |
| SRC10 | nflverse `snap_counts_2023..2026.csv.gz` | AGGREGATOR | pinned sha256 | Playing time, drives proxy, usage rank |
| SRC11 | nflverse `stats_player_week_2024..2026.csv.gz` | AGGREGATOR | pinned sha256 | QB/team-top-WR same-game correlation |
| SRC12 | `own5-hub/captures/raw/reserve/20261118T032838Z.html.gz` | REPO | byte capture 2026-11-18T03:28:38Z | Reserve-list register (25 rows) |
| SRC13 | `data/nfl-desk-6cbf25fa/injury_reads/capture_injuries_2026-11-18.csv` | REPO | 2026-11-18T03:55:13Z | Prior injury read for the Week 11 delta |
| SRC14 | `data/games_2026.json` | REPO | `meta.as_of` 2026-11-02 | The 136-game log being audited, not used as a corpus |

## What was deliberately not used

- **The repository's 136-game log** as a corpus. 16 of its rows have no score and 3 fixtures are absent.
  It is audited row by row and published as an artifact, not trusted as truth.
- **An unnamed aggregator's closing line** for Week 11. It cannot be attributed, so it appears only in the
  flag list (F07), never in a table.
- **The pinned snapshot's Week 11 totals** as a "market" number. They are stale relative to today's operator
  boards; market columns come only from operator reads.
- **Any salary, contract, jersey or depth-chart source.** Not used for depth, by rule.

## Access limits, stated openly

The agent sandbox could not open nfl.com or the operator hosts (TLS handshake refused). Every official and
operator read in this desk was taken through a server-side page fetch, which returns text and not bytes, so
**no server-byte sha256 exists for today's reads** (flag F09). Byte-level captures exist only where a
committed capture already did that work, and those are labelled REPO. The committed workflow runs the
byte-level capture on GitHub's runners, which can reach the hosts.
