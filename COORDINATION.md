# COORDINATION.md — Shared Task Board

**Repo:** sassnarep3-star/Own5
**Purpose:** NFL line-generation & betting-strategy research project. Shared task board for all sessions.
**Last updated:** 2026-11-02 (UTC)

## Session registry

| Session ID | Branch | Status | Notes |
|---|---|---|---|
| arena-44bc1e2f | `arena/44bc1e2f-own5` | active | Platform-mandated branch (Arena session branch). Scope: full repo (sole session registered so far). Acts as data + integration session. |

> **Branch note:** Arena platform sessions are pinned to their own session branch; this session works on `arena/44bc1e2f-own5` (not `session-<id>/<task>`) per platform constraint. Any other session must register its own branch here before starting work.

## Task board

| ID | Task | Status | Owner | Files | Notes |
|---|---|---|---|---|---|
| T1 | Repo review & coordination setup | done | arena-44bc1e2f | COORDINATION.md, README.md | Repo reviewed at 426b19d: empty except README.md ("# Own5"). |
| T2 | Collect 2026 NFL standings (verified, per-row source) | in progress | arena-44bc1e2f | data/standings_2026.json | Source target: NFL.com standings. |
| T3 | Collect 2026 Week 1–7 final scores (verified) | unclaimed | arena-44bc1e2f | data/scores_2026.json | Will source from NFL.com / ESPN box scores. |
| T4 | Collect Week 8 schedule + available betting lines | unclaimed | arena-44bc1e2f | data/week8_lines_2026.json | Lines blank + flagged where no official source confirms. |
| T5 | Strategy research (signals, EV, CLV, correlation, gates) | unclaimed | arena-44bc1e2f | docs/strategies.md | Every claim must link to a source. |
| T6 | Quant analysis on verified data (remove-luck metrics) | unclaimed | arena-44bc1e2f | analysis/compute_metrics.py, analysis/metrics_output.json | Computed only from verified scores; script re-runnable. |
| T7 | Executive summary | unclaimed | arena-44bc1e2f | docs/executive_summary.md | |
| T8 | GitHub Pages site (landing + category subpages + tables) | unclaimed | arena-44bc1e2f | docs/ (site root) | Clean dashboard UI, all rows source-linked. |
| T9 | Flagged for Review page | unclaimed | arena-44bc1e2f | docs/flagged.html | Unverified items listed with reason + source attempts. |
| T10 | Link check / build verification | unclaimed | arena-44bc1e2f | tools/link_check.py | Internal links + external source URLs checked. |
| T11 | Integration, PR to main, merge, GitHub Pages deploy | unclaimed | arena-44bc1e2f | COORDINATION.md | Run only after T2–T10 done. |

Status values: `unclaimed` | `in progress` | `done` | `needs review` (needs review = published on Flagged for Review page, does not block).

## Change requests (log here instead of editing files owned by another session)

_(none yet)_

## Task log — sources, verification, irregularities

### T1 — Repo review (done)
- Reviewed at commit 426b19d. Files: README.md only (content: "# Own5").
- Irregularities: none (empty project scaffold). GitHub auth OK as `sassnarep3-star`.

_(Further entries appended as tasks complete.)_

## Integration record

| Item | Value |
|---|---|
| PR | _(pending)_ |
| Merge result | _(pending)_ |
| GitHub Pages | _(pending)_ |
| Build check | _(pending)_ |
