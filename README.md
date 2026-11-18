# Own5 — Sports Line-Origination Research (multi-session)

> **Repository review (2026-11-18, branch `arena/51cf3786-own5`):** every desk verifier was run from the repo root ([`repo-review/verifiers.html`](repo-review/verifiers.html)); two failing verifiers were fixed; official NFL pages were spot-checked ([`repo-review/spot-checks.html`](repo-review/spot-checks.html)); 16 irregularities are listed on the [Flagged for Review page](repo-review/flagged.html). Start from the [NFL integration hub](nfl-integration-a620f5a5/index.html) and the [repo review](repo-review/index.html). Rebuild the review with `python3 repo-review/run_verifiers.py && python3 repo-review/build.py && python3 repo-review/verify.py`.


This repository hosts work from **three parallel agent sessions** (see `COORDINATION.md`): an **NBA Line-Origination Lab** (session `9c3a0a69`, served at `/docs/`) and an **NFL Research Desk** with detail pages (sessions `cd43258e` and `0f468a47`, served at the site root).

| Dashboard | Scope | Live URL | Session |
|---|---|---|---|
| **NFL Official Injury-Report Capture Desk** | NFL 2026 — verified Week 10 injury-report counts (14 games, 28 club tables, 347 rows, one hashed read), 4 byes verified against the official schedule, Terms s.1.3 read (automated capture blocked pending written consent, decision D-01), decision-readiness table, Flagged for Review | https://sassnarep3-star.github.io/Own5/nfl-desk-b8227c47/ | `b8227c47` (`nfl-desk-b8227c47/`, `COORDINATION.md` § Session b8227c47) |
| **NBA Line-Origination Lab** | NBA — singles, parlays, player-prop combos; validation gates; leaderboard design | https://sassnarep3-star.github.io/Own5/docs/ | `9c3a0a69` (`docs/`, `research/nba/`, `analysis/`, `EXECUTIVE_SUMMARY.md`) |
| **NFL Research Desk** | NFL — line origination, strategy lab, correlation questions, review register | https://sassnarep3-star.github.io/Own5/ | `cd43258e` + `0f468a47` (root, `pages/`, `data/`, `scripts/`, `tools/`, `tests/`) |
| **NFL Strategy Lab** | NFL — own lines from official data, pre-registered singles/parlays/prop combos, validation gates G0–G7, computed correlations, luck-deflated leaderboard | https://sassnarep3-star.github.io/Own5/nfl-strategy-lab/ | `arena-f1d30421` (`nfl-strategy-lab/`, `research/arena-f1d30421/`, `data/`, `scripts/compute_*`, `scripts/originate_lines.py`) |
| **NFL Line Lab** | NFL — reconciled W1–9 game log + standings (32/32 exact), W8/W9 lines, model-vs-market origination, gate-scored strategy leaderboard, flagged items | https://sassnarep3-star.github.io/Own5/line-lab/ | `arena-44bc1e2f` (`line-lab/`, `data/standings_2026.json`, `data/games_2026.json`, `data/lines_upcoming_2026.json`, `tools/reconcile.py`, `tools/build_line_lab_site.py`, `analysis/compute_metrics.py`) |
| **NBA Line Desk 2026-27** | NBA 2026-27 — official standings, team stats and Edwards logs; signals and correlations; luck-vs-skill; strategies with validation gates G1–G8; leaderboard; executive summary; flagged-for-review page | https://sassnarep3-star.github.io/Own5/nba-line-desk/ | `9cf7de11` (`nba-line-desk/`, `data/nba-2026-27/`, `research/nba-2026-27/`, `tools/nba_line_desk/`, `tests/test_nba_line_desk.py`) |
| **NFL Decision-Readiness Desk** | NFL — 81-requirement decision-readiness matrix (blocking gate + number that would clear it + observed number) on a landing page; questions/suggestions/sources/flagged/review subpages; additive to the price/results desk | https://sassnarep3-star.github.io/Own5/nfl-560ed315/ | `560ed315` (`nfl-560ed315/`, `research/nfl-560ed315/`, `.github/workflows/nfl-560ed315.yml`) |
| **NFL Decision-Readiness** | NFL — consolidated decision-readiness matrix (85 requirements × blocking gate × clearing number), per-strategy two-sided falsification, removal-of-luck panel, suggestions/questions/flagged registers | https://sassnarep3-star.github.io/Own5/nfl-readiness-cba42531/ | `cba42531` (`nfl-readiness-cba42531/`, `research/nfl-cba42531/`, `.github/workflows/nfl-readiness-cba42531.yml`) |
| **NFL Decision-Readiness Desk** | NFL 2026 — decision-readiness table (requirement → blocking gate → the number that clears it), questions and suggestions registers, 145 official finals reconciled 32/32 to the standings, 39 originated week-11 markets, 700 depth slots, replacement-depth and matchup-deficiency matrices, luck panel; market-price columns blank and flagged | https://sassnarep3-star.github.io/Own5/nfl-desk-e46fb855/ | `e46fb855` (`nfl-desk-e46fb855/`, `.github/workflows/nfl-desk-e46fb855.yml`) |
| **NFL Official Re-read & Flagged for Review** | NFL 2026 — Week 10 injury report re-read line by line against nfl.com (347 official rows vs 326 published), claim-by-claim verdicts with official links, official trades and reserve-list rows, Flagged for Review register | https://sassnarep3-star.github.io/Own5/nfl-audit-a699fc53/ | `a699fc53` (`nfl-audit-a699fc53/`, `.github/workflows/nfl-audit-a699fc53.yml`) |
| **NFL Decision Desk — e1d60f5d** | NFL 2026 — verified 32-team standings and Week 11 schedule from nfl.com, questions register (have/missing/answers), suggestions register (reviewable paths), sources register, flagged-for-review, executive summary; every row source-linked or blank-and-flagged; 0 strategies certified | https://sassnarep3-star.github.io/Own5/nfl-desk-e1d60f5d/ | `e1d60f5d` (`nfl-desk-e1d60f5d/`, `.github/workflows/nfl-desk-e1d60f5d.yml`) |
| **NFL Currency & Corrections Desk** | NFL 2026 — fresh official captures (2026-11-17T00:38–00:55Z, hash-pinned): 149 finals + standings reconciled **32/32** after publishing a club-code alias defect that had silently dropped 18 club-games in a prior feed; first repo-wide reserve-list and transactions register (62 dated events, 13 stale depth rows); injury-report delta **0 of 147 values** across two reads; 80-row requirement ledger (39 met, 22 partial, 16 blocked, 2 rejected); week-11 registration recorded pre-kickoff with market columns blank by policy; 5 corrections to claims carried forward | https://sassnarep3-star.github.io/Own5/nfl-desk-35a1feb2/ | `35a1feb2` (`nfl-desk-35a1feb2/`, `.github/workflows/nfl-desk-35a1feb2.yml`) |
| **Own5 NFL Hub (single entry point)** | NFL 2026 — one decision-readiness table (80 brief lines → status, blocking gate, number that clears it), daily official injury-report captures with sha256 and UTC stamps, re-checks against nfl.com on 2026-11-18, questions, suggestions awaiting your choice, Flagged for Review | https://sassnarep3-star.github.io/Own5/own5-hub/ | `9cabfdb9` (`own5-hub/`, `.github/workflows/own5-hub-*.yml`) |

