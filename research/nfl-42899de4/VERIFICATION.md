# Verification — Week-11 per-team injury desk (session 42899de4)

Date: 2026-11-19 (UTC). Verifier: `nfl-teamview-42899de4/verify.py` (fail-closed).
Tests: `nfl-teamview-42899de4/tests/test_verify.py` (11 negative controls).

## 1. Row pins (frozen for this snapshot)

| File | Rows | Composition |
|------|------|-------------|
| `injury_report_w11.csv` | 255 | 253 player rows (24 clubs) + 2 explicit `no_injuries_reported` (CIN, WAS) |
| `injury_report_w10.csv` | 347 | 347 player rows (28 clubs; 4 W10 byes absent) |
| `fixtures_w11.csv` | 13 | one per Week-11 game |
| `fixtures_w10.csv` | 14 | one per Week-10 game (final scores) |
| `byes.csv` | 10 | 6 W11 + 4 W10 |
| `team_view_w11.csv` / `team_view_w10.csv` | 32 / 32 | all clubs, playing + bye |
| `team_delta_w10_w11.csv` | 32 | all clubs |
| registers | 11 flagged / 8 questions / 8 suggestions / 9 sources / 10 requirements | |

## 2. Independent cross-captures (read-only, not data sources)

| Capture | Claimed | This session | Result |
|---------|---------|--------------|--------|
| `nfl-desk-715e2cd4/data/availability_week11.csv` (read 2026-11-19T06:55Z) | 253 rows, 24 clubs | 253 player rows, 24 clubs | **match** (key-set: club+player+practice+game status identical) |
| `nfl-line-audit/data/availability_week11.csv` (read 2026-11-19T06:53Z) | 255 rows, 26 clubs | 255 rows incl. 2 no-injury entries, 26 clubs | **match** (253 + 2 = 255) |
| `data/nfl-desk-f2e20e96/injury_wk10_players.csv` | 347 rows | 347 rows | **match** (0 keys only-in-mine, 0 keys only-in-theirs) |
| `data/decision-desk/injuries_wk10_players.csv` | 276 rows | 347 rows | **mismatch → F-TV-10**: 85 keys only in mine, 14 only in theirs; treated as stale/partial, reported not edited |

Reg11 club-count detail (matches both W11 captures): IND 11, HOU 15, PIT 10,
PHI 15, AZ 12, KC 15, BAL 6, CAR 13, TB 6, DET 8, MIA 11, BUF 15, TEN 9,
DAL 14, NO 10, CHI 5, NYJ 8, LAC 11, JAX 13, NYG 6, LV 6, DEN 9, MIN 10,
SF 15; CIN/WAS explicit zero; byes ATL CLE GB LAR NE SEA.

## 3. Verifier checks (all green)

1. Row pins (above) + reg11 253/2 split.
2. Source allowlist: every data `source_url` is `https://www.nfl.com/(injuries|schedules|games)/…`;
   blank sources require a flag reference; register URLs restricted to nfl.com or this repo.
3. `starters_out` and `replacement_named` blank in both team views (F-TV-01/02).
4. Independent recomputation of every club's listed/practice/designation/QB
   counts from the row-level CSVs vs the published views; blank-not-zero rules
   enforced (BYE → all blank; unpublished designations → designation columns blank).
5. Delta recomputation: every delta cell equals W11 − W10 or is blank with a
   reason (bye side / W11 unpublished); F-TV-03 flag present where required.
6. Flag referential integrity: every `F-TV-*` used in data exists in `flagged.csv`.
7. Deterministic rebuild: `compute_views.py` + `build_site.py` reproduce all 16
   committed outputs byte-for-byte.
8. Site integrity: 12 pages, internal links resolve, every page carries an
   official nfl.com source link, no wall-clock timestamps in HTML.

## 4. Negative controls (corruption must fail)

| Test | Injection | Expected |
|------|-----------|----------|
| control | none | pass |
| corrupted count | IND listed 11→12 | fail (recomputation) |
| starter value | starters_out="Patrick Mahomes" | fail (F-TV-01) |
| zero-fill | PIT net_injury_count blank→0 | fail (F-TV-03) |
| bad source | `example.com` URL on a row | fail (allowlist) |
| silent blank | fixture source blanked without flag | fail (blank+flag) |
| deleted row | one reg11 row removed | fail (row pin) |
| forged delta | delta_listed=99 | fail (delta math) |
| bye values | ATL BYE row with listed=5 | fail (F-TV-06) |
| undefined flag | F-TV-99 used | fail (referential integrity) |
| tampered HTML | index.html edited | fail (byte-identical rebuild) |

All 11 run green via `python3 -m pytest nfl-teamview-42899de4/tests/test_verify.py -q`.

## 5. Known unverified / pending

- **Starters / replacements / reserve list** — no official source read; columns
  blank + flagged (R-TV-01, R-TV-02, R-TV-06 blocked).
- **Sunday designations** — not yet printed at read time; delta for 22 clubs
  awaits a later Week-11 read (F-TV-03/04, suggestion S-02-01).
- **Pages deploy + PR merge** — recorded in `COORDINATION.md` when complete.
