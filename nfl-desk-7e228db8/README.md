# nfl-desk-7e228db8 — NFL Verification & Decision Desk

Session `7e228db8`, branch `arena/7e228db8-own5`, official reads 2026-11-19 UTC.

A static GitHub Pages desk (served from the repo root Pages source at
`/Own5/nfl-desk-7e228db8/`) that:

1. **originates Week 11 lines** — side → total → moneyline, fair/market/difference as
   separate columns (market blank by policy until a licensed price source exists);
2. **keeps a price-snapshot store** — 39 immutable opens with inputs SHA-256 (R020/R039);
3. **publishes a verified results feed** — 150 finals through Week 10, reconciled 32/32 to
   the official standings (including the recovered Week 8 MNF missing from the shared corpus);
4. **tracks the official injury report** as a timestamped, hash-pinned capture with blanks
   preserved and reserve-list/stale-roster irregularities flagged;
5. **separates signal from staking** on a pre-registered leaderboard that is intentionally
   empty of results, with random/favourite control baselines (R024/R029/R-controls);
6. **computes correlations from official standings only**, n=32 with Fisher CI (R009/R026);
7. **renders the decision-readiness table** (one row per requirement: gate + number to
   clear + observed), a reviewable **suggestions register**, a **questions register**, and
   a **Flagged for Review** page with the repo-wide verifier sweep.

## Rebuild

```bash
python3 nfl-desk-7e228db8/build_desk.py   # data: ratings, lines, snapshots, correlations
python3 nfl-desk-7e228db8/build_site.py   # pages (deterministic, byte-identical)
python3 nfl-desk-7e228db8/verify_desk.py  # fail-closed: 1600+ checks
python3 -m unittest discover -s nfl-desk-7e228db8/tests -t nfl-desk-7e228db8
python3 nfl-desk-7e228db8/run_sweep.py    # repo-wide verifier sweep (scratch-copy isolated)
```

No third-party packages; Python 3.11+ stdlib only. `opened_at` is pinned so rebuilds are
byte-identical; the git commit hash is the pre-registration (spec v1-frozen-2026-11-19).

## Files

- `build_desk.py` — data engine (reconciliation gate, ratings, lines, snapshots, correlations)
- `build_site.py` — page renderer (15 pages, no JS required for content)
- `verify_desk.py` — fail-closed verifier (links, pinned counts, invariants, provenance)
- `tests/test_desk.py` — 19 unit tests including two negative controls
- `run_sweep.py` — repo-wide verifier sweep (isolated scratch copy)

Data lives in `../data/nfl-desk-7e228db8/` (CSV/JSON) and `../data/nfl-desk-7e228db8/raw/`
(hash-pinned verbatim excerpts + manifest). Research documents in
`../research/nfl-7e228db8/`.
