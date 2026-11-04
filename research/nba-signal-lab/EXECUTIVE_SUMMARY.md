# Executive Summary — NBA Signal Lab (session 6d508fee)

**As of 2026-11-03 (UTC). Scope: `nba-signal-lab/**` + `research/nba-signal-lab/**`.**
Live site: `https://sassnarep3-star.github.io/Own5/nba-signal-lab/index.html` (after merge).
Every figure below is recomputed in-repo by `nba-signal-lab/compute.py` from hand-transcribed
official NBA rows; every dataset row carries its official source URL. Unverified values are
blank and flagged — nothing is inferred.

## 1. What this desk is

A signal-generating NBA research desk that (a) originates its own lines, (b) prices player-prop
combos and parlays with measured dependence, (c) runs every strategy through validation gates
G01–G10 before any credit, and (d) strips luck before anything counts as skill. It is a
competition desk (leaderboard + reward tiers) with **0 certified strategies** today — that is
the honest state, not a placeholder.

## 2. Verified data (M2)

| Dataset | n | Validation |
|---|---|---|
| 2026-27 team table (30 teams) | 30 rows | W-L cross-check vs independent standings page: 30/30 exact |
| 2025-26 team table + standings (30 teams) | 60 rows | splits sum to record per team; re-fetch verification caught + fixed 3 transcription errors |
| Player game logs 2025-26 (Dončić 64, Edwards 61) | 125 rows | scoring & rebound identities hold on 125/125; per-player GP/PTS/REB/AST/3PM reproduce the official leaders page **exactly** |
| 2026-11-04 slate | 6 games | each row from official team-schedule pages; DET-PHI cross-confirmed on both teams' pages |

Sources for manual review: `https://www.nba.com/standings`, `https://www.nba.com/stats/teams/traditional`,
`https://www.nba.com/stats/leaders?Season=2025-26`, `https://www.nba.com/stats/player/<id>/boxscores`,
`https://www.nba.com/<team>/schedule` — full register in `data-notes.md` and on the site's
Verification page.

## 3. Own model lines (M3)

Blended net-rating model (parameters fixed pre-fit and flagged): S = w·net₂₆₂₇ + (1−w)·net₂₅₂₆,
w = n/(n+20); expected home margin = S_home − S_away + HFA(2.5 pts, flagged constant);
totals from blended (PF/g + PA/g).

| Game (2026-11-04) | Model home spread | Model total | Market |
|---|---|---|---|
| MIN @ HOU | HOU −4.2 | 228.1 | BLANK — no verified odds source |
| PHI @ DET | DET −10.1 | 225.4 | BLANK |
| IND @ MEM | MEM −8.2 | 233.0 | BLANK |
| ATL @ WSH | WSH +8.0 | 232.7 | BLANK |
| LAL @ SAC | SAC +11.9 | 232.7 | BLANK |
| POR @ PHX | PHX +0.7 | 228.4 | BLANK |

Slate is 6 of the official 14 games (flag F-SLATE: pre-registered top-4-per-conference sourcing;
Boston's schedule page is JS-only). Market columns stay blank (flag F-MARKET). HFA sensitivity
at 2.0/2.5/3.0 published.

## 4. Correlation values (M4) — headline findings

- **Same-game prop legs are positively dependent.** Joint hit rates exceed the independence
  product by 10–16% for 2-leg combos and 27% for the 3-leg combo PTS≥25 & AST≥5 & REB≥5
  (lift 1.27). Same-game parlays priced by multiplying marginals overstate true probabilities;
  the desk's phi table is the correction input.
- **PTS×3PM is the strongest continuous coupling** (r = 0.69, 95% CI [0.58, 0.77]); PTS×MIN
  0.58 [0.45, 0.68]; REB×AST 0.43 [0.27, 0.56]; PTS×REB 0.37 [0.20, 0.51]; PTS×AST 0.19
  [0.02, 0.36]; AST×3PM 0.12 [−0.06, 0.29].
- **PTS×WIN is weak** (point-biserial r = 0.09 [−0.09, 0.26]) — scoring volume legs are far
  more correlated than player-outcome legs.
- **Cross-game legs behave independently:** lag-1 PTS autocorrelation ≈ 0 for both players
  (Dončić −0.04 [−0.29, 0.21]; Edwards 0.06 [−0.20, 0.31]) — supports multi-game parlay
  independence (gate G05) within this sample.

All CIs are Fisher-z; rows pooled at player-game level with per-player breakdowns published.
Sample: 125 player-games (top-2 2025-26 scorers) — exploratory labels apply.

## 5. Luck removal (M5) — the brutal math

- Break-even at −110 = **0.5238** (110/210, arithmetic).
- Detecting a true 55% bettor vs break-even at one-sided α=0.05, 80% power needs
  **≈2,243 graded bets**; 57% needs ≈719; 60% needs ≈263.
- Exact binomial tails: a 30–20 run (60%) is **p = 0.17**; 60–100 (60%) is p = 0.077.
  Hot streaks of typical sample size cannot pass as skill.
- Deflated scoring (shrink toward break-even, prior weight 25 bets) + Šidák/Bonferroni
  multiple-testing bounds (m = 5…50) are wired into the leaderboard.
- **No return is attributed to skill: 0 strategies certified, 0 graded bets.**

## 6. Strategy catalog & gates (M6–M7)

Five candidate strategies (singles on model sides/totals, cross-game parlay, 2-leg and 3-leg
same-game prop combos) are catalogued with their measured evidence and all start PENDING.
Gates G01–G10 cover sourcing, sample size, break-even, multiple testing, independence,
correlation pricing, holdout discipline, market grading, reproducibility and luck-stripping.
G08 (market gate) is structurally blocked until a verified odds source exists.

## 7. Competition desk (M8)

Leaderboard runs on audit units with deflated scoring and tiered rewards (50/30/20).
**Prize pool is BLANK + flagged (F-ODDS)** — no verified funding source exists. Entries are
the five strategies at 0 graded bets; ranks are placeholders until grading is possible.

## 8. Verification & flags (M11)

16/16 automated checks pass (identities, cross-page agreement, split sums, league identities,
checksums). The verification loop demonstrably works: the first compute run flagged a
Portland split row; re-fetch found two more streak mismatches; all three were corrected
against the official page. Six open flags are published on the site's **Flagged for Review**
page (market blanks, slate coverage, small samples, HFA constant, player-log scope, prize pool).
Source-page irregularities (JS-only pages, HTTP 500 static JSON, mislabeled "Margins & Stats",
~50-row render caps) are documented with URLs for manual review.

## 9. What this desk does NOT claim

No betting advice. No certified edge. No invented odds, prices, injuries or lineups. No
filling of unverifiable values. Small-sample estimates are labeled exploratory with CIs.

*Sources: nba.com standings, team traditional stats, leaders, player boxscores, team schedules
(all fetched 2026-11-03 via platform fetcher; sandbox egress to NBA hosts is blocked).
Full URL register: `research/nba-signal-lab/data-notes.md`.*
