# Own5 — Sports Line-Origination Research (multi-session)

This repository hosts work from **three parallel agent sessions** (see `COORDINATION.md`): an **NBA Line-Origination Lab** (session `9c3a0a69`, served at `/docs/`) and an **NFL Research Desk** with detail pages (sessions `cd43258e` and `0f468a47`, served at the site root).

| Dashboard | Scope | Live URL | Session |
|---|---|---|---|
| **NBA Line-Origination Lab** | NBA — singles, parlays, player-prop combos; validation gates; leaderboard design | https://sassnarep3-star.github.io/Own5/docs/ | `9c3a0a69` (`docs/`, `research/nba/`, `analysis/`, `EXECUTIVE_SUMMARY.md`) |
| **NFL Research Desk** | NFL — line origination, strategy lab, correlation questions, review register | https://sassnarep3-star.github.io/Own5/ | `cd43258e` + `0f468a47` (root, `pages/`, `data/`, `scripts/`, `tools/`, `tests/`) |
| **NFL Strategy Lab** | NFL — own lines from official data, pre-registered singles/parlays/prop combos, validation gates G0–G7, computed correlations, luck-deflated leaderboard | https://sassnarep3-star.github.io/Own5/nfl-strategy-lab/ | `arena-f1d30421` (`nfl-strategy-lab/`, `research/arena-f1d30421/`, `data/`, `scripts/compute_*`, `scripts/originate_lines.py`) |
| **NFL Line Lab** | NFL — reconciled W1–9 game log + standings (32/32 exact), W8/W9 lines, model-vs-market origination, gate-scored strategy leaderboard, flagged items | https://sassnarep3-star.github.io/Own5/line-lab/ | `arena-44bc1e2f` (`line-lab/`, `data/standings_2026.json`, `data/games_2026.json`, `data/lines_upcoming_2026.json`, `tools/reconcile.py`, `tools/build_line_lab_site.py`, `analysis/compute_metrics.py`) |
| **NBA Line Desk 2026-27** | NBA 2026-27 — official standings, team stats and Edwards logs; signals and correlations; luck-vs-skill; strategies with validation gates G1–G8; leaderboard; executive summary; flagged-for-review page | https://sassnarep3-star.github.io/Own5/nba-line-desk/ | `9cf7de11` (`nba-line-desk/`, `data/nba-2026-27/`, `research/nba-2026-27/`, `tools/nba_line_desk/`, `tests/test_nba_line_desk.py`) |

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
