# Data Notes & Source Register — NBA Signal Lab (session 6d508fee)

All data was fetched from official NBA properties on **2026-11-03 UTC** via the platform
page-fetcher (the sandbox cannot reach nba.com over curl/wget — outbound TLS to NBA hosts is
blocked, curl exit 35). Rows were hand-transcribed into `nba-signal-lab/data/*.csv`; each row
carries a `source_url` column pointing at its official page for manual review.

## Fetch register

| ID | URL (official) | Transcribed | Validation |
|---|---|---|---|
| E1 | https://www.nba.com/standings | 2026-27 standings, 30 teams (W-L, GB, CONF, DIV, HOME, ROAD, NEU, OT, L10, STREAK) | W-L cross-check vs E2 = 30/30 exact; split sums asserted |
| E2 | https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season | 30 team per-game rows (full shooting + rebounding + turnovers + PF + net) | W-L vs E1; Σ(net×GP)=0 asserted |
| E3 | https://www.nba.com/standings?Season=2025-26 | 2025-26 final standings, 30 teams | splits sum to record; **re-verification pass found 3 transcription errors (POR neutral/OT, PHX & LAC streaks), corrected against the official page** |
| E4 | https://www.nba.com/stats/leaders?Season=2025-26 | player registry (IDs + GP/PTS/REB/AST/3PM season averages) | used as checksum targets for E5–E6 |
| E5 | https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26 (+`&DateFrom=2025-10-01&DateTo=2025-11-20`) | Anthony Edwards 2025-26 game log — **61 rows** (50 rendered + 11 early window) | scoring/rebound identities 61/61; averages reproduce E4 (28.8/5.0/3.7/3.4) exactly |
| E6 | https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26 (+`&DateFrom=2025-10-01&DateTo=2025-12-19`) | Luka Dončić 2025-26 game log — **64 rows** (50 + 14) | identities 64/64; averages reproduce E4 (33.5/7.7/8.3/4.0) exactly; game 0022500019 cross-checked with Edwards' log (W/L consistent) |
| E7 | https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season | 30 prior-season team rows (model priors) | W-L vs E3; Σ(net×GP)=0 |
| E8 | https://www.nba.com/rockets/schedule, /sixers/, /pistons/, /grizzlies/, /wizards/, /lakers/, /blazers/ + /timberwolves (via HOU row) | 2026-11-04 slate rows (date, tip time as listed, H/A, opponent, arena, TV) | DET-PHI game confirmed on both teams' pages (times/arena/TV agree) |
| E9 | https://www.nba.com/games?date=2026-11-03 and ?date=2026-11-04 | official game-count calendar (Nov 3: 0 games; Nov 4: 14 games) | slate completeness flag (6 of 14 sourced) |
| E10 | https://www.nba.com/standings?Season=2025-26&Section=margins | attempted PF/PA margin section | renders situational splits instead — dead end, documented |

## Transcription validation protocol

1. **Row identities** (in `compute.py`, asserted in tests): PTS = 2·(FGM−3PM)+3·3PM+FTM and
   REB = OREB+DREB on every game-log row (125/125 pass).
2. **Checksums**: per-player GP + 1-dp averages recomputed from the logs must equal the
   official leaders-page values — exact match on both players.
3. **Cross-page agreement**: team W-L must match across two independent official renderings
   (standings page vs team-stats page) — 60/60 rows match.
4. **Split sums**: HOME+ROAD+NEU W-L must equal the record per team — all 60 rows pass after
   the re-verification fix.
5. **No duplicates**: (player_id, game_id) unique.
6. **Re-fetch diffing**: the verification pass re-fetched the 2025-26 standings and compared
   row-by-row; 3 errors were found and fixed (evidence of the loop working).

## Derived values (documented derivations, never guesses)

- **PA/g = PTS/g − +/−/g** — official pages publish PTS/g and net/g; PA/g is exact up to the
  pages' 1dp rounding (±0.1 flagged).
- **Home win % (empirical HFA evidence)** = ΣHOME wins / (ΣHOME wins+losses) from official
  split columns (2026-27 and 2025-26).
- **Break-even rate 0.5238** = 110/210 (arithmetic from a −110 price; not an NBA statistic).
- **Model lines, correlations, power values** — computed in-repo (`compute.py`), formulas in
  `methodology.md`; parameters (K_BLEND=20, HFA=2.5, DSR prior=25) are flagged model choices.

## Irregularities observed at source (for manual review)

1. `https://www.nba.com/games?date=2026-11-04` renders only calendar + counts without JS;
   the 14 individual games are not in the static HTML. → slate sourced from team-schedule
   pages; coverage 6/14 flagged (F-SLATE).
2. `https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json` returns HTTP 500.
3. `https://www.nba.com/standings?Section=margins` shows situational splits (3pts or less,
   score 100+, opponent .500+ …), **not** PF/PA margins despite the section name.
4. Player box-score pages render ~50 rows max; the remaining rows require the official
   DateFrom/DateTo filters (after which row counts matched the official "Rows" totals exactly).
5. `https://www.nba.com/celtics/schedule` (celtics.com custom layout) is JS-only — 38
   unstructured chunks, no readable table. Boston's Nov-4 game could not be sourced; flagged,
   not guessed.
6. Team schedule pages label all tip times "PDT" on nba.com; times are transcribed as listed,
   no timezone conversion inferred.
7. Some game IDs break the sequential pattern (e.g. 0022501228 for Dec 14 — NBA Cup games get
   separate ID ranges); IDs are transcribed exactly as rendered.

## Known scope limits (flagged on-site)

- Game logs cover the **top-2 2025-26 scorers** (Dončić, Edwards) = 125 player-games.
  Gilgeous-Alexander/Brown/Maxey are registered with official checksums (F-PLAYERS).
- 2026-27 team samples are 5–8 games (F-SMALL) — model shrinks to the 2025-26 prior.
- No odds/market data could be verified (F-MARKET); no prize-pool source (F-ODDS).
