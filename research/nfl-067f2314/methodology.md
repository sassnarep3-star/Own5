# Methodology & frozen spec v1 — session 067f2314 (2026-11-19 UTC)

This document is the **pre-registration** for this desk. It was committed to git before the
Week 11 evaluation window opened. The commit is the registration; the rule text below may only
be changed by a new pre-registered commit, never silently.

## 1. Scope

A clean, source-linked GitHub Pages dashboard for the NFL line-origination brief:
originate own lines (side → total → moneyline), keep a price-snapshot store, a verified
results feed, a gated leaderboard that separates signal from staking, correlations from
official numbers only, an injury/availability view, a decision-readiness table (one row per
requirement), and a Flagged for Review page. No bet is placed; no strategy is certified.

## 2. Data inputs (all official, captured 2026-11-19 UTC via the sandbox page-fetch tool)

| Input | Source | Rows | Use |
|---|---|---|---|
| 2026 league standings | https://www.nfl.com/standings/league/2026/REG | 32 clubs | per-game rates, model inputs, correlations |
| Week 11 schedule | https://www.nfl.com/schedules/2026/by-week/week-11 | 13 fixtures + 6 byes | fixture context, origination slate |
| Week 10 finals | https://www.nfl.com/scores/2026/reg10 | 14 finals | results feed; HFA/sigma constants |
| Week 11 injury report | https://www.nfl.com/injuries/league/2026/reg11 | 255 rows / 26 teams | availability capture |
| Week 11 scores page | https://www.nfl.com/scores/2026/reg11 | status check | confirm TNF not final at read time |

Page text was retrieved as rendered text (not raw server bytes). Values are transcribed
row-by-row; the desk verifier re-checks counts and reconciliations.

## 3. Frozen model spec (v1)

**Team strength.** `NET/G = NET / GP` from the official standings (GP = W+L+T). This is the
only team-level input; it is officially sourced and opponent-implicit through the standings.

**Constants (derived in-repo from the 14 official Week-10 finals, n=14).**
- Home-field advantage `HFA = mean(home margin) = -5.64` points.
- Score-difference scale `sigma = sample stdev(home margin) = 15.29` points.

Both are small-sample estimates (n=14) and are flagged F06-33. They are frozen for this desk
and supersedable only by a pre-registered change computed on a larger official sample.

**Originated markets, in dependency order.**
1. **Side** — model fair spread (home perspective): `model_fair_spread = -(NET/G_home - NET/G_away + HFA)`.
2. **Total** — `model_total = ((PF/G_home + PA/G_away) + (PF/G_away + PA/G_home)) / 2`.
3. **Moneyline** — `P(home) = 1 / (1 + exp(-margin / sigma))`; fair decimal odds = `1/P` and `1/(1-P)`.

**Storage.** Every market row stores its probability and its inputs (not just a pick). Every
market opens an immutable price snapshot with a SHA-256 of its inputs.

**Market columns.** Model fair line, market line and difference are separate columns. No
official operator price source exists in the sources read this session, so market and
difference columns are **blank + flagged F06-03** by policy. This is the honest state: the
residual against the market cannot be computed until the price-data policy is decided (Q15).

## 4. Correlations

Pearson correlations computed in-repo from the 32-club official standings only. `n` is
published with every value. No correlation uses non-official inputs.

## 5. Leaderboard & gates

Strategies are pre-registered (10 entries: 5 singles strategies, 2 control baselines, 3
held combo divisions) with a two-sided "what would change our mind" falsifier on every row.
Signal (Brier skill, DSR, n, calibration CI) and staking (units, ROI, CLV) are separate
scorecards. Backtest numbers never appear on the leaderboard (gate G11). Certification
requires G02 (market prices), G04 (luck removal), G05 (n ≥ 200) and G07 (calibration) — none
pass today, so **zero strategies are certified**. Parlays and prop combos stay behind the
joint-evidence gate G12. The demotion gate G10: a live strategy returns to paper if DSR < 0
or the calibration CI excludes 0 for two consecutive windows.

## 6. Verification rules (hard)

1. Every factual value in any table/row links to an official, verified source.
2. If a value cannot be confirmed from an official source, it is left blank and flagged on
   the Flagged for Review page. Never inferred, never filled in.
3. The verifier is fail-closed: pinned row counts, reconciliation rules, row provenance
   (source link or explicit UNVERIFIED badge on every table row), internal-link integrity,
   and build determinism. A corrupted dataset must fail the build (negative controls in the
   test suite prove this).
