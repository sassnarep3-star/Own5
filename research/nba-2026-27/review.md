# Repository review — NBA-relevant artifacts (task S1, session 9cf7de11)

Review date 2026-11-03 (UTC). Scope: the NBA artifacts already in `main`. Flags only: no existing file was edited. Each finding is also recorded in `data/nba-2026-27/flags.csv` and shown on the Flagged for Review page.

| Artifact | Finding | Flag | Sources |
|---|---|---|---|
| `README.md` | Lists the NBA lab (`docs/`) and the NFL desks, but not `nba-2026-lab/` (text search: 0 matches). Adds the new desk as one row (this session). | F02 | [S12](https://github.com/sassnarep3-star/Own5/blob/main/README.md) |
| `research/nba/correlations.md` | Says the sandbox "has no network route to stats.nba.com". nba.com HTML pages load in this session (S01–S04, S08). The stats JSON API returned errors, so the note is partly outdated. | F03 | [S13](https://github.com/sassnarep3-star/Own5/blob/main/research/nba/correlations.md) |
| `research/nba/correlations.md`, `research/nba/strategies.md`, `docs/` | Cite nba-prop-bets.com, oddsindex.com and edgebetting.ai for correlation directions. None is an official source. Not re-used here. | F04 | [S13](https://github.com/sassnarep3-star/Own5/blob/main/research/nba/correlations.md) |
| `nba-2026-lab/`, `research/nba-2026/` | Built on the 2025-26 season (Edwards 2025-26 log only). The 2026-27 season is in progress. | F01 | [S04](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26), [S03](https://www.nba.com/stats/player/1630162/boxscores?Season=2026-27) |
| `nba-2026-lab/data/edwards_2025_26_recent10.csv` | All 10 rows match the official 2025-26 log cell by cell (result, points, threes, rebounds, assists, minutes, game ID). | F10 (verified) | [S04](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |
| `nba-2026-lab/compute.py` | Reproduces its published coefficients on its 10-row sample. The sample is small, so the values describe only that sample. | F10 (verified) | [S04](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |
| Official data pages | Minnesota has 8 official games, but Edwards appears in only 4 official 2026-27 rows. The cause is not stated in the sources and is not inferred. | F05 | [S02](https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular+Season), [S03](https://www.nba.com/stats/player/1630162/boxscores?Season=2026-27) |
| `COORDINATION.md` | The brief asks for `session-<id>/<task>` branch names. The platform requires the fixed branch `arena/9cf7de11-own5`, so tasks are IDs on that one branch. | F11 | [S14](https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md) |

## Not reviewed in detail

- `docs/` pages (session 9c3a0a69) were checked only for the third-party domains in the table above. Their numeric content was not re-verified.
- `analysis/prop_correlations.py` was not run.
- Injury-report PDFs (S06) were not parsed.
