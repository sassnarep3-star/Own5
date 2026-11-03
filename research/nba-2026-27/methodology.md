# NBA Line Desk 2026-27 — methodology and verification log

Session `9cf7de11`. Branch `arena/9cf7de11-own5`. Build date 2026-11-03 (UTC).
Published site: `nba-line-desk/` (served at `/Own5/nba-line-desk/`).

## 1. Scope

- Official 2026-27 data only (nba.com standings, team traditional stats, Anthony Edwards game logs), plus the 2025-26 final standings (S08) for the prior-season predictor.
- Signals, strategies, validation gates G1–G8, a leaderboard, power ratings, a luck test, an executive summary, a sources register and a "Flagged for Review" page.
- No market odds are used. No official source publishes NBA prices in a verifiable form (flag F07). Every price, CLV, ROI and reward cell is blank and flagged.

## 2. Data acquisition and verification

| Step | Source | Result |
|---|---|---|
| Standings 2026-27 | S01 nba.com/standings | 30 teams; W-L, PCT, GB, home/road, last 10, streak |
| Team traditional stats 2026-27 | S02 nba.com/stats/teams/traditional | 30 teams; per-game values |
| Edwards logs 2026-27 | S03 nba.com/stats/player/1630162/boxscores | 4 official games |
| Edwards logs 2025-26 | S04 same page, Season=2025-26 | 10 most recent rows matched cell by cell to `nba-2026-lab/data/edwards_2025_26_recent10.csv` |
| Standings 2025-26 | S08 nba.com/standings?Season=2025-26 | 30 teams; each W+L = 82 |
| Games page | S05 nba.com/games | Scores and records only; no odds (used as a cross-check) |
| Injury policy | S06 official.nba.com | Policy and PDF index; PDFs not parsed (F09) |
| Responsible gaming | S07 pr.nba.com | Campaign content; release date not in text (F12) |
| Prop restrictions | S09–S11 (press) | REPORTED only; no NBA memo text found (F06) |

Re-transcription check: the standings-vs-team-stats W-L values were compared team by team; the Edwards 2025-26 rows were compared to the existing repo CSV across six fields.

## 3. Reconciliation checks (`tools/nba_line_desk/checks.py`)

20 checks, all passing at build time. Examples: standings W-L = team-stats W-L for all 30 teams; GP = W+L; WIN% = W/GP; PCT recomputed; FG%, 3P%, FT% recomputed from makes and attempts (tolerance 0.5 pp); REB = OREB + DREB; league margin identity Σ GP×(+/−) ≈ 0 (sum 2.00 against a rounding tolerance of 10.7); league W = L = 107; player PTS = 2(FGM−3PM)+3(3PM)+FTM for every row; Edwards 2026-27 averages reproduce the official header (33.3 / 4.8 / 3.5).

## 4. Pre-registered analysis plan

Fixed before the results were produced:

- **Same-season association.** Eight candidate signals (SIG02–SIG09) against 2026-27 win%. Pearson r, Fisher CI, permutation p (10,000 shuffles, seed 20261103), Bonferroni alpha = 0.05/8 = 0.00625.
- **Out-of-sample.** The 2025-26 final win% (SIG13) is the only predictor from an earlier season. Two targets (2026-27 win% and 2026-27 margin), alpha = 0.05/2 = 0.025.
- **Validation eligibility.** A signal is validated only if it is predictive (pre-game knowable), passes its corrected test, and every team has at least 20 games. The same eligibility applies to strategies through G1–G8.
- **Excluded from tests.** Season margin (outcome measure), home/road/last-10 win% (components of the target, or identical to it in this sample).

### Deviation (disclosed as F16)

SIG03 (implied opponent points = PTS − (+/−)) was first listed as a candidate. Because the margin is the outcome, SIG03 is outcome-derived. After the first run showed r = −0.75, it was reclassified as outcome-derived. It stays in the k = 8 count and is excluded from validation. The change is disclosed; it is not hidden.

## 5. Results (computed by `compute.py`, reproduced by the tests)

- Same-season: 3 of 8 candidates pass the corrected test (PTS r = 0.51, TOV r = −0.54, SIG03 r = −0.75). All three come from the same games as the target, so none is predictive (F17). Validated: 0.
- Out-of-sample: 2025-26 win% vs 2026-27 win%, r = 0.501 (95% CI 0.171–0.729), permutation p = 0.0049, passes alpha 0.025. Margin target: r = 0.436 (CI 0.090–0.688), p = 0.0148, passes. Statistically supported; not validated because the sample gate fails (minimum 5 games per team) and no priced data exists (F18).
- Luck: 0 of 30 teams beyond chance at p < 0.05 (about 1.5 expected). About 97 games per team are needed for a ±10-point win% estimate.
- Power: 783 priced bets to detect a 55% true win rate (80% power, two-sided alpha 0.05, normal approximation).
- Player-level (exploratory, n = 14): reported on the Correlations page, not used in any gate.
- Reproduction: the 10-row nba-2026-lab values (PTS×AST −0.0239; PTS×REB 0.5762; 3PM×PTS 0.7974; REB×AST 0.2053; PTS×win 0.2925) are recomputed and match exactly (F10).

## 6. Validation status

Every strategy is NOT VALIDATED or UNVERIFIED. G2 (priced data) fails for all strategies, so none can pass. C-03 to C-05 depend on a reported 2026-27 prop restriction (F06). They are marked UNVERIFIED, not prohibited, until an official page confirms it.

## 7. Limits

- One season, 30 teams, 5–8 games each. Every estimate has a wide interval.
- Same-season box-score relationships are descriptive. They are not predictive.
- The prior-season association may already be priced by the market. This cannot be checked without priced data.
- Press reports (S09–S11) are not official facts. They are not used as inputs.
