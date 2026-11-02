# COORDINATION.md — Shared Task Board

Repo: `sassnarep3-star/Own5` — Project "Own5": originate and analyze our own NFL lines/strategies with verified official sources, published as a GitHub Pages dashboard.

Session ID for this session: `arena-09d847e1-own5` (branch `arena/09d847e1-own5`).

## Rules
- Claim a task by writing the session ID + file scope below, then commit & push the claim immediately.
- Never start a task another session has claimed (unless the claim is >60 min stale with no commits — then note the handoff here).
- Keep scopes non-overlapping. Cross-session file requests go in the "Requests" section, not in edits.
- Small, frequent commits. `git pull --rebase` before every push.
- Nothing is "verified" unless checked against an official source, with the link recorded.
- Shared outputs (table data, site index/nav) are only finalized by the integration session.

## Task Board

| ID | Task | Status | Owner session | Files touched |
|----|------|--------|---------------|---------------|
| T1 | Repo review (line-by-line, flag irregularities) | in progress | arena-09d847e1-own5 | README.md, COORDINATION.md, docs/repo-review.md |
| T2 | Verified 2025 final standings dataset | unclaimed | — | data/standings_2025.json |
| T3 | Verified 2025 regular-season scores (Weeks 1–18) | unclaimed | — | data/scores_2025.json |
| T4 | Verified 2026 Week 1 schedule + key dates | unclaimed | — | data/schedule_2026_w1.json |
| T5 | Verified 2025 player stats (passing/rushing/receiving leaders) | unclaimed | — | data/player_stats_2025.json |
| T6 | Official source registry | unclaimed | — | data/sources.json, docs/sources.md |
| T7 | Line-origination methodology (model spread/total from verified stats) | unclaimed | — | analysis/methodology.md, analysis/model_lines.json |
| T8 | Strategy definitions + validation gates + backtest on 2025 data | unclaimed | — | analysis/strategies.json, analysis/backtest_2025.json, analysis/validation_gates.md |
| T9 | Correlation analysis (skill vs luck: Pearson r, binomial significance) | unclaimed | — | analysis/correlations.json, analysis/correlation_report.md |
| T10 | Leaderboard (strategies ranked by backtest metrics) | unclaimed | — | analysis/leaderboard.json |
| T11 | Executive summary | unclaimed | — | EXECUTIVE_SUMMARY.md |
| T12 | GitHub Pages site (landing + category subpages, tables, dashboard UI) | unclaimed | — | index.html, pages/*.html, assets/*, scripts/build_site.py |
| T13 | Flagged-for-review page content | unclaimed | — | data/flagged.json, pages/flagged.html |
| T14 | Integration: merge, re-verify, PR to main, merge, Pages deploy, record results | unclaimed | — | COORDINATION.md, all shared outputs |

## Claims (this session claims all tasks — no other active sessions observed)

- `arena-09d847e1-own5` claims T1–T14 (single active session; scopes are its own files as listed above).

## Requests (cross-session file changes)

- None.

## Log

- 2026-11-02: COORDINATION.md created. Repo contains only `README.md` ("# Own5"). Session `arena-09d847e1-own5` claimed T1–T14.
