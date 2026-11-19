# VERIFICATION LOG — session 7e228db8 (2026-11-19)

Line-by-line verification performed, in order. Every external value below was read from an
official page via the platform page-fetch tool on 2026-11-19; hashes and timestamps are in
`data/nfl-desk-7e228db8/raw/manifest.csv`.

## Official reads

| # | Page | Chunks | What was taken | Cross-checks |
|---|---|---|---|---|
| 1 | nfl.com/standings/league/2026/REG | 0–1/2 | W, L, T, PCT, PF, PA, NET per club (32 rows) | PCT arithmetic; NET=PF−PA; PF/G vs game-centre PPG (4 clubs) |
| 2 | nfl.com/schedules/2026/by-week/week-9 | 0–1/2 | 15 finals + byes PIT/TEN | counted 15; PIT/TEN GP consistent with standings |
| 3 | nfl.com/schedules/2026/by-week/week-10 | 0–1/2 | 14 finals + byes CHI/DEN/PHI/TB | counted 14; W-L-T additive check |
| 4 | nfl.com/schedules/2026/by-week/week-11 | 0–2/3 | 13 games, kickoffs, networks, venue strings, 6 byes, Week 16–18 announcement | 26 clubs playing, 6 byes |
| 5 | nfl.com/injuries/league/2026/reg11 | 0–6/7 | all club tables (255 capture rows incl. 2 "No Injuries Reported" markers) + dated news list | team count 26; status vocabulary |
| 6 | nfl.com/games/colts-at-texans-2026-reg-11 | 0/3 | venue (HOUSTON, TX / RELIANT STADIUM), at-a-glance stats, injury strip | PPG cross-check vs standings |
| 7 | nfl.com/games/vikings-at-49ers-2026-reg-11 | 0/3 | venue (MEXICO CITY / ESTADIO BANORTE), at-a-glance stats, injury strip | PPG cross-check vs standings |
| 8 | nfl.com/schedules/2026/by-week/week-8 | 0–1/2 | Week 8 MNF CHI 34 @ SEA 17 (corpus patch evidence) | arithmetic proof of the single missing game |

## Reconciliation (the desk's hard gate)

- Corpus (W1–8, 120 finals) + Week 9/10 reads = 149 finals → reconciliation FAILED for CHI
  and SEA with an exact single-game residual (CHI needed a 34/17 win; SEA the mirror loss).
- Read the official Week 8 page: MNF Nov 2 = CHI 34 @ SEA 17. Added as
  `results_2026_corpus_patch.csv` (source-linked). → **150 finals, 32/32 clubs exact.**
- Fail-closed behaviour exercised: the build refuses to publish on any mismatch.

## Checks executed locally

- `verify_desk.py`: 1640 checks, 0 failures (links, pinned counts, invariants, provenance).
- `tests/` (unittest): 19 tests, OK — including two negative controls proving the verifier
  rejects a filled market column and fires the drift alarm on a dropped snapshot row.
- Determinism: two consecutive `build_desk.py` + `build_site.py` runs produce byte-identical
  outputs (opened_at pinned; see METHODOLOGY).
- Repo-wide verifier sweep (`run_sweep.py`, scratch-copy isolation): 43 scripts — 39 PASS,
  4 FAIL (nba-commission: broken internal link; nfl-b34253a1: workflow hash pins drift with
  merges; nfl-command-desk: registration commit not on main lineage; repo-review: stale
  verifier_runs.csv audit → F7-20). Re-run after the day's sibling merges.

## Irregularities found and published

20 items on the desk's Flagged page (F7-01 … F7-20). High-severity: F7-02 (stale roster row),
F7-03 (reserve-list gap), F7-06 (corpus missing final), F7-07 (no market prices by policy),
F7-14 (in-sample model). No value was inferred or filled; blanks are explicit and flagged.

## Not done (open)

- Fri/Sat injury re-reads (single-session limitation; suggested for CI — S7-01).
- Operator price capture (blocked: Q7-01), transactions/snap/depth sources (Q7-04–Q7-06).
- Walk-forward of the two total estimators (needs prospective weeks; S7-08).
