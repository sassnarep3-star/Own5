# Own5 — NFL Line Origination & Skill-Based Strategy Leaderboard

**Live site (GitHub Pages):** https://sassnarep3-star.github.io/Own5/
**Executive summary:** [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) · **Flagged for Review:** [docs/flagged.md](docs/flagged.md)

A self-running analytics project that:

1. **Originates its own NFL lines** from official league data (`scripts/originate_lines.py` →
   `data/model_lines_2026_wk9.csv` — 2026 Week 9, all 15 games).
2. **Defines and tests betting strategies** — singles, cross-game parlays, and same-game player-prop
   combos — under pre-registered **validation gates** (G0–G7) that separate skill from luck.
3. **Measures correlation values** for parlay/SGP pricing (game-line legs ≈ independent; QB↔WR prop
   legs r = 0.76).
4. **Runs a leaderboard competition** with luck-deflated scoring and rewards that vest only for
   gate-passing strategies.

## Headline findings (computed, reproducible)

* Closing favorites cover **48.1%**; home underdogs **52.6%**; overs **49.1%** (10,729 games, 1980–2024).
* Best catalog strategy (home dog ≥7) hit **56.37%** (n=793) but **fails** the Bonferroni-corrected
  significance gate — **zero strategies certified as skill**, by design; S1/S2 continue live.
* A break-even bettor posts a "55% season" over 200 bets **20.8%** of the time; proving true 55%
  skill needs **~2,243 graded bets** (80% power).
* 2-leg fixed parlays need a **27.47%** joint hit rate that break-even legs (≈23.6%) cannot supply.

## Repository layout

| Path | Contents |
|---|---|
| `research/` | methodology: line origination, strategies, validation gates, correlation, luck-vs-skill, leaderboard |
| `data/` | computed CSVs + verified official tables (every row carries source links) · [data/README.md](data/README.md) |
| `scripts/` | analysis, prop correlations, line origination, site build + verification (inputs pinned to commit SHAs) |
| `docs/` | GitHub Pages site (generated from the CSVs by `scripts/build_site.py`) |
| `EXECUTIVE_SUMMARY.md` | the summary |
| `COORDINATION.md` | shared task board (parallel-session protocol), sources, verification log |

## Verification policy

Every table row has a source link to an official site or a pinned source. Values that cannot be
confirmed are **left blank and flagged** ([docs/flagged.md](docs/flagged.md) — F1–F11) — nothing is
ever inferred or filled in. Community datasets (historical lines, archived play-by-play) are pinned
to commit SHAs and flagged; game scores were spot-verified 16/16 against official nfl.com pages.

## Reproduce

```bash
python3 scripts/download_data.sh        # pinned inputs (play-by-play mirror; spreadspoke CSV is in data/raw/)
python3 scripts/compute_analysis.py     # base rates, correlations, backtests, luck tables
python3 scripts/compute_prop_correlations.py
python3 scripts/originate_lines.py
python3 scripts/build_site.py           # regenerate docs/ site from the CSVs
python3 scripts/verify_site.py          # line-by-line site check (links + sources)
```

*Research project — not betting advice.*
