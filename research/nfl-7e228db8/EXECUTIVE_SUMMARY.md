# EXECUTIVE SUMMARY — session 7e228db8 (2026-11-19, UTC)

## What was verified today (official nfl.com reads; timestamps + SHA-256 in raw/manifest.csv)

1. **Standings through Week 10** — all 32 clubs; column mapping cross-confirmed against two
   official game centres' published points-per-game.
2. **Verified results feed: 150 finals** — W1–8 corpus (120) + Week 8 MNF CHI 34 @ SEA 17
   recovered from the official Week 8 page (the shared corpus was missing it; proved by
   reconciliation, F7-06) + Week 9 (15) + Week 10 (14) read 2026-11-19.
   **Reconciliation: 32/32 clubs match the official standings exactly (W-L-T, PF, PA).**
3. **Week 11 schedule** — 13 games, 6 byes (ATL CLE GB LA NE SEA), venues, networks; the
   league's dated Week 16–18 schedule-announcement text published beside the live schedule.
   MIN@SF is the Mexico City international game (Estadio Banorte, official game centre).
4. **Injury report (Wednesday read, 2026-11-19T07:03Z)** — 255 rows across 26 clubs (two
   clubs report "No Injuries Reported"); blanks preserved and marked; dated news headlines
   captured as evidence for reserve/roster events.

## What was computed (deterministic, stdlib-only, spec frozen pre-window)

- **Opponent-aware SRS ratings** from game-level results (opponent-aware per the brief).
- **HFA fitted at −0.93 points** (n=150; home teams won 45.3%) — unusual, published as
  computed, tested prospectively (F7-10).
- **39 originated markets** for Week 11 (side → total → moneyline): fair spread, fair total,
  no-vig moneyline probabilities, fair decimal odds; probabilities + inputs SHA-256 stored
  per row (R035); market/residual/CLV columns blank by policy (F7-P01).
- **Correlations** from official standings only, n=32 with Fisher CI: NET/G↔PCT r=0.882
  [0.771, 0.941]; PF/G↔PCT r=0.715 [0.488, 0.852]; PA/G↔PCT r=−0.704 [−0.845, −0.471];
  PF/G↔PA/G r=−0.291 [−0.581, 0.064].
- **Repo-wide verifier sweep**: 37 desk verifiers executed in a scratch copy — 34 PASS,
  3 FAIL (causes published on the desk's Flagged page and in COORDINATION.md).

## What is honestly missing (owner decisions block these)

- **Operator prices** → market columns, residual, CLV, ROI, vig-free decomposition stay
  blank (Q7-01; policy R039). Nothing is estimated.
- **Automated multi-day capture** → injury timestamp series has one read this week (Q7-03).
- **Reserve lists / transactions / snap counts / depth order** → availability features and
  the backup-deficiency matrix stay parked (Q7-04–Q7-06).
- **Out-of-sample evidence** → the leaderboard is intentionally empty of results; the
  prospective shadow begins with tonight's IND@HOU (lines committed pre-kickoff).

## Decision-readiness snapshot

39 of 80 requirement rows Met · 18 Partially met · 22 Unmet · 1 In progress — every row
names its blocking gate and the number that would clear it (desk readiness page). The two
owner decisions that unblock the most: **Q7-01 (licensed price source)** and **Q7-03
(scheduled capture terms)**.

## Flagged for review (highlights; 19 items on the desk's Flagged page)

- F7-02: LAC still lists Daiyan Henley while the 2026-11-10 NFL.com news reports his trade
  to DEN — stale roster evidence (R064).
- F7-03: DET's Aidan Hutchinson absent from the Week 11 report amid a significant-knee-injury
  report — "not listed" must not mean "available" (R072).
- F7-06: shared corpus missing Week 8 MNF — patched in this namespace; owner adoption pending.
- F7-07: no verified operator prices anywhere in the repo — ROI claims are impossible by
  policy, not pending.
- F7-10: negative fitted HFA — surprising; published, not assumed.
- F7-19 (+sweep): three desk verifiers fail on main (stale pins/links) — causes documented;
  one (35a1feb2 committed-artefact drift) fixed by this session under the takeover rule.
