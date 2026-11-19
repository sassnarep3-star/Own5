# Executive summary — Week-11 per-team injury desk (session 42899de4)

**Date:** 2026-11-19 (UTC) · **Branch:** `arena/42899de4-own5` · **Scope:** own brief lines only (per-team view, clocked reads + delta, fixtures/byes, registers, site, verification).

## What was delivered

1. **First-hand reads** of the official NFL Week-11 and Week-10 injury reports and both schedules (S-01…S-04), transcribed to row-level CSVs: **255 rows (W11)** and **347 rows (W10)**, every row carrying an official `nfl.com` source link.
2. **Per-team decision view** (`team_view_w11.csv` / `team_view_w10.csv`, 32 clubs each): report state (listed / explicit zero / bye), listed players, DNP/LP/FP practice counts, Out/Questionable/Doubtful + **net injury count**, QB rows on report, and blank-and-flagged **starters out** / **replacements named** columns.
3. **W10 → W11 delta** (`team_delta_w10_w11.csv`): listed-count and DNP deltas for the 22 clubs that played both weeks; designation deltas for the 4 clubs whose Week-11 designations are printed; every non-computable cell blank with a reason, never zero-filled.
4. **Fixtures & byes**: 13 Week-11 games (printed kickoff/network, Mexico City international noted), 14 Week-10 finals (Munich international noted), 10 bye rows — official schedules only.
5. **Registers**: 11 flagged irregularities, 8 questions/answers, 8 suggestions, 9 sources, 10 decision-readiness rows (gate + number to clear).
6. **Site**: 12-page dashboard (`nfl-teamview-42899de4/pages/`) — landing with headline tiles + per-team table, subpages for teams, delta, both row-level reports, fixtures, registers, exec summary.
7. **Verification**: fail-closed verifier (pins, source allowlist, blank-not-zero rules, independent recomputation, byte-identical rebuild, site link integrity) + **11 negative controls** proving corruption is rejected; CI workflow runs all three stages on every PR touching this desk.

## The decision state (Wednesday of Week 11)

- Designations are printed **only** for Thursday's IND at HOU game (IND net 9 = 5 Out + 4 Q; HOU net 7 = 4 Out + 3 Q) and for CIN/WAS "No Injuries Reported" (explicit zero). The other **22 Sunday/Monday clubs have blank designation columns because the report has not printed them yet** — published as blank with F-TV-03, never as zero.
- **Starters out** and **replacements named** are blank for all 32 clubs: no official announced-starter or depth source was read this session and nothing is inferred (F-TV-01/02; gates K-027, K-035).
- Bye clubs (ATL CLE GB LAR NE SEA in W11; CHI DEN PHI TB in W10) are blank in every report column — distinct from the explicit zero of CIN/WAS (F-TV-06).
- No reserve/IR list was read, so "not on report" is never presented as "available" (R-TV-06 blocked).

## Trust chain

First-hand reads → row-level CSVs → deterministic roll-up (`compute_views.py`) → fail-closed `verify.py` → 11 negative-control tests → CI byte-diff on PR → Pages. Cross-checks: W11 transcription matches **two** independent same-day captures (253/253 player rows; 255/255 incl. no-injury rows); W10 matches a third **347/347**; a fourth capture disagrees and is flagged **F-TV-10** (reported, not edited).

## Brief-line status (10 lines in scope)

- **MET (6):** clocked reads + delta published; point-in-time snapshots with no jersey-order inference; every row sourced or blank+flagged; official fixtures/byes; cross-capture reconciliation; deterministic site with registers.
- **PARTIAL (1):** net injury count — printed for 4/32 clubs, blank-by-publication-state for 22, bye for 6 (re-read later in the week: S-02-01).
- **BLOCKED (3):** starters out (K-027), replacements named (K-035), reserve list (S-02-04) — each needs exactly one official source read to clear.

## Irregularities worth the reader's attention

- **F-TV-10:** `data/decision-desk/injuries_wk10_players.csv` (276 rows) disagrees with the official reg10 page (347 rows) — 85 official rows missing there, 14 extra. This desk's copy matches `nfl-desk-f2e20e96` exactly.
- **F-TV-11:** the delta compares a final Week-10 print against a mid-week Week-11 print — labelled in every affected row.
- **F-TV-08:** injury-page news-rail headlines (Mayfield, Geno Smith, Addison, Maye) were observed but **not** modelled — only printed report rows are data.

Full evidence: `research/nfl-42899de4/VERIFICATION.md`, `METHODOLOGY.md`; registers in `data/nfl-teamview-42899de4/`.
