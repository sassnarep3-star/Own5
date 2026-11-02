# Executive Summary — NBA Line-Origination Project

**Repo:** sassnarep3-star/Own5 · **Site:** https://sassnarep3-star.github.io/Own5/docs/ · **Date:** 2026-11-02

## Objective

Build the research foundation, validation machinery, and competition structure for **originating NBA betting lines** — pricing markets independently and betting only when our price beats the available price — across three bet classes: **singles** (sides/totals/ML), **player props**, and **parlays / correlated prop combos (SGP)**.

## What was produced

1. **Strategy catalog (8 candidate signal families)** — rest/schedule spots, official-injury-report latency, home/travel/altitude context, streak persistence, pace-interaction props, usage-vacuum props, CLV-based line origination, and correlated-SGP construction. Each is documented with its hypothesis, build plan, and sources (`research/nba/strategies.md`). **None is claimed to be profitable; all are candidates pending validation.**
2. **Nine validation gates (G0–G8)** that every strategy must pass before leaderboard entry: pre-registration, parameter budget, walk-forward out-of-sample, de-vigged CLV with bootstrap CI, deflated-Sharpe/PBO multiplicity control, Monte Carlo permutation nulls, economic realism, parlay correlation audit, and fractional-Kelly staking (`research/nba/validation-gates.md`).
3. **Correlation framework** for parlays/prop combos: a 10-pair direction taxonomy (sourced), a prohibition on negatively correlated legs, and tooling to compute actual coefficients from official box scores. **Numeric r values are intentionally blank** — no official/primary source publishes them, and this project never infers values (`research/nba/correlations.md`, `analysis/prop_correlations.py`).
4. **Luck-removal methodology**: grade on de-vigged closing-line value (skill signal in ~200–500 bets) instead of W/L (needs thousands); empirical-Bayes shrinkage of scores; permutation nulls; falsification criteria required per strategy (`research/nba/skill-vs-luck.md`).
5. **Leaderboard competition**: divisions per bet class; score = 70% shrunken CLV + 20% flat-stake yield + 10% process compliance; Gold/Silver/Bronze reward tiers; anti-gaming rules including mandatory registration of all tried variants. **Current board is empty by design** (`research/nba/leaderboard.md`).
6. **Dashboard site** (GitHub Pages, `docs/`): landing page plus subpages per category, all findings in table form, every row carrying a source link and tier (OFFICIAL / PRIMARY / INDUSTRY), and a dedicated **Flagged for Review** page.

## Key verified findings (sources on every row — see site Sources page)

- **Back-to-backs are the most consistent schedule depressant:** 44% win rate vs. ~50% null across 2019/20–2024/25 (arXiv:2606.27957); winning likelihood rises significantly from B2B to one rest day (Esteves et al. 2021, PubMed 32172667).
- **Official injury-report timing creates a defined reaction window:** statuses due 5 p.m. local the day before, 1 p.m. game-day for back-to-back second games, game-day reports 11 a.m.–1 p.m. (official.nba.com).
- **Short-horizon persistence exists:** P(win | previous win) = 54.5% vs. 50% memoryless null (arXiv:2606.27957) — but any such effect is only an edge if the closing line misses it.
- **Home advantage is real but shrinking** (≈64% in the 1980s to ≈57% in the 2010s across major sports, Pollard & Gómez 2021 as cited in IJRSS; exact recent NBA percentages from third-party datasets are flagged, not asserted).
- **CLV is the accepted skill metric**; de-vig first, benchmark against a sharp close, and expect statistical signal in hundreds, not thousands, of bets (industry convention, flagged as such).

## Honest limitations (flagged, not hidden)

- **No numeric prop correlations yet** — blank until computed from official NBA box scores (sandbox had no route to stats.nba.com).
- **No performance claims anywhere** — no bets have been placed; the leaderboard is empty until strategies pass the gates.
- Industry-sourced thresholds (e.g., "+1–2% CLV is strong," 200-bet minimums) are conventions, not laws, and are listed on the Flagged for Review page.
- Pre-existing irregularity: GitHub Pages was already enabled on this repo before any content existed (noted in COORDINATION.md).

## Recommended next steps

1. Stand up official box-score ingestion (nba_api → stats.nba.com) and fill the correlation table with computed, sourced values.
2. Pre-register (G0) the two highest-prior strategies — S2 injury-report latency and S8 correlated-SGP — and start timestamped paper-trading to accumulate the 200-bet CLV sample.
3. Add automated odds capture (bet-time and closing) to make Gate G3/G6 auditable.
