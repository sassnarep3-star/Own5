# Executive Summary — Own5: NFL Line Origination & Skill-Based Strategy Leaderboard

**Date:** 2026-11-02 | **Session:** arena-f1d30421 | **Status:** complete, self-contained; live site published (links at bottom)

## 1. What this project is

A self-running system that (a) **originates its own NFL lines** from official data, (b) defines and
**tests betting strategies** — singles, parlays, and player-prop combos — under statistical
validation gates designed to **separate skill from luck**, and (c) runs them as a **leaderboard
competition** with rewards reserved for gate-passing, luck-adjusted performance. No manual input is
required; every number is computed by scripts in this repo or transcribed from official NFL pages
with per-row links.

## 2. Headline findings (all computed, all reproducible)

1. **The market is close to efficient, but not perfectly.** On 10,228 NFL games (1980–2024), the
   closing favorite covers only **48.1%** of the time; home underdogs cover **52.6%**; overs hit
   **49.1%**. The historical underdog lean matches independent academic work
   (Szalkowski et al. 2012; Paul & Weinbach).
2. **The best-looking strategy still fails the luck test.** "Home underdog getting 7+" hit
   **56.37% (n=793, +8.4% modeled ROI)** — nominal p = 0.013, but the pre-registered
   multiple-comparisons gate (α = 0.05/8 = 0.00625) rejects it. Under our rules, **zero strategies
   are certified as skill today** — by design. They enter the leaderboard as Candidates and must
   prove themselves live (closing-line-value gate).
3. **One season of results cannot prove skill.** A break-even bettor has a **20.8% chance** of
   posting a 55% record over 200 bets; detecting a true 55% handicapper with 80% power needs
   **~2,243 graded bets (~8 NFL seasons)**. The entire validation/gating design follows from this
   (exact binomial + power analysis in `data/luck_skill.csv`).
4. **Parlay math punishes the naive.** Cross-game legs are genuinely independent (measured 0.984
   ratio vs product) — so a 2-leg fixed parlay at −110/−110 needs a **27.47%** joint hit rate that
   two break-even legs (≈23.6%) cannot deliver. Parlays only make sense from gate-passing legs.
5. **Player-prop combos are where real correlation lives.** QB passing yards vs top-WR receiving
   yards correlate **r = 0.76** (6,186 team-game sample); QB yards vs game total r = 0.35; RB rush
   yards vs team margin r = 0.21 ("winning script runs the ball"). Same-game prop parlays must be
   priced with empirical joint probabilities, never naive multiplication (gate G5).
6. **Our own lines, live.** The transparent v1 model (shrunk net-points ratings + 2.0-pt home-field
   advantage measured at **2.22 pts** on 2002–2024 data) has originated lines for **all 15 games of
   2026 Week 9** (`data/model_lines_2026_wk9.csv`), every input linked to official NFL pages.
   Market-line columns are deliberately blank: no official public source of market lines exists —
   flagged, never inferred.

## 3. How luck is removed (short version)

* Pre-registration + Bonferroni correction across every strategy variant tried (k = 8).
* Era-split stability gates (no single-period flukes).
* Closing-line-value gate for live promotion (ROI is noisy; CLV is the leading skill indicator).
* Deflated leaderboard scoring (Bailey & López de Prado 2014 methodology), Bayesian shrinkage of
  displayed win rates, fractional-Kelly bankroll rules (Thorp 2011).
* Every strategy that was tried is published — winners and losers — to kill survivorship bias.

## 4. Validation gate framework (7+1 gates)

G0 provenance → G1 sample size → G2 corrected significance → G3 closing-line value →
G4 out-of-sample stability → G5 correlation accounting → G6 robustness → G7 execution/capacity.
Full definitions and current pass/fail matrix: `research/validation-gates.md` and the site.

## 5. Verification discipline

* **Every table row on the site carries a source link.** Rows whose values cannot be confirmed
  against an official source are left **blank and flagged** on a dedicated "Flagged for Review"
  page — nothing is inferred or filled in.
* Official-source verification examples: 2026 standings (32 teams, W-L-T/PF/PA) and the full
  2025 Week 1 scoreboard (16 games) transcribed from nfl.com with per-game links; all 16 rows
  were cross-checked against the historical dataset (100% score match in the sample).
* Known irregularities (community dataset provenance, mixed-type line fields, one ambiguous team
  name in the historical file,2025 season coverage gap in the dataset) are catalogued with severity
  and evidence on the Flagged for Review page. None blocks use; all are visible.

## 6. Leaderboard & rewards

Strategies compete on a luck-deflated score (CLV 40% / deflated Sharpe 30% / sample discipline 20% /
calibration 10%), with rewards proposed to vest only for `Validated` entries and claw back against
lucky Finals runs. Reward pool amounts are proposals awaiting owner decision (flagged as such).
Initial board: S2 and S1 as Candidates; everything else Research — with losing strategies published.

## 7. What's live now

* **Site (GitHub Pages):** https://sassnarep3-star.github.io/Own5/ — dashboard with strategy tables,
  gate matrix, correlation tables, luck-vs-skill tables, our Week-9 lines, sources registry, and the
  Flagged for Review page.
* **Data:** 8 computed CSVs + verified official tables, each row carrying source links
  (`data/`).
* **Code:** 4 Python scripts + 1 download script, inputs pinned to commit SHAs (`scripts/`).
* **Coordination:** all work logged in `COORDINATION.md` with sources, verification steps, and
  irregularities.

## 8. Recommended next steps (for the owner)

1. Decide the reward pool (blank + flagged until decided).
2. Connect a verifiable odds feed (licensed) so market columns fill and live CLV tracking starts —
   this is the only blocker between the framework and live `Validated` entries.
3. Extend the prop-line backtest once a verifiable prop-line source exists (framework + correlations
   are already done).
4. Review the Flagged for Review page; request changes to any item.

---
*Integrity statement: this summary restates only values computed in `data/` from pinned inputs or
transcribed from official NFL pages with links. Where no official source exists (market lines,
reward amounts), the fields are blank and flagged. Methodology sources are listed in
`research/` and on the site's Sources page.*
