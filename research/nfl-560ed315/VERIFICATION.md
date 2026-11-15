# Verification log — Own5 NFL Decision-Readiness & Verification Desk

**Session:** `560ed315` · **Date:** 2026-11-15 UTC

## What was verified, line by line

1. **Coordination claim.** Session `560ed315` claimed a strictly additive, non-overlapping scope
   (`nfl-560ed315/**`, `research/nfl-560ed315/**`, one scoped workflow, append-only `COORDINATION.md`
   and `README.md`) and pushed the claim **before** any build work began.
   Source: https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md

2. **Official standings re-read.** The 2026 NFL League Standings page was fetched on 2026-11-15 and the
   32-team W-L-T / PF / PA table was read as the benchmark for the observed-number column.
   Source: https://www.nfl.com/standings/league/2026/REG

3. **Observed numbers computed, not typed.** `readiness.py` reads the verified sibling CSVs and computes
   the `current_number` for each requirement mechanically. Spot-checks:
   - `DR-02` → **137 official games** (from `results_feed.csv`)
   - `DR-01` → **156/390 populated** (from `price_snapshots.csv`)
   - `DR-31` → **705 slots / 31 clubs** (from `replacement_depth.csv`)
   - `DR-15` → **9 official pairs** (from `correlations_official.csv`)
   - `DR-27` → **162 gate evaluations** (from `gate_matrix.csv`)
   - `DR-09` → **0 certified of 18 board rows** (from `leaderboard.csv`)

4. **Unverified values left blank.** Requirements whose current count cannot be computed from a verified
   source are published with an empty `current_number` and `flag = UNVERIFIED` (42 rows). They are not
   inferred or filled.

5. **Source-or-flag invariant.** `verify.py` walks every generated page and asserts that every body-table
   row is either source-linked or carries an explicit `UNVERIFIED` badge. Result: **208 rows across 7
   pages, 0 failures**.

6. **No broken internal links.** Every local `.html` link resolves to a file that exists. Result: **0
   broken links**.

7. **Landing table present.** `index.html` renders the decision-readiness table
   (`data-table="readiness_landing"`) and `readiness.html` renders the filterable version
   (`data-table="readiness"`). Confirmed by `verify.py`.

8. **Unit tests.** 12 tests pass (`python3 -m unittest discover -s tests -v`), covering the register
   shape, the computed metrics, the unverified-blank rule, register counts, page existence, landing
   table presence, and the verify harness.

9. **Determinism.** `readiness.py`, `registers.py` and `build_site.py` are pure functions of their
   inputs; re-running produces byte-identical CSVs and HTML.

## Commands to reproduce

```sh
cd nfl-560ed315
python3 readiness.py      # builds data/decision_readiness.csv
python3 registers.py      # builds questions/suggestions/sources/flagged.csv
python3 build_site.py     # builds the 7 pages
python3 verify.py         # row-level source-or-flag + link + landing-table proof
python3 -W ignore -m unittest discover -s tests -v
```

## Scope confirmation

No file outside `nfl-560ed315/**`, `research/nfl-560ed315/**`, `.github/workflows/nfl-560ed315.yml`,
and the append-only `COORDINATION.md` / `README.md` entries was modified. The sibling desk's files
(`nfl-desk-3fb93d11/**`) were read for the verified registers and left untouched.
