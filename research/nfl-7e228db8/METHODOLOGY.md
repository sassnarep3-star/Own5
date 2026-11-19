# METHODOLOGY — NFL Verification & Decision Desk (session 7e228db8)

## Pre-registration

The model specification below was **frozen before the Week 11 evaluation window opened**
(first originated game: IND @ HOU, Thursday 2026-11-19 8:15 PM ET = 2026-11-20T01:15:00Z).
The git commit hash of this file plus `build_desk.py` is the registration (R075/R077).
Spec version: `v1-frozen-2026-11-19`.

## Data provenance

Every official read used the platform page-fetch tool (processed text, not raw server
bytes — limitation F7-15, inherited from prior desks). Verbatim excerpts are stored under
`data/nfl-desk-7e228db8/raw/` with SHA-256 hashes and UTC timestamps in `raw/manifest.csv`.

| Input | Source | Read (UTC) |
|---|---|---|
| League standings through Week 10 | https://www.nfl.com/standings/league/2026/REG | 2026-11-19T06:56Z |
| Week 9 finals (15) | https://www.nfl.com/schedules/2026/by-week/week-9 | 2026-11-19T07:01:30Z |
| Week 10 finals (14) | https://www.nfl.com/schedules/2026/by-week/week-10 | 2026-11-19T06:59Z |
| Week 8 evidence for the corpus patch | https://www.nfl.com/schedules/2026/by-week/week-8 | 2026-11-19T07:24Z |
| Week 11 schedule (13 games + byes) | https://www.nfl.com/schedules/2026/by-week/week-11 | 2026-11-19T06:57:30Z |
| League injury report (reg11) | https://www.nfl.com/injuries/league/2026/reg11 | 2026-11-19T07:03Z |
| Game centre IND@HOU | https://www.nfl.com/games/colts-at-texans-2026-reg-11 | 2026-11-19T07:06Z |
| Game centre MIN@SF | https://www.nfl.com/games/vikings-at-49ers-2026-reg-11 | 2026-11-19T07:06Z |
| Corpus W1–8 (120 finals) | data/games_2026.json (repo, prior session; verification levels declared in its meta) | committed 2026-11-02 |

Standings column mapping was cross-confirmed: PF/G derived from the standings equals the
"POINTS PER GAME" values published on both official game centres (SF 31.2 = 281/9; MIN 19.6 =
176/9; IND 20.8 = 208/10; HOU 25.9 = 233/9).

## Reconciliation gate (hard)

Derived W-L-T, PF and PA per club from the results feed must equal the official standings
capture exactly for all 32 clubs. This gate caught a real defect: the shared W1–8 corpus
was missing Week 8 MNF (CHI 34 @ SEA 17) — the arithmetic residual (CHI +34 PF/+17 PA win;
SEA the mirror) identified the exact missing game, which was then read from the official
Week 8 schedule page and applied as a patch in this desk's namespace (F7-06). After the
patch: **150 finals, 32/32 clubs exact**.

## Model spec v1 (frozen)

1. **Ratings.** SRS-style least-squares margin ratings on all 150 verified finals:
   `margin_home = r_home − r_away + HFA + e`, with `Σr = 0` enforced exactly (KKT system,
   pure-stdlib Gaussian elimination). Opponent-aware by construction (R-ingest).
2. **Home advantage.** Fitted, not assumed: **HFA = −0.93 points** (n=150; home teams won
   45.3% of finals). Negative HFA is unusual; it is published as computed (F7-10) and will
   be tested prospectively; a venue/roof split is proposed (S7-09) once roof facts are
   captured (R066).
3. **Spread (side).** `fair_spread_home = −round(2·μ)/2` where `μ = r_home − r_away + HFA`.
   Half-point precision makes pushes impossible at the fair line.
4. **Total.** `expected_total = (pace_home + pace_away)/2`, `pace = (PF+PA)/GP` from the
   official standings; published rounded to the nearest half point.
5. **Moneyline.** `p_home = P(margin > 0) = 1 − Φ(−μ/σ_m)`, `σ_m` = residual SD of the
   margin fit (10.37). Fair decimal odds = 1/p (no-vig, no operator price involved).
6. **Origination order.** Side → total → moneyline (R022), enforced by column order and
   asserted in tests.
7. **Stored outputs.** Every line row stores `p_home`, `p_cover(fair)`, `p_over(fair)`, and
   the full input vector as JSON with its SHA-256 (R035). At the fair line, by construction,
   `p_cover ≈ p_over ≈ 0.5` — asserted between 0.45–0.55 by the verifier.
8. **Price snapshots.** 39 immutable opens (13 games × 3 markets) with the inputs hash.
   `opened_at` is pinned to this session's capture-window close (2026-11-19T07:30:00Z) so
   the build is a pure function of committed inputs; the git commit hash records the actual
   commit time. Market open/close, residual and CLV are **blank by policy** (F7-P01) until
   a licensed operator source exists (Q7-01) — the price-data policy is R039.

## Known limitations (published, not hidden)

- The fit is **in-sample** on the 150-final corpus (F7-14). The pre-registered backtest
  corpus is this same feed; its evaluation protocol is registered but NOT run, and no
  backtest number appears on the leaderboard (R029). The prospective shadow baseline starts
  with IND@HOU (kickoff 2026-11-20T01:15Z) — originated lines were committed pre-kickoff.
- Injury designations are a single Wednesday read; deltas need Fri/Sat re-reads (F7-05/F7-08).
- Reserve lists, transactions and snap counts are not captured; depth features stay parked
  (Q7-04–Q7-06).
- Correlations are computed from the official standings only, n=32 per row, Fisher-z CI
  published (R009/R026). They describe team-quality metrics, not bet-leg dependence; combo
  ranking stays behind the G9 joint-evidence gate.