| **NFL Decision Console** | NFL 2026 — own lines originated side→total→moneyline for the 13 week-11 games (65 market rows, market column blank and flagged); 80-requirement decision-readiness table; 18 reviewable suggestions with a decision control; 22 questions with discovery routes; 889 depth slots from a fresh 32-club sweep with a like-for-like delta; deficiency matrix (232 pairings); injury deltas; luck panel; 4 empty gated leaderboards; line-by-line repo audit | https://sassnarep3-star.github.io/Own5/nfl-c98c6270/ | `c98c6270` (`nfl-c98c6270/`, `research/nfl-c98c6270/`, `.github/workflows/nfl-desk-c98c6270.yml`) |
| **NFL Week 10 injury-report desk (38430fe3)** | Official nfl.com Week 10 injury report read in full 2026-11-18: 347 rows, 28 clubs, 14 games, with claim checks, delta vs 2026-11-12, decision readiness and a Flagged for Review page. Source: `nfl-desk-38430fe3/` · [Desk](https://sassnarep3-star.github.io/Own5/nfl-desk-38430fe3/) |

| **NFL Week 11 Official-Source Desk** | NFL 2026 — official Week 11 slate (13 games, 6 byes; read 2026-11-18 03:13Z); Week 11 injury report **not published** at read time (URL serves Week 10); 25 NFL desk directories cross-checked against the 5c5f4aaf directory; 2 blocking and 8 review flags; 6 suggestions and 8 questions, all pending review; venues left blank | https://sassnarep3-star.github.io/Own5/nfl-desk-3cb7800c/ | `3cb7800c` (`nfl-desk-3cb7800c/`, `research/nfl-3cb7800c/`, `.github/workflows/nfl-desk-3cb7800c.yml`) |
| **NFL Venue & Schedule-Announcement Desk** | NFL 2026 — the venue of every Week 11 fixture (13/13) transcribed from the official NFL game centre (location + stadium as separate columns, per-row official links); the Mexico City question (3cb7800c flag F-03) resolved from the official game centre (Vikings at 49ers: MEXICO CITY / ESTADIO BANORTE); the league's dated schedule announcement (May 8, 2026 announcement; May 14, 2026 release hub) published beside the live Week 11 schedule page; clean dashboard + subpages, deterministic build, fail-closed verifier, 12 unit tests | https://sassnarep3-star.github.io/Own5/nfl-venue-390e13fd/ | `390e13fd` (`nfl-venue-390e13fd/`, `research/nfl-venue-390e13fd/`, `.github/workflows/nfl-venue-390e13fd.yml`) |

| **NFL Command Desk (4078a9ad)** | NFL 2026 — decision layer over the whole repo: 73-requirement ledger (27 met / 10 partial / 33 blocked / 2 rejected) with gate and clearing number per row; verified results corpus **150 games reconciled 32/32** to official standings (recomputed every build, with planted-defect tests); Week 11 13 fixtures + 6 byes with venue method stated, dated 2026-05-14 announcement beside it; 44 injury rows re-read, **17 stale** vs the 2026-11-12 capture incl. the three named Lions players now OUT; 5 pre-registered strategies, signal/staking separated, **0 certified**; 18 questions with discovery routes; 12 reviewable suggestions; 14 flags | https://sassnarep3-star.github.io/Own5/nfl-command-desk/ | `4078a9ad` (`nfl-command-desk/`, `research/nfl-4078a9ad/`, `.github/workflows/nfl-command-desk.yml`) |

Shared policy: **every table row carries a source link; values that cannot be confirmed from an official/primary source are left blank and published on a Flagged-for-Review page — never inferred. No performance claims; no bets placed; leaderboards empty until strategies pass validation gates.**

---

## NBA Line-Origination Lab (session 9c3a0a69)

**Live site:** https://sassnarep3-star.github.io/Own5/docs/ · **Executive summary:** [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md)

| Path | Contents |
|---|---|
| `EXECUTIVE_SUMMARY.md` | Objective, deliverables, key verified findings, limitations, next steps |
| `research/nba/strategies.md` | 8 candidate signal strategies (S1–S8) with hypotheses and sources |
| `research/nba/validation-gates.md` | 9 validation gates (G0–G8) every strategy must pass |
| `research/nba/correlations.md` | Correlation framework C1–C10; numeric values intentionally blank pending official-data computation |
| `research/nba/skill-vs-luck.md` | Luck removal: de-vigged CLV grading, shrinkage, permutation nulls, falsification |
| `research/nba/leaderboard.md` | Competition design: scoring, divisions, reward tiers, anti-gaming rules |
| `analysis/prop_correlations.py` | Computes prop correlations from official NBA box scores (nba_api / CSV); never emits placeholders |
| `analysis/validation_gates.py` | Gate checker (G3 CLV bootstrap, G5 permutation null) for a logged-bet CSV |
| `docs/` | Static NBA dashboard (10 pages) |

Source tiers: **OFFICIAL** (NBA league sources) · **PRIMARY** (peer-reviewed / preprint / author-hosted research) · **INDUSTRY** (betting-industry conventions, concepts only — flagged where they carry numbers).

---

# OWN5 · NFL Research Desk

**Live dashboard:** https://sassnarep3-star.github.io/Own5/
**Executive summary:** [research/EXECUTIVE_SUMMARY.md](research/EXECUTIVE_SUMMARY.md) · [site version](executive-summary.html)

Evidence-first research into NFL line origination, singles, parlays, player props and prop combinations. A static, responsive dashboard with source-linked tables, category filters, search and CSV export. No account, secret, backend or manual data entry is needed to browse it.

## Evidence status · 2026-11-02

- 14 primary sources checked (including the official initial GitHub repository tree) within explicitly documented scopes; 11 source-backed definitions.
- 8 **proposed, untrained** strategy candidates; 7 mandatory validation gates; 6 correlation questions.
- **0 validated strategies, 0 measured correlations, 0 published bets.** Empirical prices, probabilities, samples, returns, ranks and prize amounts are blank (`null`), not inferred.
- Timestamped historical official-source prices, matched outcomes, pregame features and complete prop/combination settlement rules were not obtained. These gaps are published on [Flagged for Review](https://sassnarep3-star.github.io/Own5/pages/review.html) and on the [session detail flagged page](flagged.html).
- Competition governance and non-cash badges are proposals. No funded cash rewards or actual payout service.

Luck cannot be eliminated from sports outcomes. Statistical evidence and prospective replication reduce false confidence; they do not guarantee future returns. This is research, not betting advice, a live sportsbook, or a jurisdictional eligibility determination.

---

## NFL Strategy Lab (session arena-f1d30421)

**Live site:** https://sassnarep3-star.github.io/Own5/nfl-strategy-lab/ · **Executive summary:** [`research/arena-f1d30421/EXECUTIVE_SUMMARY.md`](research/arena-f1d30421/EXECUTIVE_SUMMARY.md) · **Flagged for Review:** [`research/arena-f1d30421/flagged.md`](research/arena-f1d30421/flagged.md)

Self-running line origination + skill-based strategy leaderboard: our own lines for all 15 games of
2026 Week 9 (official standings/schedule inputs, measured HFA 2.22→2.0 pts), 8 pre-registered
backtested strategies (1980–2024), validation gates G0–G7, and computed correlation values.

**Computed findings (reproducible via `scripts/`):** favorites cover 48.1% / home underdogs 52.6% /
overs 49.1% (10,729 games); best strategy (home dog ≥7, 56.37%, n=793) **fails** Bonferroni gate
(p=0.0134 > 0.00625) → zero strategies certified as skill, by design; a break-even bettor posts a
55% season over 200 bets 20.8% of the time (needs ~2,243 bets to prove true 55% skill);
2-leg −110 parlays need 27.47% joint vs ≈23.6% from break-even legs; QB passing yards vs top-WR
yards r = 0.76 (n=3,852 team-games) → same-game prop legs need empirical joint pricing.

| Path | Contents |
|---|---|
| `research/arena-f1d30421/` | methodology: line origination, strategies, validation gates, correlation, luck-vs-skill, leaderboard, flagged registry, executive summary |
| `data/` (base_rates, correlation_*, backtest_results, luck_skill, model_lines_2026_wk9, verified_official_results) | computed CSVs + verified official tables, every row source-linked |
| `scripts/compute_analysis.py`, `compute_prop_correlations.py`, `originate_lines.py` | analysis engine + line origination (inputs pinned to commit SHAs) |
| `scripts/build_site.py`, `verify_site.py` | generates `nfl-strategy-lab/` from the CSVs; line-by-line check (every row sourced or explicitly blank+flagged) |

```sh
python3 scripts/download_data.sh && python3 scripts/compute_analysis.py
python3 scripts/compute_prop_correlations.py && python3 scripts/originate_lines.py
python3 scripts/build_site.py && python3 scripts/verify_site.py
```


---

## NFL Line Lab (session arena-44bc1e2f)

**Live site:** https://sassnarep3-star.github.io/Own5/line-lab/ · **Executive summary:** [`line-lab/executive-summary.html`](line-lab/executive-summary.html) · **Flagged:** [`line-lab/flagged.html`](line-lab/flagged.html) · **Verification:** [`line-lab/verification.html`](line-lab/verification.html)

Complete 2026 line-origination project built in one autonomous session: official standings (nfl.com) plus a full Weeks1–9 game log reconciled **line-by-line —32/32 teams' W-L-T and PF/PA match official standings exactly** (`python3 tools/reconcile.py`); ESPN/DraftKings Week8+9 boards with open-line attribution flags; Pythagorean walk-forward backtests with luck-adjusted gates (home-field and momentum strategies rejected on2026 data; Pyth picks61/103=.592, p=.0756 → pending); Week9 model-vs-market divergences flagged as candidates, not bets. Rebuild: `python3 tools/build_line_lab_site.py && python3 tools/link_check.py`.

## Pages

[Overview](https://sassnarep3-star.github.io/Own5/) · [Strategy lab](https://sassnarep3-star.github.io/Own5/pages/strategies.html) · [Line origination](https://sassnarep3-star.github.io/Own5/pages/markets.html) · [Correlations](https://sassnarep3-star.github.io/Own5/pages/correlations.html) · [Validation](https://sassnarep3-star.github.io/Own5/pages/validation.html) · [Leaderboard](https://sassnarep3-star.github.io/Own5/pages/leaderboard.html) · [Sources](https://sassnarep3-star.github.io/Own5/pages/sources.html) · [Review](https://sassnarep3-star.github.io/Own5/pages/review.html)

### Session `0f468a47-own5` — full data-table detail pages (2026-11-02)

[Executive Summary](executive-summary.html) · [Strategies & Leaderboard](detail-strategies.html) · [Signals](signals.html) · [Validation Gates](detail-validation.html) · [Correlations](detail-correlations.html) · [Bet Types & Combos](bet-types.html) · [Data & League Facts](data.html) · [Sources registry](detail-sources.html) · [Flagged for Review](flagged.html)

These root-level pages render every `data/*.csv` row in full, each with its official `source_url`, plus the 2026-11-02 verified snapshot (32-team standings, Week 8 results, byes, passing leaders) and in-repo computed correlations (e.g., net points/game vs win% r = 0.8391, n = 32, from [nfl.com/standings](https://www.nfl.com/standings/)).

## Reproduce locally

Python 3.11+ builds the site and runs its core tests using only the standard library. Node 22 and npm are needed only for browser tests.

```sh
python scripts/seed.py                 # Deterministic reviewed register; not a data crawler
python scripts/build.py                # Rebuild 8 static HTML pages
python -m unittest discover -s tests -v
node --check assets/app.js
npm ci --ignore-scripts                 # Test-only Chromium and Playwright dependencies
python -m http.server 3000 --bind 0.0.0.0
# In another terminal:
npm run test:browser
```

Open http://localhost:3000 locally. All browser assets and page navigation use relative URLs, including GitHub Pages project-path hosting. The production site has no npm runtime dependency. No external fonts, analytics or third-party JavaScript are loaded. Tables and source links remain available without JavaScript; search, filters and CSV require it.

`npm run test:browser` requires Linux/Chromium-compatible runtime libraries. Bundled NSS/NSPR support is extracted to an OS temporary directory by the test harness. Screenshots are ignored scratch artifacts.

### Session `0f468a47-own5` toolchain (detail pages)

```sh
python3 tools/seed_data.py              # writes all data/*.csv with per-row source_url
python3 tools/compute_correlations.py   # Pearson r from official standings snapshot (asserts NET=PF-PA, PCT, sumW=sumL)
python3 tools/build_site.py             # renders the detail pages + data/*.json from CSVs + research/*.md
python3 tools/check_site.py             # verifies every CSV row has a source link; no broken internal links
```

## Repository map

- `data/research.json`: reviewed records, primary-source scopes, missing empirical fields and review items.
- `data/*.csv` / `data/*.json` (session `0f468a47-own5`): 15 source-linked data tables (sources, league facts, teams, byes, standings snapshot, Week 8 results, passing leaders, bet types, bet combos, signals, validation gates, strategies, leaderboard, correlations, flagged items).
- `scripts/seed.py`: canonical reviewed register generator. Change this first if revising research, then regenerate.
- `scripts/build.py`: deterministic static page generator. HTML in root and `pages/` is generated output, committed for Pages.
- `scripts/analytics.py`: input-checked pricing, de-vig, Pearson, Brier, Holm and fail-closed audit-declaration utilities. Synthetic tests are not NFL results.
- `tools/` (session `0f468a47-own5`): seed/compute/build/check pipeline for the detail pages above.
- `assets/`: dependency-free responsive UI and client-side table tools.
- `research/`: executive summary, methodology/data contracts and source-verification record (uppercase files = session `arena-cd43258e`; lowercase files = session `0f468a47-own5`, incl. `verification-log.md`).
- `tests/`: Python integrity/math tests and Chromium desktop/mobile interaction tests.
- `.github/workflows/verify.yml`: rebuild, row/link checks, math tests and browser smoke tests on pushes and PRs.
- `COORDINATION.md`: ownership, verification, integration and publication history (all sessions).
- `nfl-strategy-lab/` + `research/arena-f1d30421/` (session `arena-f1d30421`): NFL Strategy Lab site and methodology; `scripts/compute_analysis.py`, `compute_prop_correlations.py`, `originate_lines.py`, `build_site.py`, `verify_site.py`.

## Verification and deployment

Every data-table row carries an official source link. On project-policy and strategy rows, those links are methodological references, **not verification that the policy is officially endorsed or the strategy profitable**. The external review scope is the precise finding recorded in each source entry, not every line of every linked website. See [the verification log](research/VERIFICATION.md) and [the session 0f468a47-own5 verification log](research/verification-log.md).

GitHub Pages was already configured from `main` at repository root. `.nojekyll` publishes the committed static files directly; the separate verification workflow checks them before integration. The integration PR, checks and Pages build result are recorded in [COORDINATION.md](COORDINATION.md). No API keys or betting credentials are stored or requested. Nothing places bets or sends financial transactions.

## Responsible gambling

Sports betting is restricted to adults of legal age in their jurisdiction and carries real risk of loss. Help is available 24/7 and confidential: **1-800-GAMBLER (1-800-426-2537)**, text 800GAM, or chat — [National Council on Problem Gambling](https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/).

---

## Own5 Evidence Desk (session e0e66278)

**Live desk:** https://sassnarep3-star.github.io/Own5/own5-desk/ · **Executive summary:** [docs/EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md) · **Flagged for Review:** https://sassnarep3-star.github.io/Own5/own5-desk/review.html

An additive, source-audited NFL research desk that preserves the existing root dashboard, NBA lab, NFL Strategy Lab and NFL Line Lab. It publishes 15 independent Week 9 research lines, six registered strategy families, 11 fail-closed validation gates, a 17-game Burrow–Chase correlation study, 78 verified fact rows and 13 review flags. **0 strategies qualify and 0 rewards are issued.** Market odds, current props, edge and CLV remain blank because no verified sportsbook archive was obtained.

| Path | Contents |
|---|---|
| `own5-desk/` | Generated static desk served by legacy Pages at `/Own5/own5-desk/` |
| `data/own5_desk/` | This session's source register, verified facts, derived lines, correlations, strategies, leaderboard and review items |
| `research/evidence/`, `research/build_snapshot.py` | Frozen official excerpts and typed extraction/reconciliation |
| `nfl_model/`, `tests/test_math.py`, `tests/test_model.py`, `tests/test_contracts.py` | Standard-library modeling, settlement, correlation, contracts and gates |
| `site/`, `scripts/build_data.py`, `scripts/check_site.py`, `scripts/publish_desk.py` | Desk generator, integrity checks and additive legacy-Pages publication |
| `docs/METHODOLOGY.md`, `docs/SOURCE_AUDIT.md`, `docs/REQUIREMENTS.md`, `docs/VERIFICATION_REPORT.md` | Protocol and verification record |

```sh
npm ci --ignore-scripts
npm run desk:check      # combined unit tests + desk data/site build + link/provenance audit
npm run desk:publish    # copy verified dist/ into own5-desk/ for legacy Pages
npm run desk:start      # local desk preview on 0.0.0.0:8000
```

The existing root dashboard and its CI guard are unchanged. This desk is published as an additive subdirectory because GitHub Pages is already served from `main` at `/` by earlier sessions.

## NBA Desk — own lines from official data (session 4396568c)

Live: https://sassnarep3-star.github.io/Own5/nba-desk/index.html · Code and data: `nba-desk/` · Write-ups: `research/nba-4396568c/`.

Originates 16 NBA lines (2026-11-04 and 11-05) from official NBA.com team data, tests the method out of sample, measures team-level correlations, pre-registers six strategies (singles, parlays, prop combos) behind nine fail-closed gates, and tabulates luck-vs-skill sample sizes. **0 strategies qualify, 0 rewards are issued and no market quotes were verified**; 15 flags are listed on the *Flagged for Review* page. Every table row links to the official page it came from; unconfirmed values are blank.

Reproduce: `python3 nba-desk/analysis.py && python3 nba-desk/build.py && python3 -m unittest discover -s nba-desk/tests -q && python3 nba-desk/check.py`.

---

## NBA Signal Lab (session 6d508fee)

**Live site:** https://sassnarep3-star.github.io/Own5/nba-signal-lab/index.html · **Executive summary:** [`research/nba-signal-lab/EXECUTIVE_SUMMARY.md`](research/nba-signal-lab/EXECUTIVE_SUMMARY.md) · **Flagged for Review:** https://sassnarep3-star.github.io/Own5/nba-signal-lab/flagged.html

| Path | Contents |
|---|---|
| `nba-signal-lab/` | Pages site (11 pages): dashboard, executive summary, own model lines, correlations, strategies & gates G01–G10, luck-vs-skill, leaderboard, verified data (125 player-game rows + 60 team rows, every row source-linked), analysis, verification, flagged-for-review |
| `nba-signal-lab/data/` | Hand-transcribed official datasets (2026-27 + 2025-26 standings & team stats, 2025-26 Dončić/Edwards game logs with per-row nba.com game URLs, 2026-11-04 slate) + computed `outputs.json` |
| `nba-signal-lab/compute.py` | Deterministic engine: 16/16 verification checks (cross-page agreement, scoring identities, official-leader checksums), model lines, correlations (Fisher-z CIs, phi/lift for prop combos, lag-1 independence), luck engine (exact binomial tails, power analysis, deflated scoring, multiple-testing bounds) |
| `research/nba-signal-lab/` | `EXECUTIVE_SUMMARY.md`, `data-notes.md` (source register + transcription protocol + source irregularities), `methodology.md` |

Verified highlights: same-game prop legs hit 10–27% above the independence product (phi table);
lag-1 PTS autocorrelation ≈ 0 (cross-game parlay independence holds); a true 55% bettor needs
≈2,243 graded bets to prove skill vs −110 break-even; **0 strategies certified**, market/odds
columns blank + flagged. Shared policy holds: every row source-linked, unverifiable values blank
and published on the Flagged page, never inferred.
---
## NBA Line Commission (session arena-a46d621e, snapshot 2026-11-05)

**Live site:** https://sassnarep3-star.github.io/Own5/nba-commission/index.html ·
**Executive summary:** [`research/nba-commission/EXECUTIVE_SUMMARY.md`](research/nba-commission/EXECUTIVE_SUMMARY.md) ·
**Flagged for review:** https://sassnarep3-star.github.io/Own5/nba-commission/flagged.html

The **2026-11-05 official snapshot**, its own lines, and the repository's first *cross-board
reconciliation audit*. Six NBA boards already existed here, each frozen on 2026-11-02 … 11-04; none had
been re-verified against the official pages on a later date. This board re-fetches, recomputes and
records the differences rather than assuming the earlier work was right.

| Path | Contents |
|---|---|
| `nba-commission/` | 14-page dashboard site: own lines, player props, correlations, strategies, gates G01–G12, skill-vs-luck, leaderboard, verified data, repo audit, verification, sources, flagged |
| `nba-commission/data/` | 2026-27 standings (30 rows), team traditional stats (30 rows), 2026-11-05/06 slate (11 rows), 2026-27 game logs (12 rows), inherited 2025-26 logs (125 rows) and priors (30 rows), computed `outputs.json` — every row carries an official nba.com `source_url` |
| `nba-commission/compute.py` | deterministic engine: 11 data checks, own lines (7-variant sensitivity), correlations (Fisher-z), prop-combo joint prices, exact-binomial power, gates, leaderboard, flags |
| `nba-commission/build.py`, `verify.py`, `checks/` | site builder, provenance/link/render/idempotency audit, 18 unit tests |
| `research/nba-commission/` | `EXECUTIVE_SUMMARY.md`, `methodology.md`, `data-notes.md`, `repo-audit.md` |

Verified highlights (all computed in-repo, all source-linked): net rating vs win% **r = 0.9206**
[0.8385, 0.9619] (n = 30); PTS × 3PM **r = 0.7165** (n = 137) and a same-game PTS≥25 + 3PM≥3 combo that
hits **65.7%** vs 56.5% if independent (lift ×1.16, so a marginal-multiplying parlay prices it
~16% too generously); lag-1 points correlation +0.056 / −0.041 (cross-game legs look independent, n small);
a 55% edge needs **≈2,248 graded bets** to clear α = 0.05 / 80% power against a −110 break-even of
0.52381; the 2026-27 home/road split (62–59, p = 0.856) **does not** measure home-court advantage, so
HFA = 2.5 pts stays a flagged assumption with 0.0 and 3.0 runs published per game.
**0 of 8 strategies certified, 0 graded bets, market columns blank and flagged (F01)** — no sportsbook
price was verified in this session.

Repo audit result: earlier boards are arithmetically sound (125/125 log identities, published
PTS × 3PM correlation reproduced to four decimals, 6/6 independently re-fetched rows exact) and the
2026-11-03 snapshot reconciles to today's standings through exactly the 14 official games of 11-04.
One real defect found and flagged, not fixed: an inherited CSV header contains U+0430 CYRILLIC SMALL
LETTER A (`blkа_pg`) — F13. Repo-wide internal links: 0 broken across 153 pages.

```sh
python3 nba-commission/compute.py && python3 nba-commission/build.py && python3 nba-commission/verify.py
python3 -m unittest discover -s nba-commission/checks
```

## NBA Evidence Desk — session 61a311c2

**Live site:** https://sassnarep3-star.github.io/Own5/nba-research-61a311c2/index.html · **Executive summary:** [`research/nba-research-61a311c2/EXECUTIVE_SUMMARY.md`](research/nba-research-61a311c2/EXECUTIVE_SUMMARY.md) · **Flagged for Review:** https://sassnarep3-star.github.io/Own5/nba-research-61a311c2/review.html

Additive, evidence-first NBA desk: 241 canonical source-linked rows (237 verified values, 4 blank availability rows flagged), 434-file baseline inventory, 11 model-only Nov 5–6 lines, 12 within-player correlations, 10 threshold-combo frequencies, 47 chronological forecast rows, 6 registered strategies and G01–G12 fail-closed gates. **0 strategies qualify; no ROI, probabilities, ranks or funded rewards are fabricated.** 19 irregularities/gaps are published on the Flagged for Review page.

Reproduce: `python3 nba-research-61a311c2/engine.py && python3 nba-research-61a311c2/audit_repo.py && python3 nba-research-61a311c2/build.py && python3 -m unittest discover -s nba-research-61a311c2 -p 'test_*.py' -v`.



---

## SF Rent Review · evidence-first dashboard (session c334a668)

**Pages path:** https://sassnarep3-star.github.io/Own5/sf-rent-review/ · **Executive summary:** [`research/sf-rent-review/EXECUTIVE_SUMMARY.md`](research/sf-rent-review/EXECUTIVE_SUMMARY.md) · **Flagged for review:** [`sf-rent-review/review.html`](sf-rent-review/review.html)

An additive, privacy-first research site on San Francisco rent increases. It
links each table row to an official source, leaves unverified property-specific
values blank, distinguishes policy suggestions from rules, and does not issue a
notice or legal clearance. The source snapshot is 2026-11-06; check the
[Rent Board's current rates](https://www.sf.gov/reports--current-rates-including-rent-increase-relocation-sec-deposit)
and obtain legal advice before action. See [`sf-rent-review/README.md`](sf-rent-review/README.md)
for reproducible generation and tests.

## SF Rental Increase Review — Outer Sunset 94122 (session e028ae77)

**Live site:** https://sassnarep3-star.github.io/Own5/sf-rent-94122/index.html · **Executive summary:** [`research/sf-rent-94122/EXECUTIVE_SUMMARY.md`](research/sf-rent-94122/EXECUTIVE_SUMMARY.md) · **Flagged for Review:** https://sassnarep3-star.github.io/Own5/sf-rent-94122/flagged.html · Companion brief: [`rental-increase-sf/`](rental-increase-sf/index.html) (session 7659538a)

Anonymized, source-linked review of reasonable rental increases for two rent-controlled units in a 1940 building in SF 94122. Key verified values: SF annual allowable increase **1.6%** (3/1/2026–2/28/2027; 60% of Bay Area CPI-U), once per 12 months, 30/90-day written notice, rent increase license required, banking rules, AB 1482 (8.8% SF region 8/1/2026–7/31/2027, not operative where the local ordinance is stricter), Costa-Hawkins vacancy decontrol, and the federal Fair Housing Act (no federal rent cap; anti-discrimination). 20 official sources; every table row source-linked; unverifiable values left blank and published on the Flagged for Review page (F01–F12). Tenant identities anonymized (placeholder names); dates/amounts retained as user-provided and marked unverified. Not legal advice.

Reproduce/verify: `python3 sf-rent-94122/build.py && python3 sf-rent-94122/verify.py`.

---

## NFL Decision Desk (session 38a1fc27, 2026-11-12)

**Live site:** https://sassnarep3-star.github.io/Own5/nfl-decision-desk-38a1fc27/ ·
**Executive summary:** [`research/38a1fc27/EXECUTIVE_SUMMARY.md`](research/38a1fc27/EXECUTIVE_SUMMARY.md) ·
**Verification:** [`research/38a1fc27/VERIFICATION.md`](research/38a1fc27/VERIFICATION.md) ·
**Flagged:** [`research/38a1fc27/FLAGGED.md`](research/38a1fc27/FLAGGED.md)

A self-running desk for the current season that adds the pieces no earlier scope had: an explicit
**suggestions register with a decision workflow**, a **questions register** gating decisions, and an
**injury / lineup-depth engine** that measures what a missing starter is actually worth. It also
re-derives the claims published by earlier sessions line by line.

| Path | Contents |
|---|---|
| `nfl-decision-desk-38a1fc27/` | 14-page static site (overview, requirements, suggestions, questions, own lines, strategies, gates, correlations, injuries & depth, repo audit, summary, sources, flagged, verification) |
| `research/38a1fc27/` | methodology, verification log, audit, pre-registration, gate definitions, flags, questions, requirements |
| `data/decision-desk/` | computed tables (own lines, injuries, deficiency, ledger, correlations, claim checks) + `raw/` pinned inputs with SHA-256 provenance |
| `tools/decision_desk/` | fetch → parse → compute → export → build → verify pipeline (Python standard library only) |

**Headline results (all reproducible):** own spread and total for all 14 Week 10 games; one
percentage point of relative lineup deficiency is worth −0.039 points of margin (p = 6×10⁻⁵) of
which the market already prices ≈49%; fading the more-injured team is 51.4% ATS over 782 bets
(p = 1.0), i.e. **no betting edge**; QB passing yards vs his WR1's yards correlate at r = 0.50 and
the empirical same-team joint hit rate is 32.5% versus 24.8% if independent; **zero strategies
certified** because gate G4 (closing-line value) and G8 (verified operator price) cannot pass
without a timestamped price history.

**Irregularities flagged for review:** four previously published figures do not reproduce
(home-underdog cover rates, home dogs +7, the 0.76 QB/WR correlation and the 20.8% luck figure), and
this session's own first injury backtest is retained as a documented sign-convention error that
manufactured a false 57.4% edge.

```sh
python3 tools/decision_desk/fetch_sources.py     # official pages + pinned mirrors (runner only)
python3 tools/decision_desk/build_all.py         # parse, compute, export, audit
python3 tools/decision_desk/build_site.py        # render nfl-decision-desk-38a1fc27/
python3 tools/decision_desk/verify.py            # fails on any unsourced row or broken link

## NFL Decision Desk — line origination, signals & depth tracking (session 26d4cafb)

**Live site:** https://sassnarep3-star.github.io/Own5/nfl-desk-26d4cafb/ ·
**Executive summary:** [`research/nfl-26d4cafb/executive-summary.md`](research/nfl-26d4cafb/executive-summary.md) ·
**Flagged for Review:** https://sassnarep3-star.github.io/Own5/nfl-desk-26d4cafb/flagged.html ·
**Dossier index:** [`research/nfl-26d4cafb/README.md`](research/nfl-26d4cafb/README.md)

An 18-page, official-source-only analytics dashboard for the **2026 NFL season, Week 10**
(snapshot 2026-11-12 UTC). It reviews the repository line by line against official sources,
originates its own Week 10 lines, tracks Offense/Defense 1st-through-4th-string depth
deficiencies, runs signal strategies through ten fail-closed validation gates on a leaderboard,
publishes correlation and prop-combo values with Frechet-Hoeffding bounds, and separates luck
from selective skill.

Key verified values: **136** completed official games reconciling **32/32 teams with 0
mismatches** on W/L/T/PF/PA to [nfl.com/standings](https://www.nfl.com/standings/); **16** of
those games were missing from the repository's 2026-11-02-frozen boards and were re-fetched from
NFL.com; 2026 home-field advantage is **-0.054 pts** on 130 non-neutral games
(95% CI [-2.34, +2.23], p = 0.96) versus the **+2.0** the existing boards assume; **2 of 10**
strategies clear all ten gates; **16** items are open on the Flagged for Review page
(none blocking). No official market or player-prop lines exist, so market, price, edge and CLV
columns are deliberately left blank rather than filled from a third-party scrape.

The improvement proposals on the [Suggestions](https://sassnarep3-star.github.io/Own5/nfl-desk-26d4cafb/suggestions.html)
page are **proposals only** — no site-wide change was implemented from this session, and a
reviewer picks a path (`PATH-A`..`PATH-D`) before anything is changed.

Reproduce/verify:

```
cd nfl-desk-26d4cafb
python3 engine.py            # rebuild all CSV/JSON from the official inputs
python3 build.py             # render the 18-page dashboard
python3 export_research.py   # regenerate research/nfl-26d4cafb/*.md
python3 verify.py            # 25 line-by-line checks (0 failures)
python3 -m unittest discover -s nfl-desk-26d4cafb/tests   # 60 tests
```

---

## NFL line-origination and strategy desk (`nfl-desk-d38e90c5`, session d38e90c5)

A standalone, official-source-only desk that **originates its own NFL lines** and publishes them with
a model fair line, a market line and the difference as three separate columns, side/spread first,
total second, moneyline third.

Live site: https://sassnarep3-star.github.io/Own5/nfl-desk-d38e90c5/

What it contains:

| Page | Content |
|---|---|
| Overview | landing page with the headline numbers and the publication order |
| Requirements | every requirement with the artefact that satisfies it and its honest status |
| Executive summary | findings, evidence and what is deliberately blank |
| Own lines | 297 originated markets (99 spread, 99 total, 99 moneyline) with fair line / market line / difference |
| Price snapshots | append-only store, opening + closing record for every originated market |
| Verified results | 137 official final scores, reconciled against the official standings |
| Leaderboard | **signal quality** and **staking performance** as two separate scorecards |
| Correlations | official-source correlations, `n` published with every value |
| Demotion gate | fail-closed gate with an explicit live -> paper decision per strategy |
| Strategies | single bets, parlays and player-prop combinations with their blocking reasons |
| Injuries / Depth tracker | 347 official injury rows with 1st-4th string depth and named replacements |
| Questions and unknowns | questions, information, answers, unknowns and discovery steps |
| Suggestions | options and the recommended path before implementation |
| Repo audit | line-by-line review of the existing NFL desks with drift and irregularities |
| Flagged for review | every unverified value and irregularity, with manual-review links |
| Sources | the official source register behind every published row |

Key verified values (2026-11-14): **137** completed official games reconciling **32/32** clubs with
**0** mismatches on W/L/T/PF/PA (aggregate PF = PA = 6,291); **73** walk-forward out-of-sample
predictions with MAE **10.24** points, Brier **0.2291** vs a **0.2443** base-rate baseline, log loss
**0.6480** vs **0.6818**, winner hit rate **60.3%** and calibration slope **0.869**; **347** official
Week 10 injury rows matched to the official depth charts of all **32** clubs (**31** transcribed,
Houston publishes an image only).

No official market or player-prop prices exist: `nfl.com/betting/` returns 404 and no operator feed
was reachable, so market line, market price, difference, CLV and market ROI are deliberately left
**blank** and published on the Flagged for Review page instead of being filled from a third-party
scrape. All six strategies are `PAPER`: the gate fails closed, so nothing is promoted while a
required criterion cannot be evaluated.

Reproduce and verify:

```
cd nfl-desk-d38e90c5
python3 pipeline.py     # rebuild every dataset from the pinned official inputs
python3 build_site.py   # render the 20-page site
python3 verify.py       # 115 line-by-line checks (0 failures)

---

## NFL Price-Snapshot & Verified-Results Desk (session 3fb93d11, 2026-11-14)

**Live site:** https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/ ·
**Executive summary:** [`research/nfl-3fb93d11/EXECUTIVE_SUMMARY.md`](research/nfl-3fb93d11/EXECUTIVE_SUMMARY.md) ·
**Flagged for Review:** https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/flagged.html

A 16-page desk built around eight requirements: a **price-snapshot store** recording opening and
closing numbers for every market we originate; a **verified results feed** so backtests and ROI can
be computed at all; origination in the order **side → total → moneyline**; **model / market /
difference** as three separate columns; a **leaderboard that scores signal separately from staking**;
tracking the **depth of a replacement** rather than the fact of one; **correlations from official
numbers only, each with its n**; and a **demotion gate** that returns a live strategy to paper.

Key verified values: **137** official 2026 finals, rebuilt into standings that reproduce
[nfl.com/standings](https://www.nfl.com/standings/league/2026/REG) **32/32 with 0 mismatches**; the
pinned mirror agrees on **136/137** and disagrees on none; **78** originated markets (26 games ×
side, total, moneyline) with **σ = 12.925** and home-field advantage **+0.213 pts**; the side model's
margin forecast correlates with the actual margin at **r = 0.3187** (p = 0.0060, n = 73); the totals
model is worth **0.02 points** over a constant; **705** depth slots across **31** clubs with **7**
currently filled by a backup; **9** admissible correlation pairs and **7** previously published
values moved to a withheld register; **0 strategies certified** and **0 bets placed**.

The price store's opening and closing rows are **empty and flagged**, because **nfl.com publishes no
betting prices**. That single gap is why gate G2 fails for every family. It is recorded explicitly
rather than filled in.

Reproduce/verify:

```sh
python3 nfl-desk-3fb93d11/run.py      # rebuild every CSV + the 16-page site (deterministic)
python3 nfl-desk-3fb93d11/verify.py   # row-level proof: every published row is sourced or UNVERIFIED
python3 -W ignore -m unittest discover -s nfl-desk-3fb93d11/tests   # 51 tests
```

---

## NFL Market Desk — consolidation + executable pricing core (session 83a7d6a8, 2026-11-15)

**Served at:** https://sassnarep3-star.github.io/Own5/nfl-market-desk/ ·
**Executive summary:** [`research/nfl-83a7d6a8/EXECUTIVE_SUMMARY.md`](research/nfl-83a7d6a8/EXECUTIVE_SUMMARY.md) ·
**Methodology:** [`research/nfl-83a7d6a8/METHODOLOGY.md`](research/nfl-83a7d6a8/METHODOLOGY.md) ·
**Verification log:** [`research/nfl-83a7d6a8/VERIFICATION_LOG.md`](research/nfl-83a7d6a8/VERIFICATION_LOG.md)

A 13-page desk that reconciles the eleven NFL desks already in this repository rather than adding a
twelfth unaudited slice. It tracks the reviewer's brief as **78 numbered requirements**, each with a
machine-checked evidence pointer, its blocking gate and **the number that would clear it**; a
**34-item flag register** (14 inherited from PR #79 under an `INH-` namespace, 20 from this desk under
`OWN-`); **15 questions** with the cheapest route to each answer; and **19 suggestions**, each with
its options, the recommended path and the rule that would reverse it.

Verified values: **145** official 2026 finals reconciling **32/32** against
[nfl.com/standings](https://www.nfl.com/standings/league/2026/REG) on W-L-T, PF and PA; **39**
originated Week-11 markets with fair line, market line and difference as three separate columns;
**195** price-snapshot rows of which **78 carry a number and 117 are empty by policy with a flag**;
**9** pre-registered strategy families with published SHA-256 rule files; **264** graded bets;
**12** validation gates (**6 MET, 1 PARTIAL, 5 NOT MET**); **3** control baselines on the same games;
**5** official correlations each with its n and p, and 5 withheld with the reason; **551** depth rows
from **11** clubs with shared and empty slots preserved; **14** named replacements, all 2nd string,
**0** compounding; and **0** strategies certified, **0** bets placed, **0** rewards issued.

The model is honest about itself: on the validation window (weeks 5–8) its Brier score is **0.2427**
against the market's **0.2192** on 57 games, and on the final holdout (weeks 9–10) it is **0.1524**
against **0.1570** on 24 games. A 24-game holdout is not an edge and is not presented as one. The
personnel ablation gives **−1.892 points per extra unavailable player with a standard error of
2.260** — an interval spanning zero — so no injury penalty is applied anywhere, and the replacement
table is published as evidence rather than as an adjustment.

Reproduce/verify (stdlib only, no packages installed):

```sh
cd nfl-market-desk
python3 build_results.py && python3 build_model.py && python3 build_prices.py \
  && python3 build_strategies.py && python3 build_availability.py \
  && python3 build_registers.py && python3 build.py && python3 build_summary.py
python3 verify.py                      # 10 checks: row-level source coverage, links, evidence
                                       # paths, flag namespaces, hashes, drift, determinism
python3 tests/test_market_desk.py      # 27 tests
```

## NFL Decision Desk — questions, suggestions and verified schedule (session e1d60f5d, 2026-11-17)

**Live desk:** https://sassnarep3-star.github.io/Own5/nfl-desk-e1d60f5d/

A small, self-contained, source-verified decision desk. It publishes the **verified 2026 NFL standings** (32 teams, W-L-T/PF/PA/PCT reconciled to nfl.com) and the **Week 11 schedule** (13 games + 6 byes, with the Vikings@49ers Mexico City neutral-site game confirmed), plus:

- **Executive summary** — what we have, what we still need, bottom line.
- **Questions register** (10 questions, 7 blocking) — what we have, what we lack, and the cheapest route to each answer, before any decision can be reasonably made.
- **Suggestions register** (12 suggestions, 11 awaiting decision) — improvement paths with options, a recommended path, and the test that would change the call; nothing is implemented without a reviewer decision.
- **Sources register** (10 sources) and **Flagged-for-Review** (12 flags, 7 blocking) — every published value traces to an official source; unverified values are left blank and flagged, never inferred.

Every table row carries an official source link (nfl.com standings / schedule / game centre). No bets are placed, no performance is claimed, and no strategy is certified until it passes validation gates.

Reproduce/verify (stdlib only, no packages installed):

```sh
cd nfl-desk-e1d60f5d
python3 build.py            # deterministic rebuild of all 8 pages
python3 verify.py           # 241 row-level source/link/determinism checks, 0 failures
python3 -m unittest discover -s tests -v   # 16 tests, all passing
```

The build is byte-for-byte deterministic; CI re-runs it and fails on any drift (`git diff --exit-code`).


---

## NFL Decision Review Hub (session 3bba0722 · 2026-11-17)

**Review site:** https://sassnarep3-star.github.io/Own5/nfl-review-3bba0722/ ·
**Executive summary:** [`research/nfl-3bba0722/EXECUTIVE_SUMMARY.md`](research/nfl-3bba0722/EXECUTIVE_SUMMARY.md) ·
**Suggestions for review:** https://sassnarep3-star.github.io/Own5/nfl-review-3bba0722/suggestions.html ·
**Flagged for review:** https://sassnarep3-star.github.io/Own5/nfl-review-3bba0722/flagged.html

An additive, source-checked decision docket. It records the 2026-11-17 official-source recheck, 14 known/missing-information questions, 14 priority readiness gates, 13 unapproved suggestions and 13 flagged/rechecked findings. Each table row links to an official league, club, operator or government source, or is explicitly flagged; repository evidence is labeled separately. The hub does not modify earlier data, claim a strategy edge, publish market prices, or implement suggestions.

Key source caveats: the requested Week 12 NFL injury URL returned a Week 10 page; the reviewed NFL Game Book has a written-permission notice for other use; the Texans depth page is image-only in the retrieved content and the Packers page prefixes jersey numbers; the official NFL reserve list is now located, but older snapshots were not backfilled. Only one Game Book and two club depth pages were rechecked in this session, so this is not a complete 32-team audit.

Rebuild and verify (stdlib only):

```sh
python3 nfl-review-3bba0722/build_site.py
python3 nfl-review-3bba0722/verify.py
python3 -m unittest discover -s nfl-review-3bba0722/tests -v
```

---

## NFL portfolio integration — session a620f5a5 (2026-11-17)

**Entry point (after Pages deploy):** `https://sassnarep3-star.github.io/Own5/nfl-integration-a620f5a5/` ·
[Executive summary](nfl-integration-a620f5a5/EXECUTIVE_SUMMARY.md) ·
[Cross-desk audit](nfl-integration-a620f5a5/audit.html) ·
[Questions](nfl-integration-a620f5a5/questions.html) ·
[Suggestions](nfl-integration-a620f5a5/suggestions.html) ·
[Flagged for Review](nfl-integration-a620f5a5/flagged.html) ·
[Official sources](nfl-integration-a620f5a5/sources.html)

This is the repository-wide landing page for existing NFL decision desks. It adds the dated NFL Media
schedule-release announcement beside the live Week 11 schedule, links to the row-by-row readiness and
analysis pages, publishes a cross-desk audit, and provides a score-free prospective leaderboard view.
It does not copy raw Game Book player rows or make any strategy bet-eligible. The hub's read of the
official pages is dated 2026-11-17; the market desk's model/price/availability snapshots are dated
through 2026-11-15, while the separate e1d60f5d standings/schedule desk was read on 2026-11-17.
The hub also links the [a699fc53 row-level injury/transactions audit](nfl-audit-a699fc53/index.html),
the [e1d60f5d official standings and Week 11 schedule pages](nfl-desk-e1d60f5d/index.html), and the
[3bba0722 decision-review docket](nfl-review-3bba0722/index.html).

**Integration findings that remain open:** legacy strategy pages still display historical outcome
metrics despite the prospective-only requirement; operator opening/closing prices are not verified;
Week 10 injury tables disagree across captures; the Week 11 injury URL returned Week 10; the 32-team
roster/depth graph is incomplete; Game Book reuse requires written permission; fixture venue sources
are not all individual Game Centers; and the 78-row, 72-row and 14-gate readiness/review registers are unmapped.
All items are published with source links or explicit UNVERIFIED labels. Owning-session files are not
edited by this integration; see the cross-session requests in `COORDINATION.md`.

Rebuild and verify:

```sh
python3 nfl-integration-a620f5a5/build_site.py
python3 nfl-integration-a620f5a5/verify.py
python3 scripts/build.py
```

---

## NFL review desk · session 98a211b8

**Live page:** https://sassnarep3-star.github.io/Own5/nfl-98a211b8/ · **Flagged for Review:** https://sassnarep3-star.github.io/Own5/nfl-98a211b8/flagged.html

Bounded review, not another decision desk: a repo review register (each check linked), a dated capture log of the official nfl.com injury pages with a line-by-line comparison of 44 visible rows against the repo copy, links the NFL desk directory published by session 5c5f4aaf (PR #102) rather than duplicating it, and a Flagged for Review register. Sources: `nfl-98a211b8/data/sources.csv`. Rebuild and verify: `python3 nfl-98a211b8/build.py && python3 nfl-98a211b8/verify.py`.
