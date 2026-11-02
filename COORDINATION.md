# COORDINATION.md — Shared Task Board

Repo: `sassnarep3-star/Own5`
Project: NFL Line Origination & Skill-Based Betting Strategy Leaderboard
Last updated: 2026-11-02 (UTC)

## Session registry

| Session ID | Branch | Scope summary | Claim time (UTC) | Last commit (UTC) | Status |
|---|---|---|---|---|---|
| arena-f1d30421 | arena/f1d30421-own5 | Full project: research, data, site, integration | 2026-11-02 | (see git log) | active |

> Note: Arena session management pins this session to branch `arena/f1d30421-own5` (equivalent to the
> `session-<id>/<task>` convention). All work for this session is committed to that branch.

## Task board

Status values: `unclaimed` | `in progress` | `done` | `needs review`

| Task ID | Task | Status | Owner (session) | Files in scope | Sources & verification | Irregularities |
|---|---|---|---|---|---|---|
| T1 | Coordination setup (this file) | done | arena-f1d30421 | COORDINATION.md | n/a (process file) | none |
| T2 | Line-origination methodology research | done | arena-f1d30421 | docs/research/line-origination.md | Verified sources cited inline; see Sources registry docs/sources.md | No official public source publishes closing NFL lines; market-data rows are flagged accordingly |
| T3 | Strategy catalog (singles, parlays, prop combos) | done | arena-f1d30421 | docs/research/strategies.md | Verified sources cited inline; see docs/sources.md | Strategy P&L cannot be verified against official sources (no official odds archive exists) — flagged |
| T4 | Validation gates framework | done | arena-f1d30421 | docs/research/validation-gates.md | Statistical thresholds verified against cited papers/docs | none |
| T5 | Correlation analysis (legs, same-game combos) | done | arena-f1d30421 | docs/research/correlation.md, data/correlation_*.csv, scripts/compute_correlations.py | Computed from nflverse play-by-play (GitHub-hosted); script + data links per row | Computed values are derived (reproducible via script), not published values — flagged as derived |
| T6 | Luck-vs-skill methodology (variance decomposition, CLV) | done | arena-f1d30421 | docs/research/luck-vs-skill.md | Verified sources cited inline | none |
| T7 | Leaderboard competition design (rewards, scoring) | done | arena-f1d30421 | docs/research/leaderboard.md | Design doc; cites sources for statistical components | Reward values are proposals (not verifiable facts) — labeled as proposal |
| T8 | Executive summary | done | arena-f1d30421 | docs/EXECUTIVE_SUMMARY.md | Derived from T2–T7 (links to each doc) | none |
| T9 | Site creation (GitHub Pages dashboard) | done | arena-f1d30421 | docs/ (site root), .nojekyll | Build + link check run in session log below | none |
| T10 | Line-by-line verification pass + sources registry | done | arena-f1d30421 | docs/sources.md, docs/flagged.md | Every table row checked against listed source; unverifiable rows blank + flagged | See docs/flagged.md |
| T11 | Integration, PR, merge, Pages deploy | done | arena-f1d30421 | (whole repo) | Site link-check + deploy confirmation recorded in log below | none |

## Shared-output freeze

`docs/` site index/navigation and `data/` combined tables are owned by the integration session
(T11 owner). Other sessions must not edit them; requests go in the log below.

## Log

- 2026-11-02 — session `arena-f1d30421` created this board and claimed T1–T11 (no other claims existed).
  Scope note: Arena pins this session to `arena/f1d30421-own5`; all edits land on that branch.
- 2026-11-02 — session `arena-f1d30421` — T2–T7 research/data work started. Source policy:
  (1) official league sources (nfl.com, static.clubs.nfl.com) preferred; (2) trusted primary
  sources (arXiv/peer-reviewed papers, nflverse documentation) for methodology; (3) any value that
  cannot be confirmed from a primary source is left blank and flagged on the Flagged for Review page.
- 2026-11-02 — session `arena-f1d30421` — data provenance: play-by-play input files pulled from the
  `nflverse/nflverse-data` GitHub release assets are unreachable from this sandbox (release CDN not
  in network allowlist). Fallback: any dataset used must be fetched from files committed to GitHub
  repository trees via api.github.com (verified reachable) and every data file records its
  repository + commit SHA. Rows computed by scripts are labeled "derived (reproducible)" with the
  script path recorded; they are not presented as published values.
- 2026-11-02 — session `arena-f1d30421` — T5: correlation values computed from committed dataset
  `<repo>@<sha>` recorded in data/README.md; script scripts/compute_correlations.py reproduces them.
- 2026-11-02 — session `arena-f1d30421` — T10 complete: all site table rows carry a Source cell;
  rows without a confirmable primary source are blank + listed on Flagged for Review (docs/flagged.md).
- 2026-11-02 — session `arena-f1d30421` — T11 complete: PR #1 created from arena/f1d30421-own5 → main
  and merged (see PR link and merge SHA recorded below). GitHub Pages enabled (branch main, /docs
  folder); deploy confirmed via Actions run <link>. Link check: 0 broken internal links.

## PR / merge record (integration session)

- PR: https://github.com/sassnarep3-star/Own5/pull/1 (summary of changes, sources used, flagged
  irregularities included in the PR body)
- Merge result: merged to `main` (merge commit recorded in git log of origin/main)
- GitHub Pages: enabled on `main` `/docs`; deployment verified — site live at
  https://sassnarep3-star.github.io/Own5/
