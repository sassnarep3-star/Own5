# OWN5 NFL Line Originator — Executive Summary

**Session:** `ccc5caf2` · **Branch:** `arena/ccc5caf2-own5` (from main cb2d3b84) · **Date:** 2026-11-18 (UTC)
**Desk:** `nfl-desk-ccc5caf2/` · **Live (planned):** GitHub Pages at `https://sassnarep3-star.github.io/Own5/nfl-desk-ccc5caf2/`

## Objective

Implement the full NFL line-origination brief: originate our own NFL lines (side → total → moneyline), build a skill-based strategy leaderboard with validation gates, cover singles/parlays/prop combos, track injuries and depth deficiencies, remove luck via proper scores and uncertainty, pre-register every strategy, and publish a verified, source-linked GitHub Pages site — every table row source-linked or blank-and-flagged, never inferred.

## What is verified (official sources, read 2026-11-18)

| Input | Source | Result |
|---|---|---|
| 2026 regular-season standings | https://www.nfl.com/standings/league/2026/REG | 32/32 clubs; W-L-T, PF, PA reproduced exactly |
| Week 11 schedule | https://www.nfl.com/schedules/2026/by-week/week-11 | 13 games, Nov 19–23 2026, with kickoff times, networks, venues |
| Week 10 injury report | https://www.nfl.com/injuries/ | Parsed; e.g. Lions Kerby Joseph (Out), Cade Mays (Out), D.J. Reed (Out), Amon-Ra St. Brown (Questionable) |

## What is computed (model outputs, not odds — no edge claimed)

| Output | Value | Basis |
|---|---|---|
| Fair lines, Week 11 | spread + total for all 13 games (side → total → moneyline) | PF/PA model, HFA +1.22, neutral Mexico City = 0 |
| QB↔WR1 correlation | r = 0.50 | n = 1,255 team-games, 2024–2026 (nflverse, AGGREGATOR tier) |
| Spread vs total (phi) | 0.006 | n = 7,103 games, 2010–2026 |
| Lineup deficiency → margin | −0.039 pts per percentage point | n = 887, p = 6.1×10⁻⁵ |
| Fade-the-injured ATS edge | 51.4% over 782 bets | p = 1.0 — no edge |

## What is missing (blocking)

- **Operator closing-price history** (Q01/Q02, F01/F02) — without it, no CLV (G4), no market integrity (G8), no certification, no skill claim.
- **Player-prop lines** (F03) — no official prop-line archive exists; prop strategies cannot be priced economically.
- **Machine-readable official depth chart** (F16) — depth is snap-share inference, not official.
- **Jurisdiction & reward funding** (Q04/Q05) — rewards stay points-only until answered.

## Certified strategies: zero

All candidate strategy families (ST-01…ST-05) are pre-registered but blocked by the verified-market gate (G8) and CLV gate (G4). The leaderboard is intentionally empty. Backtest numbers are forbidden on the leaderboard until a strategy is certified.

## Irregularities flagged (F01–F18)

Key items: prior home-underdog claims do not reproduce (F08); prior QB/WR correlation 0.76 does not reproduce, recomputed 0.50 (F09); prior luck figure 20.8% does not reproduce, exact binomial 25.1% (F10); first-pass sign-convention error 57.4% → 51.4% (F11). Full list on the Flagged for review page.

## Decisions that need a human

1. Capture a real, timestamped operator price history (S01) — without it nothing can be certified.
2. Adopt the sign-convention regression test (S02).
3. Close jurisdiction and reward-funding questions (Q04, Q05) before publishing any reward amount.
4. Accept or reject the corrections to the four non-reproducing prior figures.
5. Treat lineup deficiency as a pricing input (recommended), not a bet trigger.

## Verification policy

Every factual value links to an official/primary source. Values that cannot be confirmed are left blank and flagged — never inferred, never filled in. No hallucinations.

## Bottom line

Infrastructure is in place and inputs are verified from official nfl.com sources. No strategy is certified, no edge is claimed, and no bets are placed. Not ready to bet.

*Research only — no bets are placed, no performance is claimed, nothing here is betting advice. Not affiliated with the NFL. Support: 1-800-GAMBLER.*
