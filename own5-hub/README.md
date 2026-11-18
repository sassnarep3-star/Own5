# Own5 NFL Hub — `own5-hub/`

Single entry point for the NFL line-origination work. Served at
<https://sassnarep3-star.github.io/Own5/own5-hub/> once merged to `main`.

## What is here

| Path | What it is |
|---|---|
| `index.html` | Dashboard with the **decision-readiness table**: one row per brief line (80), status, blocking gate, number that clears it, source |
| `executive-summary.html` | Short, dated summary; every number comes from the data files |
| `requirements.html` | Full requirements register with source class and verification |
| `verified.html` | Re-checks made against the official pages on 2026-11-18 (match, mismatch, not established) |
| `injuries.html` | Daily capture ledger (sha256, UTC time, pins) and per-club counts. No player names |
| `questions.html` | Questions and information gaps, with the cheapest route to each answer |
| `suggestions.html` | Options, recommendation and "what would change our mind" per suggestion. **Nothing implemented** |
| `flagged.html` | Flagged for Review: irregularities and unverified items, with source links |
| `sources.html` | Every source and how it was read |
| `data/*.csv` | The authored registers that the pages are generated from |
| `captures/` | Official captures: `manifest.csv`, raw injury HTML (gzipped), `injury_counts_daily.csv` |
| `capture.py`, `parse_injuries.py`, `derive_counts.py` | Daily capture, structural parser, counts derived from raw bytes |
| `build.py`, `verify.py`, `tests/` | Generator, verification gates G1–G7, unit tests |

## Run it

```bash
python3 own5-hub/tests/test_hub.py        # or: python3 -m unittest discover -s own5-hub/tests
python3 own5-hub/build.py                 # regenerate the pages from data/ and captures/
python3 own5-hub/verify.py                # gates G1-G7; exit 1 on any failure
python3 own5-hub/capture.py               # fetch the three official pages now (needs network)
```

## Rules the hub enforces

1. Every table row either links to a source it cites, or shows a `NO SOURCE` / `UNVERIFIED` badge.
2. A source's class must match its host: `OFFICIAL` means nfl.com; repo links must point to a file that exists.
3. A row with no source cannot be `DONE` on the strength of a source it does not have.
4. Captures are append-only. Raw bytes are re-hashed against the manifest, and club counts re-derive byte-for-byte.
5. Suggestions are not implemented until a choice is recorded.

## Scheduled jobs

- `own5-hub-capture.yml`: daily 13:20 UTC. Fetches the injury report, standings and reserve list, pins their structure, commits the captures with `[skip ci]`. A failed pin fails the job.
- `own5-hub-runner-probe.yml`: manual diagnostic (also runs on push to the branch). Checks the three pages return HTTP 200 from a GitHub runner.

## Known limits (see `flagged.html`)

- Storing raw captures in a public repo has not been cleared against nfl.com's terms (F04).
- Standings and reserve pages keep hashes only; their pins are presence checks (F09).
- The sandbox cannot reach nfl.com; all captures come from GitHub runners.
