# Executive summary — NBA line-origination research

**Snapshot:** 2026-11-05 · **Status:** research published; zero strategies certified; no bets placed.

## Bottom line

The official evidence is organized and reconciled, and the repository now has a deterministic line/dependence/validation engine and a simple static dashboard. **No betting edge is certified.** The settled/prospective ledger is empty, so ROI, CLV, Deflated Sharpe, PBO, ranks and rewards are intentionally blank. Publishing the research does not convert missing evidence into performance.

## What was verified

- 30-team current and prior official advanced tables, current traditional table and standings; W–L agrees across the three current renderings, and 15 integrity checks pass.
- Exactly two official November 5 games: Orlando at Phoenix and Miami at Golden State.
- The official noon injury report: five Orlando and four Golden State players Out; Miami and Phoenix had not submitted. No availability was inferred for unlisted players.
- 12 archived FanDuel prices across spread, moneyline and total for both games. The Miami–Golden State event page independently matched the board; the Orlando event page was location-gated. Exact quote timestamp, jurisdiction and ticket terms remain blank and flagged.
- 125 selected player-games: 64 Dončić and 61 Edwards, re-reviewed against official logs and reconciled to official season means. **Correction:** Edwards ranked third, not second, behind Dončić and Gilgeous-Alexander; this is not a top-two-scorer sample.

## Own lines

The transparent baseline shrinks current ratings toward the prior season with `K=20`, matches pace and opponent defense, and uses a disclosed zero home-advantage baseline with ±2-point sensitivity:

| Game | Projected score | Fair home spread | Fair total |
|---|---:|---:|---:|
| Orlando at Phoenix | ORL 111.50 – PHX 111.66 | PHX −0.16 | 223.16 |
| Miami at Golden State | MIA 115.34 – GSW 115.41 | GSW −0.07 | 230.75 |

These are experimental point estimates, not calibrated probabilities or recommendations. The largest archived total difference is Golden State–Miami under 236.5 versus model 230.75 (5.75 points), but incomplete availability, roster drift, tiny current samples and the uncalibrated margin distribution block any betting claim. Win probability and EV remain blank.

## Dependence and props

- Pooled points–threes correlation is 0.689; per-player values are 0.666 Dončić and 0.696 Edwards.
- Points–assists falls from 0.193 pooled to 0.044 after player centering, a concrete aggregation warning.
- Edwards PTS≥25 + 3PM≥3 hits 0.5574 jointly versus an independence product of 0.4407 (lift 1.2646). Dončić PTS≥25 + AST≥5 hits 0.7656 versus 0.7520 (lift 1.0182).
- Positive dependence means an independence product **understates** the joint hit probability. It does not validate a parlay price. Lag-1 scoring diagnostics are not evidence that actual parlay legs are independent.

Intervals are conditional block-bootstrap or per-player exact binomial intervals, not league-wide guarantees. Current prop/combo market prices were not verified, so prop edges remain blank.

## Skill versus luck

At a hypothetical −110 break-even, exact 80% power for a true 55% hit rate requires **2,248 independent bets** at one-sided α=0.05, or **4,055** under a 5%/8 Bonferroni screening scenario. Dependence increases the evidence burden. Eight candidates are predeclared; Holm, Deflated Sharpe and CSCV/PBO machinery is implemented, but no trial-return matrix or settled ledger exists. Every strategy is blocked on outcome, dependence, calibration, economics and replication gates.

## Leaderboard and rewards

The leaderboard is intentionally empty. Only strategies passing all ten gates can rank. The proposed reward is a non-cash Gold/Silver/Bronze badge for the top certified entries; no funded cash prize, payout mechanism or winner is verified. Cash amounts and ranks stay blank.

## Repository review

Every inherited file at baseline `54e8dee` was structurally scanned: **434 files, 64,598 lines**, 70 Python files, 50 JSON files, 8 JavaScript files, 66 CSVs and 139 HTML files. Python/JSON/JS syntax checks pass. The audit records 26 findings, including nine inherited directory links without an index page, stale coordination/README wording, a confusable CSV header, root-only link-checker coverage, ResourceWarnings and methodological overstatements in the prior signal-lab summary. Exact file/line review links are in `audit/findings.csv` and the Flagged for Review page.

This is a structural/provenance audit plus scoped official re-review of the new snapshot and reused player sample; it is not a claim that every historical fact in all inherited files was independently re-fetched. Shared broken links are repaired only during final integration and the combined site is reverified before merge.

## Decision

Publish the evidence, experimental lines, blocked strategies and review register. **Do not place bets, award rewards or claim skill.** The next required evidence is a point-in-time historical game/market ledger, complete availability, exact-leg dependence validation, selection-bias control and a frozen prospective replication window.
