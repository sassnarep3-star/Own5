# COORDINATION.md — Shared Task Board

This file is the single source of truth for who is working on what. **Read it before starting any work.
Claim a task here, commit + push the claim immediately, and never start a task another session has claimed.**

Repo: `sassnarep3-star/Own5` · Default branch: `main` · Site: https://sassnarep3-star.github.io/Own5/

## Rules of the board

1. **Claim before you work.** Write your session ID, ISO-8601 UTC timestamp, and the exact file scope
   (globs) you will touch. Commit and push that claim in its own commit before touching any other file.
2. **Non-overlapping scopes only.** Each session works on its own branch `session-<id>/<task>` (or a git
   worktree) and edits only the files inside its claimed scope.
3. **Shared files are integration-only.** `docs/index.html`, `docs/assets/nav.js`, `docs/data/*.json`
   (the site's aggregated data), and `README.md` are changed only by the final integration session, after
   all other tasks are done.
4. **Cross-scope change needed?** Log a request in the "Cross-scope requests" section instead of editing.
5. **Small, frequent commits.** Run `git pull --rebase` before every push.
6. **Merge conflicts:** stop, resolve without discarding the other session's work, and log what happened in
   the Activity log.
7. **Finish:** record sources used, verification performed, and any irregularities here; mark the task `done`.
8. **Stale claims:** a claim older than 60 minutes (or from a crashed session) with no commits may be taken
   over by another session. Note the handoff in the Activity log.
9. **`needs review`** means the item is published on the site's *Flagged for Review* page; it does not block
   anything.

### Status vocabulary
`unclaimed` · `in progress` · `needs review` · `done`

---

## Task board

| ID | Task | Status | Owner (session) | File scope | Last update (UTC) |
|----|------|--------|-----------------|------------|-------------------|
| T01 | Coordination board + repo scaffolding (dirs, ignore rules, session conventions) | done | `arena-f70496ec` | `COORDINATION.md`, `.gitignore`, `docs/.nojekyll` | 2026-11-02T21:10Z |
| T02 | Data source registry: official/primary sources, licence, access URL, what each is used for | in progress | `arena-f70496ec` | `DATA_SOURCES.md`, `data/raw/README.md` | 2026-11-02T21:10Z |
| T03 | Game-level data ingest + validation (games, closing lines, moneyline/spread/total) | unclaimed | — | `pipeline/ingest_games.py`, `data/processed/games_*.csv` | — |
| T04 | Player-level data ingest + validation (weekly player stats, per-game prop outcomes) | unclaimed | — | `pipeline/ingest_players.py`, `data/processed/players_*.csv` | — |
| T05 | Validation gates framework (data-integrity, no-lookahead, sample-size, ROB, luck) | unclaimed | — | `pipeline/gates.py`, `reports/gates.md` | — |
| T06 | Scoring engine: CLV, flat-stake ROI, Kelly, bootstrap CI, t-test, PSR/DSR | unclaimed | — | `pipeline/scoring.py` | — |
| T07 | Luck removal / skill-vs-luck decomposition (autocorrelation, persistence, permutation) | unclaimed | — | `pipeline/luck.py`, `reports/luck.md` | — |
| T08 | Single-bet strategies (spread/ML/total) + leaderboard output | unclaimed | — | `pipeline/strategies/single*.py`, `docs/data/single_bets.json` | — |
| T09 | Player-prop strategies + prop outcome dataset (rec/rush/pass yards, TD, receptions) | unclaimed | — | `pipeline/strategies/props*.py`, `docs/data/props.json` | — |
| T10 | Correlation matrix: same-game & cross-game leg correlations, parlays/SGP pricing | unclaimed | — | `pipeline/correlation.py`, `docs/data/correlation.json` | — |
| T11 | Parlay / prop-combo strategy evaluation (joint probability, hit-rate vs. pricing) | unclaimed | — | `pipeline/strategies/parlay*.py`, `docs/data/parlays.json` | — |
| T12 | Line-origination model (own fair lines vs. market, CLV back-test) | unclaimed | — | `pipeline/origination.py`, `docs/data/origination.json` | — |
| T13 | Site: layout, CSS, navigation, landing page | unclaimed | — | `docs/index.html`, `docs/assets/*` | — |
| T14 | Site: category subpages (single bets, props, parlays, correlation, origination, methodology) | unclaimed | — | `docs/*.html` (except index) | — |
| T15 | Site: Flagged for Review page (unverified values + irregularities, with source links) | unclaimed | — | `docs/flagged.html`, `reports/flagged.json` | — |
| T16 | Executive summary (Markdown + site page) | unclaimed | — | `reports/EXECUTIVE_SUMMARY.md`, `docs/executive-summary.html` | — |
| T17 | Link checker + build verification for the site | unclaimed | — | `pipeline/check_site.py` | — |
| T18 | Final integration: merge, re-verify combined data, build, publish Pages, open + merge PR | unclaimed | — | `README.md`, `docs/data/*.json`, `docs/assets/nav.js`, `reports/INTEGRATION.md` | — |

> Session IDs follow `arena-<8 hex>` for Arena agent sessions (this session: `arena-f70496ec`; its branch is
> `arena/f70496ec-own5`).
> Non-Arena sessions use `session-<id>` and branch `session-<id>/<task>`.

---

## Cross-scope requests

_(none yet)_

---

## Activity log

| When (UTC) | Session | What |
|-----------|---------|------|
| 2026-11-02T21:10Z | `arena-f70496ec` | Read repo (only `README.md`, 6 bytes, 1 commit). Created board. Confirmed GitHub Pages already enabled on `main` `/` → https://sassnarep3-star.github.io/Own5/ . Claimed T02. |

---

## Environment constraints discovered (important for every session)

The sandbox has **outbound network access only to** `github.com`, `codeload.github.com`, `api.github.com`,
`registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`. Consequences, measured on 2026-11-02:

* `github.com` release **asset downloads are blocked** (`release-assets.githubusercontent.com` is not
  reachable), and `raw.githubusercontent.com` / `media.githubusercontent.com` are **blocked**. So
  `nflreadpy` / `nfl_data_py` / `nflfastR` loaders **cannot** be used here.
* Workaround that *does* work: `git clone` of repositories that **commit their data files as blobs**
  (`github.com` + `codeload.github.com` are reachable), plus `gh api` for JSON metadata.
* For verification against sites that are not reachable from the sandbox (`pro-football-reference.com`,
  `nfl.com`, `espn.com`, `sportsbook` sites, …), use the agent **web-fetch** tool, which reaches the public
  internet through a different egress. Every number that appears on the site must be traced to a URL that
  was actually retrieved and read.

### Verified data endpoints (reachable from sandbox)

| Dataset | URL | Verified how |
|---------|-----|--------------|
| nfldata (games, closing_lines, sc_lines, initial_lines, win_totals, predictions) | `git clone https://github.com/nflverse/nfldata.git` | cloned; `data/*.csv` present, 21 files |
| Multi-book NFL line history, 2006→ | `git clone --filter=blob:none --sparse https://github.com/mrcaseb/nfl-data.git` then `data/nfl_lines_odds.csv.gz` (479,089 rows, markets: money_line/spread/total) | cloned and parsed |
| Weekly player stats per season | `https://github.com/nflverse/nfl_data_py` → `data/schedules/<year>.csv` (1999-2021) | tree listing verified |
| Availability + per-week player box scores (2015-2025) | `git clone --depth 1 --filter=blob:none --sparse https://github.com/hvpkod/NFL-Data.git` → `NFL-data-Players/<season>/<week>/{QB,RB,WR,TE,K}.csv` | cloned 2024/W1, 2025/W18 |
| Historical consensus spread lines | `sc_lines.csv` in nfldata | cloned |

All of the above are **third-party aggregations**; see `DATA_SOURCES.md` for how each is traced back to a
primary source and for the official-source cross-checks performed.
