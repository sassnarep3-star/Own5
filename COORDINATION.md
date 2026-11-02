# Coordination board

Session: `arena-cd43258e` · Branch: `arena/cd43258e-own5` · Started: 2026-11-02 UTC.

This repository initially contained only a six-byte README. No prior claims or open pull requests were found. The Arena session branch is fixed; this session cannot create the separately named branches requested in the project brief. This session is also the final integration owner. Other sessions should not edit the scopes claimed below.

| Task | Status | Owner | File scope |
|---|---|---|---|
| Official-source research and evidence register | done | arena-cd43258e | data/**, research/** |
| Dashboard, category pages, executive summary | done | arena-cd43258e | index.html, assets/**, pages/**, .nojekyll |
| Validation tests and methodology engine | done | arena-cd43258e | scripts/**, tests/**, package.json, package-lock.json |
| Integration, documentation, Pages publication | in progress | arena-cd43258e | README.md, COORDINATION.md, .github/**, .gitignore |

## Rules

No empirical edge, odds, correlation, player statistic, payout, or performance result will be invented. Unknown empirical values stay blank and appear on Flagged for Review. Methodological choices are explicitly labeled project policy, not verified NFL facts. Only primary-source links qualify as evidence; source scope and retrieval limitations are recorded. “Needs review” is nonblocking and means the item is published on the review page.

## Activity

- 2026-11-02: Inspected all existing repository content (`README.md`: `# Own5`), clean working tree, no coordination file, no open PRs. GitHub API reports Pages configured from `main` root at https://sassnarep3-star.github.io/Own5/.
- 2026-11-02: Claimed all non-overlapping work scopes above before implementation. No other session claims exist. Research sources, test results, PR, and deployment outcome will be recorded below.
- 2026-11-02: Research completed with 13 scoped primary-source checks: NFL Football Operations rulebook, NFL.com schedules/injuries/stats, NFL Next Gen Stats glossary, DraftKings Virginia general and market rules, and official scikit-learn/SciPy/statsmodels methodology docs. Exact links, findings, selected excerpts and limitations: `data/research.json` and `research/VERIFICATION.md`. Unreadable injury-policy URL and missing numeric table headers were not used to infer facts.
- 2026-11-02: Implemented eight static pages, 11 sourced definitions, eight proposed strategies, five pricing frameworks, six unmeasured correlation questions, seven project-policy gates and proposed non-cash competition rules. Every table row has a primary-publisher link; methodology references are explicitly not performance evidence.
- 2026-11-02: Local verification: 27 Python tests passed; JS syntax passed; Chromium visited all eight pages at desktop and mobile widths; search, filters, CSV URL preservation, empty state, blank values and no-JS rendering passed. All internal HTML links/fragment targets passed. Screenshots inspected. Browser's initial missing NSS/NSPR dependency was resolved using its bundled support libraries.

## Nonblocking research review items

| Task | Status | Owner | Published location |
|---|---|---|---|
| R01 historical prices; R02 as-of outcome/features; R03 correlations | needs review | arena-cd43258e | `pages/review.html` (R01–R03), official links in each row |
| R04 exact prop/combo settlement; R05 unreadable injury policy | needs review | arena-cd43258e | `pages/review.html` (R04–R05) |
| R06 no empirical validation; R07 unfunded rewards; R08 jurisdiction | needs review | arena-cd43258e | `pages/review.html` (R06–R08) |
| R09 live-source drift/headers; R10 empty initial repository | needs review | arena-cd43258e | `pages/review.html` (R09–R10) |

No actual NFL edge, ROI, empirical coefficient, ranking, cash payout or recommendation is claimed. Empty empirical fields remain null/blank. Research specification and site completion do not imply empirical strategy validation.

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
| T2 | Research: signal-generation strategies (singles, parlays, player-prop combos) with source links | done | 9c3a0a69 | `research/strategies.md` |
| T3 | Research: validation gates (anti-overfitting, sample size, CLV benchmark) | done | 9c3a0a69 | `research/validation-gates.md` |
| T4 | Research: correlation framework & reported correlation values for props/parlays | done | 9c3a0a69 | `research/correlations.md` |
| T5 | Skill-vs-luck separation methodology (CLV, variance decomposition, multiple-testing control) | done | 9c3a0a69 | `research/skill-vs-luck.md` |
| T6 | Leaderboard competition design (scoring, rewards, entry gates) | done | 9c3a0a69 | `research/leaderboard.md` |
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
