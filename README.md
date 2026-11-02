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
- `COORDINATION.md`: ownership, verification, integration and publication history (both sessions).

## Verification and deployment

Every data-table row carries an official source link. On project-policy and strategy rows, those links are methodological references, **not verification that the policy is officially endorsed or the strategy profitable**. The external review scope is the precise finding recorded in each source entry, not every line of every linked website. See [the verification log](research/VERIFICATION.md) and [the session 0f468a47-own5 verification log](research/verification-log.md).

GitHub Pages was already configured from `main` at repository root. `.nojekyll` publishes the committed static files directly; the separate verification workflow checks them before integration. The integration PR, checks and Pages build result are recorded in [COORDINATION.md](COORDINATION.md). No API keys or betting credentials are stored or requested. Nothing places bets or sends financial transactions.

## Responsible gambling

Sports betting is restricted to adults of legal age in their jurisdiction and carries real risk of loss. Help is available 24/7 and confidential: **1-800-GAMBLER (1-800-426-2537)**, text 800GAM, or chat — [National Council on Problem Gambling](https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/).
