# Verification log — session 067f2314 (2026-11-19 UTC)

Every check below was performed against the data committed in `nfl-desk-067f2314/` and the
official sources listed. The automated harness is `nfl-desk-067f2314/verify_desk.py`
(fail-closed; re-runnable in CI).

## Official reads (captured 2026-11-19 UTC, sandbox page-fetch tool)

| # | Source | URL | Result of read |
|---|---|---|---|
| 1 | League standings | https://www.nfl.com/standings/league/2026/REG | 32 clubs; W/L/T/PCT/PF/PA/NET captured |
| 2 | Week 11 schedule | https://www.nfl.com/schedules/2026/by-week/week-11 | 13 fixtures + 6 byes; venues, times, networks |
| 3 | Week 10 scores | https://www.nfl.com/scores/2026/reg10 | 14 finals; Munich game (NE@DET) marked neutral |
| 4 | Week 11 injury report | https://www.nfl.com/injuries/league/2026/reg11 | 255 rows / 26 teams; 16 designations (IND/HOU only) |
| 5 | Week 11 scores page | https://www.nfl.com/scores/2026/reg11 | TNF Colts@Texans not final at read time |
| 6 | Live prior desk | https://sassnarep3-star.github.io/Own5/nfl-desk-35fc3437/ | Renders correctly; decision-readiness table present |

## Automated checks (verify_desk.py — all PASS)

- **V0 drift alarm** — every CSV parses with expected columns and pinned row counts
  (32/19/14/255/39/39/4/12/10/79/15/12/33/8). A row-count change fails the build.
- **V1 row provenance** — every table row on all 15 generated pages ends in a source link
  or an explicit UNVERIFIED badge.
- **V2 internal links** — every internal href resolves to an existing page.
- **V3 standings reconciliation** — NET = PF − PA; PCT = (W + 0.5·T)/GP; GP = W+L+T for all 32 clubs.
- **V4 results feed** — 14 finals; winner = higher score; margin = |home − away|.
- **V5 originated lines** — model columns populated; market/difference blank+flagged F06-03;
  side → total → moneyline order per game; probabilities in (0,1).
- **V6 snapshots** — one snapshot per market; SHA-256 inputs valid; closings blank+flagged.
- **V7 correlations** — n = 32; |r| ≤ 1; each r matches an independent recomputation from the standings.
- **V8 gates/registers** — every gate has a status and clearing number; no strategy certified;
  every strategy has a falsifier; every requirement row has a gate, a clearing number, and a
  source link or flag.
- **V9 determinism** — a second build is byte-identical (no clocks/git/network in the build).

## Unit tests (tests/test_desk.py — 10 tests, all pass)

Positive controls: pinned counts, standings/results reconciliation, lines order and flags,
snapshot hashes, no certified strategies, requirement completeness, committed desk passes
the verifier. Negative controls: a corrupted NET value and a row stripped of its source
link and flag both **fail** the verifier (fail-closed drift alarm proven).

## Manual line-by-line review notes

- Standings PF/PA/NET transcribed from the official table; per-game rates recomputed in-repo
  and cross-checked (32/32 clubs).
- Week 11 schedule venues transcribed from the official page (hotel/venue links on the page
  corroborate NRG Stadium, Highmark Stadium, Bank of America Stadium, Soldier Field, AT&T
  Stadium, Ford Field, GEHA Field at Arrowhead, Lincoln Financial Field, SoFi Stadium,
  MetLife Stadium, Empower Field at Mile High, FedEx Field). Game-centre venue cross-check
  per fixture is pending — flagged F06-11.
- Injury rows transcribed one-by-one from the official report tables; the single
  comma-containing injury text ("Foot, Illness", Brevin Jordan) is quoted in the CSV so it
  parses correctly.
- The Thursday Night game (Colts@Texans, 2026-11-19 8:15 PM ET) had no final score at read
  time; Week 11 results feed intentionally contains zero Week-11 finals.

## Known limitations

- Page text was retrieved as rendered text via the sandbox fetch tool (not raw server bytes);
  the same limitation was noted by prior sessions.
- One read per source on one day; the injury report is an early-week (Wednesday) snapshot.
- No market price exists in any official source read; all ROI/CLV/backtest outputs remain
  blank+flagged until the price-data policy is decided.
