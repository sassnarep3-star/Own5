# NFL Decision Desk — Executive Summary

**Session:** `38a1fc27` · **Branch:** `arena/38a1fc27-own5` · **Snapshot:** 2026-11-12 (UTC)
**Live site:** https://sassnarep3-star.github.io/Own5/nfl-decision-desk/
**Data snapshot:** `data/decision-desk/raw/provenance.json` (URL, HTTP status, SHA-256, bytes, UTC time for every fetch)

## What this is

A single, self-running desk that (a) originates its own NFL lines, (b) tests strategies
against validation gates that correct for luck and multiplicity, (c) measures correlation for
parlays and prop combinations, and (d) tracks injuries and lineup depth — with every row traceable
to an official page or to the script and pinned input that produced it.

It also contains the two things the brief asked for that were missing from every earlier scope:
a **suggestions register with a decision-workflow**, and a **questions register** that states what
must be answered before a decision is reasonable.

## Verified inputs (2026-11-12)

| Input | Source | Result |
|---|---|---|
| Week 10 injury report | https://www.nfl.com/injuries/ | 276 player rows parsed; 26 clubs listed, 6 report none |
| Week 10 schedule | https://www.nfl.com/schedules/2026/by-week/week-10 | 14 games, kickoff times, neutral-site flags |
| 2026 standings | https://www.nfl.com/standings/league/2026/REG | 32 clubs; **32/32 reproduce exactly** from an independent game log |
| Injury mirror (calibration) | nflverse `injuries` release (AGGREGATOR) | 276/276 Week 10 rows agree with the official page |
| Snap counts / weekly stats / results | nflverse releases (AGGREGATOR) | pinned by SHA-256, 2023–2026 |

Two tiers are used everywhere: **OFFICIAL** (league pages) and **AGGREGATOR** (third-party mirrors of
official data). They are never conflated.

## What is computed

**Own lines — 14 Week 10 games.** Ridge ratings on final margins fitted only on prior weeks, a
two-way points model for totals, and an injury adjustment. Home-field advantage this build:
**+1.22 points**. Seven games show a model-versus-market gap of 3+ points; a gap is a research
candidate, not a bet.

**Injury value.** Controlling for prior scoring margin, one percentage point of relative lineup
deficiency is worth **−0.039 points of margin** (n = 887, p = 6.1×10⁻⁵). The market line moves
**−0.019 points per point — about 49% of the effect**. The residual is −0.020 (p = 0.024).

**No betting edge.** Fading the more-injured team wins **51.4%** ATS over 782 bets (p = 1.0). The
rule fixed on 2023–2024 and tested on 2025–2026 wins 49.0% over 104 bets. A starting quarterback out
on exactly one side: 53.2% over 94 games. The model's own walk-forward ATS record is **50.2–50.9%**.

**Correlation.** QB passing yards vs his WR1's receiving yards **r = 0.50** (n = 1,255 team-games).
At median lines the joint hit rate is **32.5%** versus **24.8%** if independent — a +7.7 pp gap that
changes the fair price of a same-team combination. Cross-market legs (spread vs total) are
independent: **phi = 0.006** (n = 7,103).

**Seven strategy families, zero certified.** Bonferroni α = 0.00714 over seven variants; every
family fails at least the CLV gate (G4) and the verified-market gate (G8), which cannot pass without
a timestamped operator price history.

## Irregularities found and flagged (full list on the site)

1. **Sign-convention error in this session's first pass** — a wrong spread sign manufactured a
   57.4% ATS "edge" that became 51.4% after correction. Regression test proposed (S02).
2. **Prior home-underdog claims do not reproduce** — 52.6% vs 49.7% ATS, and 56.4%/793 vs
   54.0%/730 for +7 dogs. Two independent datasets agree with the new figures.
3. **Prior QB↔WR correlation of 0.76 does not reproduce** — 0.50 on 2024–2026 weekly data.
4. **Prior 20.8% luck figure does not reproduce** — exact binomial gives 25.1%.
5. **No verified price history** — every market number is aggregator-sourced, timestamp unknown.
6. **No official prop lines, no machine-readable depth chart** — both handled by explicit proxies.

## Decisions that need a human

1. Capture a real, timestamped operator price history (S01) — without it nothing can ever be certified.
2. Adopt the sign-convention regression test (S02).
3. Close jurisdiction and reward-funding questions (Q04, Q05) before publishing any reward amount.
4. Accept or reject the corrections to the four non-reproducing prior figures.
5. Treat lineup deficiency as a pricing input (recommended) rather than a bet trigger.

## Bottom line

Infrastructure: done and automated. Inputs: verified, dual-sourced, timestamped. Edge: none
certified. That is the honest state, and it is the correct output of a process that removes luck
rather than one that reports a leaderboard nobody can trust.

*Research only — no bets are placed, no performance is claimed. Support: 1-800-GAMBLER.*
