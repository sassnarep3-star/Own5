# NFL read-and-decide desk — session `35a1feb2`

Everything here was read from the league's own pages on **2026-11-17 between 00:38 and 00:55 UTC** and then
derived by machine. Nothing in `data/` or in the HTML was typed in by hand after a build, and no number on
any page exists unless the read that produced it is on disk.

## Start here

| | |
|---|---|
| Site entry point | [`index.html`](index.html) |
| What is true, what is blocked, what is wrong elsewhere | [`executive-summary.html`](executive-summary.html), [`flagged.html`](flagged.html) |
| The 80-row requirement ledger | [`requirements.html`](requirements.html) |
| Frozen model, before any week settles | [`pre_registration.md`](pre_registration.md) |

## Run it

```bash
python3 engine.py                                  # raw reads + authored inputs -> every derived table
python3 build_site.py                              # every derived table -> 15 pages (deterministic)
python3 verify.py                                  # 5 gates, incl. a rebuild of the whole chain
python3 -m unittest discover -s tests -t .          # 29 tests: scorer, bounds, no-invention rules
```

No network access is needed or attempted: `nfl.com` is unreachable from the sandbox, and the point of the
`raw/` transcript is that the reading happened once, was hashed, and is never re-fetched to "confirm" a
number that has since moved.

## Layout

- `raw/official_reads_2026-11-17.txt` — the verbatim transcript of the nine official reads (R1–R9), plus
  `raw/README.md` mapping each column of every authored CSV to the read it came from.
- `data/*.csv` — seven authored input tables (transcriptions) and the rest derived. `manifest.csv` hash-pins
  the raw reads, the authored inputs, and three read-only captures carried forward from a prior desk.
- `engine.py` — every number on every page. It prints its own headline results, so a run is reviewable in CI
  logs without opening a spreadsheet.
- `scoring.py` — Brier, base-rate skill, log loss, Wilson intervals, Bonferroni, the game-cluster bound, and
  a power calculation. Written and unit-tested **before** any registered week has settled, because a scorer
  tuned after seeing results is not a scorer.
- `build_site.py` — renders the 15 pages, appends a per-row provenance column, and renders a blank cell as an
  em dash rather than a zero.
- `verify.py` — determinism, capture hashes, transcript containment, row-level provenance, internal links, and
  agreement between each summary JSON and the table it summarises.
- `pre_registration.md` — the frozen instrument. The window opens 2026-11-19T20:15Z; no forecast may be
  written after kickoff and no model may be changed inside a registered week.

## What the desk refuses to do

These refusals are the substance of the work, not caveats:

1. **No invented market price.** No admitted book was reachable, so every market column is blank and every
   difference-vs-market cell reads `undefined - no admitted market price`. 39 model rows are recorded as
   shadow forecasts instead, with their own hashes.
2. **No backtest number on the leaderboard.** Both leaderboards (signal, staking) carry blank score cells
   because Week 11 is unplayed; the walk-forward totals live on the analytics page, labelled as what they are.
3. **No starter inference from a depth column or jersey order.** Where a gamebook was not published, the row
   says so.
4. **No "absent means did not happen".** The reserve-list register is capped at ~25 rows per page, and a
   missing snap-sheet row only means "did not play" inside games whose sheet exists — the universe is bounded
   in the code, not in a footnote.
5. **The injury signal is a delta, never a level.** Two dated reads of the same report changed **0 of 147**
   field values, which is the evidence that daily capture of a static file is the wrong design.

## Two findings worth the trip

- **A club-code alias defect in a carried-forward feed.** `LA`/`AZ` in the standings versus `LAR`/`ARI` in a
  prior desk's results feed silently dropped 18 club-games while every league total still balanced. The desk
  keeps both codes, publishes the alias map, and reconciles **32 of 32** clubs. Any prior desk's team-level
  numbers that skipped this join are suspect.
- **Two claims carried forward from earlier sessions that the register does not support** — that no priced
  games exist in this repo (7,439 of 7,548 are priced) and that Baltimore put both quarterbacks on IR (the
  only BAL reserve row in the window is a defensive lineman; the other QB was traded). Both are published as
  corrections, not quietly dropped.

## Editing

Never edit `data/*.csv` that `engine.py` writes, or any `.html`. Edit the authored input, rerun `engine.py`,
`build_site.py`, `verify.py`. `.nojekyll` is present because this directory is served verbatim by Pages from
the repository root; deleting it breaks the deployed desk.
