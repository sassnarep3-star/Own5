# Verification Log — session 8ad92a0e (2026-11-19 UTC)

Method: every published value was either (a) transcribed from an official nfl.com page read this
session via the platform page-fetch tool (processed text — limitation F8-18), or (b) computed in-repo
from those transcriptions by `nfl-desk-8ad92a0e/compute.py`, or (c) adopted from a committed repo file
after an explicit reconciliation test. Unconfirmable cells are BLANK and flagged. Nothing is inferred.

## Official reads performed this session

| # | Source | URL | Read (UTC) | Result |
|---|---|---|---|---|
| S8-01 | 2026 league standings | https://www.nfl.com/standings/league/2026/REG | 2026-11-19T11:10Z | 32 clubs; arithmetic checks pass (NET=PF−PA 32/32; PCT=(W+0.5T)/G 32/32); league sums W=L=149, T=2, PF=PA=6,923 |
| S8-02 | Week 11 schedule | https://www.nfl.com/schedules/2026/by-week/week-11 | 2026-11-19T11:10Z | 13 fixtures + 6 byes; every club appears exactly once; TNF IND@HOU, SNF MIN@SF (Mexico City), MNF CIN@WAS |
| S8-03 | Week 10 scores | https://www.nfl.com/scores/2026/reg10 | 2026-11-19T11:11Z | 14 finals; byes CHI/DEN/PHI/TB; matches adopted feed 14/14 |
| S8-04 | Injury report Wk11 | https://www.nfl.com/injuries/league/2026/reg11 | 2026-11-19T11:12Z | all 7 chunks read; 253 player rows / 26 clubs; 9 Out, 7 Questionable (all TNF); DNP 83 / LP 87 / FP 83; CIN+WAS "No Injuries Reported" |
| S8-05 | Week 9 schedule | https://www.nfl.com/schedules/2026/by-week/week-9 | 2026-11-19T11:15Z | 15 finals; matches adopted feed 15/15; byes PIT/TEN |

## Line-by-line checks (printed, not asserted)

1. **Standings arithmetic:** NET = PF − PA for all 32 clubs; PCT reproduces (W + ½T)/G for all 32.
2. **Schedule completeness:** 13 games × 2 + 6 byes = 32 clubs, no duplicates, no gaps.
3. **Feed vs direct reads:** weeks 9 and 10 of the adopted 150-game feed match today's official
   transcription row-by-row (15 + 14 = 29/29 exact scores).
4. **Reconciliation:** per-club W-L-T/PF/PA across all 150 feed rows equals the official standings
   for **32/32 clubs exactly** (this is the adoption gate; see `results.html`).
5. **Cross-session corroboration:** 253 rows / 26 clubs / 9 Out / 7 Q / DNP 83 / LP 87 / FP 83 —
   independently matches session 715e2cd4's Week-11 counts.
6. **Model identities:** `verify.py` recomputes every fair side line and total from the standings
   inputs and compares to the published rows (tolerance 0.051).
7. **Origination order:** every game publishes SIDE before TOTAL before MONEYLINE.
8. **Blank-by-policy:** all market/difference/snapshot-close cells empty (39 + 39 + 39 checks);
   leaderboard performance cells empty (6 rows × 3 columns).
9. **Determinism:** two consecutive builds are byte-identical; `verify.py` = **3,009 checks, 0 failures**.
10. **Tests:** 13 unit tests pass, including **7 negative controls** (filled market cell, dropped
    standings row, stripped source URL, broken internal link, filled leaderboard score, tampered
    final score, — each must fail the verifier; plus determinism, order, blanks, links).

## Irregularities found (published as F8-01…F8-18 on flagged.html)

- **F8-01 (blocking):** no licensed operator price source — every market cell blank.
- **F8-02 (high):** no depth/inactive/snap evidence read — replacements and availability graph not built.
- **F8-03:** 2026 HFA measured **negative** (−0.98 pts, n=150).
- **F8-04:** walk-forward skill positive only vs weak baselines; no market benchmark.
- **F8-05:** brief's Lions "Out" claim contradicted by the current official report (blank statuses).
- **F8-06:** printed cross-club player rows (e.g. Murray under MIN, Evans under SF) recorded verbatim.
- **F8-07:** root dashboard stamped AS OF 2026-11-02 (generator-owned, not edited).
- **F8-08:** repo sprawl — 69 desks, 706 pages, 44 workflows, 17 open PRs (observed 2026-11-19).
- **F8-09:** pre-existing/empty CI on main for another desk; not touched.
- **F8-10…F8-18:** report-timestamp, count-discrepancy, corpus-version, early-window, adopted-venue,
  depth-route, unfunded-pool and processed-text limitations.

## Scope discipline

- Edited only: `nfl-desk-8ad92a0e/**`, `data/nfl-desk-8ad92a0e/**`, `research/nfl-8ad92a0e/**`,
  `.github/workflows/nfl-desk-8ad92a0e.yml` (new), one README row, append-only COORDINATION block.
- Zero other-session files modified; zero shared generators touched.
