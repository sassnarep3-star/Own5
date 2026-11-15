# Executive summary — Own5 NFL Decision-Readiness & Verification Desk

**Session:** `560ed315` (branch `arena/560ed315-own5`, base `a03dfb7`) · **Built:** 2026-11-15 UTC
**Additive scope:** `nfl-560ed315/**`, `research/nfl-560ed315/**`, `.github/workflows/nfl-560ed315.yml`

## What this desk is

The brief's central decision-support ask is: **"Put a decision-readiness table on the landing page:
one row per requirement, with the gate that blocks it and the number that would clear it."** This desk
delivers exactly that. It is additive to the NFL price/results desk (session `3fb93d11`, which built
the price store, verified results feed, origination pipeline, gates, leaderboard and correlations) and
edits none of its files.

For **each of the 81 requirements** in the brief, the decision-readiness table publishes:

- **blocking gate** — the validation gate (or named rule) that currently holds the requirement back;
- **number that would clear it** — the concrete threshold, count or condition that would satisfy that gate;
- **observed today** — the observed number, **computed mechanically from verified sibling data** where a
  count is derivable, and left blank with an `UNVERIFIED` badge where no official source can supply it.

## Headline numbers (computed, not asserted)

| Metric | Value | Computed from |
|---|---|---|
| Requirements in the register | 81 | `data/decision_readiness.csv` |
| Met | 22 | status roll-up |
| Partially met | 19 | status roll-up |
| Not started | 39 | status roll-up |
| In progress | 1 | status roll-up |
| Observed values that cannot be verified | 42 | rows with `flag = UNVERIFIED` |
| Official 2026 finals in the verified results feed | 137 | `results_feed.csv` (sibling) |
| Price-snapshot rows populated / total | 156 / 390 | `price_snapshots.csv` (sibling) |
| Replacement-depth slots / clubs | 705 / 31 | `replacement_depth.csv` (sibling) |
| Originated markets | 78 | `originated_markets.csv` (sibling) |
| Official correlation pairs (each with n) | 9 | `correlations_official.csv` (sibling) |
| Gate evaluations | 162 | `gate_matrix.csv` (sibling) |
| Certified strategies | 0 of 18 board rows | `leaderboard.csv` (sibling) |

Every `observed today` value above was read from the verified sibling CSVs; none was typed by hand.

## The four blocking gaps that gate certification

These are the requirements that cannot be closed from any source currently available, and they block
the whole certification chain:

1. **F-01 — no official price exists.** nfl.com publishes no spreads, totals or moneylines, and no
   operator publishes a public, machine-readable, timestamped price history. Gate **G2 (price
   provenance)** cannot pass for any strategy, so closing-line value, real-price ROI and demotion
   triggers D1a/D1b/D1f are unmeasurable. This is the single root blocker.
2. **F-10 — the certification sample is too small.** The official feed holds 137 games; after warm-up
   each family produced 4–51 graded bets against gate **G1's 300-bet minimum**.
3. **F-08 — no player-prop lines.** Neither nfl.com nor the mirror publishes prop lines, so the
   prop-combo family produced zero graded bets and gate **G7 (correlation audit)** cannot pass for any
   parlay or prop combination.
4. **F-04 — the Week 11 injury report is not published yet.** The Week 11 URL serves the Week 10
   report, so every Week 11 market is originated with no injury or replacement-depth adjustment.

## How to read the register

- **Met** = the requirement is satisfied in full from verified data.
- **Partially met** = the machinery exists but a gate or source is missing (usually F-01).
- **Not started** = no implementation exists; the requirement is registered so it is not forgotten,
  with the gate and the clearing number stated up front.
- **Observed today = UNVERIFIED** = no official source can supply the number today; it is left blank
  and flagged, never inferred.

## Deliverables

| Deliverable | Where |
|---|---|
| Decision-readiness table (landing page + filterable page) | `nfl-560ed315/index.html`, `readiness.html` |
| Questions / information-have-vs-missing register | `nfl-560ed315/questions.html` |
| Suggestions for review (options + recommended path + review test) | `nfl-560ed315/suggestions.html` |
| Sources register | `nfl-560ed315/sources.html` |
| Flagged for review (irregularities + unverified blanks) | `nfl-560ed315/flagged.html` |
| Repo review / verification log | `nfl-560ed315/review.html` |
| Deterministic engine + registers | `readiness.py`, `registers.py`, `data/*.csv` |
| Verification harness + unit tests + CI | `verify.py`, `tests/`, `.github/workflows/nfl-560ed315.yml` |

## Verification performed

`verify.py` walks every generated page and asserts that **every body-table row is either source-linked
or carries an explicit UNVERIFIED badge** (208 rows across 7 pages, 0 failures), that there are **0
broken internal links**, and that the landing page renders the decision-readiness table. 12 unit tests
pass. The build is deterministic (byte-identical across runs).

## Honest limitations

- Luck cannot be eliminated from sports outcomes. Statistical evidence and prospective replication
  reduce false confidence; they do not guarantee future returns.
- The observed-number column is only as current as the verified sibling snapshots it reads (retrieved
  2026-11-14). A live re-read of nfl.com standings on 2026-11-15 confirmed the benchmark is live; the
  register is rebuilt on every run.
- This is research, not betting advice, a live sportsbook, or a jurisdictional eligibility determination.
