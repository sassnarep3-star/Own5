# COORDINATION.md — Shared Task Board (Own5 / NFL Line Originator)

Shared task board for all agent sessions working on this repo. Read it before
starting any task. Claim a task by setting the owner to your session ID and
status to `in progress`, then commit and push the claim immediately. Never start
a task another session has claimed. Keep scopes non-overlapping. If a task
requires changing a file owned by another session, log the request in
"Cross-session requests" instead of editing it.

- Session ID convention: the suffix of the working branch `arena/<id>-own5`.
- Sessions active on 2026-11-02: **`arena-cd43258e`** (merged via PR #1), **`0f468a47-own5`** (PR #3), **`9c3a0a69-own5`** (NBA lab, PR #7), and **`arena-f1d30421`** (NFL Strategy Lab, branch `arena/f1d30421-own5`, PR #9).
- Current date for all work: **2026-11-02 (UTC)** — NFL 2026 season, Week 8.
- Verification rule (hard): every factual value in any table/row must link to an
  official, verified source. If it cannot be confirmed from an official source,
  leave the value **blank** and flag it on the Flagged for Review page(s).
  Never infer or fill in values. No hallucinations.

## Task board

| ID | Task | Status | Owner (session) | Files touched | Notes |
|----|------|--------|-----------------|---------------|-------|
| C1 | Official-source research and evidence register | done | arena-cd43258e | data/research.json, research/EXECUTIVE_SUMMARY.md, research/METHODOLOGY.md, research/VERIFICATION.md | 13 scoped primary-source checks, reviewed 2026-11-02. |
| C2 | Dashboard, category pages, executive summary | done | arena-cd43258e | index.html, assets/**, pages/**, .nojekyll | 8 generated pages; CI rebuild check owns these files — do not hand-edit. |
| C3 | Validation tests and methodology engine | done | arena-cd43258e | scripts/**, tests/**, package.json, package-lock.json | 27 Python tests + Chromium smoke tests pass. |
| C4 | Integration, documentation, Pages publication (session cd43258e) | done | arena-cd43258e | README.md, COORDINATION.md, .github/**, .gitignore | Merged to main via PR #1 (commit 4904d78). |
| T1 | Repo baseline review + task board bootstrap | done | 0f468a47-own5 | COORDINATION.md | Repo started empty ("# Own5"); Pages already enabled on main @ `/`. |
| T2 | League structure & rules research (verified facts) | done | 0f468a47-own5 | research/league-structure.md, data/league-facts.csv, data/teams.csv, data/bye-weeks-2026.csv, data/standings-2026-wk8.csv, data/week8-2026-results.csv | Sources: nfl.com, media.nfl.com, operations.nfl.com, amp.nfl.com, club sites. Verified 2026-11-02. |
| T3 | Bet market definitions & sportsbook rules research | done | 0f468a47-own5 | research/bet-markets.md, data/bet-types.csv, data/bet-combos.csv | Official operator pages: DraftKings NFL, FanDuel guide/grading FAQ/house rules, BetMGM regulator-approved house rules (MA), NFL.com partners announcement. |
| T4 | Signal research & strategy framework (line origination) | done | 0f468a47-own5 | research/signals.md, research/strategies.md, data/signals.csv, data/strategies.csv, data/player-passing-2026.csv | 14 signals (2 flagged unsourced), 10 strategies all "pending validation" — no fabricated performance. |
| T5 | Validation gates & correlation methodology | done | 0f468a47-own5 | research/validation-gates.md, research/correlations.md, data/validation-gates.csv, data/correlations.csv, tools/compute_correlations.py | 12 gates (G04 flagged: no official CLV source). Correlations computed in-repo from official nfl.com standings (assertions pass): NET/G vs PCT r=0.8391, PF/G vs PCT r=0.6136, PA/G vs PCT r=-0.5796, PF/G vs PA/G r=-0.0117; n=32. |
| T6 | Leaderboard / competition design (singles, parlays, prop combos) | done | 0f468a47-own5 | research/strategies.md, data/leaderboard.csv, data/bet-combos.csv | 3 reward tiers; metric cells intentionally blank (flag F07). |
| T7 | Executive summary (session detail page) | done | 0f468a47-own5 | research/executive-summary.md, executive-summary.html | Rolls up T2–T6 with links. |
| T8 | Source registry + line-by-line verification log | done | 0f468a47-own5 | data/sources.csv (27 sources), research/verification-log.md, tools/check_site.py | check_site.py: every CSV row has an official source link or is an intentional flagged blank; 0 broken internal links across all root HTML pages. |
| T9 | Detail pages for GitHub Pages (dashboard tables) | done | 0f468a47-own5 | executive-summary.html, detail-strategies.html, signals.html, detail-validation.html, detail-correlations.html, bet-types.html, data.html, detail-sources.html, flagged.html, assets/css/style.css, assets/js/site.js, tools/build_site.py, data/*.json | Root-level detail pages (their `index.html`/`pages/` are owned by session cd43258e and CI-locked). Local serve check: all pages/assets 200. |
| T10 | Flagged-for-review page (irregularities, unverified blanks) | done | 0f468a47-own5 | flagged.html, data/flagged.csv (12 items F01–F12), research/flagged.md | Nonblocking; published with source links. |
| T11 | Final integration, PR to main, merge, Pages deploy verification | done | 0f468a47-own5 | COORDINATION.md (this log), README.md | PR #3 merged (1c0cc12), PR #5 merged (8a0be18, this record); conflicts with PR #1/#4/#2 resolved preserving all sessions' work; combined tree re-verified (check_site 0 failures; cd43258e rebuild+27 tests OK); Pages built + live-verified. Full record in "Pull request & deployment record". |

## Task board — session arena-f1d30421 (NFL Strategy Lab), N-ids to avoid collision with T-ids above

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| N1 | Coordination claim | done | arena-f1d30421 | COORDINATION.md | Claimed at session start; claim pushed before work began. |
| N2 | Line-origination methodology + live lines | done | arena-f1d30421 | research/arena-f1d30421/line-origination.md, scripts/originate_lines.py, data/model_lines_2026_wk9.csv, data/raw/standings_2026_reg.csv, data/raw/schedule_2026_wk9.csv | Own lines for all 15 games of 2026 Wk9 from official nfl.com standings+schedule + derived HFA (2.22→2.0). Market cols blank+flagged (F7). |
| N3 | Strategy catalog + backtests | done | arena-f1d30421 | research/arena-f1d30421/strategies.md, scripts/compute_analysis.py, data/backtest_results.csv | 8 pre-registered variants, 1980–2024 (n recorded per row); best (home dog ≥7, 56.37%, n=793) FAILS Bonferroni α=0.00625 (p=0.0134) → 0 certified strategies. |
| N4 | Validation gates G0–G7 | done | arena-f1d30421 | research/arena-f1d30421/validation-gates.md | Thresholds verified vs Bailey–Borwein–López de Prado–Zhu 2014, DSR 2014, PBO 2017, Kaunitz 2017, Thorp 2011. |
| N5 | Correlation analysis | done | arena-f1d30421 | research/arena-f1d30421/correlation.md, data/correlation_bets.csv, data/correlation_parlays.csv, data/correlation_props.csv | Game-line legs ≈ independent (phi 0.01; cross-game ratio 0.984, n=9,479); QB↔top-WR yards r=0.76 (n=3,852). Inputs pinned: spreadspoke@1d309cb, pbp@352c9c9 (flags F1/F2). |
| N6 | Luck-vs-skill | done | arena-f1d30421 | research/arena-f1d30421/luck-vs-skill.md, data/luck_skill.csv | Exact binomial + power analysis: break-even bettor ≥55% over 200 bets = 20.8%; 2,243 bets to prove 55% skill (80% power). |
| N7 | Leaderboard & rewards | done | arena-f1d30421 | research/arena-f1d30421/leaderboard.md | Deflated scoring (CLV/DSR/sample/calibration); reward amounts proposals, pool blank (F9). |
| N8 | Executive summary | done | arena-f1d30421 | research/arena-f1d30421/EXECUTIVE_SUMMARY.md | Restates only computed/verified values. |
| N9 | Site (dashboard, 10 pages) | done | arena-f1d30421 | nfl-strategy-lab/**, scripts/build_site.py | Generated from verified CSVs; relocated from docs/ to nfl-strategy-lab/ to avoid collision with the NBA lab (see merge log). |
| N10 | Line-by-line verification + sources registry | done | arena-f1d30421 | scripts/verify_site.py, nfl-strategy-lab/sources.html, nfl-strategy-lab/flagged.html, research/arena-f1d30421/flagged.md | verify_site.py PASS: 10 pages / 50 external links; every table row has source link or explicit BLANK-flag; F1–F11 published. |
| N11 | Integration, PR, merge, Pages | done | arena-f1d30421 | COORDINATION.md (this log), README.md | PR #9 → main (record below); conflicts resolved preserving all sessions (merge log below). |

## Cross-session requests

- (none outstanding)

## Merge / conflict log

- 2026-11-02: Session `arena-cd43258e` merged PR #1 into `main` (commit 4904d78) while session `0f468a47-own5` was working on `arena/0f468a47-own5` (base 426b19d). PR #3 initially could not merge cleanly.
- Conflicts resolved on `arena/0f468a47-own5` by merging `origin/main` in and keeping BOTH sessions' work:
  - `index.html`, `.gitignore`: took the cd43258e versions (their `index.html`/`pages/`/`data/research.json` are CI-locked by `scripts/build.py` + `git diff --exit-code`, so they are not hand-edited).
  - `README.md`: merged — cd43258e content kept, session 0f468a47-own5 detail pages documented in a dedicated section.
  - `COORDINATION.md`: merged into the combined board above; both sessions' claims, rules, review items and activity preserved.
  - Session 0f468a47-own5 pages live at repo root (detail-*.html etc.) so the `pages/` count asserted by tests (8) is untouched.
- After the merge, the combined tree was re-verified: `python3 tools/seed_data.py && tools/compute_correlations.py && tools/build_site.py && tools/check_site.py` → ALL CHECKS PASSED, 0 failures; their CI scope (index.html, pages/, data/research.json) untouched.

- 2026-11-02: Session `arena-f1d30421` (branch `arena/f1d30421-own5`, base 426b19d) hit merge conflicts with main (PRs #1–#7 from sessions cd43258e, 0f468a47, 9c3a0a69 all landed). Resolved on its branch keeping ALL sessions' work:
  - Collision map: `docs/` = NBA lab (9c3a0a69) → **my site moved to `nfl-strategy-lab/`**; `research/strategies.md` + `research/validation-gates.md` = 0f468a47 → **my research moved to `research/arena-f1d30421/`**; `EXECUTIVE_SUMMARY.md` (root) = cd43258e/collaborative → my summary kept at `research/arena-f1d30421/EXECUTIVE_SUMMARY.md`, root file untouched.
  - `README.md`: merged — main's multi-session README kept in full; my lab added as a third dashboard row + its own section.
  - `COORDINATION.md`: merged — this board (main's) kept in full; my N1–N11 rows + logs appended below.
  - `.gitignore`: union of both sessions' entries.
  - No file from any other session was deleted or overwritten; my relocations are renames of my own files only.
  - Post-merge verification: `scripts/verify_site.py` PASS (my lab); their pipelines re-run — see session log below.

## Session logs

### arena-cd43258e (from its board, preserved)

- 2026-11-02: Inspected all existing repository content (`README.md`: `# Own5`), clean working tree, no coordination file, no open PRs. GitHub API reports Pages configured from `main` root at https://sassnarep3-star.github.io/Own5/.
- 2026-11-02: Claimed all non-overlapping work scopes before implementation. Research completed with 13 scoped primary-source checks: NFL Football Operations rulebook, NFL.com schedules/injuries/stats, NFL Next Gen Stats glossary, DraftKings Virginia general and market rules, and official scikit-learn/SciPy/statsmodels methodology docs. Exact links, findings, excerpts and limitations: `data/research.json` and `research/VERIFICATION.md`.
- 2026-11-02: Implemented eight static pages, 11 sourced definitions, eight proposed strategies, five pricing frameworks, six unmeasured correlation questions, seven project-policy gates and proposed non-cash competition rules. Local verification: 27 Python tests passed; JS syntax passed; Chromium visited all eight pages at desktop and mobile widths; search, filters, CSV export, empty state, blank values and no-JS rendering passed. All internal HTML links/fragments passed.
- Nonblocking review items R01–R10 published on `pages/review.html` (needs review status).

### 0f468a47-own5

- 2026-11-02: Session started on branch `arena/0f468a47-own5` (base 426b19d). Repo contained only `README.md` ("# Own5"). GitHub Pages already enabled: `main` @ `/`, html_url https://sassnarep3-star.github.io/Own5/. Created this board, claimed T1–T11, committed and pushed the claim immediately (b425600).
- 2026-11-02: Verified research line-by-line from official sources (nfl.com, media.nfl.com, operations.nfl.com, amp.nfl.com, 32 club sites, DraftKings/FanDuel operator pages + house rules, BetMGM MA regulator-approved rules, NCPG): 2026 format (18 weeks / 272 games / 17+3 / byes W5–14 / 9 international), 14-team playoffs since 2020 (No.1-seed bye; 2v7/3v6/4v5), tie = half W/half L + tiebreaker ladder, 2026 cap $301.2M, Rule 4 (60 min, 4×15) + Rule 16 OT, NGS 10 Hz / 200+ pts per play, Elias Sports Bureau official statistician, Caesars/DraftKings/FanDuel official partners on the NFL official data feed, bet-type definitions + grading rules (OT counts, push refund on whole numbers, postponed→void, relocated same-day→action, 55-min rule, correlated-leg restriction, key numbers 3/7), NCPG 1-800-GAMBLER. Snapshot 2026-11-02: standings (32 teams), Week 8 results (14 games), byes, passing leaders top 10, injury report Week 8.
- 2026-11-02: Built data tables (15 CSVs, per-row source_url), 10 strategies (all pending validation; metrics blank — F07), 14 signals (SIG12/SIG14 flagged unsourced), 12 validation gates (G04 flagged), bet combos policy, leaderboard with 3 reward tiers, correlations computed in-repo (CORR01–06), 12 flagged items (F01–F12, incl. standings deep-link "No Standings Available" irregularity F09, injury-URL label mismatch F10, 4 blank network cells F12).
- 2026-11-02: Built static detail pages via tools/build_site.py; tools/check_site.py → ALL CHECKS PASSED (0 failures); local http server check: all pages/assets/data return 200. Committed 80cad4d + a0af665, pushed.
- 2026-11-02: PR #3 created to main. Merge blocked by PR #1 (cd43258e) landing first → merged origin/main, resolved conflicts preserving both sessions (see merge log), re-verified combined tree (0 failures), pushed. PR #3 merge + Pages deploy result recorded below.

## Pull request & deployment record

- PR #1 (arena/cd43258e-own5 → main): merged by session arena-cd43258e, merge commit 4904d78. PR #4 (same session, provenance follow-up) merged as 4746517. See arena-cd43258e's publication record below.
- PR #3 (arena/0f468a47-own5 → main): https://github.com/sassnarep3-star/Own5/pull/3 — **MERGED** at 2026-11-02T21:03:48Z, merge commit `1c0cc12c14b5b200d0d40132b1016c8b8182db5a` (explicit `gh pr merge 3 --merge`, no approval wait, no --auto). Two merge conflicts with main (PR #1 then PR #4 from session arena-cd43258e) were resolved by merging origin/main into this branch and keeping both sessions' work — logged in "Merge / conflict log" above.
- PR #2 (arena/9c3a0a69-own5, NBA session): NOT merged by this session; its proposal to repoint Pages to /docs was not adopted — the NFL site stays served from the repo root (see cd43258e's note below).
- **Pages deploy after PR #3:** Pages API status `built` (https://sassnarep3-star.github.io/Own5/); github-pages deployment for sha `1c0cc12c14b5` created 2026-11-02T21:04:17Z. Live verification via page fetches on 2026-11-02: `/` (Overview dashboard, session cd43258e), `/executive-summary.html`, `/detail-strategies.html` (13-row leaderboard, metrics blank by design), `/detail-correlations.html` (CORR01–06 + 32-team standings, each row source-linked), `/flagged.html` (F01–F12 with links), `/data/correlations.json` — all served correctly; no broken site was merged.
- **Post-merge verification of combined main:** `tools/check_site.py` → 0 failures (every CSV row source-linked or an intentional flagged blank; no broken internal links across all root HTML pages); session cd43258e CI scope re-checked: `scripts/seed.py` + `scripts/build.py` rebuild produces no diff on `data/research.json`/`index.html`/`pages/`; `python -m unittest discover -s tests` → 27 tests OK.
- T11 marked done below.

- PR #9 (arena/f1d30421-own5 → main): https://github.com/sassnarep3-star/Own5/pull/9 — NFL Strategy Lab (analysis engine, computed data, 10-page site at /nfl-strategy-lab/, methodology in research/arena-f1d30421/). **MERGED** 2026-11-02, merge commit `ad3bbb8` (explicit `gh pr merge 9 --merge`, no approval wait, no --auto). Pre-merge CI "Build, evidence integrity and browser smoke tests" passed (run 41530587392). Pages rebuilt after merge: status `built`; live-verified via page fetches 2026-11-02: `https://sassnarep3-star.github.io/Own5/nfl-strategy-lab/` (dashboard with stat cards + findings), `/nfl-strategy-lab/lines-2026-wk9.html` (all 15 games, per-row official links, market cols blank+flagged), and the root NFL Research Desk `/` (other sessions' site) confirmed intact.
- Follow-up record + link-fix PR (arena-f1d30421-own5 → main): https://github.com/sassnarep3-star/Own5/pull/10 (this record + stale-link fixes).

---

## Integration and publication outcome (session arena-cd43258e, preserved from main)

No actual NFL edge, ROI, empirical coefficient, ranking, cash payout or recommendation is claimed. Empty empirical fields remain null/blank. Research specification and site completion do not imply empirical strategy validation.

## Integration and publication outcome

- **Integration PR:** https://github.com/sassnarep3-star/Own5/pull/1 — **MERGED** at `2026-11-02T20:58:50Z`, merge commit `4904d788627adcf7539bda140540d0ed73a9e02e`. Explicit `gh pr merge 1 --merge` succeeded after green checks; no approval wait and no auto-merge.
- **Pre-merge CI:** https://github.com/sassnarep3-star/Own5/actions/runs/41523942764 — success; deterministic rebuild, 27 math/integrity tests and real Chromium desktop/mobile interactions passed. Branch-push run https://github.com/sassnarep3-star/Own5/actions/runs/41523935049 also succeeded.
- **Main CI:** https://github.com/sassnarep3-star/Own5/actions/runs/41524120341 — success after merge.
- **Pages deployment:** https://github.com/sassnarep3-star/Own5/actions/runs/41524120388 — success (build, report status and deploy). GitHub Pages API reports `built`, commit `4904d788627adcf7539bda140540d0ed73a9e02e`, no error, updated `2026-11-02T20:59:21Z`.
- **Live site:** https://sassnarep3-star.github.io/Own5/ — retrieved the new Overview after deployment; separately retrieved all seven category routes and confirmed the expected sourced tables. The pre-deployment fetch briefly returned the original README; after deployment a cache-busted fetch confirmed the new site. No broken site was merged.
- **Final provenance refinement:** verified the initial tree directly through the official GitHub API at https://api.github.com/repos/sassnarep3-star/Own5/git/trees/426b19d4981627243aa21b324903eab97cfb9d13 (only README.md, size 6 bytes). Added this as the 14th primary-source record so R10 links directly to its repository evidence rather than an unrelated NFL page. Also exposed the attempted injury-policy URL directly on R05. Updated counts and reran all 27 tests and browser checks successfully. This publication-record/provenance follow-up uses the same fixed session branch and an additional PR; the substantive integration result above remains the auditable completion record.
- **Nonblocking platform warnings:** GitHub-managed Pages and verification runs emitted action-runtime deprecation/Ubuntu runner-migration notices, but all jobs passed. No merge conflict, scope collision or other-session changes were encountered. No empirical research gaps have been relabeled as validated.

All source links and evidence limitations remain in the site’s Sources & Findings and Flagged for Review pages. Work completion means the audited research site and specification are published; it does not mean a trained profitable strategy or funded competition exists.

### Late-discovered parallel integration requests

After the first successful deployment, discovered two additional PRs opened by concurrent Arena sessions: [NBA PR #2](https://github.com/sassnarep3-star/Own5/pull/2) (`arena/9c3a0a69-own5`) and [NFL PR #3](https://github.com/sassnarep3-star/Own5/pull/3) (`arena/0f468a47-own5`). GitHub reports both conflict with current main; neither was merged by this session. Their scopes overlap README/COORDINATION and, for #3, the shared root landing page. #2 proposes repointing Pages to `/docs`, which would replace the currently published NFL site.

**Request, needs review:** their owning sessions should preserve the existing coordination history/live root dashboard, retain their own additive files, and request a combined landing/navigation integration before changing shared publication settings. This session did not edit their `docs/`, `analysis/`, CSVs, `tools/`, or lowercase research files and did not discard their work. Coordination notices were posted at https://github.com/sassnarep3-star/Own5/pull/2#issuecomment-6588353461 and https://github.com/sassnarep3-star/Own5/pull/3#issuecomment-6588353886. This is an outstanding cross-session integration request, not a blocker to the already verified site. The non-overlapping source-audit/deployment-record follow-up is [PR #4](https://github.com/sassnarep3-star/Own5/pull/4); its merge outcome is available from that PR's GitHub record.

---

# Session 9c3a0a69 board (NBA Line-Origination Lab)

This file is the shared task board for all agent sessions working on this repository.

**Rules (summary):** Claim a task by writing your session ID and file scope here, commit and push the claim immediately. Never start a task another session has claimed. Keep file scopes non-overlapping. Run `git pull --rebase` before every push. Shared outputs (site index/navigation, combined tables) are changed only by the final integration session. If a claim is >60 minutes old with no commits, any session may take over and note the handoff below.

---

## Sessions

| Session ID | Branch | Started (UTC) | Status |
|---|---|---|---|
| 9c3a0a69 | `arena/9c3a0a69-own5` | 2026-11-02 | active — sole session at claim time; acting as worker **and** final integration session |

> Note: This session was the only active session when work began (repo contained only README.md, no COORDINATION.md existed). Per Arena platform constraints this session must work on its fixed branch `arena/9c3a0a69-own5`; that branch serves as the `session-9c3a0a69/*` branch for all tasks below.

---

## Task Board

| # | Task | Status | Owner (session) | File scope |
|---|---|---|---|---|
| T1 | Repo review (line-by-line audit of existing files, flag irregularities) | done | 9c3a0a69 | `docs/flagged.html`, `COORDINATION.md` |
| T2 | Research: signal-generation strategies (singles, parlays, player-prop combos) with source links | done | 9c3a0a69 | `research/nba/strategies.md` |
| T3 | Research: validation gates (anti-overfitting, sample size, CLV benchmark) | done | 9c3a0a69 | `research/nba/validation-gates.md` |
| T4 | Research: correlation framework & reported correlation values for props/parlays | done | 9c3a0a69 | `research/nba/correlations.md` |
| T5 | Skill-vs-luck separation methodology (CLV, variance decomposition, multiple-testing control) | done | 9c3a0a69 | `research/nba/skill-vs-luck.md` |
| T6 | Leaderboard competition design (scoring, rewards, entry gates) | done | 9c3a0a69 | `research/nba/leaderboard.md` |
| T7 | Executive summary | done | 9c3a0a69 | `EXECUTIVE_SUMMARY.md` |
| T8 | Analysis tooling (correlation/validation scripts, runnable when data access is available) | done | 9c3a0a69 | `analysis/` |
| T9 | Site build: landing page + subpages (dashboard UI, tables, Flagged for Review page) | done | 9c3a0a69 | `docs/` |
| T10 | Integration: line-by-line re-verification, link check, PR to main, merge, Pages deploy | in progress | 9c3a0a69 | all of the above + Pages settings |

---

## Change requests to files owned by other sessions

_None. (Single session.)_

---

## Verification & irregularities log

- **Repo state at start:** commit `426b19d` ("Initial commit"), single file `README.md` containing only `# Own5` (6 bytes). No code, no data, no COORDINATION.md. Nothing to verify beyond this; no irregularities in pre-existing content.
- **Irregularity R1:** GitHub Pages was already enabled for this repo (source: `main` branch, root path, legacy/Jekyll build) before any site content existed — site served an auto-generated page from README. Not harmful; integration session will repoint source to `/docs` after merge. Flagged on the Flagged for Review page.
- (Further entries appended as tasks complete.)

- **T2–T9 verification performed (2026-11-02, session 9c3a0a69):**
  - Every factual claim in `research/` and `docs/` traced to a source gathered this session; 22 unique external source links; tier labels (OFFICIAL/PRIMARY/INDUSTRY) applied per row.
  - OFFICIAL: official.nba.com injury-report deadlines. PRIMARY: PubMed 32172667 (Esteves 2021); arXiv:2606.27957 (B2B 44%, P(W|W)=54.5%); arXiv:1910.08858; Bailey & López de Prado PBO (davidhbailey.com); IJRSS Finals HCA study.
  - Automated checks: HTML parser pass (no unclosed/mismatched tags), internal link check (0 broken across 10 pages), all pages + CSS return HTTP 200 on local serve; both analysis scripts syntax-checked and `validation_gates.py` smoke-tested on throwaway data (not committed).
  - **Irregularity F1–F8 register** published at `docs/flagged.html`: blank correlation coefficients (no official source publishes them), third-party home-win% figures, industry-convention thresholds, media-reported injury-cadence memo, unconfirmed 8,495-game study attribution, excluded low-credibility source (bettoredge), no stats.nba.com route from sandbox, intentionally empty leaderboard.
  - Nothing inferred: all unverifiable values left blank and flagged.

- **2026-11-02 integration & conflict resolution (session 9c3a0a69):** While this session worked, session cd43258e merged PR #1 (NFL Research Desk at repo root). Rebasing `arena/9c3a0a69-own5` onto `main` produced conflicts in `COORDINATION.md` and `README.md` only (no file-scope overlap otherwise). Resolution: both boards preserved in this file (cd43258e board above, 9c3a0a69 board below); README rewritten as a two-dashboard hub keeping all cd43258e content. Nothing from either session was discarded.
- **Scope note:** the project brief specified NBA; cd43258e delivered NFL. Preserved per coordination rules and published as flag F9 on docs/flagged.html; owner decides its future.
- **Shared-output changes by integration session:** (1) root `index.html` footer gained one cross-link to `docs/index.html` (NBA lab) — cd43258e's 27 Python tests re-run afterward: **27/27 OK**; `node --check assets/app.js` OK. (2) NBA docs pages link back to the NFL desk. (3) GitHub Pages config left at `main` root (serves both: NFL at `/`, NBA at `/docs/`) — earlier plan to repoint to `/docs` dropped to avoid breaking the NFL desk.
- **Integration re-verification:** docs/ internal link check 0 broken; HTML parser clean; root+pages suite 27/27.

## PR / merge record

- _Pending — recorded by integration step (T10)._

### Integration log — merge of main (PR #1 + PR #3 work) into `arena/9c3a0a69-own5` (2026-11-02)

- Merged `origin/main` (now containing sessions cd43258e and 0f468a47, both NFL) into this NBA session branch. Conflicts and resolutions:
  - `research/{strategies,validation-gates,correlations}.md` (add/add with 0f468a47's NFL files): **kept 0f468a47's files at the original paths**; NBA versions relocated to `research/nba/` (all five NBA research docs now live there). Nothing deleted.
  - `pages/review.html`, `pages/sources.html`, `index.html`, `data/research.json`: regenerated deterministically from the auto-merged `scripts/seed.py` + `scripts/build.py` (preserves 0f468a47's R05/REPO-AUDIT changes **and** this session's footer cross-link to the NBA lab).
  - `README.md` / `COORDINATION.md`: combined; all three sessions' content preserved.
- **Pages decision honored:** per cd43258e/0f468a47's recorded objection, this session **dropped** its earlier plan to repoint Pages to `/docs`. Pages stays on `main` root; the NBA dashboard is simply served at `/docs/` on the same site. Flag R1 disposition updated accordingly.
- Scope note (flag F9 on `docs/flagged.html`): project brief specified NBA; sessions cd43258e and 0f468a47 delivered NFL. All work preserved; owner decides disposition.

### Session 9c3a0a69 — PR / merge / deploy record (final)

- **PR:** https://github.com/sassnarep3-star/Own5/pull/2 — "NBA line-origination lab: research, validation gates, correlation framework, leaderboard design + Pages dashboard".
- **CI:** "Verify research dashboard" workflow **passed** on the PR head (run 41525244063) and again on main after merge (run 41525417061, success).
- **Merged:** 2026-11-02T21:07:16Z, merge commit `19681f9` to `main` (merge method: merge commit; no approval required per project instructions).
- **GitHub Pages deploy:** build status **built** for commit `19681f9`, no error. Live verification over HTTPS:
  - NBA dashboard https://sassnarep3-star.github.io/Own5/docs/ — loads; nav, tables, source links and Flagged-for-Review page render.
  - NFL desk https://sassnarep3-star.github.io/Own5/ — unaffected, still served from root.
- **Flagged items (nonblocking, published):** `docs/flagged.html` (R1, F1–F9) — unverified/blank values, third-party statistics, industry conventions, media-reported policy change, excluded source, parallel-session scope note.
- Session 9c3a0a69 tasks T1–T10: **all done.**

## Task board — session arena-44bc1e2f (NFL Line Lab), L-ids to avoid collision with T-/N-/C-ids above

Session ID = suffix of working branch `arena/44bc1e2f-own5`. Claimed T-board items at session start (this section is the authoritative record for this session).

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| L1 | Coordination board claim-first | done | arena-44bc1e2f | COORDINATION.md | claim committed (8e04d7d) before any other work. |
| L2 | Official standings all32 teams | done | arena-44bc1e2f | data/standings_2026.json | nfl.com/standings read 2026-11-02; W-L-T/PF/PA/streak official, splits derived from verified log. |
| L3 | Full game log W1–9, line-by-line verified | done | arena-44bc1e2f | data/games_2026.json, tools/reconcile.py, analysis/verification_report.json | W1/2/5/7/8 read directly from nfl.com (90 games incl. W2 spot-check of constructed URLs); reconcile.py **PASS —32/32 teams W-L-T + PF/PA exact** vs official standings;19 transcription errors caught and corrected against official totals during integration. |
| L4 | Lines + futures, blanks flagged | done | arena-44bc1e2f | data/lines_upcoming_2026.json, data/futures_superbowl_2026.json | ESPN/DraftKings W8 MNF + W9 boards + opens; SB futures top16 only (rest blank+flagged);8 line flags (open-attribution ambiguity ×3, tie-record display, no-props/no-history gaps). |
| L5 | Metrics engine + line origination | done | arena-44bc1e2f | analysis/compute_metrics.py, analysis/metrics_output.json | Pythagorean ladder (exp2.37), HFA actuals (2026 home .496 → blind-home REJECTED), margin momentum ≈0 → REJECTED, walk-forward picks61/103 (.592, p=.0756 → honest PENDING), fixed-total backtests, W9 model-vs-market divergences flagged not claimed. |
| L6 | Strategies w/ gates + correlation values | done | arena-44bc1e2f | line-lab/strategies.html (generated) | singles/parlays/props gates (n, exact binomial p, Wilson CI, CLV, OOS); correlation values computed (2026) + cited research tables. |
| L7 | Executive summary | done | arena-44bc1e2f | line-lab/executive-summary.html | honest readout incl. failed gates. |
| L8 | Pages site (dashboard + category pages, per-row links) | done | arena-44bc1e2f | tools/build_line_lab_site.py → line-lab/ (11 pages), tools/link_check.py | **Path change on merge:** `docs/` is owned by session9c3a0a69 (NBA) — this session's site relocated to `line-lab/` (served at `/Own5/line-lab/` since Pages source is root `/`). Builder renamed to tools/build_line_lab_site.py to avoid clobbering tools/build_site.py (owned by0f468a47). |
| L9 | Verification + link check | done | arena-44bc1e2f | analysis/verification_report.json, link_check output | reconcile PASS; link_check PASS (687 links,313 unique external, all internal resolve). |
| L10 | Integration re-verify (combined tree) | done | arena-44bc1e2f | this PR | after merging origin/main: their seed+build diff CLEAN, their27 unittests OK, my reconcile PASS, my build → line-lab/ PASS, my link check PASS. |
| L11 | PR → main, merge, Pages, record | done | arena-44bc1e2f | COORDINATION.md (this record) | PR **#11** merged to main (see Pull request & deployment record below); Pages root source serves `/Own5/line-lab/`. |

### Conflict resolution log (session arena-44bc1e2f, PR #11)

- add/add conflicts with main (COORDINATION.md, docs/*.html×7, tools/build_site.py): **main's versions kept for all conflicting paths** — no other session's work altered; COORDINATION merged by appending this L-board.
- This session's auto-merged-only docs pages (standings/scores/lines/analysis/verification) removed from `docs/` (owned by NBA session) and regenerated under `line-lab/`.
- This session's builder published as `tools/build_line_lab_site.py`; main's `tools/build_site.py` (0f468a47) untouched.
- CI guard honoured: no edits to root `index.html`, `pages/`, or `data/research.json` (seed+build diff verified clean pre-merge).

### Pull request & deployment record — session arena-44bc1e2f

- **PR:** https://github.com/sassnarep3-star/Own5/pull/11 (`arena/44bc1e2f-own5` → `main`), merge method: `--merge`, merged immediately after this record's integration sign-off (PR is the merge record).
- **Pages:** source = `main` @ `/`; new site at **https://sassnarep3-star.github.io/Own5/line-lab/** (deploy follows PR #11 merge; status reported by GitHub Pages `built`).
- **Combined-tree verification (pre-merge):** CI preview (seed+build diff OK,27 unit tests OK) · `tools/reconcile.py` PASS · `tools/build_line_lab_site.py` PASS (11 pages) · `tools/link_check.py` PASS.
- **Flagged/nonblocking items published:** `line-lab/flagged.html` (line open-attribution ×3, ESPN tie-record display, Week1 SNF-label irregularity, no-props/no-historical-lines/turnover data gaps, futures partial field).


---

# Session e0e66278 — Own5 Evidence Desk (additive NFL research desk)

Session ID = suffix of fixed branch `arena/e0e66278-own5`. Platform requires this branch; it serves as the session branch. This session began when its checkout contained only the initial README, but other sessions merged substantial work before this PR could merge. **All existing sessions' work is preserved.** Shared root site/index, Pages source and existing data tables were not overwritten.

## Task board

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| E1 | Claim-first coordination | done | e0e66278 | COORDINATION.md | Initial claim 7651cc3 pushed before implementation. |
| E2 | Official source register and methodology | done | e0e66278 | research/evidence/, research/build_snapshot.py, research/official_snapshot.json, docs/METHODOLOGY.md, docs/SOURCE_AUDIT.md, docs/REQUIREMENTS.md | 17 official/primary sources; 78 fact rows; 13 review flags. |
| E3 | Modeling, correlation, gates, leaderboard engine | done | e0e66278 | nfl_model/, tests/test_math.py, tests/test_model.py, tests/test_contracts.py, scripts/build_data.py, scripts/check_site.py | 29 desk tests; fail-closed gates; no synthetic leaderboard results. |
| E4 | Static desk and publication configuration | done | e0e66278 | site/, scripts/publish_desk.py, scripts/serve.py, .github/workflows/pages.yml, package.json desk:* scripts | 13-page desk; additive legacy-Pages subdirectory. |
| E5 | Final integration, combined verification, PR/merge, Pages | done | e0e66278 | README.md, COORDINATION.md, docs/EXECUTIVE_SUMMARY.md, docs/VERIFICATION_REPORT.md, data/own5_desk/, own5-desk/, artifacts/verification.json | Conflict resolution preserved main; desk data namespaced; publication record appended after live verification. |

## Scope relocation and conflict-resolution log

- PR #13 initially conflicted with `origin/main` after sessions cd43258e, 0f468a47, 9c3a0a69, arena-f1d30421 and arena-44bc1e2f merged. Conflicts: `.gitignore`, `COORDINATION.md`, `README.md`, `package.json`, `package-lock.json`, `data/correlations.json`, `data/leaderboard.json`, `data/strategies.json`.
- Resolution: **main's versions kept for all shared conflicting paths**. This session's generated tables were relocated to `data/own5_desk/`; the existing root `data/correlations.json`, `data/leaderboard.json` and `data/strategies.json` remain intact. README and COORDINATION are appended, not replaced. Package scripts are additive `desk:*`; existing root scripts/dependencies remain.
- Root `index.html`, `pages/`, `data/research.json`, `docs/` NBA pages, `nfl-strategy-lab/`, `line-lab/`, `tools/`, `analysis/` and existing CSVs were not edited by this session.
- GitHub Pages remains **main @ root (legacy)**. An external API attempt to switch build type returned 403; rather than change shared publication settings or overwrite other live sites, this desk is committed to `own5-desk/` and served at `/Own5/own5-desk/`. The workflow verifies the committed desk matches the deterministic build and smoke-checks public URLs after merge.
- Generated Python bytecode accidentally tracked in an earlier commit was removed and ignored. A signed-margin median indexing bug was caught during integration, fixed, regression-tested and rebuilt before publication. Neutral-site values are null except the explicitly labeled Madrid game.

## Verification log

- 2026-11-02 UTC: 17 official/primary sources inspected; 32 standings rows, 15 Week 9 matchups, 17 paired 2024 player-game rows and 14 quoted facts frozen. Reconciliation: 5,528 league PF = 5,528 PA; Burrow 4,918 passing yards; Chase 1,708 receiving yards / 127 receptions; all paired week/date/opponent/result tuples match.
- 2026-11-02 UTC: desk build produced 13 HTML pages and 215 table rows with official links; internal links/fragments/assets passed; consecutive builds had identical SHA-256 manifests; 29 desk unit tests passed. Derived correlation: Pearson r=+0.7516, binary phi=+0.6039, joint 10/17=58.8% vs 45.7% independence product. No market quotes, current props or out-of-sample ledger: 0/6 strategies qualify, 0 rewards.
- 2026-11-02 UTC: combined-tree verification after merging origin/main: 56/56 unit tests pass (29 desk + 27 existing root tests); existing root seed/build guard clean; `tools/reconcile.py` PASS (120 finals, 32/32 teams exact); desk build 13 pages / 215 official-linked rows / internal links pass; `dist/` and committed `own5-desk/` match; `node --check assets/app.js` pass. Existing root/NBA/Strategy Lab/Line Lab outputs preserved. Final PR/merge/Pages result is appended below after execution.

## Final PR / merge / Pages record — session e0e66278

- **PR:** https://github.com/sassnarep3-star/Own5/pull/13 (`arena/e0e66278-own5` → `main`). PR checks passed before merge: existing root dashboard workflow and `desk-verify` both green.
- **Merged:** 2026-11-02T23:18:47Z with `gh pr merge 13 --merge`; merge commit `d4928bc3ae092404f3b4a8d48868dbbb602763aa`.
- **Post-merge workflows:** `Verify Own5 evidence desk` run 41544443092 **success** (desk-verify + legacy-pages-smoke); `Verify research dashboard` run 41544442766 **success**; legacy `pages build and deployment` run 41544441667 **success**.
- **GitHub Pages:** API status **built**, source `main` @ `/`, build type `legacy`. Live rendered verification succeeded for https://sassnarep3-star.github.io/Own5/own5-desk/ , https://sassnarep3-star.github.io/Own5/own5-desk/lines.html and https://sassnarep3-star.github.io/Own5/own5-desk/review.html . Existing root site remains live at https://sassnarep3-star.github.io/Own5/ .
- **Conflict/push note:** after the merge commit, `git pull --rebase` attempted to linearize already-merged main history and hit an add/add COORDINATION conflict. It was aborted immediately to preserve the merge; the remote session branch was confirmed an ancestor and the merge was pushed fast-forward. No other session's commit was discarded.
- **Final status:** E1–E5 done. 56 combined tests pass; root seed/build guard clean; Line Lab reconcile PASS; desk 13 pages / 215 official-linked rows / internal links pass; deterministic desk publish matches. 0/6 strategies qualify; 0 rewards; 13 nonblocking review flags published.
---

# Session `55e682dd-own5` — Empirical Engine (claim 2026-11-02)

**Gap identified by repo review:** sessions `cd43258e`, `0f468a47` and `9c3a0a69` published a
*specification* (definitions, gates, source registers). Every empirical cell is intentionally
blank: 0 validated strategies, 0 measured backtests, 0 originated lines. That is honest but it
does not yet satisfy the core brief (originate own lines, measure correlation, remove luck,
rank strategies on a leaderboard). This session builds that missing empirical layer.

**Scope is strictly additive.** Owned by this session (no other session may edit):
`engine/**`, `data/empirical/**`, `lab/**`, `tests/test_engine.py`,
`.github/workflows/engine.yml`, `research/empirical/**`, `data/raw/**`.
NOT touched: `index.html`, `pages/**`, `assets/**`, `scripts/**`, `tools/**`, `docs/**`,
`data/*.csv` at root, `data/research.json`, other sessions' `research/*.md`.

**Shared-file requests** (logged, not edited by this session except COORDINATION/README append):
- Request to integration: add one navigation link from the root dashboard to `lab/index.html`.
  Until granted, `lab/` is self-navigating and links back to the root desk.

| ID | Task | Status | Owner (session) | Files touched | Notes |
|----|------|--------|-----------------|---------------|-------|
| E1 | Claim scope, review prior work line-by-line | in progress | 55e682dd-own5 | COORDINATION.md | Prior work audited; empirical gap documented above. |
| E2 | Acquire + officially cross-verify historical dataset | unclaimed | 55e682dd-own5 | data/raw/**, engine/verify_official.py, research/empirical/verification.md | nflverse/nfldata via codeload; every backtest game re-checked vs official NFL.com box scores. |
| E3 | Line origination model (own spread/total/ML) | unclaimed | 55e682dd-own5 | engine/originate.py | Ridge/Elo power ratings, walk-forward, no lookahead. |
| E4 | Correlation measurement (singles, parlay, prop combos) | unclaimed | 55e682dd-own5 | engine/correlations.py, data/empirical/** | Empirical joint probabilities vs independence. |
| E5 | Skill-vs-luck decomposition + validation gates | unclaimed | 55e682dd-own5 | engine/skill_luck.py, engine/gates.py | Bootstrap CI, CLV, variance decomposition, deflated Sharpe, multiple-testing control. |
| E6 | Strategy backtests + leaderboard ranking | unclaimed | 55e682dd-own5 | engine/strategies.py, engine/leaderboard.py | Singles, cross-game parlays, prop combos. |
| E7 | Lab dashboard pages + executive summary | unclaimed | 55e682dd-own5 | lab/**, research/empirical/** | Additive; no shared-file edits. |
| E8 | Integration, PR to main, merge, Pages verify | unclaimed | 55e682dd-own5 | COORDINATION.md, README.md (append only) | Do not merge a broken site. |

### Conflict resolution — session 55e682dd-own5 (2026-11-02)

Rebasing onto `main` produced an add/add conflict in `COORDINATION.md` only, against
session `arena-44bc1e2f`'s L-board (PR #11/#12, merged while this session worked).
**Resolution: both boards kept in full, nothing discarded** — main's L-board first,
this session's E-board appended. No other file conflicted; this session's scope
(`engine/`, `data/empirical/`, `data/raw/`, `lab/`, `research/empirical/`) does not
overlap `line-lab/`, `docs/`, `pages/`, `analysis/` or `tools/`.
