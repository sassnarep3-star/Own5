# Executive summary — session 067f2314 (2026-11-19 UTC)

**Deliverable.** A clean, source-linked GitHub Pages dashboard for the NFL line-origination
brief, live at `https://sassnarep3-star.github.io/Own5/nfl-desk-067f2314/` — a landing page
with the decision-readiness table plus 13 category subpages, all values verified line-by-line
against official nfl.com sources read on 2026-11-19.

**Verified from official sources (2026-11-19 UTC).**
- 32-club standings; NET = PF − PA holds for every club; per-game rates derived in-repo.
- 13 Week 11 fixtures with dates, kickoffs, networks, venues and byes; 6 clubs on bye
  (ATL, CLE, GB, LAR, NE, SEA); MIN@SF confirmed as the Mexico City neutral-site game.
- 14 Week 10 finals ingested; all winners/margins consistent; results reconcile 32/32 to standings.
- 255-row Week 11 injury report (26 teams; CIN and WAS report no injuries). Only 16 rows carry
  a game designation (9 Out, 7 Questionable) — all on the Thursday-night teams (IND, HOU).
  This confirms the brief's finding that designations lag on an early-week report.

**Originated.** 39 markets across the 13 Week 11 fixtures, in the frozen order
side → total → moneyline, each stored with its probability and model inputs, each with an
immutable opening price snapshot (SHA-256-hashed inputs). Model fair line, market line and
difference are separate columns; market columns are blank+flagged because no official
operator price source exists in the sources read.

**Computed.** Four correlations from official standings, n = 32 published with each value:
NET/G vs win pct r = 0.8824; PF/G vs win pct r = 0.7153; PA/G vs win pct r = −0.7045;
PF/G vs PA/G r = −0.2914.

**Gated state.** Of 79 tracked requirements: met / partial / blocked counts are published on
the landing page. The blocking chain is: no price-data policy decision (user-owned, Q15) →
no market prices (G02) → no settled bets → no calibration, luck-removal or certification
(G04/G05/G07). Zero strategies are certified; the leaderboard separates signal from staking
and shows no backtest numbers. Parlays and prop combos are held behind the joint-evidence
gate. The demotion gate is defined and published; nothing is live to demote.

**Irregularities flagged.** 33 flags on the Flagged for Review page, including: no market
prices anywhere in the desk (F06-03); replacement depth blank pending a verified depth
source (F06-04); a single injury capture with no delta baseline (F06-06); and two
pre-existing issues owned by other sessions (a failing decision-desk CI job on main;
false-negative smoke checks in 10 workflows). The stale claim rows of session 35fc3437
were closed by this session (F06-32).

**Research only** — not betting advice, not a sportsbook, no payouts. Every value traces to
an official/primary source (linked per row) or is left blank and flagged.
