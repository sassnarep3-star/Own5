# Verification log — NFL Origin Desk (session 2b6d55c1)

**Rule (hard):** every factual value in any table row links to an official, verified source. If it
cannot be confirmed from an official source, the value is left **blank** and flagged on the Flagged
for Review page. Never infer or fill in values. No hallucinations.

## Method

All NFL values were read from official nfl.com pages via the page-fetch tool on 2026-11-19 (UTC).
Each read is timestamped in `data/nfl-desk-2b6d55c1/sources.csv`. Computed values (fair lines,
correlations) are derived in-repo from those official inputs and carry `verification_status =
computed_from_official` plus an inputs hash.

## Sources verified

| # | Source | URL | Read (UTC) |
|---|---|---|---|
| S01 | NFL 2026 League Standings | https://www.nfl.com/standings/league/2026/REG | 2026-11-19T06:55:00Z |
| S02 | NFL Week 10 Schedule/Results | https://www.nfl.com/schedules/2026/by-week/week-10 | 2026-11-19T07:10:00Z |
| S03 | NFL Week 11 Schedule | https://www.nfl.com/schedules/2026/by-week/week-11 | 2026-11-19T07:20:00Z |
| S04 | NFL Week 11 Scores | https://www.nfl.com/scores/2026/week-11 | 2026-11-19T07:30:00Z |
| S05 | NFL Injury Report Week 11 | https://www.nfl.com/injuries/league/2026/reg11 | 2026-11-19T07:40:00Z |
| S06 | 2026 NFL Rulebook | https://operations.nfl.com/rules-officiating/2026-nfl-rulebook | 2026-11-19T08:00:00Z |
| S07 | DraftKings General Betting Rules | https://sportsbook.draftkings.com/help/general-betting-rules/general-rules | 2026-11-19T08:05:00Z |
| S08 | SciPy pearsonr docs | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html | 2026-11-19T08:10:00Z |

## Irregularities found (line-by-line)

- **FZ-01:** Standings read 2026-11-19 may reflect a partial Week-10 update: BUF shows 8-1 despite
  beating NYJ 31-12 on Nov 15. PF/PA used as-is; W-L treated as potentially stale.
- **FZ-02:** Home-field advantage HFA = 2.0 is a labeled prior, not fitted (Week-10 home margin is a
  noisy +12.1 over 14 games).
- **FZ-03:** Logistic scale 13.7 is an NFL convention, not derived in-repo.
- **FZ-04:** No verified operator price source; market_line and difference blank+flagged for all 39
  markets.
- **FZ-05:** Mexico City neutral site (MIN@SF): HFA prior still applied though a neutral-site game may
  not carry a home team.
- **FZ-06:** Reserve/IR list not captured; "not listed" on the injury report not yet proven to mean
  unavailable.
- **FZ-07:** Only 10 of 32 club injury tables read; 22 clubs NOT READ.
- **FZ-08:** Only 2 of 13 Week-11 venues verified (NRG Stadium, Estadio Banorte); 11 blank+flagged.
- **FZ-09:** Single injury-hub capture only; no immutable multi-day snapshot with retained hash yet.
- **FZ-10:** No pre-registered backtest corpus and no removal-of-luck panel yet (pre-season).

## Automated checks

- `verify_desk.py`: 767 checks, 0 failures.
- Unit tests: 13/13 OK (incl. negative controls).
- Deterministic: `build_desk.py` uses no clock, network, or git; output is reproducible for a given
  input set.
