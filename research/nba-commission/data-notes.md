# Data notes & source register — NBA Line Commission (session arena-a46d621e)

All data fetched **2026-11-05 (UTC)** through the platform page fetcher. The sandbox cannot reach
nba.com over curl/wget (outbound TLS is restricted to GitHub hosts); the fetcher renders the official
pages and the tables below were transcribed by hand into `nba-commission/data/*.csv`.

## Fetch register

| ID | URL (official) | Transcribed | Validation |
|---|---|---|---|
| E1 | https://www.nba.com/standings | 2026-27 standings, 30 teams (W-L, PCT, GB, CONF/DIV/HOME/ROAD/NEUTRAL/OT/L10/STREAK) | W-L vs E2 = 30/30 exact; split sums 30/30 (X01, X03) |
| E2 | https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season | 30 team per-game rows (shooting, rebounding, turnovers, net) | GP = W + L 30/30; Σ(net×GP) = 0.7 (X02, X04) |
| E3 | https://www.nba.com/schedule?date=2026-11-05 | 11 slate games (2 on 11-05, 9 on 11-06): date, tip (ET), venue, city, competition | 11 unique game ids; every team in E1 (X09) |
| E4 | https://www.nba.com/stats/player/1630162/boxscores?Season=2026-27 | Anthony Edwards 2026-27: 4 rows | headline 33.3 / 4.8 / 3.5 reproduced exactly (X06) |
| E5 | https://www.nba.com/stats/player/1629029/boxscores?Season=2026-27 | Luka Dončić 2026-27: 8 rows | headline 38.5 / 8.1 / 8.0 reproduced exactly (X06) |
| E6 | https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26&DateFrom=2025-10-01&DateTo=2025-11-20 | re-fetch of 6 rows already inside the inherited 2025-26 log | 6/6 exact match field by field (X10) |
| E7 | https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season | prior-season team means, reused from session 6d508fee | internal consistency only; page not re-fetched (F07) |
| E8 | https://www.nba.com/games?date=2026-11-05 | attempted slate page | renders "No Games Scheduled" while its own calendar shows 2 games — dead end, flagged F05 |

Methodology references (no NBA values taken from them): Notices of the AMS 2014 (overfitting),
Bailey & López de Prado 2014 (deflation), arXiv 1710.02824 (market efficiency), statsmodels
(multiple-testing corrections). See the site's Sources page.

## Transcription protocol

1. Tables were read from the rendered official page, one column at a time, and written into CSV.
2. Every row carries `source_url`; a missing or non-official URL fails verification.
3. Row identities are asserted (`PTS`, `REB`, `GP = W + L`, split sums).
4. Checksums: recomputed per-player averages must equal the official headline averages printed on
   the same page, to one decimal, using round-half-up.
5. Where a page's own rendering was ambiguous (rounded net values, "--" GB for conference leaders,
   duplicate rank numbers on ties) the value is transcribed as printed and the ambiguity is flagged
   rather than resolved by inference.

## Derived values (documented, never guessed)

- `PA/g = PTS/g − net/g` — exact given the two published columns, to the pages' 1-decimal rounding.
- League average points (113.43) — GP-weighted mean of the 30 official rows.
- Home win rate (0.5124) — home wins ÷ home decisions across the 30 official home/road splits.
- Own lines, correlations, prop prices, power figures — computed in `compute.py`; formulas in
  `methodology.md`; parameters (K_BLEND = 20, K_PROP = 20, HFA = 2.5, PRIOR_PSEUDO = 25) are named
  model choices and flagged.

## Irregularities observed at the source

1. `https://www.nba.com/games?date=2026-11-05` renders "No Games Scheduled" although the month
   calendar on the same page shows 2 games for that date. Slate taken from `/schedule`; discrepancy
   recorded (F05).
2. The team-traditional table prints *duplicate rank numbers* for tied teams (e.g. three rows ranked
   14) — a presentation artifact, not a data error; values were taken from the rows, not the ranks.
3. The standings GB column shows `--` for conference leaders whose records differ in games played
   (POR 6-1 above LAL and HOU at 7-2), because GB is computed against win% rank. Read with care (F14).
4. Player box-score pages cap at 50 rendered rows; longer seasons require the official
   `DateFrom`/`DateTo` filters. The 2026-27 pages are short enough to render fully.
5. Nine of the eleven slate games are Emirates NBA Cup group-play games listed on the regular-season
   schedule. Their treatment in the standings was **not** verified in this session (F06).
6. Inherited CSV headers from `nba-signal-lab` contain a Cyrillic U+0430 in `blkа_pg`. This session's
   copy normalises the key; the original files were not edited (F13).
