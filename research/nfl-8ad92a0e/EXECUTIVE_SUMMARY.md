# Executive Summary — NFL Decision & Origination Desk (session 8ad92a0e)

**Date of verification:** 2026-11-19 (UTC) · **Branch:** `arena/8ad92a0e-own5` · **Live site:** `/nfl-desk-8ad92a0e/`

## What was done

1. **Coordination first.** The shared task board (`COORDINATION.md`) was read; this session's scope
   (AD-01…AD-09) was claimed and pushed before any build work, in an additive namespace only.
2. **Fresh official reads (2026-11-19), line by line:**
   - 2026 league standings — 32 clubs (W-L-T, PCT, PF, PA, NET) — source: nfl.com/standings/league/2026/REG
   - Week 11 schedule — 13 fixtures + 6 byes (ATL, CLE, GB, LA, NE, SEA), Mexico City marker — source: nfl.com/schedules/2026/by-week/week-11
   - Week 10 scores — 14 finals direct-read (incl. Munich international game) — source: nfl.com/scores/2026/reg10
   - Week 11 injury report — read in full, all 7 chunks: **253 player rows, 26 clubs, 9 Out, 7 Questionable** — source: nfl.com/injuries/league/2026/reg11
   - Week 9 schedule — 15 finals direct-read as a spot-check of the adopted corpus.
3. **Verified results feed.** A 150-game 2026 feed (weeks 1–10) was adopted only after (a) all 29
   week-9/week-10 rows matched today's direct official reads exactly, and (b) per-club totals
   reproduced the official standings **32/32 exactly** (W-L-T, PF, PA). League identities hold:
   W = L = 149, T = 2, PF = PA = 6,923.
4. **Line origination (side → total → moneyline).** 39 markets for the 13 Week-11 fixtures, model
   `m8-2026-11-19-walkforward-v1` (shrinkage k=8, HFA and σ measured from the 150 official finals).
   Model fair line, market line and difference are separate columns; every row stores a probability
   plus an inputs hash. **Market/difference cells are BLANK** — no licensed price source exists
   (policy P-8AD-01, flag F8-01).
5. **Price-snapshot store.** 39 opening snapshots (pinned open time, inputs hash, policy stamp);
   closing cells blank pending a price source.
6. **Removal-of-luck panel.** Chronological walk-forward over the 149 decisive finals (ties excluded):
   Brier **0.2427**, skill vs expanding home-win rate **0.0664** (week-cluster bootstrap 95% CI
   **[0.0283, 0.1029]**, 1,000 resamples), vs p=0.5 skill ≈ 0.029; side MAE 10.57 pts; home win rate
   0.4564 (n=149). The skill is positive only against **weak internal baselines** — with no market
   benchmark (F8-01) nothing is certified.
7. **Correlations** computed only from official numbers: 8 rows from the standings (n=32) and 1 from
   the finals feed (n=150), each with a Fisher-z 95% CI and n published.
8. **Availability.** The full Week-11 report transcribed with per-row read clocks: 9 Out and 7
   Questionable — all in the Thursday game; CIN and WAS print "No Injuries Reported". **Replacement
   depth, inactives and snap counts are BLANK** (no depth source read — F8-02/F8-16). The brief's
   Lions "Out" claim (VR-08/VR-12) does **not** match the current official page (blank game statuses)
   — recorded verbatim as F8-05.
9. **Registers.** Decision-readiness table (**65 requirements**: 30 met, 16 partial, 13 blocked,
   5 rules adopted, 1 open) on the landing page; **18 questions** with discovery routes and blank
   answers; **14 suggestions** with blank decision cells (review-before-implement); **18 flags** on
   the Flagged-for-Review page; **12 gates**, **6 pre-registered strategies** (git hash =
   registration), **0 certified**, reward pool unfunded.

## Honest bottom line

- **0 strategies certified · 0 graded bets · 0 rewards.** The leaderboard carries no performance
  numbers by design (gate G8-11 forbids backtest numbers there).
- Every unconfirmable value is **BLANK** and flagged; nothing is inferred.
- The single most valuable unlock is a **licensed price source** (Q8-01): it opens the market gate,
  residuals, CLV, ROI and the reward design. The second is a **verified depth source** (Q8-04).

## Where to look

| Page | Contents |
|---|---|
| `index.html` | Dashboard + 65-row decision-readiness table |
| `lines.html` / `snapshots.html` | 39 originated markets, 39 opening snapshots |
| `results.html` | 150-final feed + 32/32 reconciliation evidence |
| `leaderboard.html` | Signal/staking split, gates, pre-registrations, luck panel |
| `correlations.html` | 9 official-only correlations with n |
| `availability.html` | 26-club summary + 253 player rows |
| `questions.html` / `suggestions.html` / `flagged.html` / `sources.html` | Registers |
| `executive-summary.html` | This summary as a page |
