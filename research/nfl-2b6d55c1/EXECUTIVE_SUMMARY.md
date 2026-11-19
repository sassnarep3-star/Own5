# OWN5 NFL Origin Desk — Executive Summary (session 2b6d55c1)

**Branch:** `arena/2b6d55c1-own5` (base `main` = `d634b08`, current == origin/main).
**Namespace (additive):** `nfl-desk-2b6d55c1/**`, `data/nfl-desk-2b6d55c1/**`,
`research/nfl-2b6d55c1/**`, `.github/workflows/nfl-desk-2b6d55c1.yml`. No other session's files
edited.

## What this desk does

It originates NFL lines from first principles using only officially sourced numbers, publishes a
verified results feed, a price-snapshot store, correlations with n, a signal/staking-separated
leaderboard, an availability/injury view (deltas never levels), a decision-readiness table, and a
questions/suggestions register — all on a static GitHub Pages site. Every table row is linked to an
official source or explicitly blank-and-flagged. Nothing is inferred.

**Live site:** `https://sassnarep3-star.github.io/Own5/nfl-desk-2b6d55c1/` (after Pages deploy).

## Official sources read (2026-11-19)

| Source | URL | Used for |
|---|---|---|
| NFL 2026 League Standings | https://www.nfl.com/standings/league/2026/REG | All 32 clubs: W-L-T-PCT-PF-PA-NET |
| NFL Week 10 Schedule/Results | https://www.nfl.com/schedules/2026/by-week/week-10 | 14 finals + CHI/DEN/PHI/TB byes |
| NFL Week 11 Schedule | https://www.nfl.com/schedules/2026/by-week/week-11 | 13 fixtures + ATL/CLE/GB/LAR/NE/SEA byes |
| NFL Week 11 Scores | https://www.nfl.com/scores/2026/week-11 | Confirms the 13 Week-11 matchups |
| NFL Injury Report Week 11 | https://www.nfl.com/injuries/league/2026/reg11 | 10 of 32 clubs read (IND, HOU, PIT, PHI, AZ, KC, BAL, CAR, TB, DET) |
| 2026 NFL Rulebook | https://operations.nfl.com/rules-officiating/2026-nfl-rulebook | Market-grading context only |

## Originated lines — Week 11 (side → total → moneyline)

Computed in-repo from official standings (PF/G, PA/G) with HFA = 2.0 pts (labeled prior, **not
fitted**) and logistic scale 13.7. Every row stores probability + inputs + inputs hash.

| Game | Away @ Home | Model fair side (home +) | Model fair total | Home win prob |
|---|---|---|---|---|
| W11-01 | Colts @ Texans | 5.93 | 49.1 | 0.6065 |
| W11-02 | Dolphins @ Bills | 11.11 | 47.7 | 0.6923 |
| W11-03 | Ravens @ Panthers | 3.56 | 48.7 | 0.5645 |
| W11-04 | Saints @ Bears | 7.06 | 47.9 | 0.6260 |
| W11-05 | Titans @ Cowboys | 6.20 | 51.0 | 0.6112 |
| W11-06 | Buccaneers @ Lions | 3.89 | 46.4 | 0.5705 |
| W11-07 | Cardinals @ Chiefs | 11.75 | 45.5 | 0.7022 |
| W11-08 | Steelers @ Eagles | -2.94 | 41.6 | 0.4465 |
| W11-09 | Jets @ Chargers | -0.28 | 43.7 | 0.4949 |
| W11-10 | Jaguars @ Giants | -4.56 | 45.1 | 0.4176 |
| W11-11 | Raiders @ Broncos | 4.57 | 48.3 | 0.5826 |
| W11-12 | Vikings @ 49ers (Mexico City) | 3.94 | 43.3 | 0.5715 |
| W11-13 | Bengals @ Commanders (MNF) | -4.22 | 49.4 | 0.4236 |

**Market line and difference columns are blank+flagged** for all 39 markets: no verified operator
price source exists (price-data policy P-01, flag FZ-04). We do not fabricate market prices or
residuals.

## Verified results feed — Week 10

14 finals ingested from the official Week-10 schedule, reconciled to team records. Example: Commanders
24, Giants 21 (Thu Nov 12); Lions 35, Patriots 10 (Munich); 49ers 46, Cowboys 40; Bengals 38, Steelers
18 (SNF); Chargers 23, Ravens 20 (MNF). Byes: CHI, DEN, PHI, TB.

## Correlations (official standings only, n=32, published with each value)

| Variables | r | n | 95% CI |
|---|---|---|---|
| PF/G vs PCT | +0.7152 | 32 | [0.4882, 0.8515] |
| PA/G vs PCT | −0.7043 | 32 | [−0.8454, −0.4713] |
| NET/G vs PCT | +0.8824 | 32 | [0.7710, 0.9415] |
| PF/G vs PA/G | −0.2911 | 32 | [−0.5808, 0.0641] |
| W vs PCT | +0.9916 | 32 | [0.9828, 0.9960] |

Computed in-repo; n published on every row.

## Leaderboard (signal separated from staking)

Seven strategies pre-registered (registration hash frozen in git). **0 certified.** Backtest numbers
are forbidden from ever appearing on the leaderboard (G03). Control baselines (random picks;
favorites only) are listed (CTRL-01, CTRL-02) but not ranked for skill. No performance figure exists
yet — this is pre-season.

## Availability & injury (deltas never levels)

Week-11 official injury report read with a UTC clock. 10 of 32 clubs read; the remaining 22 are NOT
READ (blank+flagged, never inferred). Out designations read: Mallory, Raimann, Tillery, Ward (IND);
Harrison Jr., Hunter, Jordan, Marks (HOU). The injury signal is treated as a surprise (change),
never a level. "Not listed" is not treated as available (reserve/IR not captured — flagged FZ-06).

## Decision readiness (30 requirements)

| Status | Count |
|---|---|
| Met | 8 |
| Partial | 15 |
| Unmet | 7 |

Key unmet: roster/IR sweep (R-13), removal-of-luck panel (R-16), Game Book starters (R-22), dated
schedule announcement (R-24), immutable multi-day snapshots (R-27), inactive lists/snap counts (R-28),
public/private layer split (R-29), per-team injury view (R-30). These are tracked on the
decision-readiness page, not hidden.

## Flags (non-blocking, published)

FZ-01 … FZ-10. Highest-severity: FZ-04 (no verified operator price source → market/residual blank),
FZ-07 (22 clubs' injury reports unread), FZ-09 (single injury capture only, no immutable snapshot).
Full register: Flagged for Review page.

## What is NOT in this desk

No settled bets, no backtest numbers on the leaderboard, no fabricated market prices, no
inferred depth or snaps, no cash rewards, no skill claims. This is a specification and pre-season
baseline, not a betting feed.

## Verification

- `verify_desk.py`: **767 checks, 0 failures** (row-count drift alarms, provenance, no backtest
  numbers on leaderboard, no broken internal links).
- Unit tests: **13/13 OK**, including negative controls (a filled market line or a backtest number on
  the leaderboard is rejected).
