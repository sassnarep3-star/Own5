# Methodology — Own5 NFL Decision-Readiness & Verification Desk

## Purpose

Turn the full requirement list of the Own5 NFL line-originator brief into a single **decision-readiness
matrix**: one row per requirement, each carrying the gate that blocks it and the number that would
clear it. The matrix exists so that a decision can be made on evidence rather than on a static
snapshot of "done / not done".

## Design rules

1. **One row per requirement.** Every requirement in the brief — including the detailed sub-items — is a
   row. No requirement is folded away, and no row is added that is not in the brief.
2. **Gate, not opinion.** The `blocking_gate` column names a concrete validation gate (G0–G8, the
   demotion triggers D1a–D1f, or a named source/provenance rule). It is never a vague "blocked".
3. **A number, not a phrase.** The `clearing_number` column is a concrete threshold, count or
   condition that would satisfy the gate (e.g. "300 graded results from an official publisher",
   "a verified MARKET_OPEN and MARKET_CLOSE snapshot for all originated markets", "one route verified
   for all 32 clubs").
4. **Observed numbers are computed, not typed.** The `current_number` column is produced by
   `readiness.py` reading the verified sibling CSVs (session `3fb93d11`) mechanically:
   - 137 official games ← `results_feed.csv`
   - 156/390 populated price snapshots ← `price_snapshots.csv`
   - 705 slots / 31 clubs ← `replacement_depth.csv`
   - 78 markets ← `originated_markets.csv`
   - 9 official correlation pairs ← `correlations_official.csv`
   - 162 gate evaluations ← `gate_matrix.csv`
   - 0 of 18 certified board rows ← `leaderboard.csv`
   A requirement whose current number cannot be computed from a verified source gets an empty
   `current_number` and `flag = UNVERIFIED`.
5. **No hallucinations.** A value that cannot be confirmed from an official source is left blank and
   flagged on the Flagged-for-Review page. It is never inferred or filled.
6. **Read-only for others.** This desk writes only `nfl-560ed315/**`, `research/nfl-560ed315/**`, one
   scoped workflow, and append-only entries to `COORDINATION.md` and `README.md`. It reads the sibling
   desk's CSVs but never edits them.

## Status vocabulary

- **Met** — satisfied in full from verified data.
- **Partially met** — machinery exists; a gate or source is missing.
- **Not started** — no implementation; registered so it is not forgotten, with gate + clearing number.
- **In progress** — owned and being delivered by this session.

## Determinism

`readiness.py`, `registers.py` and `build_site.py` are pure functions of their inputs. Re-running them
produces byte-identical CSVs and HTML. `verify.py` re-walks the generated HTML and fails the build if
the source-or-flag invariant, the internal-link check, or the landing-table presence check is broken.

## Provenance of the observed numbers

The observed counts are read from verified registers that earlier sessions transcribed directly from
official nfl.com pages, each row carrying its source URL and a UTC retrieval stamp. This desk does not
re-derive the underlying facts; it consolidates them and, where a count is directly derivable, computes
the observed number from them. The 2026 NFL League Standings page was re-read on 2026-11-15 to confirm
the benchmark is live.
