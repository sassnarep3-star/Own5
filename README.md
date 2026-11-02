# Own5 — Sports Line-Origination Research

This repository hosts **two independent, evidence-first research dashboards** built by parallel agent sessions (see `COORDINATION.md`):

| Dashboard | Scope | Live URL | Session |
|---|---|---|---|
| **NBA Line-Origination Lab** | NBA — singles, parlays, player-prop combos; validation gates; leaderboard design | https://sassnarep3-star.github.io/Own5/docs/ | `9c3a0a69` (`/docs`, `research/`, `analysis/`) |
| **NFL Research Desk** | NFL — line origination, strategy lab, correlation questions, review register | https://sassnarep3-star.github.io/Own5/ | `cd43258e` (repo root, `pages/`, `data/`, `scripts/`, `tests/`) |

Both share the same verification policy: **every table row carries a source link; values that cannot be confirmed from an official/primary source are left blank and published on a Flagged for Review page — never inferred. No performance claims exist anywhere in this repo; no bets have been placed; leaderboards are empty until strategies pass validation gates.**

---

## NBA Line-Origination Lab (session 9c3a0a69)

**Live site:** https://sassnarep3-star.github.io/Own5/docs/ · **Executive summary:** [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md)

| Path | Contents |
|---|---|
| `EXECUTIVE_SUMMARY.md` | Objective, deliverables, key verified findings, limitations, next steps |
| `research/strategies.md` | 8 candidate signal strategies (S1–S8) with hypotheses and sources |
| `research/validation-gates.md` | 9 validation gates (G0–G8) every strategy must pass |
| `research/correlations.md` | Correlation framework C1–C10; numeric values intentionally blank pending official-data computation |
| `research/skill-vs-luck.md` | Luck removal: de-vigged CLV grading, shrinkage, permutation nulls, falsification |
| `research/leaderboard.md` | Competition design: scoring, divisions, reward tiers, anti-gaming rules |
| `analysis/prop_correlations.py` | Computes prop correlations from official NBA box scores (nba_api / CSV); never emits placeholders |
| `analysis/validation_gates.py` | Gate checker (G3 CLV bootstrap, G5 permutation null) for a logged-bet CSV |
| `docs/` | Static NBA dashboard (10 pages) |

Source tiers: **OFFICIAL** (NBA league sources) · **PRIMARY** (peer-reviewed / preprint / author-hosted research) · **INDUSTRY** (betting-industry conventions, concepts only — flagged where they carry numbers).

---

## NFL Research Desk (session cd43258e)

**Live dashboard:** https://sassnarep3-star.github.io/Own5/
**Executive summary:** [research/EXECUTIVE_SUMMARY.md](research/EXECUTIVE_SUMMARY.md)

Evidence-first research into NFL line origination, singles, parlays, player props and prop combinations. A static, responsive dashboard with source-linked tables, category filters, search and CSV export. No account, secret, backend or manual data entry is needed to browse it.

### Evidence status · 2026-11-02

- 13 primary sources checked within explicitly documented scopes; 11 source-backed definitions.
- 8 **proposed, untrained** strategy candidates; 7 mandatory validation gates; 6 correlation questions.
- **0 validated strategies, 0 measured correlations, 0 published bets.** Empirical prices, probabilities, samples, returns, ranks and prize amounts are blank (`null`), not inferred.
- Timestamped historical official-source prices, matched outcomes, pregame features and complete prop/combination settlement rules were not obtained. These gaps are published on [Flagged for Review](https://sassnarep3-star.github.io/Own5/pages/review.html).
- Competition governance and non-cash badges are proposals. No funded cash rewards or actual payout service.

Luck cannot be eliminated from sports outcomes. Statistical evidence and prospective replication reduce false confidence; they do not guarantee future returns. This is research, not betting advice, a live sportsbook, or a jurisdictional eligibility determination.

### Pages

[Overview](https://sassnarep3-star.github.io/Own5/) · [Strategy lab](https://sassnarep3-star.github.io/Own5/pages/strategies.html) · [Line origination](https://sassnarep3-star.github.io/Own5/pages/markets.html) · [Correlations](https://sassnarep3-star.github.io/Own5/pages/correlations.html) · [Validation](https://sassnarep3-star.github.io/Own5/pages/validation.html) · [Leaderboard](https://sassnarep3-star.github.io/Own5/pages/leaderboard.html) · [Sources](https://sassnarep3-star.github.io/Own5/pages/sources.html) · [Review](https://sassnarep3-star.github.io/Own5/pages/review.html)

### Reproduce locally

Python 3.11+ builds the site and runs its core tests using only the standard library. Node 22 and npm are needed only for browser tests.

```sh
python scripts/seed.py                 # Deterministic reviewed register; not a data crawler
python scripts/build.py                # Rebuild 8 static HTML pages
python -m unittest discover -s tests -v
node --check assets/app.js
npm ci && npm run test:browser         # Optional Chromium link/render checks
```
