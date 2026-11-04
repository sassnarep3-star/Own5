# Raw evidence log — session 6d508fee (NBA signal desk)

Every dataset row in `nba-signal-lab/data/` was transcribed from an official
NBA property fetched through the platform page-fetcher on 2026-11-03 UTC
(sandbox bash cannot reach nba.com — outbound HTTPS to NBA hosts is blocked,
verified: curl exit 35). Values were transcribed by hand from the rendered
official pages; checksums below were recomputed against independent official
pages to detect transcription errors. Nothing is inferred or filled in.

## Fetch register (2026-11-03 UTC)

| # | URL (official) | What was transcribed | Checksum performed |
|---|----------------|----------------------|--------------------|
| E1 | https://www.nba.com/standings | 2026-27 standings, 30 teams (W-L, CONF, DIV, HOME, ROAD, Neutral, OT, LAST10, STREAK) | W-L cross-checked vs team traditional table (E2): all 30 match |
| E2 | https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season | 30 team rows (GP, W, L, WIN%, MIN, PTS, FGM-FGA-FG%, 3PM-3PA-3P%, FTM-FTA-FT%, OREB, DREB, REB, AST, TOV, STL, BLK, BLKA, PF, PFD, +/-), per-game mode | GP/W/L vs E1 all 30 exact; league Σ(+/- × GP) = 0 asserted in compute |
| E3 | https://www.nba.com/standings?Season=2025-26 | 2025-26 final standings, 30 teams (W-L, HOME, ROAD, Neutral, OT) | HOME/ROAD/Neutral split sums to W-L per team (asserted in compute) |
| E4 | https://www.nba.com/stats/leaders?Season=2025-26 | Player registry + season averages used as game-log checksums (Luka Dončić 1629029, Shai Gilgeous-Alexander 1628983, Anthony Edwards 1630162, Jaylen Brown 1627759) | GP + PTS/REB/AST/3PM averages re-averaged from transcribed game logs must match to 1dp (asserted in compute) |
| E5 | https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26 | Anthony Edwards 2025-26 game log rows (Match Up + game URL, W/L, MIN, PTS, 3PM, REB, AST, STL, TOV) | see E4 checksums (GP 61, PTS 28.8, REB 5.0, AST 3.7, 3PM 3.4) |
| E6 | https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26 | Luka Dončić 2025-26 game log rows | E4 (GP 64, PTS 33.5, REB 7.7, AST 8.3, 3PM 4.0) |
| E7 | https://www.nba.com/stats/player/1628983/boxscores?Season=2025-26 | Shai Gilgeous-Alexander 2025-26 game log rows | E4 (GP 68, PTS 31.1, REB 4.3, AST 6.6, 3PM 1.7) |
| E8 | https://www.nba.com/stats/team/1610612745/traditional 2025-26 team traditional | prior-season per-game team stats (2025-26) | PF/g identity vs standings wins (soft), Σ(+/- × GP) = 0 |
| E9 | https://www.nba.com/<team>/schedule (8 team pages) | Nov 4, 2026 slate rows (date, time, H/A, opponent, arena) | each game cross-confirmed when both teams' pages fetched |
| E10 | https://www.nba.com/games?date=2026-11-03 and ?date=2026-11-04 | official game-count calendar (Nov 3: 0 games; Nov 4: 14 games) | used only for counts + slate completeness flag |

## Irregularities observed during transcription

- The 2026-27 standings page (E1) and the team traditional page (E2) are
  independent official renderings; all 30 W-L records agree exactly.
- `https://www.nba.com/games?date=2026-11-04` renders only the calendar and
  game counts without JavaScript; the 14 individual matchups could not be
  enumerated from that page. Slates were taken from official team schedule
  pages instead (E9). Completeness limitation published as flag.
- `https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json`
  returned HTTP 500 through the fetcher (not usable).
- `https://www.nba.com/standings?Section=margins` renders situational splits
  (3pts or less, score 100+, ...), not PF/PA margins; PF/PA were therefore
  taken from E2 (PTS per game and +/- per game; PA/g = PTS/g − +/−g is a
  documented derivation subject to 1dp rounding of both inputs — flagged).
- Player box-score pages report "Rows" counts (e.g. 61 Rows for Edwards
  2025-26); transcribed row counts must equal these.
