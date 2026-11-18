# NFL official injury-report capture desk (session b8227c47)

Live: https://sassnarep3-star.github.io/Own5/nfl-desk-b8227c47/

## What this desk does
- Verifies the official NFL.com Week 10 injury report from one full read (SHA-256 recorded): 14 games, 28 club tables, 347 rows.
- Cross-checks the 14 games and the four bye clubs (CHI, DEN, PHI, TB) against the official Week 10 schedule.
- Records the served-week check: the Week 11 URL returns HTTP 302 to Week 10, so no Week 11 designation is published.
- Reads the NFL.com Terms and Conditions s.1.3 and records the decision needed before any automated capture.

## What this desk does not do
- **No scheduled or automated capture.** NFL.com Terms s.1.3 prohibit systematic retrieval of data to compile a database without express prior written consent. `capture.py` exits 4 unless `NFL_CAPTURE_CONSENT=1` is set, and no schedule exists. See `terms.html` and decision D-01.
- Publishes no player-level rows (Terms s.1.1 licence limit). Counts, hashes and links only.

## Files
| Path | Purpose |
|---|---|
| `parse.py` | Parser for the injury-report markup, pinned to the header, two tables per game and two club codes per game; raises `DriftError` on drift |
| `capture.py` | Consent-gated capture with served-week check, hashing and ledger (disabled without consent) |
| `build.py` | Builds the six pages from `data/*.csv`; deterministic, no network |
| `verify.py` | Verification gate: links, row-level official link, counts, determinism |
| `tests/test_desk.py` | Unit tests on synthetic fixtures (no nfl.com content) and committed-data reconciliation |
| `data/` | Registers: `week10_read.csv`, `week10_games.csv`, `week10_byes.csv`, `readiness.csv`, `tos_review.csv`, `flagged.csv`, `sources.csv`, `ledger.csv` (empty) |

## Run
```
python3 -m unittest discover -s tests -v
python3 verify.py
python3 build.py
```
Each verification step is independent of the network.

## Decisions needed (not decided by this desk)
- **D-01** Consent, authorized feed, or stop automated capture of the injury report.
- **D-02** Legal read of Terms s.1.3 commercial-use wording for this public repository.
- **D-03** Git history of this branch holds the raw probe bytes; squash-merge or accept.

Not betting advice. No performance claims.
