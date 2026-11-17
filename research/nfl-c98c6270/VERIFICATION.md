# Own5 NFL Decision Console — verification record (session `c98c6270`)

Every claim below is reproduced by `python3 run.py` (engine → site → verify)
and by `python3 -W ignore -m unittest discover -s tests`.

## Sources read for this session

| Source | URL | Read (UTC) | Used for |
|---|---|---|---|
| Official 2026 standings | https://www.nfl.com/standings/league/2026/REG | 2026-11-17 | Ratings inputs, luck panel, correlations, reconciliation |
| Week-11 schedule | https://www.nfl.com/schedules/2026/by-week/week-11 | 2026-11-17 | The 13-game origination slate, kickoffs, venues, byes |
| Week-10 schedule | https://www.nfl.com/schedules/2026/by-week/week-10 | 2026-11-17 | 13 official finals; LAC@BAL published pending |
| Week-10 injury report | https://www.nfl.com/injuries/league/2026/reg10 | 2026-11-17 | Availability, replacement depth, deficiency |
| Week-11 injury report | https://www.nfl.com/injuries/league/2026/reg11 | 2026-11-17 | **Serves the week-10 report** — week 11 is not published |
| 32 club depth charts | `https://www.<club>.com/team/depth-chart` | 2026-11-17 | 889 machine-readable slots across 31 clubs |
| MIN@SF game centre | https://www.nfl.com/games/vikings-at-49ers-2026-reg-11 | 2026-11-16 | Venue (Estadio Banorte, Mexico City — neutral site) |
| Official inactives (route proof) | https://www.atlantafalcons.com/news/atlanta-falcons-week-10-inactives-vs-kansas-city-chiefs | 2026-11-17 | Proves flag F-05 is closable |
| Official game book (route proof) | https://www.patriots.com/news/gamebook-patriots-vs-lions-week-10 | 2026-11-17 | Proves flag F-05 is closable |

Carried forward, read-only, never edited:
`nfl-desk-e46fb855/data/results_feed.csv` (weeks 1–9, 136 finals),
`nfl-desk-e46fb855/data/injuries.csv` (first read of the week-10 report),
`nfl-desk-e46fb855/data/depth_slots.csv` (the 2026-11-15 depth read used as the
delta baseline).

## Verification performed

1. **Row-level provenance on the emitted HTML**, not on the CSVs: 2 234 body
   rows across 17 pages, every one carrying a SOURCE, COMPUTED, GOVERNANCE or
   UNVERIFIED badge and a resolvable link (`verify.py`, check R-02).
2. **Determinism**: `engine.py` then `build_site.py` run twice; the committed
   artefacts must not drift (the workflow runs `git diff --exit-code`).
3. **Cross-source reconciliation**: the game-by-game record rebuilds the official
   standings for 32 of 32 clubs (W-L-T, PF, PA).
4. **Link integrity**: every internal link resolves, every external link is
   https, no localhost or raw.githubusercontent anywhere (check R-03).
5. **Honesty rules** (tests, group B): no market value, no ROI/CLV string with a
   number, no ranked leaderboard row, no certified strategy, no implemented
   suggestion, no jersey-number depth, no inferred injury delta, no transcription
   of the Houston image.
6. **Statistics** (tests, group A): the binomial tail is checked against closed
   forms and against a 60 000-draw Monte Carlo, and does not overflow at
   n = 4 000; Pearson r is bounded and matches hand-computed values; Fisher
   intervals contain the estimate and narrow with n; the power curve is
   monotone; the American-odds conversion round-trips.
7. **Register consistency** (tests + `verify.py`): every requirement names a gate
   that exists; a requirement reads MET only when its gate also reads MET; every
   flag's evidence path points at a file that is on disk.

## Irregularities found

| Flag | Severity | What it is |
|---|---|---|
| F-01 | blocking | No market price of any kind exists anywhere in the repository |
| F-02 | blocking (Houston) | Houston publishes its depth chart as an image |
| F-03 | blocking | The week-11 injury report is not published; availability falls back to week 10 |
| F-04 | blocking | No official snap counts, so the brief's preferred depth signal is unavailable |
| F-05 | blocking | No official inactives or game book has been captured — **but this session proved both are published on club sites** |
| F-06 | blocking | No transactions or reserve list has been read |
| F-12 | blocking | One season only, so gate G1 (n ≥ 300) is unreachable |
| F-21 | review | The two depth captures are not the same shape: e46fb855 took Offense and Defense, this session also took Special Teams. The published delta is restricted to the shared units so the comparison is like-for-like |
| F-22 | review | 62 of 730 like-for-like depth rows differ between the two reads. Not yet evidence of a club-side change — a third read is needed to rule out a parser difference |
| F-14 | review | The Pythagorean exponent (2.37) and the spread sigma (13.5) are published conventions, not league values |
| F-16 | review | Clubs label their own depth charts "unofficial" |
| F-17 | review | Ratings are ridge-penalised (1.0 pt²); required for identifiability |
| F-19 | review | Only 4 of 31 clubs date their depth chart; the rest are blank by policy |

## Bugs found and fixed in this session

1. `luck_power()` raised `OverflowError: int too large to convert to float`
   because `math.comb(n, i) * p**i` overflows for n ≥ ~1 030. Replaced with a
   log-gamma tail (`_binom_tail`), tested to n = 4 000.
2. The totals estimators averaged per-team rates, which over-weighted clubs with
   fewer games played. Replaced with an aggregate over all team-games.
3. `load_injuries()` contained dead code referencing a file that does not exist.
4. Four depth capture rows had a 7-field shape (the note sat in the rank-4
   column); the parser silently read them as a shared first string. Fixed at the
   source and the shared-first-string test now keys on rank 1 only.
5. The depth delta compared 889 rows against 702, inflating "added" to 221. Both
   captures are now restricted to Offense and Defense (730 like-for-like rows).
6. The moneyline step was recorded as depending on the total, contradicting
   R-03 in its own data. Corrected to step 1.

## Scope

This session wrote only:
`nfl-c98c6270/**`, `research/nfl-c98c6270/**`,
`.github/workflows/nfl-desk-c98c6270.yml`, one additive `README.md` row, and an
append-only `COORDINATION.md` block. No file belonging to another session was
changed.
