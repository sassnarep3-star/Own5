# Own5 — Raw-data integrity audit (session 68bfa568)

**Branch:** `arena/68bfa568-own5` (from `main` @ `92d5017`). **Scope:** read-only checks of the repo's existing raw data and CI state. No new official NFL values were captured.

## Executive summary

1. **The local raw data is intact.** All 12 nflverse files in `data/decision-desk/raw/` match the SHA-256 hashes recorded in `provenance.json` ([hash_check.csv](hash_check.csv)).
2. **The "7,548 games / 7,439 priced / 163 of 272 in 2026" claim is correct** when recomputed from `games.csv.gz` ([claim_check.csv](claim_check.csv)). The price field is a third-party aggregated line from nflverse, not an official NFL or sportsbook feed, and the file does not separate opening from closing numbers. Any desk that calls these "official" prices is wrong.
3. **Three official nfl.com captures cannot be re-verified.** Their hashes are recorded, but the saved HTML was never committed, only text extracts. Flagged.
4. **The root site is stale.** `index.html` on `main` still shows the 2026-11-02 state.
5. **CI on `main` has two failing workflows** (see [ci_state.csv](ci_state.csv)):
   - "NFL portfolio integration" (run 43997969907): fails at `pages-smoke` — "Confirm the root and integration hub are published on GitHub Pages".
   - "Verify NFL B34 Week 10 research desk" (run 43998367488): fails at "Check deterministic generated outputs".
6. **Live access limits:** from this sandbox, `www.nfl.com` and `sassnarep3-star.github.io` do not respond (curl returns no HTTP status). Any value that needs a live official read is therefore unverified in this session.

## What this session did not do

This brief asks for ~60 items. Most need live nfl.com reads (injury reports, depth charts, game books, transactions, reserve list, game centre venues), a pre-registration freeze, a backtest corpus, and a published site. None were done here. The brief also asks for per-session branches named `session-<id>/<task>`, which conflicts with this session's fixed branch, so work stays on `arena/68bfa568-own5`. Nothing was merged to `main`, because the brief's merge condition ("all tasks done, integration verified") is not met.

## Flagged for review

| ID | Item | Evidence |
|----|------|----------|
| A-F1 | nfl.com HTML captures not committed; hashes unverifiable | `provenance.json` `pages[]`; `hash_check.csv` rows 13–15 |
| A-F2 | Line fields in `games.csv.gz` are third-party, open/close not separable | `claim_check.csv` row 2 |
| A-F3 | `NFL portfolio integration` failing on `main` (`pages-smoke`) | run 43997969907 |
| A-F4 | `Verify NFL B34 Week 10 research desk` failing on `main` (determinism check) | run 43998367488 |
| A-F5 | Root `index.html` shows 2026-11-02 dates | `claim_check.csv` row 5 |
| A-F6 | "24 sibling desks" count not reproduced (25 NFL/own5 dirs) | `claim_check.csv` row 6 |

## Sources (for manual review)

- nflverse schedules (games): https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz
- nflverse player stats: https://github.com/nflverse/nflverse-data/releases/tag/stats_player
- nflverse injuries: https://github.com/nflverse/nflverse-data/releases/tag/injuries
- nflverse snap counts: https://github.com/nflverse/nflverse-data/releases/tag/snap_counts
- Official NFL pages referenced in provenance (unverifiable from sandbox): https://www.nfl.com/injuries/ · https://www.nfl.com/schedules/2026/by-week/week-10 · https://www.nfl.com/standings/league/2026/REG
- GitHub Actions runs: https://github.com/sassnarep3-star/Own5/actions/runs/43997969907 · https://github.com/sassnarep3-star/Own5/actions/runs/43998367488
