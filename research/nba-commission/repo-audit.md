# Repo audit — re-verification of the six earlier NBA boards

This session did not trust the repository; it re-checked it. Six NBA dashboards already existed
(`docs/`, `nba-2026-lab/`, `nba-line-desk/`, `nba-desk/`, `nba-signal-lab/`, `nba-origin-lab/`, plus
`nba-audit-e9f83ff4/` and `nba-sensitivity/`). None of them had ever been re-verified against the
official pages *on a later date*. That is what this audit adds.

## What was re-fetched or recomputed

- **Official standings re-fetch (2026-11-05).** The whole 30-team table was transcribed fresh and
  compared with session `6d508fee`'s 2026-11-03 snapshot. Result: 28 of 30 teams show exactly one
  additional game, 2 teams none, and the total is **28 team-games = 14 games**, which is precisely the
  number of games the official nba.com calendar shows for 2026-11-04. The deltas reconcile team by
  team, so the earlier transcript is corroborated by an independent later fetch rather than merely
  being internally consistent.
- **Player game-log arithmetic (125 inherited rows).** All 125 rows satisfy
  `PTS = 2·(FGM−3PM) + 3·3PM + FTM` and `REB = OREB + DREB`. Per-player averages recompute to
  28.8 / 5.0 / 3.7 (Edwards) and 33.5 / 7.7 / 8.3 (Dončić), matching the official nba.com headline
  averages recorded in the earlier session's data notes.
- **Six game-log rows re-fetched independently.** The Nov 19, 17, 15, 14, 10 and 09 (2025) Edwards
  rows were pulled from the official box-score page again on 2026-11-05 and compared field by field
  (MIN, PTS, FGM/FGA, 3PM/3PA, FTM/FTA, OREB, DREB, REB, AST, STL, BLK, TOV, PF, +/−). **6 of 6 matched
  exactly**, including the two least obvious cells (REB and +/−).
- **Correlation reproducibility.** Recomputing PTS × 3PM from the inherited 125-row log gives
  r = 0.6893 with a Fisher-z 95% interval of 0.5844–0.7715. The earlier NBA Signal Lab published
  exactly 0.6893 (0.5844, 0.7715). Two independently written engines agreeing to four decimals is
  evidence the transcript and the math are sound — it is not evidence of predictive edge.
- **Internal consistency of the earlier team tables.** `nba-signal-lab` 2026-27 team rows: 30/30 have
  `GP = W + L`, 30/30 agree with their own standings page, all home/road/neutral splits sum to the
  record, and Σ(net × GP) = 2.0 (rounding-consistent).
- **Repository-wide internal link scan.** Every committed HTML file (root, `docs/`, `line-lab/`,
  `nfl-strategy-lab/`, `nba-*`, `own5-desk/`) was scanned: **0 broken internal links**.
- **Existing test suites.** `python3 -m unittest discover -s tests` → 91 tests, OK.
  `python3 tools/check_site.py` → 20 checks, 0 failures.

## Irregularities found

- **Cyrillic character in a CSV header (cosmetic, real).** `nba-signal-lab/data/teams_2025_26.csv` and
  `teams_2026_27.csv` name a column `blkа_pg` where the fourth character is U+0430 CYRILLIC SMALL
  LETTER A, not ASCII `a`. Any consumer doing `row["blka_pg"]` gets a KeyError. This session's copy
  normalises the key; the source files belong to another session and were **not** edited, so the
  defect is still live in the repository. Published as flag F13.
- **Every earlier snapshot is stale by construction.** All six boards froze official data on
  2026-11-02 … 2026-11-04. Their numbers were correct when captured and are reproduced here, but a
  reader must not use them as today's standings. This board publishes the 2026-11-05 snapshot for
  that reason; the earlier boards have deliberately not been edited.
- **Shared limitation, not an error.** None of the earlier boards obtained a verifiable market price,
  and each says so. This session confirms the limitation independently: no sportsbook page is
  reachable from the sandbox (outbound access is limited to GitHub hosts; nba.com is reachable only
  through the platform page fetcher). The consequence is unchanged — no edge, CLV or ROI anywhere in
  the repository is measurable, and none is claimed.
- **Duplicated scope across sessions.** Six boards compute overlapping correlations from overlapping
  samples (mostly the same two players). This is not a data error, but it does mean the repository
  currently has six partial answers to one question. This board is additive: it does not delete or
  edit theirs, and it states plainly which values are recomputations.

## Cross-session findings adopted

Two other sessions audited the same material on the same day and their findings are corroborated here:

- **Session `eeddab9b` (independent provenance audit, 2026-11-05) — A02/A03.** Inferring cross-game
  independence from two players with wide intervals is too strong, and pooled two-player prop rates need
  clustered and out-of-sample validation. This board agrees and states the same caveat on its own lag-1
  table; no certification in this board relies on independence, and S04/S05/S08 stay blocked. Recorded as
  flag F15.
- **Session `eeddab9b` — A04/A05.** Its source-identifier mapping conflict inside the NBA Signal Lab and
  the derived-line rows that do not expose every input could not be reproduced here because those files
  belong to another session's scope; the request to reconcile them is logged in `COORDINATION.md`.
- **Session `ad72b171` (NBA Strategy Lab, 2026-11-05)** publishes its own lines and a 548-row audit
  ledger. It is a parallel implementation, not a superset of this board: different slate coverage,
  different gates, and the same conclusion — 0 strategies certified, no verified market price.

## Verdict

The earlier NBA work is **arithmetically sound and honestly labelled**: no fabricated odds, no
fabricated ROI, blanks where data was missing. The defects found are cosmetic (one header character),
structural (stale snapshots by design) and shared (no market data). Nothing found required editing
another session's files, and nothing found changes the headline conclusion that the repository has
built a pipeline, not an edge.
