# Own5 — NFL Lines & Strategies (self-originated, officially verified)

Own5 originates its own NFL betting-style lines and tests signal-generating strategies as a **leaderboard competition** —
single bets, parlays, and player-prop combos — built **only** on verified official NFL sources. Every table row on the
published site links to an official source; anything unverifiable is left **blank**, marked *unverified*, and published
on the **Flagged for Review** page. Nothing is inferred.

- **Live site:** GitHub Pages (main branch, repo root) — dashboard landing + category subpages under `pages/`.
- **As-of date:** 2026-11-02 (UTC). 2026 season data through Week 8; target slate = **2026 Week 9** (15 games from Thu 2026-11-05).
- **Session / branch:** `arena-09d847e1-own5` on `arena/09d847e1-own5` (see `COORDINATION.md` for the task board and handoff log).
- Analytics only — this is not wagering advice. Sports-wagering legality varies by jurisdiction (e.g., generally prohibited in South Korea); see flag F15.

## Contents

| Path | What it is |
|---|---|
| `index.html`, `pages/*.html`, `.nojekyll` | Static Pages site (inline styles only, no external assets) — generated, do not hand-edit |
| `scripts/analyze.py` | Analysis engine: verification checks, walk-forward backtest, correlations, gated strategies, leaderboard, Week 9 originated lines |
| `scripts/build_site.py` | Site generator (reads `data/` + `analysis/`, writes the HTML, runs an internal link check) |
| `data/` | Verified raw datasets (9 JSON files) + official source registry + flagged-items register |
| `analysis/` | Generated analysis outputs (6 JSON + `methodology.md` + `site_link_check.json`) |
| `docs/` | `repo-review.md` (line-by-line review with irregularities), `sources.md` (rendered source registry) |
| `EXECUTIVE_SUMMARY.md` | Executive summary with headline results |
| `COORDINATION.md` | Multi-session coordination: task board, claims, rules, handoff log, PR/merge record |

## Reproduce

```bash
python3 scripts/analyze.py     # data/*.json  -> analysis/*.json   (pure stdlib, no network, deterministic)
python3 scripts/build_site.py  # data/ + analysis/ -> index.html, pages/*.html, .nojekyll + link check
```

## Headline results (2026-11-02)

- Data verification: **10/10 automated consistency checks pass** (2025 + 2026 standings cross-foot exactly against the 120 final 2026 game results for all 32 teams).
- Walk-forward backtest, 2026 W1–W8 (120 games, no lookahead): model margin vs actual Pearson **r = 0.289**.
- Gate-approved strategies (all 6 validation gates, incl. binomial p<0.05 and W7–W8 holdout): **S2** selective spread direction (68.6% win rate, p=0.0055), **S4** same-game 2-leg parlay (ROI +40.5%, p=0.0052), **S3** total direction (63.3%, p=0.0022), **S1** spread direction all games (58.0%, p=0.0493). S5 (weekly parlay) fails the n≥30 gate; S6 (own line at −110) is the negative control and loses; S7 (W9 QB props) is unrated/flagged.
- Week 9 originated lines: 15 spreads/totals + 17 QB passing-yards prop lines (13 slots blank + flagged).
- Full detail: `EXECUTIVE_SUMMARY.md`, `analysis/`, and the live site pages.
