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
| T2 | Line-origination methodology research | done | arena-f1d30421 | research/line-origination.md | Methodology sources verified 2026-11-02 (links inline + Sources registry on site): nfl.com official pages, 2025 NFL Record & Fact Book (static.clubs.nfl.com), arXiv:1710.02824 | No official public source publishes market lines — flagged F1/F7 |
| T3 | Strategy catalog (singles, parlays, prop combos) | done | arena-f1d30421 | research/strategies.md | Backtests computed by scripts/compute_analysis.py from pinned dataset @1d309cb; literature cross-checks: Szalkowski et al. 2012, Paul & Weinbach (links in doc) | Modeled ROI assumes −110 (prices absent) — flagged F8 |
| T4 | Validation gates framework | done | arena-f1d30421 | research/validation-gates.md | Thresholds verified against cited papers: Bailey–Borwein–López de Prado–Zhu 2014 (Notices AMS), DSR 2014 (JPM, doi:10.3905/jpm.2014.40.5.094), PBO 2017, Thorp 2011 | none |
| T5 | Correlation analysis (legs, same-game combos) | done | arena-f1d30421 | research/correlation.md, data/correlation_bets.csv, data/correlation_parlays.csv, data/correlation_props.csv, scripts/compute_analysis.py, scripts/compute_prop_correlations.py | Computed from pinned datasets (spreadspoke @1d309cb; pbp @352c9c9); every CSV row carries dataset + script links; reproducible | Derived values (reproducible) — pbp era caveat flagged F2 |
| T6 | Luck-vs-skill methodology | done | arena-f1d30421 | research/luck-vs-skill.md, data/luck_skill.csv | Exact binomial + power analysis computed; thresholds cross-checked vs Szalkowski et al. (52.38%) | none |
| T7 | Leaderboard competition design (rewards, scoring) | done | arena-f1d30421 | research/leaderboard.md | Scoring components cite Bailey & López de Prado 2014, Thorp 2011 | Reward amounts are proposals; pool blank pending owner — flagged F9 |
| T8 | Executive summary | done | arena-f1d30421 | EXECUTIVE_SUMMARY.md | Restates only computed/verified values from T2–T7 (links inline) | none |
| T9 | Site creation (GitHub Pages dashboard) | done | arena-f1d30421 | docs/ (10 pages + assets), scripts/build_site.py | Site generated from verified CSVs (build script); spot-checks of rendered values vs CSVs passed | none |
| T10 | Line-by-line verification pass + sources registry | done | arena-f1d30421 | scripts/verify_site.py, docs/sources.html, docs/flagged.html, docs/flagged.md | verify_site.py: 10 pages, 50 external links; every table row has source link or explicit BLANK-flag; internal link check PASS | F1–F11 published on Flagged for Review page |
| T11 | Integration, PR, merge, Pages deploy | done | arena-f1d30421 | (whole repo) | Recorded in "PR / merge record" below | none |

## Shared-output freeze

`docs/` site index/navigation and `data/` combined tables are owned by the integration session
(T11 owner). Other sessions must not edit them; requests go in the log below.

## Task completion details (sources / verification / irregularities)

* **T2–T4, T6, T7 (research):** sources listed inline in each doc and on the site Sources page
  (official NFL pages; 2025 NFL Record & Fact Book; Bailey/Borwein/López de Prado/Zhu 2014 ×2;
  Thorp 2011; Kaunitz et al. 2017; Szalkowski et al. 2012; Paul & Weinbach). Verification: each URL
  re-fetched or searched during the session; bibliography recorded in docs/sources.html.
* **T5 (correlation):** computed values only. Inputs pinned: spreadspoke @ `1d309cb7f8f58a9eceb36293979dbcb1af70db94`,
  pbp mirror @ `352c9c9b0bce0ffa8ce85681cf9ed50c0398f462`. Verification: sign conventions tested
  statistically (favorite SU 65.6%, cover 48.1% excl. pushes); dataset scores spot-verified 16/16
  vs nfl.com 2025 Week 1 (data/verified_official_results.csv). Irregularities: F1–F6 (flagged page).
* **T8 (exec summary):** no new numbers — every figure traces to data/*.csv or research/*.md.
* **T9 (site):** built by scripts/build_site.py directly from data CSVs (no hand-copied numbers);
  rendered-value spot checks vs CSVs passed.
* **T10 (verification):** scripts/verify_site.py PASS — 10 pages; internal links resolve; every
  table row carries ≥1 source link or explicit BLANK-flag chip; no null values leaked; Sources
  registry contains both dataset pins + official pages + literature. Unverifiable values left blank
  and listed F1–F11 on the Flagged for Review page.

## Log

- 2026-11-02 — session `arena-f1d30421` created this board and claimed T1–T11 (no other claims existed).
  Scope note: Arena pins this session to `arena/f1d30421-own5`; all edits land on that branch.
- 2026-11-02 — source policy: (1) official league sources (nfl.com, static.clubs.nfl.com);
  (2) trusted primary sources (arXiv/peer-reviewed papers) for methodology; (3) any value that
  cannot be confirmed from a primary source is left blank and flagged on the Flagged for Review page.
- 2026-11-02 — data provenance: nflverse release assets unreachable from this sandbox (release CDN
  not in network allowlist); fallback = datasets committed to GitHub trees via api.github.com, every
  file recording repo + commit SHA. Computed rows labeled derived (reproducible), never presented as
  published values.
- 2026-11-02 — data integrity: dataset 2025 Week 1 scores matched official nfl.com game pages
  16/16 (e.g., [Ravens 40 @ Bills 41](https://www.nfl.com/games/ravens-at-bills-2025-reg-1));
  sign conventions validated statistically; ambiguous team-name row excluded (F3); mixed-type
  line field coerced, never imputed (F4).
- 2026-11-02 — T5 complete: correlation values computed (game-level phi ≈ 0.01; fav-cover vs fav-SU
  0.71; QB vs top-WR yards 0.76; cross-game pairs ratio 0.984, n=9,479) — CSVs + scripts committed.
- 2026-11-02 — T2 complete: originated model lines for all 15 games of 2026 Week 9 from official
  standings + schedule + derived HFA (2.22 → 2.0); market columns blank + flagged (F7).
- 2026-11-02 — T10 complete: site link-check PASS (10 pages / 50 external links); all table rows
  sourced or explicitly flagged; F1–F11 published.
- 2026-11-02 — T11 complete: PR created from arena/f1d30421-own5 → main and merged; GitHub Pages
  enabled (main, /docs); deploy verified — links recorded below.

## PR / merge record (integration session)

- PR: https://github.com/sassnarep3-star/Own5/pull/1 (summary of changes, sources used, flagged
  irregularities in PR body)
- Merge result: merged to `main` (merge commit in origin/main git log)
- GitHub Pages: enabled on `main`, folder `/docs`; deployment verified live at
  https://sassnarep3-star.github.io/Own5/
- Follow-up record PR: https://github.com/sassnarep3-star/Own5/pull/2 (this file's post-merge record)
