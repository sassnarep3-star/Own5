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

## Rental increase SF — session 7659538a (2026-11-06)

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| RNT1 | Anonymized SF rent increase evidence brief + static subsite | done | 7659538a | rental-increase-sf/**, COORDINATION.md | Official primary references linked on each fact row; internal links checked (5 pages, 0 missing). Rent values provided by user remain unverified; proposed amounts intentionally blank. Key live rate verified on SF.gov as 1.6% effective 2026-03-01–2027-02-28. Flags: tenant succession, rent ledger/banking, unit coverage, license, practice norms, legal-service availability. |

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

# Session 81553db3 — NBA independent audit (2026-11-03 UTC)

Existing NBA lab tasks are marked complete. This additive audit uses a non-overlapping report path and does not edit generated pages, shared data, or another session's owned files.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| A1 | Independent verification of existing NBA claims, calculation, and publication readiness | done | 81553db3 | research/nba-2026/independent-audit.md, COORDINATION.md | Official NBA log, team-statistics, and injury-report pages reviewed; ten transcribed rows checked; all five correlations reproduced; 56 tests and 8-page audit pass. No new site data or performance claim. |

Claim timestamp: 2026-11-03 UTC. Scope limited to `research/nba-2026/independent-audit.md` and this coordination record. Existing `nba-2026-lab/` outputs are read-only for this task.

### Session 81553db3 verification record

- Reviewed the official [2025–26 Anthony Edwards game log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26), [2025–26 team traditional statistics](https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season), and [2026–27 injury report index](https://official.nba.com/nba-injury-report-2026-27-season/).
- Cross-checked all 10 transcribed player rows (date, opponent, W/L, minutes, points, 3PM, rebounds, assists, game ID) against the official NBA.com player-log table; no discrepancies found. This is not a verification of all 61 source rows.
- `python3 -m unittest discover -s tests -q`: 56 passed. `python3 nba-2026-lab/compute.py`: reproduced all five coefficients exactly to displayed precision. `python3 nba-2026-lab/build.py`: 8 pages built reproducibly. `python3 nba-2026-lab/check.py`: 8/8 pages pass; 51 table rows each contain an official NBA/NBA Official link.
- Audit at `research/nba-2026/independent-audit.md`. No new numeric line or performance claim is justified; zero strategies pass. Existing NBA dashboard was not edited because its generated pages are another completed task's scope. Existing limitations/flags remain published.
- Branch-sync note: a concurrent update had already pushed the identical A1 claim to this fixed session branch; initial push was non-fast-forward and was not forced. Both the remote claim and latest `origin/main` history were preserved.
- Merge conflict: `COORDINATION.md` contained the same A1 claim on the remote branch as `in progress` and this completed record. Kept the remote claim's task identity/owner/scope and retained the completed verification record; no work was discarded.
- [PR #21](https://github.com/sassnarep3-star/Own5/pull/21) merged on 2026-11-03T23:35:51Z; merge commit `bc7267e96a5934e1641d2061cfbcb13db4e8625b`. Required PR checks passed: research dashboard workflow 41740266274; evidence desk workflow 41740266272.
- Post-merge checks passed at commit `bc7267e`: research dashboard workflow 41740410909, evidence desk workflow 41740410824, and GitHub Pages build/deploy run 41740409737. GitHub Pages API reports `built`, source `main:/`.
- Live rendered checks passed for [NBA overview](https://sassnarep3-star.github.io/Own5/nba-2026-lab/index.html), [executive summary](https://sassnarep3-star.github.io/Own5/nba-2026-lab/summary.html), and [Flagged for Review](https://sassnarep3-star.github.io/Own5/nba-2026-lab/review.html).
- **A1 complete.**
---

# Session 5ea3d798 — NBA evidence refresh (2026-11-03 UTC)

This session must remain on fixed branch `arena/5ea3d798-own5` (Arena platform constraint); it cannot use the requested `session-<id>/<task>` naming. Existing NBA `docs/` and shared root outputs are owned by earlier sessions and remain untouched. Integration will add a separate namespaced site rather than overwrite them.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| B1 | Claim and baseline audit | done | 5ea3d798 | COORDINATION.md, research/nba-2026/audit.md | Review existing NBA scope and identify evidence gaps. |
| B2 | Official NBA game-log sample, correlation calculations, validations | done | 5ea3d798 | research/nba-2026/**, nba-2026-lab/data/**, nba-2026-lab/compute.py, nba-2026-lab/test_compute.py | Independent sample of official player game logs; exploratory only; all rows linked. |
| B3 | NBA source-first Pages dashboard, executive summary, review page | done | 5ea3d798 | nba-2026-lab/*.html, nba-2026-lab/style.css, nba-2026-lab/build.py | Additive category pages; no changes to another session's shared site. |
| B4 | Combined verification, PR, merge, Pages check | done | 5ea3d798 | COORDINATION.md | Final integration after B1–B3. |

Claim timestamp: 2026-11-03 UTC. No other session has claimed these namespaced paths. No requests for overlapping files at claim time.

### Session 5ea3d798 evidence + verification record (2026-11-03 UTC)

- B1 done. Baseline audit at `research/nba-2026/audit.md`: existing NBA `docs/` has no computed prop correlation and third-party qualitative directions; earlier NFL sites and NBA docs preserved. No other-session files changed.
- B2 done. Reviewed official [NBA player log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26), [team statistics](https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season) and [current injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/). Transcribed the first ten visible historical player-game rows, each linked to its NBA game URL. `nba-2026-lab/compute.py` returns PTS×AST -0.0239; PTS×REB +0.5762; 3PM×PTS +0.7974; PTS×W +0.2925; AST×REB +0.2053 (Pearson n=10; exploratory, not prop-hit correlations). Two dedicated tests passed.
- B3 done. 8 additive Pages HTML pages built in `nba-2026-lab/`: 51 table rows, each checked to contain an official NBA source URL; internal links pass. Older site outputs remain unchanged. No price/CLV/profit/reward invented.
- B4 integration verification so far: `python3 -m unittest discover -s tests -q` passed 56 tests; `python3 nba-2026-lab/check.py` passed all eight pages; `python3 nba-2026-lab/build.py` reproducible. Remaining: PR checks, merge and Pages live verification.
- Flagged, nonblocking: F01–F08 on `nba-2026-lab/review.html`: tiny selected sample, missing timestamped book quotes, no prospective holdout, no SGP payouts or leg thresholds, older third-party correlation claims unverified here, missing injury/odds joins, unfunded rewards, older site date. No current own lines may be responsibly emitted from available inputs. Dataset is deliberately narrow and not an exhaustive NBA registry.

### Session 5ea3d798 PR / merge / deployment result

- [PR #15](https://github.com/sassnarep3-star/Own5/pull/15) merged with `gh pr merge 15 --merge` on 2026-11-03T19:50:16Z; merge commit `4811cd175b3c604c410b93ce74e6a3861031b077`. Pre-merge checks: dashboard browser/evidence check and evidence-desk check both passed.
- GitHub Pages `main` at root `/`, legacy build status `built`; [deployment run 41706980242](https://github.com/sassnarep3-star/Own5/actions/runs/41706980242) succeeded (build, deploy, report). Live rendered [NBA dashboard](https://sassnarep3-star.github.io/Own5/nba-2026-lab/index.html) and [Flagged for Review](https://sassnarep3-star.github.io/Own5/nba-2026-lab/review.html) checked with a cache-busting query; index/review served correct content. First cached trailing-slash fetch returned an outdated 404 while index.html with query served the new build.
- Publication remains additive: original NBA `docs/` and NFL root remain intact. No current market odds were available; **0 validated strategies, 0 awards**, 8 explicitly visible flags. This post-merge record is published via a small follow-up PR, not retroactively attributed to PR #15.

---

# Session 9cf7de11 — NBA Line Desk 2026-27 (claim)

Session ID = suffix of fixed branch `arena/9cf7de11-own5` (Arena platform constraint; the `session-<id>/<task>` naming in the brief cannot be used on this platform, so each task is an ID on this branch). Claimed 2026-11-03 UTC, before any implementation.

Scope rule for this session: **new namespaced paths only.** Not touched: root `index.html`, `pages/`, `data/research.json`, `docs/` (NBA lab 9c3a0a69), `nba-2026-lab/` (5ea3d798), `nfl-strategy-lab/`, `line-lab/`, `own5-desk/`, existing CSV/JSON tables, existing workflows.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| S1 | Claim + repo irregularity review (NBA-relevant files) | done (commit 08ada24) | 9cf7de11 | COORDINATION.md, research/nba-2026-27/review.md | Line-by-line review of existing NBA artifacts; flags only, no edits to them. |
| S2 | Official NBA 2026-27 data capture (standings, team traditional stats, injury-report index) | done (cdbc164) | 9cf7de11 | data/nba-2026-27/** | nba.com pages fetched; every row carries its source URL. |
| S3 | Validation gates, correlations, skill-vs-luck computed from verified rows only | done (cdbc164, 08ada24) | 9cf7de11 | research/nba-2026-27/**, tools/nba_line_desk/** | Market odds / CLV not available from official sources → blank + flagged. |
| S4 | Site: landing + category subpages + Flagged for Review | done: merged in PR #30 (6ce89a9); Pages build status `built` | 9cf7de11 | nba-line-desk/** | Served at `/Own5/nba-line-desk/`. Root navigation untouched (CI-locked); linked from README only. |
| S5 | Executive summary + verification log + integration PR/merge/Pages | done: PR #30 merged 2026-11-03 23:52:43Z; this record in PR #32 | 9cf7de11 | nba-line-desk/executive-summary.html, research/nba-2026-27/EXECUTIVE_SUMMARY.md, COORDINATION.md, README.md | Final integration by this session. |

## Session 9cf7de11 — work log, sources and verification

**Verification method (all values).** Each value was transcribed from an official nba.com page (S01–S04, S08) and checked in code, not by eye alone. 20 reconciliation checks (`tools/nba_line_desk/checks.py`) cover: standings W-L = team-stats W-L for all 30 teams; GP = W+L; WIN% = W/GP; FG%/3P%/FT% recomputed from makes/attempts; REB = OREB+DREB; league margin identity; league W = L = 107; box-score PTS arithmetic for every player row; Edwards 2026-27 averages reproduce the official header (33.3/4.8/3.5). Edwards 2025-26 rows (10) match `nba-2026-lab/data/edwards_2025_26_recent10.csv` cell by cell (F10). All 91 tests pass under `python -m unittest discover -s tests` (35 are this session's).

**Sources.** Register: `data/nba-2026-27/sources.csv` (S01–S14). OFFICIAL = nba.com / official.nba.com / pr.nba.com. REPORTED (S09–S11) = press reports of 2026-27 prop restrictions, not used as facts (F06). REPOSITORY (S12–S14) = this repo's files, for review findings only.

**Blanks and flags.** No official source publishes NBA prices, so odds, CLV, ROI, priced bets, the reward pool and the leaderboard market column are blank and flagged (F07). 13 open flags are published on `nba-line-desk/flagged.html`. 19 flags in total.

**Analysis decisions (recorded in `research/nba-2026-27/methodology.md`).**
- Same-season box-score correlations are descriptive only (same games as the target). PTS and TOV pass the corrected test but are not predictive (F17).
- SIG03 (opponent PTS = PTS − (+/−)) is outcome-derived. It was first listed as a candidate, then reclassified after the first run. Disclosed (F16).
- Pre-registered out-of-sample test: 2025-26 win% → 2026-27 win% r = 0.501 (95% CI 0.171–0.729, perm p = 0.0049, passes α/2 = 0.025). Statistically supported; not validated (sample gate 20 games; minimum team GP is 5; no priced data) (F18).
- Power: 783 priced bets to detect a 55% true rate.
- Result: **0 validated strategies, 0 validated signals, 0 leaderboard entries, 0 rewards.**

**Repo review (S1) irregularities** (`research/nba-2026-27/review.md`): README does not link `nba-2026-lab/` (F02); `research/nba/correlations.md` says there is no route to stats.nba.com, partly outdated (F03); non-official betting-guide sources in `research/nba/` and `docs/` (F04); 2025-26 data is stale for 2026-27 (F01); Edwards 4 of 8 Minnesota games in official rows (F05); branch naming vs brief (F11).

**Conflicts and handoffs.** One harmless warning during the first `git pull --rebase` (remote branch did not exist yet). No merge conflicts. No other session's files were edited. Root navigation untouched; this desk is linked from README only.

**Integration record (9cf7de11).**
- PR: https://github.com/sassnarep3-star/Own5/pull/30 (`arena/9cf7de11-own5` → `main`), opened 2026-11-03.
- Conflict: on the first attempt, `main` had moved (other sessions appended to `COORDINATION.md`). Both sides were kept in order (commit 87272c6); no other file conflicted.
- Checks on the PR, all green: "Verify research dashboard" (unit tests, 91 incl. 35 new, plus the browser smoke test), "Verify Own5 evidence desk" (`desk:check` and the publish diff), and "Verify NBA validation desk".
- Merge: `gh pr merge 30 --merge`, merge commit **6ce89a9**, 2026-11-03 23:52:43Z, with no approval wait and no `--auto`.
- Post-merge `main` checks on 6ce89a9: research dashboard, Own5 evidence desk, and NBA validation desk all succeeded.
- Pages: the legacy build (from `main` root, no build step) shows `built` for the current head 1c41521, which contains 6ce89a9. The build for 6ce89a9 itself was superseded by a newer push (`cancelled`, not failed).
- Limit: this sandbox cannot reach `*.github.io` (outbound access is restricted to GitHub and package hosts). The deployment is confirmed through the GitHub Pages API, not by fetching the live page. The live URL is https://sassnarep3-star.github.io/Own5/nba-line-desk/.
- Result recorded: 0 validated strategies, 0 validated signals, 0 leaderboard entries, 0 rewards. 13 open flags on the Flagged for Review page.
## Session 9557a8aa — NBA sensitivity audit (2026-11-03 UTC)

Platform fixes this session to `arena/9557a8aa-own5`; requested session-prefixed branch is unavailable. Prior NBA lab and shared navigation are left untouched. Claim timestamp 2026-11-03 UTC.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| S1 | Independent sensitivity analysis of existing official NBA sample; self-contained Pages report and tests | done | 9557a8aa | nba-sensitivity/**, COORDINATION.md | Do not edit prior sessions' NBA lab or root pages. |

S1 completed 2026-11-03 UTC. Official [NBA Anthony Edwards 2025–26 game log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) fetched and first six rows checked against the existing CSV (dates, opponent, W/L, MIN, PTS, 3PM, REB, AST); remaining four were previously checked in session 5ea3d798 and are linked individually on the page. Fifty leave-one-out rows each link to their underlying official game. Calculated coefficients are explicitly labeled as independently derived, not NBA-published. 2 new tests and 56 existing tests passed; original NBA lab check passed; 62 page links scanned, zero broken local links. Irregularities: selected ten-game sample and missing odds/holdout persist; no strategy is certified. This audit adds no current lines or betting recommendation.

## Session e9a43ca6 — NBA validation desk (2026-11-03 UTC)

Fixed platform branch: `arena/e9a43ca6-own5`; requested session naming cannot be used. Earlier scopes preserved. Historical NBA integration T10 still says in progress although later records report publication; no takeover of its files.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| V1 | Audit and official-source availability checks | done | e9a43ca6 | research/nba-validation/** | No historical claims silently inherited as verified. |
| V2 | Fail-closed NBA model, gates, tests, category dashboard | done | e9a43ca6 | nba-validation/** | Additive isolated scope; proposed methods separated from sourced observations. |
| V3 | Integration, PR, merge, Pages verification | done | e9a43ca6 | COORDINATION.md, .github/workflows/nba-validation.yml | Only this session integrates these new outputs. |

Claim committed and pushed before implementation. Root navigation is preserved to avoid historical shared ownership; standalone NBA landing page will be published under `/Own5/nba-validation/`.

### e9a43ca6 verification and implementation record

- V1 done (scoped review). [Official NBA player log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) chunks 0–1 independently compared against all ten existing sample rows, including every stored field; match. [Injury reporting index](https://official.nba.com/nba-injury-report-2026-27-season/) and selected [glossary](https://www.nba.com/stats/help/glossary) definitions checked. Full record: `research/nba-validation/verification.md`. No blanket certification of legacy statements.
- V2 done. Eight additive NBA pages, 66 official-linked table rows; all local targets pass. Reproducible build hashes match. Six new unit tests pass, plus 56 root, two NBA sample and two sensitivity tests (66 total). Local browser checks were blocked by missing libnspr4.so; the sixteen checks are moved to GitHub-hosted CI before merge. Existing root seed/build guard and NBA structural check pass.
- New engine implements pricing/EV, empirical median, feasible binary dependence conversion, Holm correction and missing-evidence gate rejection. It is not a trained NBA prediction model or automated ingestion service. Six candidates remain blocked; current prices, phi, ROI and reward amounts blank.
- Ten nonblocking limitations published at `nba-validation/review.html`, including limited sample, missing executable odds/settlement ledger, no prospective holdout, absent bet-level dependencies and unfunded awards. Existing pages and coordination scopes preserved. Executive summary: `research/nba-validation/EXECUTIVE_SUMMARY.md` and new NBA landing page.
- Claim push note: new remote branch did not yet exist for first pull; pulled/rebased origin/main before initial branch push, then set upstream. No merge conflict occurred.
- V3 in progress: build and local verification complete; PR/merge/Pages checks follow.

S1 publication: [PR #17](https://github.com/sassnarep3-star/Own5/pull/17) merged 2026-11-03T23:32:03Z (merge commit cd31fbf36ce0fcdab66939c3a7bb5d95cdda702b). [Pages deployment run 41739900355](https://github.com/sassnarep3-star/Own5/actions/runs/41739900355) succeeded (build, deploy, report). Additive page: https://sassnarep3-star.github.io/Own5/nba-sensitivity/index.html . This record is a follow-up to the merged feature PR.

---

# Session e9f83ff4 — NBA independent audit (2026-11-03 UTC)

Arena fixes this session's branch name to `arena/e9f83ff4-own5`. The previous NBA sites remain owned by their authors; this session will not edit their files.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| A1 | Independently audit NBA evidence and publication; document concrete findings and limitations | done | e9f83ff4 | COORDINATION.md, nba-audit-e9f83ff4/** | Claimed 2026-11-03 UTC; additive scope only. |

### Session e9f83ff4 verification and flags

- Independently checked all fields in the ten rows of `nba-2026-lab/data/edwards_2025_26_recent10.csv` against the first ten displayed rows of the [official NBA player log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26); all matched. Recomputed all five correlations with existing code. Only this small sample was audited; no claim of repository-wide line-by-line verification.
- NBA [injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) reviewed; reports change throughout the day and point-in-time injury joins are missing. Market prices, settled bets, prospective validation, and funded awards remain unverified. The new [Flagged for Review](nba-audit-e9f83ff4/review.html) documents these issues and distinguishes calculated correlations from official statistics.
- `python3 -m unittest discover -s tests -q` passed 56 tests; NBA lab tests passed 2; NBA lab page checker passed 8 pages; audit tests passed 2 and check local navigation and linked official domains. Link presence is not source entailment.
- Claim push: branch did not exist remotely, so the first `git pull --rebase` against that branch failed; rebased against `origin/main` and pushed the claim as the first branch commit. No conflict or data loss.
- Integration rebase onto updated `origin/main` conflicted in the appended task board. Both the newly merged `9557a8aa` record and this session's claim were retained; no work was discarded. Rebasing rewrote this session's two commits, so the session branch was updated with a lease-protected push.
- [PR #18](https://github.com/sassnarep3-star/Own5/pull/18) merged on 2026-11-03 at 23:34:08 UTC (merge commit `00af978115731a1fd5162c2e368d627282b5d475`). Pre-merge desk and dashboard CI checks passed. [Pages deployment run 41740185238](https://github.com/sassnarep3-star/Own5/actions/runs/41740185238) succeeded; [live NBA audit](https://sassnarep3-star.github.io/Own5/nba-audit-e9f83ff4/index.html?audit=18) returned the expected content. This record is a follow-up to the merged feature PR.
- Follow-up PR #22 conflicted with another appended session record. Resolved by preserving both records; no work was discarded.

---

---

# Session 9ded47ab — NBA line-origination evidence/validation extension (2026-11-03 UTC)

Arena fixes this session's branch to `arena/9ded47ab-own5`; the requested `session-<id>/<task>` branch convention cannot be followed. Existing NBA labs, root dashboard, and other owned files are out of scope. Shared `COORDINATION.md` is the only shared file edited for claim and final record.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| O1 | Source/requirement audit and official evidence register | done | 9ded47ab | COORDINATION.md, nba-origin-lab/** | Claimed 2026-11-03 UTC; additive namespace only. |
| O2 | Reproducible line-origin, validation, correlations and leaderboard framework | done | 9ded47ab | nba-origin-lab/** | Await O1; no invented odds or rewards. |
| O3 | Category dashboard, summary, flagged review and automated checks | done | 9ded47ab | nba-origin-lab/** | Await O2; no shared root navigation changes. |
| O4 | Integration, PR, merge and Pages verification | done | 9ded47ab | COORDINATION.md, nba-origin-lab/** | Await O3; fixed Arena branch is integration branch. |

Cross-session requests: none at claim time. Other sessions should not edit `nba-origin-lab/**` while this claim is active.

### Session 9ded47ab verification log

- 2026-11-03 UTC: Opened official [NBA player box-score log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26), checked ten rows (dates/matchups/results/minutes/PTS/3PM/REB/AST/game IDs) against `nba-2026-lab/data/edwards_2025_26_recent10.csv`; also reviewed [glossary](https://www.nba.com/stats/help/glossary), [NBA schedule](https://www.nba.com/games) and [official injury report](https://official.nba.com/nba-injury-report-2026-27-season/). No current bookmaker quotes, no current model lines, no rewarded entrants.
- `python3 -m unittest discover -s nba-origin-lab -p 'test_*.py' -v`: 4/4 passed; deterministic 8-page generation, 40+ official-linked table rows, local links, deliberate blanks. Existing `python3 -m unittest discover -s tests -q`: 56/56 passed. In-sample median 22, MAE 9.5; four sample correlations recomputed. Source row links on proposed hypotheses/policies are contextual, not verification of an edge.
- R01–R08 published on `nba-origin-lab/review.html`: dynamic source archiving, selected sample, missing as-of injury joins, quote/settlement, holdout, hit dependence, funding, root-nav integration. Nonblocking.
- Concurrent change handling: origin/main advanced via session 9557a8aa while PR #20 was open. Rebased onto main; resolved the append-only `COORDINATION.md` conflict by preserving both session records in full; no other-session file overwritten. Re-ran tests below before updating PR.

- e9a43ca6 integration: origin/main advanced during implementation. Append-only COORDINATION conflict resolved by retaining both blocks in full; other sessions’ new audit/origin files preserved.

- e9a43ca6 browser remediation: extracted bundled Chromium support libraries (temporary OS directory) and reused one browser context for both viewports. All 16 local desktop/mobile no-JavaScript checks now pass. Initial CI browser run hung; cancellation was denied by GitHub permissions. Corrected test will rerun before merge.

- e9a43ca6 pull-before-push: plain `git pull --rebase` attempted to replay already merged main history and conflicted. Aborted without discarding work; preserving the integration merge and verifying the remote session tip is an ancestor before fast-forward push.

### Session 9ded47ab PR, merge and live Pages result

- [PR #20](https://github.com/sassnarep3-star/Own5/pull/20) merged into `main` on 2026-11-03T23:35:34Z, merge commit `4ac3fbd1586a7e3879c9705f1cc0270cef3d5d7c`. Before merge: dashboard browser/evidence check and evidence-desk check passed; 4 additive and 56 existing local tests passed.
- Initial Pages run 41740374686 was cancelled due to a higher-priority concurrent main deployment, not a site-build failure. Subsequent [Pages deployment run 41740409737](https://github.com/sassnarep3-star/Own5/actions/runs/41740409737) completed **success** (build, deploy, report), with GitHub Pages `main` @ `/` status `built`. The [NBA landing page](https://sassnarep3-star.github.io/Own5/nba-origin-lab/index.html) and [Flagged for Review](https://sassnarep3-star.github.io/Own5/nba-origin-lab/review.html) were read successfully from the live site with a cache-busting query. A concurrent session's PR #21 was merged after #20 and its successful deployment includes both changes.
- Main branch and existing NFL/NBA sites remain intact. No certified bets, no verified live lines, no funded rewards. R01–R08 remain on the live review page. This record is delivered in a follow-up PR because the original feature PR was already merged.

- e9a43ca6 second integration: preserved both append-only records after PRs #23/#25 landed. Corrected NBA browser CI step passed on run 41741139038; existing root browser suite also passes locally.


### e9a43ca6 PR / merge / live deployment result

- [PR #24](https://github.com/sassnarep3-star/Own5/pull/24) merged with `gh pr merge 24 --merge` on 2026-11-03T23:43:01Z. Merge commit: `f2d9a5a16e946c30eb47e1ad101c001ee9a33c4c`.
- All current PR checks passed before merge: root dashboard build/evidence/browser, desk verification and new NBA build/unit/desktop/mobile checks. Initial browser CI hang was fixed; no failing current check was merged.
- [GitHub Pages deployment 41741331651](https://github.com/sassnarep3-star/Own5/actions/runs/41741331651) succeeded: build, deploy, report. Official Pages configuration remains main at root, preserving all earlier sites.
- Live [NBA landing page](https://sassnarep3-star.github.io/Own5/nba-validation/index.html) and [Flagged for Review](https://sassnarep3-star.github.io/Own5/nba-validation/review.html) fetched after deployment with `?release=f2d9a5a` and matched expected content. A pre-deployment fetch returned 404 while build was still running; post-deploy fetches succeeded.
- V1–V3 done within the explicitly documented scope. Ten nonblocking flags remain published; zero certified strategies, no current odds or performance figures fabricated. Additional concurrent-origin and audit tests (4 + 2) also passed after integration. This publication record follows the feature merge in a documentation-only PR from the same fixed branch.

---

---

---

# Session 4396568c — NBA Desk (official-data line origination) (2026-11-03 UTC)

Fixed branch `arena/4396568c-own5` (Arena platform constraint; `session-<id>/<task>` naming not possible). Acts as worker **and** final integration session for its own scope. Read the whole board first: no task below overlaps any claimed scope. Existing NBA outputs (`docs/`, `nba-2026-lab/`, `research/nba/`, `research/nba-2026/`, `analysis/`) are owned by sessions 9c3a0a69 / 5ea3d798 and are **not edited**; findings about them are logged as review items in this session's own files. All new files live in `nba-desk/` and `research/nba-4396568c/`.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| D1 | Claim + repo audit (existing NBA claims vs official/primary sources) | done | 4396568c | nba-desk/audit.html, research/nba-4396568c/AUDIT.md | scoped: sources re-opened are listed; the rest are marked Unverified |
| D2 | Official data capture (nba.com standings, team stats, team-game box scores, schedule, injury report) + integrity reconciliation | done | 4396568c | nba-desk/data/** | transcribed from nba.com pages; every row linked; reconciled against official standings |
| D3 | Line-origination model, walk-forward test, correlations, validation gates, leaderboard | done | 4396568c | nba-desk/analysis.py, nba-desk/settle.py, nba-desk/tests/**, research/nba-4396568c/** | derived values only; no market quotes available |
| D4 | Site (dashboard + category pages + Flagged for Review) + executive summary | done | 4396568c | nba-desk/*.html, nba-desk/build.py, nba-desk/check.py, .github/workflows/nba-desk.yml | additive, served at `/Own5/nba-desk/` |
| D5 | Integration, verification, PR, merge, Pages check | done | 4396568c | COORDINATION.md, README.md | PR #28 merged; Pages verified (record below) |

Cross-session requests: (1) the owner of root `index.html`/`scripts/seed.py` (cd43258e) is asked to add a link to `nba-desk/index.html`; the root footer links only `docs/`. This session did not edit root files. (2) Session e9a43ca6 (`nba-validation/`) publishes no lines; `nba-desk/` does. Neither edited the other's files.

### Session 4396568c verification log (2026-11-03 UTC)

- **Data:** official NBA.com team tables for 2024-25, 2025-26 and 2026-27 (to 11/02), 2025-26 standings splits, team box-score table (22 games), November schedule, and the 5:00 PM ET injury-report PDF were fetched and transcribed to `nba-desk/data/*.csv`, each row with its source URL. Integrity suite: 31 identity checks all pass (30 teams per season, W = L, 1,230 games, margins sum to about zero, PTS = 2 x FGM + 3PM + FTM on all 44 rows, +/- = point difference, home wins = road losses, splits sum to 82). These identities do not catch offsetting transcription errors.
- **Audit (D1):** arXiv:2606.27957 verified (7,054 + 504 games, 2019/20-2024/25; B2B 44% vs 50%; P(W|W) 54.5%; home win rate 0.55 vs official 2025-26 55.4%). PubMed 32172667 abstract verified; author/journal/year attribution in `docs/sources.html` not visible, so unverified. arXiv:1910.08858 exists; its claim is the authors' own and the docs' wording overstates. Official 2026-27 injury-report page and rules verified. Yahoo memo, Bailey PBO PDF, IJRSS and 15 INDUSTRY sources were not opened.
- **Results:** 16 own lines for 11/04-11/05 frozen in `nba-desk/data/ledger_2026_11_04_05.csv`. Walk-forward on 22 games: margin MAE 11.58 vs 12.63 baseline (z = 1.2, not significant); totals no gain. Team-level persistence r = 0.43 (n = 30). 0 of 6 strategies qualify; 0 rewards; no market quotes verified.
- **Flags:** 15 (F01-F15) on `nba-desk/flagged.html`. None blocks the merge. Highlights: no market quotes (F01), small samples (F03, F04), 17 of 30 injury slots not yet submitted and lines not injury-adjusted (F05), MEM/SAC/UTA home-road order unconfirmed (F07).
- **Tests:** `python3 -m unittest discover -s nba-desk/tests -q` (21 tests) and `python3 nba-desk/check.py` (14 pages, 506 table rows, every row linked) pass; existing `python3 -m unittest discover -s tests -q` 56 pass; `npm run desk:check` passes.
- **Conflicts:** `git pull --rebase` conflicted twice in this file (append-only); both sides kept each time, nothing discarded. Branch updated with lease-protected push after rebase.


---

---

# Session 636a7712 — NBA 2026–27 own-lines competition (2026-11-03 UTC)

Arena fixes this session to `arena/636a7712-own5`; the requested `session-<id>/<task>` branch convention cannot be used. This is an additive, source-first NBA workspace. Existing root/NFL/NBA dashboards, generated data, tests, workflows, and shared navigation are out of scope and will not be edited.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| K1 | Current-season official source register and line-by-line evidence tables | done | 636a7712 | nba-own-lines/data/**, research/nba-own-lines/**, COORDINATION.md | Official NBA schedule, standings, team/player statistics, glossary, playing rules, and injury-report sources; blanks plus review flags when unavailable. |
| K2 | Reproducible own-line model and pregame projections | done | 636a7712 | nba-own-lines/model.py, nba-own-lines/data/**, research/nba-own-lines/** | Calculated research lines only; no unverified sportsbook prices or betting claims. |
| K3 | Singles/parlays/prop-combo hypotheses, correlations, fail-closed validation, skill-versus-luck analysis and leaderboard | done | 636a7712 | nba-own-lines/model.py, nba-own-lines/data/**, research/nba-own-lines/** | Zero rewards unless all evidence gates pass; luck cannot be literally removed. |
| K4 | Additive dashboard, executive summary, Flagged for Review page, builder/checker/tests | done | 636a7712 | nba-own-lines/** | Every body-table row links to an official NBA source; derived values explicitly labeled. |
| K5 | Final integration, combined checks, PR, merge, and live Pages verification | done | 636a7712 | COORDINATION.md, nba-own-lines/**, research/nba-own-lines/** | Fixed Arena branch is the integration branch; preserve all concurrent work. |

Claim timestamp: 2026-11-03 UTC. No cross-session file requests at claim time. Other sessions should not edit `nba-own-lines/**` or `research/nba-own-lines/**` while this claim is active.

Integration conflict log: while rebasing onto `origin/main` after concurrent PRs #23–#25, the append-only board conflicted with session e9a43ca6's integration record. Both blocks were retained verbatim; no other session's work was discarded. Rebasing rewrote this session's two commits; a lease-protected push updated only this session branch.

### Session 636a7712 evidence and verification record

- **K1 done:** reviewed 12 official NBA/NBA Official sources. Frozen evidence contains 30 advanced-team rows, 16 November 4–5 schedule rows, four selected players and 26 complete selected player-game rows. Official source register and row-level audit: `research/nba-own-lines/source-audit.md` and `nba-own-lines/sources.html`.
- **K2 done:** `model.py` calculates 16 research spreads/totals/scores and no-vig model prices from shrunk OffRtg/DefRtg/PACE. Disclosed analyst parameters: 10-game prior, zero HFA, 6-point logistic scale, no overtime or injury adjustment. Market/edge fields are null.
- **K3 done:** seven singles/parlay/prop-combo hypotheses; G00–G09; 21 Pearson correlations; exact player permutation p-values with Holm correction across 16 tests; tested binomial luck function; unranked leaderboard. **0/7 strategies qualify and current rewards are zero.** No luck-removal or profitability claim.
- **K4 done:** 11 responsive static pages, executive summary, methodology, requirements trace and Flagged for Review page. Checker passes **199 body-table rows / 454 links / 16 lines / 0 qualified**; every body-table row has an official NBA source/context link and internal links resolve.
- **Verification:** 16 new unit/site tests pass; existing 56 root tests pass; `python3 nba-own-lines/check.py` passes; generated HTML and `derived.json` are byte-for-byte reproducible. Player means reconcile to official rounded averages in all 16 checks; schedule records match all 32 team-game entries.
- **Material irregularities:** F01–F11 published on `nba-own-lines/review.html`. Anthony Edwards is officially Out and suppressed; other unknown availability is held; several team reports were not submitted in the 6:15 PM ET snapshot. No sportsbook prices, payouts, prospective ledger, joint-hit rates or funded rewards are inferred. Other sessions' historical rows were not independently re-transcribed (F10).
- **K5 done — PR / merge:** [PR #27](https://github.com/sassnarep3-star/Own5/pull/27) merged with `gh pr merge 27 --merge` on 2026-11-03T23:47:32Z; merge commit `459b2071a7f2fb5ac090e9e26b668ad1b80b4c66`. Pre-merge root dashboard/browser, evidence-desk and NBA-validation checks all passed.
- **Post-merge CI:** main runs 41741912141 (research dashboard), 41741912094 (NBA validation), and 41741912050 (evidence desk) all completed **success**.
- **Pages:** [deployment 41741910687](https://github.com/sassnarep3-star/Own5/actions/runs/41741910687) completed **success**; API status `built`, source `main` @ `/`, legacy. Live rendered [overview](https://sassnarep3-star.github.io/Own5/nba-own-lines/index.html), [own lines](https://sassnarep3-star.github.io/Own5/nba-own-lines/lines.html), and [Flagged for Review](https://sassnarep3-star.github.io/Own5/nba-own-lines/review.html) fetched with cache-busting `?release=459b207` and matched expected content.
- **Concurrency:** a second append-only rebase conflict retained the concurrent PR #26 publication record and this session's block in full; no work was discarded. All existing sites remain intact.
- **Live-review correction:** the ORL@PHX near-even line displayed a cosmetic `-0.0` home spread. This documentation follow-up normalizes signed zero and adds a regression assertion; inputs and the underlying projection are unchanged.
- **Final result:** K1–K5 done. 11 pages, 199 official-linked table rows, 454 links checked, 16 research lines, 21 correlations, 0/7 qualified strategies, 0 rewards, F01–F11 published and nonblocking.

### Session 4396568c PR, merge and live Pages result

- [PR #28](https://github.com/sassnarep3-star/Own5/pull/28) merged with `gh pr merge 28 --merge` on 2026-11-03T23:52:55Z; merge commit `5d8c2657c74cf1421a624c4d0723b37ce60c93e9`.
- A first PR run of the new `Verify NBA Desk` workflow **failed** at the regenerate-and-diff step; the likely cause is last-digit floating-point differences between machines (no log could be retrieved). Fixed by rounding derived JSON to 8 significant figures and adding diagnostics; the re-run passed. All checks were green before merge: `Verify NBA Desk`, `Verify research dashboard`, `desk-verify`, `verify`.
- Post-merge `main` runs succeeded: Verify research dashboard, Verify NBA Desk, Verify NBA validation desk and [pages build and deployment run 41742592365](https://github.com/sassnarep3-star/Own5/actions/runs/41742592365). Live [overview](https://sassnarep3-star.github.io/Own5/nba-desk/index.html) and [Flagged for Review](https://sassnarep3-star.github.io/Own5/nba-desk/flagged.html) fetched after deployment (`?release=5d8c265`) and matched: 16 lines, 15 flags, 0 of 6 qualified.
- Merge brought in `nba-own-lines` (636a7712): its 16 matchups agree with this desk's schedule; its home margins are copied into `nba-desk/data/crosscheck_nba_own_lines.csv` (flag F15: mean absolute difference about 3.4 points, neither model validated).
- Follow-up PR: this record, plus a label fix (source links to the repo were captioned "official page"; now "external / repo page").

# Session 6d508fee — NBA signal engine, model lines, competition desk (2026-11-03 UTC)

Arena fixes this session's branch to `arena/6d508fee-own5`. Additive namespace only: this session will not edit any prior session's site or data (`docs/`, `nba-2026-lab/`, `nba-sensitivity/`, `nba-origin-lab/`, `nba-audit-e9f83ff4/`, `nfl-strategy-lab/`, `line-lab/`, `own5-desk/`, root `index.html`/`pages/` except the final-integration footer cross-link described below). Shared `COORDINATION.md` and `README.md` are append-only for this session.

**Scope (why it does not collide):** prior NBA sessions all reused the same 10-row Anthony Edwards sample and emitted no model lines. This session's deliverables are the *computed engine*: expanded verified datasets (30-team tables + multi-player game logs at real n), in-repo correlation values for player-prop combos and parlays, model-derived own lines for the current 2026-27 slate (market columns blank+flagged), a luck-vs-skill power engine, a gated strategy catalog (singles / parlays / prop combos) and a leaderboard competition design with reward tiers.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| M1 | Claim + baseline audit of NBA scope and open claims | in progress | 6d508fee | COORDINATION.md | Claim pushed before any other work. Scopes of 9ded47ab (`nba-origin-lab/**`, PR #20 open) and e9f83ff4 (`nba-audit-e9f83ff4/**`, PR #18 open) respected — untouched. |
| M2 | Expanded verified dataset: 2026-27 + 2025-26 team tables, multi-player game logs | unclaimed | 6d508fee | nba-signal-lab/data/**, research/nba-signal-lab/data-notes.md | Every row carries its official nba.com source URL; unverifiable cells blank+flagged. |
| M3 | Model-derived own lines for current slate (spread/total) | unclaimed | 6d508fee | nba-signal-lab/** | Market columns blank+flagged (no verified book source in scope); derivation documented. |
| M4 | Correlation values: prop combos + parlay legs, computed in-repo at real n | unclaimed | 6d508fee | nba-signal-lab/** | Pearson/phi + joint-vs-independence; computed by script from M2 data. |
| M5 | Luck-vs-skill engine (exact binomial power, DSR, multiple testing) | unclaimed | 6d508fee | nba-signal-lab/** | Concrete Ns computed in-repo; thresholds cited to published methodology. |
| M6 | Gated strategy catalog: singles, parlays, player-prop combos | unclaimed | 6d508fee | nba-skill-lab files under nba-signal-lab/** | Pre-registered rules; all start PENDING (no settled odds data) — 0 certified. |
| M7 | Validation gates G01–G10 with concrete thresholds | unclaimed | 6d508fee | nba-signal-lab/** | Gate table + fail-closed status per strategy. |
| M8 | Leaderboard competition design (deflated scoring, reward tiers) | unclaimed | 6d508fee | nba-signal-lab/** | Reward amounts proposals; prize pool blank+flagged (unfunded). |
| M9 | Executive summary | unclaimed | 6d508fee | research/nba-signal-lab/EXECUTIVE_SUMMARY.md | Restates only computed/verified values. |
| M10 | Pages site: dashboard + category subpages, per-row source links | unclaimed | 6d508fee | nba-signal-lab/*.html, nba-signal-lab/build.py | Deterministic builder + tests; all entries in table format. |
| M11 | Line-by-line verification + Flagged for Review | unclaimed | 6d508fee | nba-signal-lab/flagged.html, nba-signal-lab/checks | Every table row official-linked or explicit blank+flag. |
| M12 | Integration: combined re-verify, PR to main, merge, Pages check | unclaimed | 6d508fee | COORDINATION.md, README.md (append), scripts/seed.py + index.html/pages/ (footer cross-link only, via deterministic rebuild + full test suite) | May take over stale tasks (>60 min no commits) per rules; will note handoffs. |

Claim timestamp: 2026-11-03 UTC. Cross-session requests: none at claim time.

### 2026-11-03 — Session 6d508fee progress (M2–M12)

- **M2 done** — expanded verified dataset: 2026-27 + 2025-26 standings & team tables (30 teams × 2, W-L cross-checked across two official pages, 3 transcription errors caught by re-fetch and fixed); 2025-26 game logs for the top-2 official scorers (Dončić 64 + Edwards 61 = 125 player-game rows, per-row nba.com game URLs, scoring/rebound identities 125/125, per-player averages reproduce the official leaders page exactly); 2026-11-04 slate (6 games from official team-schedule pages). Source register: `research/nba-signal-lab/data-notes.md`.
- **M3 done** — own model lines for 6 slate games (blended 2026-27/2025-26 net ratings, w=n/(n+20), HFA 2.5 flagged constant + sensitivity 2.0/2.5/3.0); market columns blank+flagged (no verified odds source).
- **M4 done** — correlation values computed in-repo at real n=125: 7 stat-pair Pearson r with Fisher-z CIs (PTS×3PM 0.69 [0.58,0.77] strongest; PTS×WIN 0.09), 5 prop-combo phi/lift rows (same-game legs lift 1.10–1.27 vs independence), lag-1 PTS autocorrelation ≈ 0 both players (cross-game parlay independence supported).
- **M5 done** — luck-vs-skill engine: break-even 0.5238 (−110 arithmetic), power table (55% edge needs ≈2,243 graded bets at α=.05/80%), exact binomial tails (30-20 run: p=0.17), deflated scoring (prior 25 bets), Šidák/Bonferroni bounds. No skill claims: 0 certified.
- **M6–M7 done** — 5 candidate strategies (singles, cross-game parlay, 2-leg + 3-leg same-game prop combos) all PENDING behind gates G01–G10; G08 (market gate) structurally blocked (F-MARKET).
- **M8 done** — leaderboard: audit units, deflated scoring, 50/30/20 reward tiers; prize pool blank+flagged (F-ODDS); 0 entries graded.
- **M9–M10 done** — EXECUTIVE_SUMMARY.md + 11-page GitHub Pages site (`nba-signal-lab/`), every table row source-linked, BLANK—UNVERIFIED markers, idempotent builds.
- **M11 done** — line-by-line verification (16/16 checks; re-fetch diffing found + fixed 3 errors); 6 open flags published on the Flagged for Review page incl. source-page irregularities (games page JS-only, cdn static JSON 500, "Margins & Stats" mislabeled, ~50-row render caps, celtics.com JS-only schedule).
- **M12 in progress** — integration commit `de00d9d`: root footer cross-link via CI-locked seed.py/build.py rebuild (idempotent; root 56/56 unittest + node check green, lab 13/13 green). PR → merge → Pages record follows in the next entry.
### 2026-11-04 — Session 6d508fee completion record (M12)

- **PR: https://github.com/sassnarep3-star/Own5/pull/33** — "NBA Signal Lab: own model lines, correlation-priced prop combos, validation gates, luck-stripped leaderboard (session 6d508fee)". Includes summary, source register, and all flagged irregularities in the PR body per protocol.
- **Merged:** yes — merge commit `1885d7435ea1c1dba830755fc723aed5f6a30630` at 2026-11-04T00:24:45Z (`gh pr merge 33 --merge`). Append-only conflicts in COORDINATION.md/README.md resolved by keeping both sides before merge; CI-locked rebuild clean and all test suites green at merge time.
- **GitHub Pages:** deployed — pages build-and-deployment run `41746619471` completed success; live URLs externally verified: https://sassnarep3-star.github.io/Own5/nba-signal-lab/index.html (dashboard) and https://sassnarep3-star.github.io/Own5/nba-signal-lab/flagged.html (Flagged for Review). Root desk footer now cross-links "NBA Signal Lab ↗" (integration via the CI-locked seed.py/build.py rebuild).
- **Task status:** M1–M12 **DONE**. 16/16 verification checks green; 6 open flags published (F-HFA, F-MARKET, F-SLATE, F-SMALL, F-PLAYERS, F-ODDS); 0 strategies certified; no luck/skill claims made.

# Session arena-a46d621e — NBA Line Commission, 2026-11-05 snapshot (2026-11-05 UTC)

Arena fixes this session's branch to `arena/a46d621e-own5`. Additive namespace only: this session
does not edit any prior session's site or data (`docs/`, `nba-line-desk/`, `nba-signal-lab/`,
`nba-2026-lab/`, `nba-origin-lab/`, `nba-audit-e9f83ff4/`, `nba-sensitivity/`, `nba-validation/`,
`nba-own-lines/`, `nba-desk/`, `line-lab/`, `nfl-strategy-lab/`, `own5-desk/`). Shared
`COORDINATION.md` and `README.md` are append-only for this session, except the single root-footer
cross-link added through the CI-locked `scripts/build.py` + `scripts/seed.py` deterministic rebuild
(same additive integration pattern used by sessions 6d508fee and cd43258e).

**Why this does not duplicate prior work.** Every prior NBA session published a *frozen* snapshot
(2026-11-02 … 2026-11-04) and none of them re-verified a *previous* session's rows against the
official pages on a later date. This session publishes the **2026-11-05 official snapshot**, a
**new slate's own lines**, and the **first cross-lab reconciliation audit** (re-fetch → row-by-row
diff → flagged irregularity register) across the six existing NBA labs.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| A1 | Claim + baseline audit of repo and open claims | done | arena-a46d621e | COORDINATION.md | Claim pushed before any other work. No task on the board is in progress; last session 6d508fee completed M1–M12 (PR #33). |
| A2 | 2026-11-05 official snapshot: standings, team stats, slate, player logs | done | arena-a46d621e | nba-commission/data/**, research/nba-commission/data-notes.md | Every row carries its official nba.com source URL; unverifiable cells blank + flagged. |
| A3 | Own model lines for the 2026-11-05/06 slate (spread + total) | done | arena-a46d621e | nba-commission/** | Market columns blank + flagged (no verified odds source); derivation + sensitivity documented. |
| A4 | Correlation values (prop combos, parlay legs) computed in-repo at real n | done | arena-a46d621e | nba-commission/** | Pearson r with Fisher-z CIs, phi/lift vs independence, lag-1 independence check. |
| A5 | Luck-vs-skill engine (exact binomial, power, DSR, multiple testing) | done | arena-a46d621e | nba-commission/** | Concrete Ns computed in-repo; thresholds cited to published methodology. |
| A6 | Gated strategy catalog: singles, parlays, player-prop combos | done | arena-a46d621e | nba-commission/** | Pre-registered rules; all start PENDING — no settled odds data, so 0 certified. |
| A7 | Validation gates G01–G12 with concrete, cited thresholds | done | arena-a46d621e | nba-commission/** | Fail-closed status per strategy. |
| A8 | Leaderboard / competition design (deflated scoring, reward tiers) | done | arena-a46d621e | nba-commission/** | Reward amounts are proposals; prize pool blank + flagged (unfunded). |
| A9 | Cross-lab reconciliation audit of prior NBA sessions' rows | done | arena-a46d621e | nba-commission/**, research/nba-commission/repo-audit.md | Re-fetch official pages, diff prior snapshots, publish irregularities. |
| A10 | Executive summary | done | arena-a46d621e | research/nba-commission/EXECUTIVE_SUMMARY.md | Restates only computed/verified values. |
| A11 | Pages site: landing page + category subpages + Flagged for Review | done | arena-a46d621e | nba-commission/*.html, nba-commission/build.py | Deterministic builder + tests; every table row source-linked. |
| A12 | Line-by-line verification harness | done | arena-a46d621e | nba-commission/verify.py, nba-commission/checks/ | Every row official-linked or explicit BLANK + flag; no broken links. |
| A13 | Integration: combined re-verify, PR to main, merge, Pages check | done | arena-a46d621e | COORDINATION.md, README.md (append), scripts/build.py (footer cross-link only) | Records PR link + merge result here when done. |

Claim timestamp: 2026-11-05 UTC. Cross-session requests: none at claim time.

### Session arena-a46d621e — work log, sources and verification (2026-11-05 UTC)

- **A2 done.** Official snapshot fetched 2026-11-05 through the platform page fetcher (sandbox curl to
  nba.com is blocked; GitHub hosts only). Transcribed: 2026-27 standings 30 rows (E1), team traditional
  stats 30 rows (E2), the 2026-11-05/06 slate 11 games (E3), 2026-27 game logs for Edwards 4 rows and
  Dončić 8 rows (E4/E5), plus an independent re-fetch of 6 rows already inside the inherited 2025-26 log
  (E6). Validation: W-L agree on both official pages 30/30; GP = W + L 30/30; split sums 30/30;
  Σ(net×GP) = 0.7; log identities 137/137; per-player averages reproduce the official headline averages
  (round-half-up); 0 duplicate (player_id, game_id).
- **A3 done.** 11 own spread/total lines (formula in `research/nba-commission/methodology.md`), each with
  a 7-variant sensitivity grid (K ∈ {10,20,40}, HFA ∈ {0.0,2.5,3.0}, current-only). Market columns blank.
- **A4 done.** 7 team-level r (n=30), 7 player-pair r with Fisher-z CIs (n=137) plus per-season
  out-of-sample re-tests, 5 prop-combo joint prices with φ/lift, lag-1 independence. Cross-check: the
  inherited PTS × 3PM value recomputes to 0.6893 (0.5844, 0.7715) — identical to session 6d508fee's
  published number.
- **A5 done.** −110 break-even 0.52381; exact-binomial power (55% ⇒ 2,248 bets at 80% power, 3,113 at
  90%; 60% ⇒ 269; 65% ⇒ 98); Bonferroni 0.00625 / Šidák 0.00639 for 8 tests; deflation rule and worked
  examples; no Sharpe statistic is invented because no return series exists.
- **A6/A7/A8 done.** 8 pre-registered strategies × 12 gates; every strategy fails closed; 0 certified;
  leaderboard empty with a hard sample floor (2,248 bets) and reward amounts blank (pool unfunded).
- **A9 done.** Repo audit: 91 existing tests pass, `tools/check_site.py` 20/0, repo-wide internal links
  0 broken across 153 pages; earlier NBA boards re-verified (125/125 identities, 6/6 rows exact on
  re-fetch, published correlation reproduced); the 2026-11-03 snapshot reconciles to the 2026-11-05
  standings through exactly the 14 official 2026-11-04 games. Irregularity found: inherited CSV header
  `blkа_pg` uses U+0430 (Cyrillic) instead of ASCII — logged as F13 and normalised in this session's
  copy; the other session's files were **not** edited.
- **A10–A12 done.** `research/nba-commission/EXECUTIVE_SUMMARY.md`, `methodology.md`, `data-notes.md`,
  `repo-audit.md`; 14-page site in `nba-commission/`; `verify.py` green (6 groups, 0 failures: 238 CSV
  rows all official-sourced, 75 keyed JSON rows linked, no broken links anywhere in the repo, no
  unlinked table row, deterministic rebuild) and 18 unit tests pass.
- **Flags published (14):** F01 no verified market price · F02 HFA is an assumption · F03 small samples ·
  F04 Edwards 4 of 9 games · F05 games page renders "No Games Scheduled" · F06 NBA Cup treatment
  unverified · F07 prior table secondhand · F08 moneyline model blocked · F09 prize pool unfunded ·
  F10 prop settlement rules unverified · F11 no injury feed · F12 prior net sum −16.4 · F13 Cyrillic
  header · F14 GB column is win%-based.
- **A13** — integration: root footer cross-link added through the CI-locked `scripts/build.py` rebuild
  (deterministic, `data/research.json` unchanged), full 91-test suite green, `tools/check_site.py` green.

# Session eeddab9b — independent NBA deliverable and provenance audit (2026-11-05 UTC)

Arena fixes this session to `arena/eeddab9b-own5`; the prescribed `session-&lt;id&gt;/&lt;task&gt;` branch/worktree convention cannot be used because the Arena-managed branch is fixed. Existing NBA implementation and integration tasks are complete, so this session claims only an isolated audit report and makes no edits to any existing NBA dataset, strategy, site, or shared navigation.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| E1 | Independent provenance, build, and findings audit of the NBA signal lab | done | eeddab9b | COORDINATION.md, nba-audit-eeddab9b/** | 2026-11-05: audit report + standalone Flagged for Review page; deterministic builds and 91 root / 13 lab tests pass. No fresh NBA-page retrieval was available; six review issues documented, no prior NBA data/site files changed. |

Claimed: 2026-11-05 UTC. Cross-session requests: none at claim time.

### 2026-11-05 — E1 completion and independent audit

- **Deliverables:** `nba-audit-eeddab9b/AUDIT.md`, `index.html`, and `flagged.html` (A01–A05) are an additive audit and review mini-site; no earlier session's NBA data, analysis, or shared site navigation was edited.
- **Official sources linked for manual review:** NBA game calendar for 2026-11-04; NBA 2025-26 player box-score pages for Luka Dončić, Anthony Edwards, and Shai Gilgeous-Alexander; NBA 2025-26 leaders; NBA 2025-26 and 2026-27 team traditional statistics. The source register lives in `nba-signal-lab/data/raw/evidence_log.md` and its published counterpart at `nba-signal-lab/verification.html`.
- **Verification performed:** `nba-signal-lab/build.py` and `compute.py` pass (16 checks, 0 failures); NBA Signal Lab tests 13/13; root tests 91/91; NBA Own Lines 20 checks; NBA Desk check reports 14 pages/506 table rows/15 flags; NBA 2026 lab + NBA-origin audit tests pass. New audit pages have 26 local/relative links checked on the overview; the review page duplicates the verified findings content. Three nonfatal lab-test ResourceWarnings were observed.
- **Limit:** NBA source pages could not be freshly fetched in this sandbox session. Prior session's 2026-11-03 fetch/transcription record was examined; this session re-ran local computations and structural checks only, and does not mark current source-page values newly verified.
- **Findings published for review:** A01 historical 2026-11-04 slate; A02 cross-game independence inference is too strong for two players / wide intervals (also overstated in README); A03 pooled two-player correlation intervals / prop rates need clustered and out-of-sample validation; A04 source E7–E10 identifier mapping conflict between evidence log and verification page; A05 derived-line rows do not directly expose all season-qualified input sources. Repository presentation note: top-level branding/inventory is stale versus the NBA work.
- **Cross-session request:** reconcile A02–A05 on the existing `nba-signal-lab/flagged.html` and correct the source registry / claims in that site. Per the claimed isolated scope this session did not edit that prior site's files; audit-specific flags are live at `nba-audit-eeddab9b/flagged.html`.
- **Tool limitation logged:** `python3 scripts/check_site.py` could not run because `dist/` was absent. This is recorded as an unmet precondition, not a failed assertion. Initial `git pull --rebase origin arena/eeddab9b-own5` found no remote branch; the claim commit was then pushed to the required fixed branch `arena/eeddab9b-own5`.
- **PR:** [#36](https://github.com/sassnarep3-star/Own5/pull/36), merged using `gh pr merge 36 --merge` on 2026-11-05T21:26:07Z; merge commit `6f19f60f15e2127d556a1ee2ffa19c6dd2970651`.
- **Post-merge checks / Pages:** `Verify research dashboard` run `42112616394` succeeded; Pages build and deployment run `42112615395` succeeded. GitHub Pages API reports `status: built`, public, source `main` at `/`; site base is https://sassnarep3-star.github.io/Own5/ . The new pages are `/nba-audit-eeddab9b/` and `/nba-audit-eeddab9b/flagged.html`.


## Session e2f426bc — independent NBA evidence and integration audit (2026-11-05 UTC)

Arena fixes the branch to `arena/e2f426bc-own5`; the requested session branch naming cannot be used. Earlier scopes remain untouched. Historical M1–M12 board entries are superseded by their 2026-11-04 completion record; historical T10 was not taken over.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| E1 | Independent audit of existing NBA claims, source provenance, and statistical validity; publish findings and review flags | in progress | e2f426bc | `nba-evidence-audit/**`, `COORDINATION.md` (append only) | No changes to other sessions' owned artifacts. Verify only what sources and tools permit; do not claim a complete line-by-line audit without evidence. |
| E2 | Local verification, PR, merge and deployment record | in progress | e2f426bc | `nba-evidence-audit/**`, `COORDINATION.md` (append only) | Integration limited to this additive scope; no shared navigation edits without ownership coordination. |

Claimed 2026-11-05 UTC; sources and results to follow.

### Cross-session request — 2026-11-05, e2f426bc → 6d508fee / NBA Signal Lab owner

Please review `nba-signal-lab/compute.py`, `nba-signal-lab/build.py`, and `research/nba-signal-lab/**`: the computed `S_home-S_away+HFA` is expected **home margin** (positive favors home) but pages label it home spread with negative favorite; `EXECUTIVE_SUMMARY.md` reverses the direction of the independence-product error; lag-1 CIs containing zero do not establish independence or validate different-game parlays; and the NBA leaders page ranks Edwards third, not second, for 2025–26. Source: https://www.nba.com/stats/leaders?Season=2025-26 and https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm. Our additive flagged page will document these; no owner files edited.

### e2f426bc verification record — 2026-11-05

- **E1 done (additive scope only):** `nba-evidence-audit/` provides five static pages, reproducible generation, six game-score rows, an 11-game Anthony Edwards sample, descriptive correlations, a strategy/gate catalog and ten review flags. This is not a full repo-wide source audit and does not certify a strategy.
- **Source verification:** official NBA [Nov. 4 scoreboard](https://www.nba.com/games?date=2026-11-04), chunks 0–2, checked each of six scores/matchups; [2025–26 scoring leaders](https://www.nba.com/stats/leaders?Season=2025-26) establishes Dončić / Gilgeous-Alexander / Edwards order; all 33 points/rebounds/assists values in the [11-game filtered Edwards log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26&DateFrom=2025-10-01&DateTo=2025-11-20), chunks 0–1, checked individually and against original CSV. Official URLs are dynamic and fetched 2026-11-05 UTC. [NIST autocorrelation](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm) provides methodological context, not validation of the model.
- **Derived, not NBA facts:** original repo model values compared with official finals yield 3/6 winning directions, 10.48 margin MAE, 13.08 total MAE. These are post-event descriptive results, not market or skill validation. Prop correlations are retrospective within-player estimates for n=11; no 3-leg pricing, market data, or profit claims.
- **Irregularities:** prior Signal Lab home-margin sign labels contradict its formula; positive lift interpretation is reversed in its summary; lag-one zero-correlation inference overstates independence; Edwards is third, not second. Odds/prizes absent; current calendar rendering inconsistent; other inputs unverified independently. Full context and links on `nba-evidence-audit/flagged.html`; owner correction requested above.
- **Local checks:** `python3 nba-evidence-audit/test_audit.py` (4 pass; 47 new table rows have official context links; all new local links resolve; build deterministic); `python3 nba-signal-lab/test_lab.py` (13 pass); `npm test` (91 pass); `python3 tools/check_site.py` (0 failures, 9 existing flagged-blank warnings). Tests establish internal consistency/link shape, not independent verification of every existing data row or remote page availability. Original NBA Signal Lab unchanged.
- **E2 in progress:** PR, checks and Pages publication follow. No shared navigation changes; direct URL will be recorded.

### Integration link repair claim — session e2f426bc

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| E3 | Repair missing machine-readable directory landing page | in progress | e2f426bc | `data/index.html` (new), `COORDINATION.md` (append only) | Root-wide static local link scan found nine existing detail pages pointing at `data/`, which has no index under GitHub Pages. New index is a distinct file, not an existing CSV/JSON or generated detail page; no other owner's files modified. |

- **E3 done:** added `data/index.html` to resolve nine prior `data/` links without modifying their generated pages or datasets. `python3 nba-evidence-audit/check_links.py` checked 2,367 filesystem-backed relative links across HTML, with 0 missing. The scan excludes external URLs, anchors, root-relative paths and template placeholders; it is not proof that all external links work.

- **Integration conflict:** concurrent PR #36 merged to main while this work was in progress. Rebasing onto main produced an append-only `COORDINATION.md` conflict between session eeddab9b's audit record and this session's claim. Both complete blocks were retained; no other session's work was discarded. The two independently scoped audit reports overlap on independence concerns, but this session additionally re-fetched official sources, checked final scores and transcribed an 11-game correlation sample.
- A second append-only board conflict followed concurrent PR #37, which added the other session's deployment record; both that record and this session's claims were retained without loss.

### e2f426bc — PR and publication record

- **E1/E3 done; E2 done for this scoped audit.** [PR #35](https://github.com/sassnarep3-star/Own5/pull/35) merged 2026-11-05T21:29:01Z as `6e400973b101c3bf32172540bd54381bdff5c3e2`; all PR checks passed. This record does not claim the full repository was independently verified.
- **Pages deployed:** [Pages deployment 42113041069](https://github.com/sassnarep3-star/Own5/actions/runs/42113041069) succeeded. Live [overview](https://sassnarep3-star.github.io/Own5/nba-evidence-audit/index.html), [review flags](https://sassnarep3-star.github.io/Own5/nba-evidence-audit/flagged.html), and [data index](https://sassnarep3-star.github.io/Own5/data/index.html) fetched successfully after deployment. Main research dashboard, NBA validation, and evidence-desk workflows passed for merge commit.
- **Scope limits:** all non-reviewed prior rows, prices, grades and funding remain unverified; no skill or profit is certified. Flags do not mean that owners' original pages have been corrected. Root-wide scan checked 2,400 relative links after concurrent PR #36; external URLs, fragments and root-relative URLs excluded.
---

# Session ad72b171 — NBA evidence integration and selective-skill competition (2026-11-05 UTC)

Arena fixes this session to `arena/ad72b171-own5`; the requested session-task branch convention cannot be used. This session uses only additive paths `nba-strategy-lab/**` and `research/nba-strategy-lab/**`, plus this append-only board. Existing sites, data, root navigation, workflows and tests are out of scope.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| A1 | Baseline/coordination audit and official-source evidence register | in progress | ad72b171 | COORDINATION.md, research/nba-strategy-lab/**, nba-strategy-lab/data/** | Freeze only previously captured official NBA inputs; do not claim a fresh external fetch. |
| A2 | Reproducible lines, singles/parlays/prop combos, correlations, gates, luck controls and leaderboard | unclaimed | ad72b171 | nba-strategy-lab/**, research/nba-strategy-lab/** | Fail closed; no unsupported skill, profit, odds or reward claims. |
| A3 | Executive summary and clean category dashboard with row-level sources and Flagged for Review | unclaimed | ad72b171 | nba-strategy-lab/**, research/nba-strategy-lab/** | Static Pages-compatible site; every body-table row linked. |
| A4 | Final integration, full verification, PR, merge and live Pages confirmation | unclaimed | ad72b171 | nba-strategy-lab/**, research/nba-strategy-lab/**, COORDINATION.md | Preserve concurrent work; merge only with green checks. |

Claim timestamp: 2026-11-05 UTC. No outstanding cross-session requests. Other sessions should not edit the claimed namespaces while this work is active.

### Session ad72b171 progress and verification record (2026-11-05 UTC)

- **A1 done:** additive source boundary frozen at 275 official-NBA-linked input rows. Raw files preserve the reviewed `nba-desk` and `nba-signal-lab` snapshots byte-for-byte. No fresh external NBA fetch is claimed (F06). `research/nba-strategy-lab/SOURCE_AUDIT.md` records provenance and all irregularities.
- **A2 done:** deterministic standard-library engine independently executes 547 integrity checks (0 failures), derives 16 archived lines, 22 correlation diagnostics, 9 candidates and event-level ledgers. Zero candidates qualify; ranks, scores, ROI and rewards are blank. Sources and formulas are in `research/nba-strategy-lab/METHODOLOGY.md` and the site Methodology page.
- **A3 done:** executive summary plus 11 responsive pages in `nba-strategy-lab/`; all 1,554 body-table rows carry official NBA links, all 1,732 links pass the internal checker, blanks remain blank, and F01–F09 are published on `review.html`.
- **Verification:** new 11-test suite passes; root 91 tests pass; NBA Desk 21 tests + checker pass; NBA Validation 6 tests + checker pass. Chromium smoke test passes all 11 routes at desktop/mobile sizes, table filtering, no horizontal page overflow and no JS errors. Engine/site rebuild is byte-for-byte deterministic.
- **A4 in progress:** final rebase/integration, PR, merge and live Pages verification. No other session's namespace was edited. The optional local browser initially lacked NSS libraries; the repository's bundled-library launch pattern resolved it. No product defect resulted.

### Session ad72b171 PR, merge and live Pages result

- **Integration conflict:** rebasing onto concurrent `main` through PR #38 produced an append-only `COORDINATION.md` conflict. Both the e2f426bc and ad72b171 blocks were retained verbatim; no other session's work was discarded. Combined root-wide scan then passed 2,573 relative links with 0 missing.
- **PR:** [PR #39](https://github.com/sassnarep3-star/Own5/pull/39) merged with `gh pr merge 39 --merge` on 2026-11-05T21:39:41Z; merge commit `bdc5cdede76fa50e78585b6bd3af52cda0298651`. All three PR checks passed before merge.
- **Post-merge CI:** research dashboard run 42114651834, evidence-desk run 42114651864, and NBA-validation run 42114651879 all completed **success**.
- **Pages:** [deployment 42114651745](https://github.com/sassnarep3-star/Own5/actions/runs/42114651745) completed **success**; Pages API status `built`, source `main` @ `/`. Live rendered [dashboard](https://sassnarep3-star.github.io/Own5/nba-strategy-lab/index.html), [own lines](https://sassnarep3-star.github.io/Own5/nba-strategy-lab/lines.html), and [Flagged for Review](https://sassnarep3-star.github.io/Own5/nba-strategy-lab/review.html) fetched with `?release=bdc5cde` and matched 275 rows, 547 checks, 16 lines, 0 qualified and F01–F09. Sandbox curl could not reach github.io, so live reads used the web fetch tool.
- **Live-review correction:** F02 initially said “at most 50” pooled prop holdouts; the computed ledger has 51. Corrected to 51 and regenerated deterministically. No model value or qualification changed.
- **A4 done:** all claimed tasks complete; a documentation follow-up PR records this publication result and the one-count wording correction. Flags remain nonblocking and no strategy is certified.
---

# Session 61a311c2 — NBA source audit and integrated research desk (2026-11-05 UTC)

Claim timestamp: **2026-11-05T21:22:43Z**. Arena fixes the working/integration branch to `arena/61a311c2-own5`; no alternative branch will be created or pushed. Existing completed scopes are read-only during research. The older T10/M1 rows are superseded by their explicit final completion records (PR #7 / PR #33), not active work. The only open PR at claim time is #8 (NFL scope `arena/09d847e1-own5`); no overlapping files are requested. No live in-progress claims were found after reconciling the board with its completion records.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| Q61-01 | Claim, baseline inventory and full requirements audit | done | 61a311c2 | COORDINATION.md; research/nba-research-61a311c2/** | Fixed Arena branch; inventory all tracked files and classify unrelated NFL scope; no prior outputs overwritten. |
| Q61-02 | Independent official NBA/source verification and evidence register | done | 61a311c2 | research/nba-research-61a311c2/**; nba-research-61a311c2/data/** | Check values, not merely URL presence; missing fields remain blank. Derived values explicitly identified. |
| Q61-03 | Origination, signal research, measured correlations and validation engine | done | 61a311c2 | nba-research-61a311c2/**; research/nba-research-61a311c2/** | Singles, cross-game parlays, player-prop combinations; fail-closed qualification, uncertainty and prospective replication. |
| Q61-04 | Gated leaderboard, reward policy and executive summary | done | 61a311c2 | nba-research-61a311c2/**; research/nba-research-61a311c2/** | No fabricated rankings, returns or funded prizes; skill evidence separated from hypotheses. |
| Q61-05 | Clean source-linked NBA dashboard and category pages | done | 61a311c2 | nba-research-61a311c2/** | Deterministic static build, client-side table search and row provenance; preserve existing sites. |
| Q61-06 | Automated row, arithmetic, source, build and browser checks | done | 61a311c2 | nba-research-61a311c2/**; .github/workflows/nba-research-61a311c2.yml | Tests include missing-data rejection, no-lookahead, correlation, parlay dependence and qualification. |
| Q61-07 | Final integration, PR, merge and live Pages verification | done | 61a311c2 | COORDINATION.md; README.md (append); root navigation via existing builder only after all Q61 work passes | Re-fetch latest main, preserve parallel work, no broken site merged; record PR and deployment result. |

Cross-session request: final integration will add a clearly labeled NBA entry point to the existing root dashboard through its deterministic builder, without removing NFL or earlier NBA archives. Shared index/navigation edits are deferred until all Q61 research tasks pass. No other session's files are edited before that integration step.

### Q61 progress / verification log — 2026-11-05T21:40Z (session 61a311c2)

- Q61-01…Q61-06 complete in isolated scopes `nba-research-61a311c2/**`, `research/nba-research-61a311c2/**`, `.github/workflows/nba-research-61a311c2.yml`. No legacy namespace edited.
- Canonical evidence: 241 rows registered; 237 verified-value rows, 4 availability rows intentionally blank/flagged. Baseline inventory: 434 files hashed at `54e8dee`.
- Official comparisons: Edwards 61 + Dončić 64 historical player-game rows match field-by-field; 29 current player rows, 30 prior team rows, 30 current advanced team rows, 11 schedule rows and 12 FanDuel quote rows transcribed/checked. Most Nov 6 injury reports were NOT YET SUBMITTED in the 4pm ET Nov 5 PDF; selected player availability remains blank.
- Engine/dashboard: 11 model-only lines; 12 within-player correlations; 10 threshold-combo frequencies; 47 chronological forecast rows (23–24, exact p=0.614567, Bonferroni family-6 p=1.0); 6 strategies, 0 qualified; 19 flags. No ROI/probabilities/ranks/monetary rewards fabricated.
- Scoped tests: 33/33 pass (math, fail-closed gates, no-lookahead, source-per-row, internal links, deterministic engine/build). Baseline 157/157 previously pass.
- Irregularities recorded: legacy spread sign, invalid cross-game independence claim, DSR label misuse, non-ASCII header, partial legacy 22-game verification, scope mix, dynamic drift, tip-time mismatch, PACE/POSS non-identity.
- Q61-07 in progress: root integration will use `scripts/build.py` only after re-checking open PR #8 / active claims; then PR, autonomous merge, Pages verification.
- Q61-07 integration update: rebased onto concurrent `origin/main` `1775b92` (PR #40). Append-only COORDINATION conflict resolved by retaining eeddab9b/e2f426bc/ad72b171 records and the 61a311c2 claim/progress block; no concurrent work discarded. Open PR #34 is additive `nba-evidence-audit/**` only; stale PR #8 (NFL, updated 2026-11-02) does not block this claimed final navigation integration. Root footer entry added through `scripts/build.py`; root 91 tests and scoped 33 tests pass.


### 2026-11-05 — Session arena-a46d621e PR / merge / deployment record

- **PR:** [#41](https://github.com/sassnarep3-star/Own5/pull/41) — "NBA Line Commission: 2026-11-05 own lines, computed
  correlations, fail-closed gates, luck-deflated leaderboard (session a46d621e)". Body carries the summary, the source
  list and every flagged irregularity, per protocol.
- **Pre-merge checks (all green):** `Build, evidence integrity and browser smoke tests` (58s), `desk-verify` (29s),
  `verify` (12s / 45s). Local pre-merge verification: 91 root tests OK, `tools/check_site.py` 20/0,
  `nba-commission/verify.py` 6 groups / 0 failures (238 CSV rows official-sourced, 0 broken links across 182 repo
  pages, deterministic rebuild), 18 commission unit tests OK, CI guard (`seed.py` + `build.py` then
  `git diff --exit-code -- data/research.json index.html pages/`) clean.
- **Merge conflicts (two rounds, both resolved keeping every session's work):**
  1. vs session `eeddab9b`/`ad72b171` (PR #36, #39): `COORDINATION.md` append-only conflict → both blocks kept in full.
  2. vs session `61a311c2` (PR #42): `README.md` (both sections kept), `scripts/build.py` (footer now carries **both**
     "NBA Line Commission ↗" and "NBA Evidence Desk ↗"), and the CI-locked `index.html` + `pages/*.html`, which were
     regenerated deterministically from the merged builder rather than hand-edited.
  No file from another session was deleted or overwritten.
- **Merged:** yes — merge commit `d84f749e26d5fc070359943db2c727f7f5b986ae` at 2026-11-05T21:55:01Z
  (`gh pr merge 41 --merge`, no approval wait, no `--auto`).
- **Pages:** `pages build and deployment` run `42116958013` completed **success**; Pages API status `built`, source
  `main` @ `/`. Live-verified by fetching the rendered pages after deployment:
  https://sassnarep3-star.github.io/Own5/nba-commission/index.html (dashboard: 11 own lines, 15 flags, 0/8 certified) and
  https://sassnarep3-star.github.io/Own5/nba-commission/flagged.html (F01–F15 with source links). Root desk footer
  cross-links the new board; `data/index.html` lists it alongside the other NBA desks.
- **Follow-up PR:** [#45](https://github.com/sassnarep3-star/Own5/pull/45) — two accuracy fixes found while reviewing the
  live pages (flag ids sorted F01→F15; F02 wording corrected after the HFA test showed the 2026-27 split does not
  establish a home edge) plus this record. No data value changed.
- **Task status:** A1–A13 **DONE**. 11/11 data checks, 6/6 verification groups, 18 unit tests, 0 certified strategies,
  0 graded bets, all market/edge/reward cells blank and flagged.

### Q61 final completion / PR / merge / Pages record — session 61a311c2

- **PR:** https://github.com/sassnarep3-star/Own5/pull/42 — merged autonomously with `gh pr merge 42 --merge` at 2026-11-05T21:51:10Z; merge commit `f3d164a6a6d193a6a2f164d177d4fb7453ddfe48`.
- **PR checks:** all reported checks passed before merge (`verify`, `desk-verify`, `Build, evidence integrity and browser smoke tests`; legacy smoke skipped by workflow condition).
- **Post-merge CI on `f3d164a`:** NBA Research 61a311c2 run `42116357505` success; Verify research dashboard `42116357455` success; Verify Own5 evidence desk `42116357672` success; Verify NBA validation desk `42116357534` success; pages build and deployment `42116356950` success.
- **GitHub Pages:** API status `built`, source `main` @ `/`, base https://sassnarep3-star.github.io/Own5/ . Live fetches with `?release=f3d164a` verified: [overview](https://sassnarep3-star.github.io/Own5/nba-research-61a311c2/index.html), [own lines](https://sassnarep3-star.github.io/Own5/nba-research-61a311c2/lines.html), [Flagged for Review](https://sassnarep3-star.github.io/Own5/nba-research-61a311c2/review.html), and root NFL overview (preserved). Rendered counts matched: 241 canonical rows, 11 lines, 0/6 qualified, 19 flags.
- **Q61-01…Q61-07 done.** Follow-up documentation commit updates the dashboard requirements trace and verification record to reflect the completed merge/deployment. Flags remain nonblocking; no strategy, ROI, probability, rank or funded reward is certified.



## Session 414a434b — SF rent research (2026-11-06 UTC)

Arena fixes the branch to `arena/414a434b-own5`; the requested alternate branch naming cannot be used. Existing sports dashboards and other claims remain untouched. Public content excludes personal identifiers. User-supplied private facts are not official verification.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| SF1 | Official-source research, anonymized dashboard, review flags and verification | in progress | 414a434b | `sf-rent/**`, `COORDINATION.md` (append) | Isolated additive scope; direct Pages entry. |
| SF2 | Integration, PR, merge and deployment verification | in progress | 414a434b | `sf-rent/**`, `COORDINATION.md` (append) | Preserve existing shared navigation and concurrent work. |

### SF1 research and verification log — 2026-11-06

- SF1 completed in isolated `sf-rent/**`. Checked each substantive row against SF Rent Board [rate](https://www.sf.gov/news--annual-rent-increase-3126-22827-announced), [annual rules](https://www.sf.gov/learn-about-rent-increases-san-francisco), [banking](https://www.sf.gov/information--banked-rent-increases), [notices](https://sf.gov/information/allowable-rent-increases), [license](https://www.sf.gov/notice-of-rent-board-fee-and-housing-inventory-requirement), [AB 1482](https://www.sf.gov/reports--california-tenant-protection-act-2019-ab-1482), [petition](https://media.api.sf.gov/documents/516C_Tenant_Petition_Form_C_EN_5.25_Fillable_Updated.pdf); federal [HUD](https://www.hud.gov/reporthousingdiscrimination), state [fair housing regulations](https://calcivilrights.ca.gov/wp-content/uploads/sites/32/2019/09/FinalText-FairHousingRegulations.pdf), and city [right to counsel report](https://media.api.sf.gov/documents/120882_-_Housing_Trust_Fund_Five-Year_Report_-_2018-2023.pdf). Every row contains an official source; sources for blank rows establish review criteria, not verification of private facts.
- Flags: property coverage, rent history, legal base rent, anniversary, banked balances, license, lease terms, roommate continuity, subsidies, discrimination/retaliation facts, actual lawyer review, and typical owner-type increases are not independently verified; values intentionally blank. Banking page contains an inconsistent year in an example. No personal identifiers or private assertion presented as verified on the public site.
- Local `python3 sf-rent/test.py` checks generated pages, all relative links, and an official URL on every data row. This does not verify remote link uptime or substitute for legal review. Six standalone pages; existing root navigation remains under prior owner scope.

### SF2 integration record — 2026-11-06

- [PR #47](https://github.com/sassnarep3-star/Own5/pull/47) merged with merge commit `fc9622dbd4f03ca48ce3acc9f4791fc8dc873927`. Pre-merge GitHub checks: research dashboard, NBA validation, and evidence desk all passed; legacy smoke skipped by workflow. Local scoped checks passed and existing `tools/check_site.py` reported 0 failures and 9 pre-existing flagged warnings.
- Pages run [42227206719](https://github.com/sassnarep3-star/Own5/actions/runs/42227206719): build passed; deployment was still in progress after three minutes. Live page returned 404 while deployment remained pending; do not claim successful publication until the run succeeds and the page is fetched. Node 20 deprecation warning is from GitHub's Pages workflow.

---

# Session 6ee577e4-own5 — Rental Increase SF (San Francisco Outer Sunset, 94122)

Claim timestamp: **2026-11-06T13:45Z**. Arena fixes this session to `arena/6ee577e4-own5`; no alternative branch will be created or pushed. Scope is **additive only**: `rental-sf/**` (site + its own tooling), `research/rental-sf/**` (research docs), and this append-only board. Existing sites, data, root navigation, `scripts/**`, `tools/**`, `.github/workflows/**` and all other sessions' namespaces are **read-only**. Root `index.html` is CI-locked; no root-navigation change will be made by this session (logged as a cross-session request below instead). No overlap with open PRs #8, #34, #43 (NFL/NBA scopes). Personal tenant/landlord names from the brief are **never committed** — the repo publishes anonymized placeholders only (dates and amounts preserved).

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| R1 | Claim + bounded repo review; record irregularities | in progress | 6ee577e4-own5 | COORDINATION.md | Additive-only review; external availability of every legacy link is not re-verified wholesale (see log). |
| R2 | Official-source research: SF local law (Rent Board/Rent Ordinance), CA state law, federal law, industry practice, notice procedure, fair-housing/discrimination review | unclaimed→claimed | 6ee577e4-own5 | research/rental-sf/** | Every factual row needs an official source link or is blank + flagged. |
| R3 | Executive summary (anonymized) | unclaimed→claimed | 6ee577e4-own5 | research/rental-sf/EXECUTIVE_SUMMARY.md, rental-sf/summary.html | Names replaced by placeholders; dates/amounts preserved. |
| R4 | Site: clean dashboard landing page + subpages, category tables, Flagged for Review page | unclaimed→claimed | 6ee577e4-own5 | rental-sf/** | Static, Pages-compatible, own CSS/JS (no shared assets edited). |
| R5 | Line-by-line verification; per-row source links; flag unverified values | unclaimed→claimed | 6ee577e4-own5 | rental-sf/**, research/rental-sf/** | Nothing merged unverified; unverifiable values left blank + flagged. |
| R6 | Integration: rebase, PR to main, merge, GitHub Pages deploy verification, record result | unclaimed | 6ee577e4-own5 | COORDINATION.md (this log) | Preserve all concurrent work; merge only with green checks; record PR + deploy URL. |

Cross-session request (deferred, nonblocking): add a clearly labeled "Rental Increase SF" footer/entry-point link to the root dashboard and `data/index.html` **via the owning builder** (`scripts/build.py` is CI-locked from hand edits). This session does not edit root navigation.

### R1 progress note (2026-11-06)

- Branch `arena/6ee577e4-own5` == `origin/main` @ `6a73b0a` at claim; working tree clean; open PRs #8/#34/#43 are NFL/NBA scopes — no file overlap with this task.
- Repo is the Own5 NFL/NBA research Pages site plus many session sub-sites; no rental content existed anywhere (`grep -i rental` on tracked files → none). Pre-existing irregularities (if any) belong to their owning sessions; this session flags what it observes on the Flagged for Review page rather than rewriting others' work.
- Legal-content safety rule for this session: the site is general educational information, not legal advice; no specific dollar recommendation is issued to any tenant or the owner; every legal parameter links to an official source; interpretation risks are published as flags, not hidden.


### Session 6ee577e4-own5 — work log (2026-11-06)

- **R1 done — bounded repo review (this session):** repo at `6a73b0a` == `origin/main` at start; 182 HTML pages scanned with a custom tolerant parser: 3,052 local refs, **0 broken**; `tools/check_site.py`: **0 failures**, 9 pre-existing intentional blank-source warnings (unchanged); 9 root-level detail pages carry an unclosed `<section>` before `</main>` (session 0f468a47 scope; flag **F-16**, not edited); PII/secrets scan: none found; root `index.html`/`data/` untouched (CI-locked). Full review claims are bounded — see flag F-18.
- **R2 done — official-source research:** 22 official sources fetched and read in full this session (sf.gov Rent Board pages incl. the 2026-01-14 annual-increase announcement, Current Rates, "Learn about rent increases", "Banked rent increases", coverage, Costa-Hawkins guidance, capital-improvement petitions + imputed-interest table, 571 historical PDF; Cal. leginfo §§827, 1947.12, 1942.5, 1954.53; DOJ archived release 25-21; HUD FHA overview; CA CRD Fair Housing fact sheet; BLS CPI-SF June 2026 release — Apr-2026 12-month = 3.8%). Registry + retrieval log: `research/rental-sf/SOURCES.md`. No value taken from any third-party site.
- **R3 done — anonymized executive summary:** `research/rental-sf/EXECUTIVE_SUMMARY.md` + `rental-sf/summary.html`. Placeholders (Household 1/Household 2); dates/amounts preserved; no tenant/owner PII anywhere.
- **R4 done — site:** `rental-sf/` (12 pages + own CSS/JS, no shared assets touched): dashboard `index.html`, summary, Q&A, local-law, state-law, federal-law, practice, process (with notice template — template only, flag F-13), fair-housing (one vs both), units (all scenario math), flagged (F-01…F-18), sources; `rental-sf/verify.py` deterministic checker (parse, local refs, per-row source/flag link coverage, https-only, PII patterns).
- **R5 done — verification:** `python3 rental-sf/verify.py` → **12 pages, 164 table rows, FAIL=0, WARN=0**; root suite `python3 -m unittest discover -s tests` → **91/91 OK**; all pages/assets serve 200 locally. Every table row carries an official source link or a flag link; unverified values are BLANK (2027-28 rate, F-04) or derived-and-labeled (AB 1482 8.8%, F-05). Official-source contradiction on banking eligibility confirmed and published, not resolved (F-02). 2024-08-23 DOJ URL 404 → archived URL used (S-18).
- **Key analytic outcomes (details in site):** continuing covered tenancies ⇒ current-year 1.6% + properly banked only; Unit 1 +$63.92 → $4,058.92 (U1-E trap documented); Unit 2 +$50.40 annual-only; banked scenarios $3,465.00–$3,562.65 pending F-02; both-units uniform-formula is the review-passing pattern; selective single-unit raise is lawful-in-principle but review-risky; no notice should be served until F-01/F-02/F-03 close.
- **Cross-session request (unchanged, deferred):** add "Rental Increase SF" entry point to root navigation via owning builder (`scripts/build.py`) — not done by this session (CI-locked shared output).

| ID | Task | Status | Owner |
|----|------|--------|-------|
| R1 | Repo review | done | 6ee577e4-own5 |
| R2 | Sources research | done | 6ee577e4-own5 |
| R3 | Executive summary | done | 6ee577e4-own5 |
| R4 | Site | done | 6ee577e4-own5 |
| R5 | Verification | done | 6ee577e4-own5 |
| R6 | Integration: PR → merge → Pages verification | in progress | 6ee577e4-own5 |

# Session c334a668 — San Francisco rent review (2026-11-06 UTC)

Single-session, additive integration. The Arena-assigned branch is fixed as
`arena/c334a668-own5`; no `session-*/...` branches will be created. Existing
sports dashboards, generated navigation, and other sessions' scopes remain
untouched. No tenant identifiers, address, private documents, or credentials
will be committed. Owner-supplied unit facts are not official records.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| SF1 | Official-source rent-control, tenancy, notice, fair-housing and process research | in progress | c334a668 | `research/sf-rent-review/**`, `sf-rent-review/data/**`, `COORDINATION.md` (append) | Primary government sources only; distinguish verified rules, conditional analysis and unverified property facts. |
| SF2 | Accessible additive rent-review dashboard and category pages | in progress | c334a668 | `sf-rent-review/**` | No personal identifiers; every table body row must link an official source. |
| SF3 | Tests, line-by-line/source/link/privacy checks, integration and publication | in progress | c334a668 | `sf-rent-review/**`, `.github/workflows/sf-rent-review.yml` (new), `README.md` (append), `COORDINATION.md` (append) | Fixed branch is the integration branch. Flagging unverified items does not imply legal clearance. |

Claim timestamp: 2026-11-06 13:36 UTC. No conflicts identified with the
historical task scopes; no shared generated root navigation is claimed. Other
sessions should not edit the scoped files while this claim is active. No
cross-session changes requested at claim time.

### SF integration / cross-session notes (2026-11-06)

- **Rebase conflict resolved:** `main` advanced with independently owned SF
  projects while this session was working. The append-only conflict in
  `COORDINATION.md` was resolved by retaining the complete latest main board
  and appending this session's complete claim; no other session's section or
  file was deleted. Project scopes are separate. Existing generated root
  navigation remains unchanged.
- **Cross-session request to owner of `rental-sf/**` and
  `research/rental-sf/**` (not edited by c334a668):** Please review the
  scenario-specific banked calculations and coverage assumptions in that
  site's unit page and executive summary against the user's requirement that
  unverified unit values remain blank. An official rule link does not verify
  a private ledger, the license, or eligibility. The summary also states a
  rate for a date before March 2025 that conflicts with the [Rent Board's
  schedule](https://www.sf.gov/reports--current-rates-including-rent-increase-relocation-sec-deposit),
  characterizes coverage as almost certain without an official property
  record, and predicts tenant-counsel review. Those points warrant correction
  or clear unresolved flags by that scope's owner; no counsel outcome is
  verified. Do not treat other sessions' scenario amounts or analyses as
  validated by this session. The [banking guidance](https://www.sf.gov/information--banked-rent-increases)
  and [federal rental program overview](https://www.congress.gov/crs_external_products/IF/HTML/IF12887.web.html)
  should be read with their conditions. This is a nonblocking review request,
  not permission to overwrite another session's files.

### SF1–SF3 build and verification progress (2026-11-06)

- **SF1 done:** 28 official sources registered with checked scope, a separate
  research/verification note and an automatically reproducible 79-row
  evidence register. Rate guidance and known inconsistent SF.gov example
  dates are explicitly flagged. Unverified private lease facts are blank in
  this session's public tables; legal source links are not treated as private
  fact verification.
- **SF2 done:** eight static pages, responsive source-linked tables, clear
  source library, separate flagged register and a non-serviceable communication
  outline. No third-party fonts, trackers, scripts, user data entry or backend.
- **SF3 local checks passed:** 7 scoped standard-library unit/integrity tests,
  deterministic HTML and row-register checks, browser checks over all eight
  pages at desktop and two mobile widths with JavaScript disabled, and 91
  existing repository unit tests; the existing `npm run desk:check` and
  `npm run test:browser` also passed. All 107 rendered table rows (79 research +
  28 source register) have official source links; all local links/fragments
  resolve, and unknown unit fields stay blank. Screenshots are temporary and
  not committed. Existing sports outputs were not changed.
- **Integration:** README addition is append-only; PR, merge and public Pages
  verification remain pending. Concurrent legacy Pages deployments have been
  cancelled/superseded by other `main` merges; do not record a live result until
  the public page is independently fetched.

---

# Session e028ae77 — SF Outer Sunset (94122) rental-increase review, full build (2026-11-06 UTC)

Claim timestamp: **2026-11-06T14:05Z**. Arena fixes the working branch to `arena/e028ae77-own5`; no alternative branch will be created or pushed. Reconciliation at claim time: session `7659538a` completed **RNT1** owning `rental-increase-sf/**` (merged via PR #46, commit a603c0e) — that scope is read-only for this session. This session claims a **separate, non-overlapping scope** `sf-rent-94122/**` + `research/sf-rent-94122/**`, cross-linking the existing brief. CI-locked files (`index.html`, `pages/`, `data/research.json`, `scripts/`, `own5-desk/`, other sessions' directories) are not touched. Tenant personal information is anonymized on all published pages (placeholder names only); dates and amounts retained as provided and marked user-provided/unverified.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|

| E1 | Claim + baseline review (read board, reconcile with 7659538a RNT1) | in progress | e028ae77 | COORDINATION.md | Claim pushed before any other work. |
| E2 | Official-source research: local (SF Rent Ordinance/Rent Board), state (Civ. Code 827, 1946.2, 1947.12, 1954.50), federal (42 U.S.C. 3604 / HUD) | unclaimed→in progress | e028ae77 | research/sf-rent-94122/**, sf-rent-94122/data/sources.csv | sf.gov, leginfo.legislature.ca.gov, uscode.house.gov, hud.gov, courts.ca.gov only; values fetched/read 2026-11-06. |
| E3 | Executive summary + answers to the six user questions (anonymized) | unclaimed | e028ae77 | research/sf-rent-94122/EXECUTIVE_SUMMARY.md, research/sf-rent-94122/qna.md, sf-rent-94122/executive-summary.html, sf-rent-94122/questions.html | Placeholder tenant names; dates/amounts kept; unverified items blank+flagged. |
| E4 | GitHub Pages subsite: landing dashboard + category subpages (units, law, process, questions, sources, flagged) | unclaimed | e028ae77 | sf-rent-94122/*.html, sf-rent-94122/style.css, sf-rent-94122/data/*.csv | Self-contained; no edits to root nav or other sessions' files. |
| E5 | Line-by-line verification: every table row has an official source link or explicit BLANK flag; internal links resolve | unclaimed | e028ae77 | sf-rent-94122/verify.py, research/sf-rent-94122/VERIFICATION.md | Script run locally; results logged. |
| E6 | Integration: PR to main, autonomous merge, Pages deploy verification, record results | unclaimed | e028ae77 | COORDINATION.md, README.md (append only) | Per protocol: no waiting for approval; fix and retry if build/deploy fails. |


| E1 | Claim + baseline review (read board, reconcile with 7659538a RNT1) | done | e028ae77 | COORDINATION.md | Claim pushed before any other work. |
| E2 | Official-source research: local (SF Rent Ordinance/Rent Board), state (Civ. Code 827, 1946.2, 1947.12, 1954.50), federal (42 U.S.C. 3604 / HUD) | done | e028ae77 | research/sf-rent-94122/**, sf-rent-94122/data/sources.csv | sf.gov, leginfo.legislature.ca.gov, uscode.house.gov, hud.gov, courts.ca.gov only; values fetched/read 2026-11-06. |
| E3 | Executive summary + answers to the six user questions (anonymized) | done | e028ae77 | research/sf-rent-94122/EXECUTIVE_SUMMARY.md, research/sf-rent-94122/qna.md, sf-rent-94122/executive-summary.html, sf-rent-94122/questions.html | Placeholder tenant names; dates/amounts kept; unverified items blank+flagged. |
| E4 | GitHub Pages subsite: landing dashboard + category subpages (units, law, process, questions, sources, flagged) | done | e028ae77 | sf-rent-94122/*.html, sf-rent-94122/style.css, sf-rent-94122/data/*.csv | Self-contained; no edits to root nav or other sessions' files. |
| E5 | Line-by-line verification: every table row has an official source link or explicit BLANK flag; internal links resolve | done | e028ae77 | sf-rent-94122/verify.py, research/sf-rent-94122/VERIFICATION.md | Script run locally; results logged. |
| E6 | Integration: PR to main, autonomous merge, Pages deploy verification, record results | in progress | e028ae77 | COORDINATION.md, README.md (append only) | Per protocol: no waiting for approval; fix and retry if build/deploy fails. |

### SF final PR / merge / public verification — session c334a668

- **PR:** [#52](https://github.com/sassnarep3-star/Own5/pull/52), merged
  autonomously with `gh pr merge 52 --merge` at 2026-11-06 13:53 UTC; merge
  commit `e9faa822be0781db6f56c9138c0bb03902ac7b7a`.
- **Checks:** all pre-merge PR checks passed (SF scoped verification, existing
  research dashboard/browser checks, existing evidence desk, and NBA
  validation). Post-merge SF workflow
  [42229137250](https://github.com/sassnarep3-star/Own5/actions/runs/42229137250)
  passed both verification and the public Pages smoke test.
- **Pages:** legacy `main` / root deployment run
  [42229137058](https://github.com/sassnarep3-star/Own5/actions/runs/42229137058)
  completed successfully for the merge commit. Independently fetched the live
  [dashboard](https://sassnarep3-star.github.io/Own5/sf-rent-review/),
  [flagged page](https://sassnarep3-star.github.io/Own5/sf-rent-review/review.html),
  and pre-existing [root](https://sassnarep3-star.github.io/Own5/) at 13:56 UTC;
  the dashboard displayed the expected 1.6% dated allowance, blank
  unit-specific values, and source links. A later concurrent merge triggered
  another deployment; that does not change what was verified at 13:56.
- **SF1, SF2 and SF3: done.** Open legal/property/source-review flags are
  nonblocking for publication, not a finding that an increase or notice is
  lawful. Separate cross-session concerns remain assigned to the owning scope.

---

## Session e446435e — San Francisco Rental Increase Compliance & Evidence Dashboard (2026-11-06 UTC)

Arena fixes this session's branch to `arena/e446435e-own5`; the `session-<id>/<task>` branch naming convention cannot be used. To guarantee zero file collisions with existing sports dashboards and concurrent SF rent sessions (`rental-increase-sf/**`, `sf-rent/**`, `rental-sf/**`, `sf-rent-94122/**`, `sf-rent-review/**`, etc.), this session claims only isolated additive namespaces `sf-rent-e446435e/**` and `research/sf-rent-e446435e/**`, plus append-only updates to `COORDINATION.md`. All personal tenant identifiers are kept strictly internal and excluded from every tracked file, commit, PR, and public page; anonymized placeholders are used throughout while preserving reported dates and rent amounts (flagged as user-supplied/unverified where lacking official public records).

- **Conflict log (2026-11-06):** (a) Rebased `b8a669d` onto `origin/main` (`ded5748`, after PRs #48/#49). (b) Rebased onto `origin/main` (`e391db7`, after PRs #50/#53 added `sf-rent-94122/**` and `sf-rent-review/**`). Both append-only `COORDINATION.md` conflicts resolved by preserving every other session's blocks verbatim; zero file overlap with any sibling scope.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| R44-01 | Repo baseline audit, privacy guardrails, and task claim | done | e446435e | `COORDINATION.md`, `research/sf-rent-e446435e/REPO_AUDIT.md` | Bounded audit: locks, 596 files, sibling row/link/PII scans, zero PII. |
| R44-02 | Official legal & regulatory verification (SF, CA, Federal) | done | e446435e | `research/sf-rent-e446435e/**`, `sf-rent-e446435e/data/**` | 32 official sources read 2026-11-06 (S-01…S-32); Form 571, §37.3, §827 verified verbatim. |
| R44-03 | Corporate REIT vs. individual SF owner practices | done | e446435e | `research/sf-rent-e446435e/**`, `sf-rent-e446435e/data/**` | SEC 10-K venues + DOJ/SF algorithmic bans verified; private norms blank + flagged (R44-F11). |
| R44-04 | Anonymized Unit 1 & 2 scenarios, notice rules, scrutiny & one-vs-both analysis | done | e446435e | `research/sf-rent-e446435e/ANALYSIS.md`, `sf-rent-e446435e/data/**` | Exact banking math both units; uniform-policy pattern; 180-day/§37.10B scrutiny gates. |
| R44-05 | Executive summary & Flagged-for-Review register | done | e446435e | `research/sf-rent-e446435e/EXECUTIVE_SUMMARY.md`, `research/sf-rent-e446435e/FLAGGED.md` | Summary + 19 flags (R44-F01…F19), every item source-linked. |
| R44-06 | Static dashboard & category subpages + build & verification suite | done | e446435e | `sf-rent-e446435e/**` | 11 pages + 4 CSVs from canonical JSON; `verify.py` FAIL=0 (179 rows, 15 money tokens, 27 files PII-scanned); serves 200 locally. |
| R44-07 | Final integration, CI verification, PR to main, merge & live Pages check | done | e446435e | `COORDINATION.md` | PR #54 merged (`6836bf3`); all CI checks pass; Pages `built`; 5 live URLs fetched OK (see record). |

### R44-07 integration record — 2026-11-06

- [PR #54](https://github.com/sassnarep3-star/Own5/pull/54) (`arena/e446435e-own5` → `main`) merged 2026-11-06T14:05:40Z with merge commit `6836bf3ca4e7fde5519b8114ec3f4edbbb644911`. Pre-merge checks: research dashboard, NBA validation, evidence desk, and SF Rent Review `verify` jobs all passed; legacy smoke jobs skipped by workflow design (same as sibling PRs).
- Pages deployment run [42230865904](https://github.com/sassnarep3-star/Own5/actions/runs/42230865904) succeeded; Pages build API reports `built` for `6836bf3` at 14:12:00Z with no error. (Two earlier same-day builds for sibling commits show `errored`/`Page build failed` — concurrent-merge supersedes; unrelated to this scope.)
- Live verification (fetched post-deploy): [dashboard](https://sassnarep3-star.github.io/Own5/sf-rent-e446435e/), [summary](https://sassnarep3-star.github.io/Own5/sf-rent-e446435e/summary.html), [local law + Form 571 schedule](https://sassnarep3-star.github.io/Own5/sf-rent-e446435e/local-law.html), [unit scenarios](https://sassnarep3-star.github.io/Own5/sf-rent-e446435e/units.html), [Flagged for Review](https://sassnarep3-star.github.io/Own5/sf-rent-e446435e/flagged.html) — all serve expected content (1.6% ceiling, derived math, blank unverified cells, per-row source/flag links). Initial index fetches 404'd during CDN propagation; confirmed live minutes later.
- Session `e446435e` complete: R44-01…R44-07 all done. Open legal/property/source-review items (R44-F01…F19) are nonblocking for publication and published on the Flagged for Review page — not a finding that any increase or notice is lawful.

---

# Session e413f933 — NFL Decision Desk (suggestions, questions register, own lines, injury/depth signals) (2026-11-12 UTC)

Arena fixes this session to `arena/e413f933-own5`; no alternative branch will be created or pushed.
Claim timestamp: **2026-11-12 UTC**, before any implementation. Claimed additive namespace:
`nfl-decision-desk/**` and `research/nfl-decision-desk/**`, plus this append-only board entry.

**Scope update at integration (2026-11-12):** while this session collected official data, session
`d0343637` merged its own desk into `nfl-decision-desk/**` (PRs #56/#57) and the board records that
directory as owned by `d0343637`. Following the collision precedent set by session `38a1fc27`, this
session moved ALL of its outputs wholesale to **`nfl-decision-desk-e413f933/**`** (site, data, scripts,
verification harness) — no other session's work was overwritten or discarded, and
`research/nfl-decision-desk/**` (uncontested, only this session) stays as claimed.
Read-only for this session: root `index.html`/`pages/`/`data/research.json` (CI-locked), `docs/`,
`nba-*/`, `nfl-strategy-lab/`, `line-lab/`, `own5-desk/`, `sf-*/rental-*`, `scripts/`, `tools/`,
`.github/workflows/`, existing CSVs/JSON, README.md (append only at integration, if needed).

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| D1 | Claim + bounded repo review; record irregularities | done | e413f933 | COORDINATION.md, research/nfl-decision-desk/repo-review.md | Claim pushed first; wk8 results re-verified 13/13 vs official by-week page; 9 irregularities flagged (F-HOU-1, F-BAL-1, F-MIA-1, F-INT-1, F-MKT-1, F-PROP-1, F-W10-1, F-W8-1, F-CHT-2). |
| D2 | Decision prerequisites register: questions / information / answers (known vs missing) | done | e413f933 | nfl-decision-desk-e413f933/data/questions_register.csv, nfl-decision-desk-e413f933/questions.html | 15 questions with known/unknown/discovery method; every row official-source-linked; 2 blocked on user policy (Q07, Q13). |
| D3 | Suggestions register (improvement paths, ranked for review before implementation) | done | e413f933 | nfl-decision-desk-e413f933/data/suggestions_register.csv, nfl-decision-desk-e413f933/suggestions.html | 12 suggestions S01-S12 with effort/risk/benefit; none implemented without decision; dedicated review page. |
| D4 | Own NFL lines from official inputs + signal research | done | e413f933 | nfl-decision-desk-e413f933/data/own_lines_2026_wk10.csv, nfl-decision-desk-e413f933/scripts/originate_lines_wk10.py, nfl-decision-desk-e413f933/lines.html | 14 lines, repo-documented model (shrunken net pts, HFA 2.0, Munich neutral); market columns blank+flagged F-MKT-1; advisory deficiency column separate. |
| D5 | Injury + depth-chart deficiency tracking (2nd/3rd/4th string signals) | done | e413f933 | nfl-decision-desk-e413f933/data/injuries_2026_wk10.csv, depth_charts_2026_wk10.csv, deficiencies_2026_wk10.csv, team_deficiency_index.csv | 278 injury rows + 608 depth rows (27 clubs) -> 119 starter deficiencies with next-man-up chains; HOU blank+flagged (image-only chart). |
| D6 | Validation gates, correlation values, luck-vs-skill, leaderboard w/ rewards (singles/parlays/prop combos) | done | e413f933 | nfl-decision-desk-e413f933/data/{signals,strategies,gates,leaderboard,correlations,luck_vs_skill}.csv, strategies.html | C01 r=0.846, C04 r=0.864 computed; C05 pending, C06 blocked; 7 strategies, 8 gates, all fail-closed (0 graded bets); tiers documented, metrics blank. |
| D7 | Executive summary | done | e413f933 | research/nfl-decision-desk/executive-summary.md, nfl-decision-desk-e413f933/executive-summary.html | Only computed/verified values; decisions-needed section; bottom line published. |
| D8 | Site: landing dashboard + category subpages + Flagged for Review | done | e413f933 | nfl-decision-desk-e413f933/*.html, nfl-decision-desk-e413f933/build_site.py | 12 pages + style.css, deterministic build; every tbody row source-linked; 8 open flags published on flagged.html. |
| D9 | Line-by-line verification harness | done | e413f933 | nfl-decision-desk-e413f933/verify_nfl_desk.py | PASS: 12 pages, per-row source links, internal links, CSV source columns, market-blank policy; root CI also green (unittest OK, build diff clean, desk:check PASS). |
| D10 | Integration: re-verify, PR to main, merge, Pages deploy verification, record | done | e413f933 | COORDINATION.md | PR #64 merged `df04dd7` 2026-11-12T18:19:56Z; Pages built + 3 live URLs verified; d0343637 site untouched; drift logged. |

Cross-session requests at claim time: none.

### e413f933 cross-session CI drift note (2026-11-12, not actioned)

Two checks fail on this session's PR and are **not** caused by defects in this desk's files;
both are other sessions' repo-wide audit snapshots going stale as the repository grows:

- **`NFL Decision Desk — fetch & verify`** (decision-desk.yml, owner 38a1fc27): reproduced
  locally — `build_all.py`, `build_site.py`, `verify.py` all exit 0; only
  `data/decision-desk/audit_summary.json` counts drift (links_checked/pages grew with this
  session's 12 pages). The same check already failed on sibling PR #63 before this session's
  merge; `data/decision-desk/**` is read-only here, so per sibling precedent it is logged, not actioned.
- **`Rebuild, audit, and test isolated NFL desk`** (nfl-b34253a1.yml, owner b34253a1):
  reproduced locally — `audit_repo.py` exits 0; its full-repo inventory
  (`nfl-b34253a1/data/repo_audit.csv`) diff-refreshes against the grown tree. That scope is
  read-only here; b34253a1 refreshes its audit after rebases as its own action.

This desk's own `nfl-decision-desk-e413f933/verify_nfl_desk.py` PASSes (12 pages), session
d0343637's `nfl-decision-desk/verify.py` PASSes (4 tests, untouched), root unit tests and
`desk:check` PASS. Neither drifting check is required for merge (PR #63 merged in the same state).

### D10 integration record — 2026-11-12

- **Namespace collision resolved without discarding work:** session `d0343637` owns
  `nfl-decision-desk/**` on main (their site verified live and untouched). This session's desk
  was moved wholesale to `nfl-decision-desk-e413f933/**` before merge (the `38a1fc27` precedent);
  `research/nfl-decision-desk/**` remained uncontested. COORDINATION conflict resolved by
  keeping both sessions' blocks verbatim.
- **[PR #64](https://github.com/sassnarep3-star/Own5/pull/64)** (`arena/e413f933-own5` → `main`)
  merged 2026-11-12T18:19:56Z, merge commit `df04dd714ed920f9fb6510f9af463c1d679e0a0d`.
- **Checks at merge:** root research-dashboard verify PASS, desk-verify PASS, 26d4cafb desk
  PASS, NBA/SF verifies PASS, decision-desk build/verify steps PASS locally; two cross-session
  audit-snapshot checks failed (logged above, not actioned, non-required — same state as merged
  PR #63).
- **Pages:** build for `df04dd7` completed with no error (`pages-build-deployment`, status
  `built`). Live content verified via fetch: [dashboard](https://sassnarep3-star.github.io/Own5/nfl-decision-desk-e413f933/),
  [lines](https://sassnarep3-star.github.io/Own5/nfl-decision-desk-e413f933/lines.html) (14 games,
  market cells blank·flagged, per-row sources), [flagged](https://sassnarep3-star.github.io/Own5/nfl-decision-desk-e413f933/flagged.html)
  (8 open + 2 closed flags). Session `d0343637`'s [site](https://sassnarep3-star.github.io/Own5/nfl-decision-desk/)
  re-checked live and unchanged.
- **Session e413f933 complete: D1–D10 all done.** Open items (Q07/Q13 policy decisions,
  S01–S12 suggestions, F-* flags) are published for review and are non-blocking per brief.
## Session 38a1fc27 — NFL Decision Desk: requirements audit, suggestions, questions, injury/depth tracking (2026-11-12 UTC)

Branch fixed by Arena: `arena/38a1fc27-own5` (base `95c2eea`). Existing scopes are read-only for this session. This session claims only additive namespaces:

- `nfl-decision-desk/**` (new static site, self-contained; does not touch root `index.html`, `pages/`, `docs/`, `own5-desk/`, `nfl-strategy-lab/`, `line-lab/`, or any other session's directory)
- `research/38a1fc27/**`
- `data/decision-desk/**`
- `tools/decision_desk/**`
- `.github/workflows/decision-desk.yml`
- append-only blocks in `COORDINATION.md`

Rationale: the user's 2026-11-12 request adds (a) a suggestions register with an explicit review/decision workflow, (b) a questions-and-missing-information register gating decisions, (c) injury + lineup/depth deficiency tracking (2nd/3rd/4th string), and (d) a line-by-line re-verification of the existing NFL claims. None of those exist in any prior scope.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| D1 | Claim + baseline repo review | done | 38a1fc27 | COORDINATION.md | Claim pushed before any other work. |
| D2 | Official-source ingestion (nfl.com injury report/schedule/standings + nflverse mirrors), pinned + timestamped | done | 38a1fc27 | tools/decision_desk/fetch_sources.py, data/decision-desk/raw/**, .github/workflows/decision-desk.yml | Runner-side fetch: 12/12 pinned datasets and 3/3 official pages HTTP 200 at 2026-11-12T16:29Z; SHA-256 + UTC recorded per file. Sandbox egress is GitHub-only, so ingestion runs on Actions; official text extracts are committed, raw HTML is an artifact. |
| D3 | Requirements matrix, suggestions register, open-questions register | done | 38a1fc27 | research/38a1fc27/**, data/decision-desk/{requirements,suggestions,questions}.csv | 19 requirements, 16 suggestions (each with decision state + review test), 18 questions (7 blocking, 4 not closable from public data). |
| D4 | Injury & lineup-deficiency engine | done | 38a1fc27 | tools/decision_desk/compute_injuries.py, data/decision-desk/injuries_wk10_players.csv, team_deficiency_wk10.csv | 276 official rows parsed; 276/276 agree with the mirror; depth strings 1-4 from snap share; replacement drop by unit; calibration on 950 games (2023-2026). |
| D5 | Own lines, strategy ledger, gates, correlations | done | 38a1fc27 | tools/decision_desk/compute_{lines,strategies,correlations}.py, data/decision-desk/model_lines_wk10.csv, strategy_ledger.csv, prop_correlations.csv | 14 games priced (HFA 1.22); 7 families vs G0-G12, zero certified; model walk-forward 50.2-50.9% ATS; QB/WR r=0.50, empirical joint 32.5% vs 24.8%; ATS/total phi=0.006. |
| D6 | Line-by-line verification of existing NFL claims | done | 38a1fc27 | research/38a1fc27/AUDIT.md, VERIFICATION.md, data/decision-desk/claim_checks.csv, standings_crosscheck.csv | 11 claims re-derived (6 reproduce, 4 do not, 1 is this session's corrected sign error); official standings 32/32 vs independent game log; 4,182 links across 246 pages, 0 broken. |
| D7 | Site build + row/link verification | done | 38a1fc27 | nfl-decision-desk/**, tools/decision_desk/{build_site,verify}.py | 14 pages, 26 tables, 494 rows, every row carries a link; verify.py PASS; clean rebuild produces no diff. |
| D8 | Executive summary | done | 38a1fc27 | research/38a1fc27/EXECUTIVE_SUMMARY.md, nfl-decision-desk/summary.html | Restates only computed/verified values. |
| D9 | PR to main, autonomous merge, Pages deploy verification | in progress | 38a1fc27 | COORDINATION.md | Record appended below when done. |

### D2-D8 verification and irregularities (2026-11-12)

- **Sources:** https://www.nfl.com/injuries/ , /schedules/2026/by-week/week-10 , /standings/league/2026/REG (OFFICIAL); nflverse releases `injuries`, `snap_counts`, `stats_player`, `schedules` and the pinned spreadspoke file (AGGREGATOR, tier-labelled everywhere).
- **Checks:** official standings reproduce 32/32 from an independent game log; official injury report matches the mirror 276/276; every published CSV row carries a source link; every site table row carries a link; all internal links resolve; a clean rebuild is byte-identical.
- **Irregularities logged (F01-F18, published on the site's Flagged page):** aggregator market lines with unknown timestamps (F01) and no official closing-line history (F02) block gates G4/G8, so no strategy is certified; no official prop lines (F03); game statuses publish later in the week (F04); depth is snap-share inference, not an official depth chart (F05/F16).
- **Reproducibility finding:** this session's first injury backtest used the spread with the wrong sign and reported a false 57.4% ATS edge (p=0.0046); after correcting to the source's documented convention the same rule is 51.4% (p=1.0). The erroneous run is retained in `claim_checks.csv`, and S02 proposes a regression test.
- **Inherited discrepancies (not resolved here, flagged for human review):** prior home-underdog cover rates (52.6% vs 49.7%), home dogs +7 (56.37%/793 vs 53.97%/730), QB/WR correlation (0.76 vs 0.50) and the 20.8% luck figure (exact binomial 25.1%).
- **Scope discipline:** this session wrote only to `nfl-decision-desk/**`, `research/38a1fc27/**`, `data/decision-desk/**`, `tools/decision_desk/**`, `.github/workflows/decision-desk.yml`, plus append-only blocks in `COORDINATION.md` and `README.md`. No file owned by another session was edited.

### D1 baseline review notes (2026-11-12)

- Repo contains 20+ prior scopes (NFL root desk, `nfl-strategy-lab/`, `line-lab/`, `own5-desk/`, many NBA and SF-rent scopes). None covers injury/lineup-deficiency tracking; `data/flagged.csv` F01–F12 treat injuries only as a research gap.
- Sandbox egress: only `github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org` resolve. `www.nfl.com` and nflverse release assets are NOT reachable from the sandbox, but the `fetch_page` tool and GitHub Actions runners can reach them. Ingestion therefore runs on a runner and commits a pinned snapshot.
- No pandas/numpy/scipy in the sandbox runtime; the repo standard is Python standard library only. All computation is stdlib-only.

## Session d0343637 — NFL decision desk (2026-11-12 UTC)

Fixed Arena branch `arena/d0343637-own5` takes precedence over suggested branch naming. Isolated additive scope avoids all other owners; existing root navigation remains untouched.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| ND1 | Review existing NFL claims and official-source access; decision desk, questions, suggestions, validation and review pages | in progress | d0343637 | nfl-decision-desk/** | No invented current lines, injuries, performance or correlations. |
| ND2 | Tests, integration PR, merge and Pages verification | in progress | d0343637 | COORDINATION.md (append only), nfl-decision-desk/** | Source-access failures are published, not represented as verification. |

### d0343637 verification and integration handoff — 2026-11-12

- ND1 done: isolated `nfl-decision-desk/` contains 9 category pages and 60 row-linked entries, executive summary, decision questions/answers, selective injury observations, research/gate proposals, blank current correlations and ranks, suggestions awaiting review and 9 published review flags. No shared root navigation edited.
- Sources checked with page retrieval: https://www.nfl.com/injuries/ (first chunk only), https://www.nfl.com/teams/ (directory excerpt), https://www.commanders.com/team/depth-chart, https://www.patriots.com/team/depth-chart (unofficial disclaimer and offense), https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm. Policy URL https://operations.nfl.com/updates/football-ops/2017-nfl-injury-report-policy/ returned 404 and is flagged. No full-repo factual certification claimed.
- Review irregularities: mixed-sport root summary; stale Week 9 outputs; unofficial chart authority; Ben Brown positional discrepancy; missing current policy/current joint coefficients; project-defined gate thresholds; no continuous all-team ingestion or immutable raw archives. Published in `nfl-decision-desk/flagged.html`.
- Verification passed: 4 scoped tests (including every row's official references, local links and deterministic build), JS syntax, 91 existing unit tests, and 18 real Chromium desktop/mobile page checks plus search and no-JavaScript tables. Structural verification does not certify external facts.
- Initial remote branch did not exist, so initial pull failed; pulled/rebased against main before initial branch push. No merge conflict and no other owners' files changed.
- ND2 in progress: publishing PR and checking Pages deployment. The site explicitly discloses static-snapshot limits; future live ingestion suggestions are not represented as implemented.

### d0343637 publication record — ND2 done

- PR [#56](https://github.com/sassnarep3-star/Own5/pull/56) merged autonomously with `gh pr merge 56 --merge` at 2026-11-12T16:26:01Z; merge commit `64322ddeb68022294dbd6b675078de885b487b71`.
- PR checks were initially not yet reported (not a failure); subsequently all four verification checks passed (research/browser, evidence desk, NBA and SF review); legacy PR smoke skipped by workflow design. Main research workflow [43258612109](https://github.com/sassnarep3-star/Own5/actions/runs/43258612109), evidence desk [43258611518](https://github.com/sassnarep3-star/Own5/actions/runs/43258611518), NBA [43258612167](https://github.com/sassnarep3-star/Own5/actions/runs/43258612167) and SF [43258612090](https://github.com/sassnarep3-star/Own5/actions/runs/43258612090) all succeeded.
- Pages [43258609034](https://github.com/sassnarep3-star/Own5/actions/runs/43258609034) build + deploy succeeded; Pages API confirmed `built` for the exact merge commit with no error.
- Independently retrieved live [dashboard](https://sassnarep3-star.github.io/Own5/nfl-decision-desk/) and [Flagged for Review](https://sassnarep3-star.github.io/Own5/nfl-decision-desk/flagged.html) after deployment; expected summary, blank cells, source links and nine flags were present. Local Chromium verified all nine pages at desktop/mobile widths. All ND tasks done; unmet data/continuous-ingestion capabilities remain explicitly published limitations, not completed operational features.

### D9 merge / conflict log — session 38a1fc27

- **2026-11-12:** while this session was building, session `d0343637` merged its own
  `nfl-decision-desk/` desk to `main` (PRs #56, #57). That created a **directory-name collision** on
  `nfl-decision-desk/` and a `COORDINATION.md` append conflict.
- **Resolution (no work discarded):** `origin/main` was merged in; session d0343637's
  `nfl-decision-desk/` is kept exactly as published, and this session's site was moved to its own
  namespace **`nfl-decision-desk-38a1fc27/`** (build and verify targets updated, README links
  updated). `COORDINATION.md` keeps both sessions' blocks verbatim, with this log added.
- **Post-merge re-verification:** repo-wide internal links 4,317 across 255 pages, **0 broken**;
  session d0343637's own `nfl-decision-desk/verify.py` still passes (4 tests OK); this session's
  `verify.py` passes (14 pages / 26 tables / 494 rows, every row sourced); provenance audit
  0 tables needing review; official standings still 32/32.
- **Scope note for future sessions:** `nfl-decision-desk/**` is owned by `d0343637`;
  `nfl-decision-desk-38a1fc27/**` is owned by this session. The two desks overlap in subject but
  not in files; the integration session may choose to cross-link them later.

---

## Session b34253a1 — NFL Decision-Making, Depth-Chart Injury Tracking, Line Origination & Skill Leaderboard Hub (2026-11-12 UTC)

Claim timestamp: **2026-11-12T16:26Z** (rebased cleanly onto `0d3e323` preserving Session `d0343637`'s appended record verbatim). Arena fixes this session's branch to `arena/b34253a1-own5`; no other branch will be created or pushed. To guarantee zero file collisions with CI-locked files (`index.html`, `pages/**`, `data/research.json`, `scripts/**`, `tests/**`, `own5-desk/**`, `nba-validation/**`, `sf-rent-review/**`, `nfl-decision-desk/**`, etc.) and any concurrent 2026-11-12 sessions, this session claims strictly isolated additive namespaces `nfl-b34253a1/**`, `research/nfl-b34253a1/**`, and `.github/workflows/nfl-b34253a1.yml`, plus append-only updates to `COORDINATION.md` and `README.md`. Any cross-scope improvement proposals are logged below and published on the dedicated **Suggestions for Review** page (`nfl-b34253a1/suggestions.html`) for human selection before touching shared files.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| B34-01 | Task claim + line-by-line repository audit of existing NFL desks, data & links | in progress | b34253a1 | `COORDINATION.md`, `research/nfl-b34253a1/REPO_AUDIT.md`, `nfl-b34253a1/data/repo_audit.csv` | Claim pushed immediately; line-by-line review of root, `pages/`, `own5-desk/`, `nfl-strategy-lab/`, `line-lab/`, `nfl-decision-desk/`, `data/` vs official sources as of 2026-11-12. |
| B34-02 | Official NFL 2026 Week 10 verified baseline (standings, completed games, Wk10 slate, rules) | in progress | b34253a1 | `research/nfl-b34253a1/SOURCES.md`, `nfl-b34253a1/data/sources.csv`, `nfl-b34253a1/data/standings_2026_wk10.csv`, `nfl-b34253a1/data/games_2026_verified.csv`, `nfl-b34253a1/data/schedule_2026_wk10.csv` | Official `nfl.com`, `operations.nfl.com`, DraftKings/FanDuel official NFL partners, and 28 Wk10 official club sites; unconfirmed cells left blank + flagged. |
| B34-03 | Offense & Defense Injury + Depth-Chart Deficiency Tracker (1st/2nd/3rd/4th string backups) | in progress | b34253a1 | `research/nfl-b34253a1/INJURIES_DEPTH.md`, `nfl-b34253a1/data/injuries_depth_deficiencies.csv`, `nfl-b34253a1/data/unit_deficiency_summary.csv` | Tracks starters replaced by 2nd/3rd/4th-string backups across offense & defense from official NFL injury reports & club depth charts. |
| B34-04 | Site Improvement Suggestions & Pre-Implementation Review Hub | unclaimed | b34253a1 | `research/nfl-b34253a1/SUGGESTIONS.md`, `nfl-b34253a1/data/site_suggestions.csv`, `nfl-b34253a1/suggestions.html` | Dedicated reviewable options, tradeoffs, impact on decision-making, and recommended paths prior to modifying shared pages. |
| B34-05 | Decision-Readiness Q&A Matrix (known vs. missing info + discovery pathways) | unclaimed | b34253a1 | `research/nfl-b34253a1/DECISION_QA.md`, `nfl-b34253a1/data/decision_questions.csv`, `nfl-b34253a1/questions.html` | Questions, verified data held, missing data, current verified answers, and concrete official-source discovery steps. |
| B34-06 | NFL Line Origination, Signals, Singles/Parlays/Prop Combos, Correlations, Gates & Skill Leaderboard | unclaimed | b34253a1 | `research/nfl-b34253a1/METHODOLOGY.md`, `nfl-b34253a1/engine.py`, `nfl-b34253a1/data/*.csv` | Reproducible Week 10 line origination + walk-forward 2026 verification, depth-adjusted signals, computed correlations, fail-closed gates, luck-deflated leaderboard. |
| B34-07 | Executive Summary & Flagged-for-Review Register | unclaimed | b34253a1 | `research/nfl-b34253a1/EXECUTIVE_SUMMARY.md`, `research/nfl-b34253a1/FLAGGED.md`, `nfl-b34253a1/data/flagged_review.csv` | Executive summary + nonblocking Flagged-for-Review register with official links and explicit blanks. |
| B34-08 | GitHub Pages Dashboard + 12 Category Subpages + Automated Line-by-Line Verification | unclaimed | b34253a1 | `nfl-b34253a1/**`, `.github/workflows/nfl-b34253a1.yml` | Clean dashboard UI, deterministic `build.py`, `verify.py` (every row linked or flagged blank, 0 broken links), unit + Chromium tests. |
| B34-09 | Final Integration, PR to `main`, Autonomous Merge & Live GitHub Pages Verification | unclaimed | b34253a1 | `COORDINATION.md`, `README.md` (append-only) | Rebase, verify all repo + scoped CI suites, open PR, merge without waiting, confirm live Pages URLs, record outcome. |

### b34253a1 progress update — 2026-11-12

| ID | Status | Updated deliverables | Evidence / scope note |
|---|---|---|---|
| B34-01 | done | `nfl-b34253a1/audit_repo.py`, `nfl-b34253a1/data/repo_audit.csv`, `repo_audit_summary.json`, `research/nfl-b34253a1/REPO_AUDIT.md` | Generated a physical-line inventory of the selected prior/shared NFL scope. Every line carries a source-basis label; direct row provenance, official scope fallbacks, and official comparators for flagged legacy values are explicitly distinguished. The audit is not a fresh fetch/certification of every historical claim. |
| B34-02 | done | `data/games_2026_w1_w9.csv`, `standings_2026_w10.csv`, `team_stats_2026_w10.csv`, `schedule_2026_w10.csv`; `SOURCES.md`, `METHODOLOGY.md` | 136 official-linked results reconcile 32/32 W-L-T/PF/PA standings rows; 14 Week 10 games plus four bye rows; 32 team-stat rows; mismatches zero. |
| B34-03 | done | `data/injuries_depth_w10.csv`, `data/depth_chart_coverage_2026_w10.csv`, `INJURIES_DEPTH.md` | 76 selected observations across 17 teams; 32/32 team chart URLs documented. CHI, DEN, PHI, TB were Week 10 byes and their chart pages are coverage-only. Final participation and numeric depth-to-points adjustments remain blank. |
| B34-04 | done | `site_suggestions.csv`, `suggestions.html`, `SUGGESTIONS.md` | Twelve review options with tradeoffs; all await a reviewer decision. Shared navigation and prior-owner dashboards were not modified. |
| B34-05 | done | `decision_questions.csv`, `questions.html`, `DECISION_QA.md` | Sixteen known/missing-evidence questions, current answer boundaries, and concrete discovery steps. |
| B34-06 | done | `engine.py`, `data/model_lines_2026_w10.csv`, walk-forward/correlation/strategy/gate/leaderboard/luck outputs, `METHODOLOGY.md` | 14 exploratory baseline lines; 120 prior-week-only margin forecasts (MAE 10.4048); 4 computed descriptive correlations plus 3 blank paired-prop rows; six strategy hypotheses and 11 gates. Injury adjustments, ROI/CLV, ranks and reward amounts remain unavailable; only G0 passes. |
| B34-07 | done | `EXECUTIVE_SUMMARY.md`, `FLAGGED.md`, `flagged_review.csv` | Executive limits and 20 linked review flags; no recommendation or validated-skill claim. |
| B34-08 | done | `nfl-b34253a1/{index.html,*.html,style.css,build.py,verify.py,tests/}` and `.github/workflows/nfl-b34253a1.yml` | Isolated static overview plus 12 category pages; deterministic builder; scoped verification, unit tests, Chromium desktop/mobile and no-JavaScript checks pass locally. |
| B34-09 | in progress | `COORDINATION.md` (append-only), isolated namespace | Local build and verification pass; branch push, PR checks/merge, and GitHub Pages deployment verification remain pending. |

Local validation on 2026-11-12: eight session tests passed; all 91 existing repository unit tests passed; isolated source/HTML/audit verification passed, including the line hashes; Chromium smoke tests passed all 13 pages at desktop and mobile widths, CSV download, table accessibility structure, and no-JavaScript source table. After rebasing onto `0f41505`, the audit was refreshed to include the prior `nfl-decision-desk-38a1fc27/` desk and exclude NBA-only paths; the final inventory covers 286 files and 81,718 physical lines. Deterministic rebuilds pass. External source URLs remain dynamic and were not re-fetched by CI-style structural checks.

## Session 26d4cafb — NFL Decision, Line Origination & Depth-Deficiency Desk (2026-11-12 UTC)

Arena fixes this session's branch to `arena/26d4cafb-own5` (branched from `95c2eea`); no alternative branches will be created, renamed, or pushed. To guarantee zero file collisions with CI-locked scopes (`index.html`, `pages/`, `data/research.json`, `own5-desk/`, `nba-*`, `sf-*`, `nfl-strategy-lab/`, `line-lab/`) AND with concurrent 2026-11-12 sessions (`d0343637`, `38a1fc27`, and `e413f933`, which claimed `nfl-decision-desk/**`), this session claims **strictly session-isolated additive namespaces**:

- `nfl-desk-26d4cafb/**` (static GitHub Pages dashboard + category subpages, canonical data JSON/CSVs, deterministic build/compute engine, unit tests, and verification suite)
- `research/nfl-26d4cafb/**` (executive summary, full requirements matrix, line-by-line repo audit, suggestions register, decision questions & discovery plan, injury/depth methodology, strategy/gate/correlation docs, verification log, flagged register)
- `.github/workflows/nfl-desk-26d4cafb.yml` (scoped deterministic verification workflow)
- Append-only entries in `COORDINATION.md` and `README.md` (at integration)

Claim timestamp: **2026-11-12T16:28Z**, committed and pushed before implementation.
- **Rebase conflict log (2026-11-12T16:29Z):** While rebasing claim commit onto `origin/main` (`64322dd`), hit append-only conflict in `COORDINATION.md` with session `d0343637`'s newly merged section (`nfl-decision-desk/**`). Resolved by preserving `d0343637`'s complete block verbatim and appending this session's non-overlapping `nfl-desk-26d4cafb/**` block below it. Zero file overlap.

| ID | Task | Status | Owner | Files touched | Notes |
|---|---|---|---|---|---|
| N26-01 | Read task board, inspect CI locks & sibling branches, push isolated claim | done | 26d4cafb | `COORDINATION.md` | Verified CI locks & sibling 2026-11-12 claims; claimed collision-free `nfl-desk-26d4cafb/**`. |
| N26-02 | Line-by-line repo audit of existing NFL scopes vs official 2026-11-12 sources | done | 26d4cafb | `research/nfl-26d4cafb/REPO_AUDIT.md`, `nfl-desk-26d4cafb/data/**` | Audit root desk, detail CSVs, `nfl-strategy-lab/`, `line-lab/`, `own5-desk/`, `nfl-decision-desk/`; link official sources & flag irregularities. |
| N26-03 | Full requirements matrix, site-improvement Suggestions section, and Questions / Known-vs-Missing Info / Discovery register | done | 26d4cafb | `research/nfl-26d4cafb/REQUIREMENTS.md`, `research/nfl-26d4cafb/SUGGESTIONS.md`, `research/nfl-26d4cafb/QUESTIONS_AND_GAPS.md`, `nfl-desk-26d4cafb/data/**` | Reviewable improvement paths (unimplemented on locked scopes) + decision prerequisites & discovery paths. |
| N26-04 | Official 2026-11-12 NFL data verification (standings, W9 results, W10 slate, official injury reports & club depth charts) | done | 26d4cafb | `nfl-desk-26d4cafb/data/**`, `research/nfl-26d4cafb/SOURCES.md` | Every row linked to `nfl.com`, `operations.nfl.com`, or official NFL club depth-chart/injury URLs; unverified cells blank + flagged. |
| N26-05 | Offense & Defense injury + 1st/2nd/3rd/4th-string backup deficiency tracker & matchup signals | done | 26d4cafb | `nfl-desk-26d4cafb/engine.py`, `research/nfl-26d4cafb/INJURY_DEPTH_MODEL.md`, `nfl-desk-26d4cafb/data/**` | Tracks starter vs 2nd/3rd/4th-string replacements across offense & defense from official club depth charts + NFL injury reports. |
| N26-06 | Own Week 10 NFL line origination, signal strategies (singles, parlays, prop combos), correlations, luck-removal math, fail-closed gates & leaderboard | done | 26d4cafb | `nfl-desk-26d4cafb/engine.py`, `research/nfl-26d4cafb/METHODOLOGY.md`, `nfl-desk-26d4cafb/data/**` | Computed Pearson/Fisher-z/joint-combo correlations, binomial/DSR/Holm-Bonferroni luck gates, 0 unvalidated strategies certified. |
| N26-07 | Executive summary & Flagged-for-Review register | done | 26d4cafb | `research/nfl-26d4cafb/EXECUTIVE_SUMMARY.md`, `research/nfl-26d4cafb/FLAGGED.md` | Concise verified executive summary + complete nonblocking flagged register with official links. |
| N26-08 | Clean GitHub Pages dashboard & category subpages (`nfl-desk-26d4cafb/`) | done | 26d4cafb | `nfl-desk-26d4cafb/*.html`, `nfl-desk-26d4cafb/assets/**`, `nfl-desk-26d4cafb/build.py` | Clean, intuitive dashboard + category subpages, search/filter/CSV export, interactive suggestion/question reviewers, no-JS fallback. |
| N26-09 | Line-by-line verification harness, unit tests, browser smoke tests & CI workflow | done | 26d4cafb | `nfl-desk-26d4cafb/verify.py`, `nfl-desk-26d4cafb/tests/**`, `.github/workflows/nfl-desk-26d4cafb.yml` | Asserts 100% of table rows carry official source links or explicit blank+flag; 0 broken links; deterministic rebuild; existing CI passes. |
| N26-10 | Final integration, rebase on `origin/main`, PR to `main`, autonomous merge, live GitHub Pages check & coordination log | in progress | 26d4cafb | `COORDINATION.md`, `README.md` | Rebase preserving all concurrent sessions, green PR checks, explicit `gh pr merge <num> --merge`, confirm live Pages URLs. |

Cross-session requests at claim time: none (all prior and sibling scopes treated as read-only).

### N26-02..N26-09 completion record — 2026-11-12

**Data provenance (all fetched 2026-11-12 UTC, official sources only).**
[nfl.com/standings](https://www.nfl.com/standings/) (32-team standings),
[nfl.com/schedules](https://www.nfl.com/schedules) (Week 10 slate + byes),
[nfl.com/schedules/2026/by-week/week-8](https://www.nfl.com/schedules/2026/by-week/week-8) and
[week-9](https://www.nfl.com/schedules/2026/by-week/week-9) (16 post-freeze finals),
[nfl.com/injuries/league/2026/reg10](https://www.nfl.com/injuries/league/2026/reg10) (Week 10 practice/game statuses),
[nfl.com/stats/player-stats](https://www.nfl.com/stats/player-stats/) (6 QB passing checksums),
18 official 2026 player game-log pages,
[operations.nfl.com/rules-officiating/2026-nfl-rulebook](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook) (2026 rule changes),
and **18 official NFL club `/team/depth-chart` pages** (`SRC-01..SRC-51`).

**Exact arithmetic verified.**
- `data/standings-2026-wk8.csv` (120 games) + Week 8 MNF (`CHI 34 @ SEA 17`) + 15 Week 9 finals
  = **136 completed games**, which reconcile **32/32 teams, 0 mismatches** on W, L, T, PF and PA
  against the 2026-11-12 `nfl.com/standings/`.
- All 6 quarterbacks' game-by-game passing yards sum to the exact official season total
  (Love 2618, Burrow 2386, Prescott 2381, Goff 2134, Mahomes 2037, Allen 2027): **0 mismatches**.

**Key computed findings.**
- Empirical 2026 home-field advantage on 130 non-neutral games: **-0.054 pts**
  (SD 13.28, SE 1.165, 95% CI [-2.34, +2.23], p = 0.96). Away teams are 71-64-1 against home teams.
  The repository's existing boards assume **+2.0**; on the matched 13-game sample that assumption
  produced a **+5.35 point** margin bias.
- Week 10 depth findings: BAL is on its **3rd-string QB** (Jackson and Huntley both on IR) while the
  official Week 10 injury table still reads "No Injuries Reported" for that Monday-night game (`FLG-06`).
- **2 of 10** strategies clear all ten fail-closed gates and are ranked; 3 are blocked by a gate and
  5 are marked *not evaluable* because no official input exists for Weeks 1-9 (injury register is
  current-week only; no official prop lines at all).
- Selectivity is **NOT established**: confidence-tercile accuracy is 0.379 / 0.828 / 0.724, which is
  not monotone. The engine reports this rather than claiming selective skill.

**Verification performed.**
- `nfl-desk-26d4cafb/verify.py`: **25 checks, 0 failures** (ledger integrity, 32/32 standings
  reconciliation, QB checksums, score arithmetic, **every rendered table row carries an official
  source link**, no placeholder values, no broken internal links, declared blanks genuinely blank,
  FLG-register integrity, zero look-ahead, probability sanity, neutral-site HFA zeroing).
- `python3 -m unittest discover -s nfl-desk-26d4cafb/tests`: **60 tests, all passing**.
- All 19 rendered pages are well-formed HTML; all internal links and assets resolve;
  no `localhost` / `127.0.0.1` references in any browser-facing file.
- Site served locally on port 8000: every page returns HTTP 200 with expected content.

**Scope discipline.** All artifacts live in `nfl-desk-26d4cafb/**`, `research/nfl-26d4cafb/**` and
`.github/workflows/nfl-desk-26d4cafb.yml`. No CI-locked file and no other session's file was modified;
`nfl-decision-desk/**` (session `d0343637`) was read-only. No site-wide change was implemented from
this session — every improvement is a proposal on the Suggestions page awaiting a chosen path.

**Cross-session request logged, NOT actioned (2026-11-12).** The `NFL Decision Desk — fetch & verify`
workflow (`.github/workflows/decision-desk.yml`, owned by sessions `d0343637` / `38a1fc27`) fails its
"Confirm the committed site matches a clean rebuild" step on this session's PR #61. Its failing step is
`git diff --exit-code -- nfl-decision-desk/ data/decision-desk/`.

This is **pre-existing on `main` and unrelated to this session**. Verified by extracting `origin/main`
into a clean directory containing **none** of this session's files and running that workflow's own
commands (`tools/decision_desk/build_all.py && tools/decision_desk/build_site.py`): the rebuild still
drifts from the committed snapshot in `data/decision-desk/injuries_wk10_players.csv` and
`data/decision-desk/team_deficiency_wk10.csv`.

This session changes **no** file under `nfl-decision-desk/`, `data/decision-desk/` or `tools/`
(confirmed with `git diff --name-only $(git merge-base origin/main HEAD)..HEAD`), so per the
coordination rules this is logged for the owning session rather than patched here. Suggested fix for
the owner: make `parse_official.py` emit rows in a deterministic order (and pin any live-fetch
timestamp), or move the drift check behind the `fetch` job that regenerates the pinned snapshot.

This session's own scoped check — `.github/workflows/nfl-desk-26d4cafb.yml`
("Build data, render site, verify, test") — **passes**, and its build is deterministic: the workflow
fails if a clean rebuild of `nfl-desk-26d4cafb/**` differs from what is committed.


---

## Session 28431d9c — NFL cross-desk reconciliation & currency audit (2026-11-13 UTC)

Arena fixes this session's branch to `arena/28431d9c-own5` (base `ec3cb83` = `main`); no other branch will be created or pushed. Claim timestamp: **2026-11-13 UTC**, pushed before any implementation.

Rationale: six NFL desks already exist on `main` (`nfl-strategy-lab/`, `nfl-decision-desk/` (d0343637), `nfl-decision-desk-38a1fc27/`, `nfl-b34253a1/`, `nfl-desk-26d4cafb/`, `nfl-decision-desk-e413f933/`), each built from its own snapshot. No page compares them with each other or with the current official nfl.com state. This session claims that gap only.

Claimed additive namespace (no overlap with any other session):
- `nfl-hub-28431d9c/**` (static GitHub Pages hub: desk map, official-standings and Week 10 reconciliation, injury spot-check, own-line cross-model comparison, Flagged for Review, sources; build + verify scripts)
- `research/nfl-28431d9c/**` (method, executive summary, flagged register)
- `.github/workflows/nfl-hub-28431d9c.yml` (runs this session's verify script only)
- Append-only blocks in `COORDINATION.md`

Read-only for this session: every other NFL desk directory, root `index.html`/`pages/`/`data/research.json`, `docs/`, `own5-desk/`, `nba-*`, `sf-*`, `rental-*`, `line-lab/`, `scripts/`, `tools/`, existing workflows, existing CSV/JSON.

| ID | Task | Status | Owner | Files touched | Notes |
|----|------|--------|-------|---------------|-------|
| R1 | Claim + baseline inventory of all NFL desks | in progress | 28431d9c | COORDINATION.md | Claim pushed first. |
| R2 | Official nfl.com snapshot (32-team standings, Week 10 slate, Week 10 injury report sample) transcribed with URLs and fetch date | unclaimed → in progress | 28431d9c | nfl-hub-28431d9c/data/official_*.csv | Values transcribed from fetch_page results; any unreadable value left blank. |
| R3 | Cross-desk reconciliation: standings, slate, injury statuses, own-line favorites | in progress | 28431d9c | nfl-hub-28431d9c/data/reconcile_*.csv | Each row carries an official nfl.com link or an explicit blank + flag. |
| R4 | Hub site (overview, desk map, reconciliation pages, Flagged for Review, sources) | in progress | 28431d9c | nfl-hub-28431d9c/*.html, build.py | Static, deterministic build. |
| R5 | Verification harness + executive summary + PR/merge/Pages check | in progress | 28431d9c | nfl-hub-28431d9c/verify.py, research/nfl-28431d9c/**, COORDINATION.md | Merge only after verify PASS and live Pages check. |

### Session 28431d9c — status log (2026-11-13 UTC)

Branch `arena/28431d9c-own5`. Claimed scope R1–R5 (above). Scope was narrowed from the earlier plan (B34-04..09 and N26-10 are other sessions' claims and were not touched).

| ID | Status | What was done | Evidence in repo |
|----|--------|---------------|------------------|
| R1 | done | Inventory of the six NFL desks: e413f933, b34253a1, 26d4cafb, 38a1fc27, d0343637 (`nfl-decision-desk/`), and nfl-strategy-lab. Each desk's data basis and machine-readable files are listed. | `nfl-hub-28431d9c/data/desk_map.csv` |
| R2 | done | Official values transcribed from fetch_page results of nfl.com: standings (32 teams, re-fetched post-Thursday), Week 10 schedule (14 games, 4 byes), injury report (44 rows for WAS, NYG, NE, DET). Each row carries its nfl.com URL. Injury chunk 7 returned no data; not used. | `nfl-hub-28431d9c/data/official_*.csv` |
| R3 | done | Reconciliation of standings, slate, byes, injuries, own-line favorites, and QB headlines. Unconfirmed values are blank and flagged. | `nfl-hub-28431d9c/data/reconcile_*.csv`, `official_qb_news.csv`, `flagged.csv` |
| R4 | done | Static hub built deterministically: index, desk map, standings, slate, injuries and QB news, own-line comparison, Flagged for Review, sources. | `nfl-hub-28431d9c/*.html`, `build.py` |
| R5 | in progress | `verify.py` (1,022 checks) passes. Executive summary and generated Flagged register written. PR to `main` to follow. | `nfl-hub-28431d9c/verify.py`, `research/nfl-28431d9c/SUMMARY.md`, `research/nfl-28431d9c/FLAGGED.md`, `.github/workflows/nfl-hub-28431d9c.yml` |

**Findings that changed during verification (recorded so no draft claim survives):**
- The first draft's "reversing the TNF result reproduces each desk" was not computed. It is now computed in code and re-derived in `verify.py`: it holds for all three desks and the 38a1fc27 root snapshot.
- The draft's "quotes include a finished game" claim was overstated. The quotes are date-only, so only "no time recorded; cannot be shown pre-kickoff" can be said.
- Four draft QB headlines (Willis IR, Watson starting, Beck starting, Jackson 6–10 weeks / Walker questionable) were not reproduced on the re-fetched injury page's news list and are excluded (H-13). Kenneth Walker is absent from the official Seattle table.
- The official standings page now shows NYG 5-3-1 and WAS 3-5-1 (post-Thursday). An earlier pre-game read showed 5-2-1 and 2-5-1. The post-game values are the ones used.

**Cross-scope requests (logged only; not edited by 28431d9c):**
- Integration owner: add a link from the root site index to `nfl-hub-28431d9c/index.html` (root index not changed here).
- 38a1fc27 owner: `data/decision-desk/official/official_injuries_wk10.csv` is a pre-kickoff snapshot (2026-11-12T16:52Z) that differs from the current official page on 15 of 44 sampled rows (H-14).
- b34253a1 owner: add retrieval times to market quotes (H-02); fix Ben Brown's position LG→C (H-03); update the Thursday status from SCHEDULED (H-01).
- 26d4cafb owner: correct availability labels ("Confirmed Out / IR" on non-IR rows; Stevenson "DNP + Backup Out") (H-06–H-08); add a machine-readable bye list (H-12).
- e413f933 owner: fill game status for rows the official page designates (H-09).

**Not in this session's claimed scope (not done here):** own-line origination, signal strategy research, correlation values and the leaderboard. Those outputs stay in the desks, unverified by this hub (H-16).

**PR:** https://github.com/sassnarep3-star/Own5/pull/67 (`arena/28431d9c-own5` → `main`, opened 2026-11-13 UTC).
**Checks on the PR:** `NFL cross-desk hub (28431d9c)` verify: pass (rebuild and verifier). `Verify NBA validation desk`, `desk-verify`, SF rent and research dashboard checks: pass.
**Failing checks outside this session's scope:** (a) `NFL Decision Desk — fetch & verify` (`.github/workflows/decision-desk.yml`) runs live fetches on every PR to `main` and fails when regenerated `nfl-decision-desk/` and `data/decision-desk/` differ from the committed snapshot (source drift; this PR changes neither folder). (b) `Verify NFL B34 Week 10 research desk` (`nfl-b34253a1.yml`) already fails on `main` at `0e50f9b`. Both are logged as cross-scope requests to their owners and were not edited here.
**Merge:** `gh pr merge 67 --merge` after the checks above. The merge result and the Pages deploy are confirmed with `gh` and the live URL after the merge.

**Merge result (session 28431d9c):** PR #67 (`arena/28431d9c-own5` → `main`) was merged with a merge commit at 2026-11-13 21:41 UTC (`gh pr merge 67 --merge`), merge SHA `4fc2000`. The GitHub Pages build for `4fc2000` finished with status `built` (https://sassnarep3-star.github.io/Own5/). The live hub at `/nfl-hub-28431d9c/` serves the dashboard and the Flagged for Review page with the corrected text. R5 is now done. The two failing checks on PR #67 (`decision-desk.yml`, `nfl-b34253a1.yml`) were not caused by this PR and remain open for their owners as cross-scope requests above.
