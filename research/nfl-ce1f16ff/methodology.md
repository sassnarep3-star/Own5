# Methodology — session `ce1f16ff`

Written so a reviewer can rebuild or reject each choice without reading the source first.

## Build order

`run.py` runs thirteen modules in dependency order:

```
inputs → results_feed → originate → grade → ledger → depth → availability
       → markets → leaderboard → gate → registers → correlate → build_site
```

The order is a dependency chain, not a preference. `originate` needs a results feed
before it can fit anything; `grade` needs the model *and* a price; `ledger` needs
graded legs to score; `gate` needs everything, because its whole job is to look for a
reason to stop. `build_site` runs last and reads only the committed CSVs — no page
computes anything, which is what makes the pages checkable by `verify.py`.

## Inputs, and what "pinned" means here

Every input is a file in this repository, read through `inputs.py`, and each one's
sha256 is compared against the digest recorded by the session that captured it
(`data/decision-desk/raw/provenance.json`). `data/input_register.csv` publishes the
comparison for all 11 mirrors: path, digest, upstream URL, capture timestamp,
and `MATCHES` or a failure. Nothing is fetched at build time; the sandbox has no
route to the sports-data hosts anyway, which is why `capture_job.py` runs in CI.

When the live release assets were re-checked on 2026-11-14, three of them
(`games`, `injuries_2026`, `snap_counts_2026`) had been republished upstream with
different digests. The desk **kept its pin** and flagged the drift (MK-F-01) instead
of refreshing it, because a mid-analysis swap of the results file would invalidate
every check that had just passed against the old bytes.

## Results feed

Official 2026 slate (14 games per week × weeks, byes excluded) reconciled row-for-row
against the pinned mirror; scores are the mirror's, re-verified two ways:
`PF − PA = NET` and "points for = points against, summed across clubs" against the
official standings for all 32 clubs. Thirteen checks, including the ones that exist
to catch a future regression rather than today's bug:

- RF-06: every slate row appears in the feed (catches a join that silently drops games —
  it caught exactly that in the availability table)
- RF-08: four byes in a 32-team week, typed as integers on purpose
- RF-12: **no PENDING row carries a score**, which is what stops a scheduled game from
  becoming a fabricated result
- RF-11: the hash chain recomputes

Regulation plus overtime. A tied game is graded as a push on side and total.

## Origination: side, then total, then moneyline

One ridge-regularised ratings fit per week, walk-forward — a model for week *w* is
fitted only on games strictly earlier in the same season, so no row in
`data/backtest_predictions.csv` can have seen its own result.

1. **Side.** Expected margin from the two teams' ratings plus a measured home-field
   term; neutral-site games lose that term. Rounded to the 0.5 tick.
2. **Total.** The sum of the same two teams' expected points. **No second fit** — a
   separately fitted total would let the two markets contradict each other.
3. **Moneyline.** Derived from stage 1's margin distribution and the model's residual
   standard deviation. The tie mass is removed using the observed tie rate
   (1 in 137 = 0.00730) and split proportionally, then converted at no vig.

`data/derivation.csv` records each stage's input and rule; a test asserts stage 3 says
"no new fit" so a future edit cannot quietly re-fit it.

## Prices, and why none of them are official

`data/price_snapshots.csv` is append-only and hash-chained. One row per
(game, market, selection, stage). Each row carries provider, source URL, capture
method, UTC timestamp, verification text and lineage (`CAPTURE` = transcribed this
session; `MIRROR` = vendored aggregator file, line vintage undocumented). A cell the
source did not publish is a **gap row** in `data/market_gaps.csv` (56 closing cells,
42 opening-moneyline cells), never a zero and never a dropped row.

Historical prices come from the mirror's aggregator column, which is enough to test a
model against and not enough to call a closing price — so `closing_rows = 0` in
`data/store_meta.csv`, and V-08 fails.

## Scoring

- Break-even for a bet is computed from **that bet's own price**, not an assumed −110.
- A push returns the stake and leaves the hit-rate denominator, but stays in the bet
  count (both numbers are published: `bets`, `settled`, `pushes`).
- A parlay with a push is voided here, with the alternative quantified (MK-Q-06),
  because operators differ and the desk will not silently pick one.
- Hit rates get Wilson intervals; the test against break-even is an exact binomial;
  all twelve registered strategies enter a **Holm** step-down; Sharpe ratios get a
  **deflated** p using the trial count recorded in `data/multiplicity.csv`.
- Sample-size honesty: `required_n` for 80% power at the observed gap is published per
  strategy, and where it exceeds the cap the row says
  `>50000` rather than rounding to something hopeful.

## Gates

Eleven promotion gates (`data/validation.csv`), where a gate can be `PASS`, `FAIL` or
`BLOCKED` and **never blank**. Four desk preconditions (feed coverage, integrity,
provenance, sample floor) apply to everybody; a strategy cannot buy its way past a
broken feed with a good backtest.

Six demotion rules (`data/gate_rules.csv`), evaluated every build against
`data/live_bets.csv`: D1 hit rate under break-even over the last 20 graded live bets
(no significance required), D2 backtest Holm p ≥ 0.05, D3 mean CLV < 0, D4 drawdown
beyond 6 units or 3× the backtest's own worst, D5 any integrity failure demotes
**everything live at once**, D6 three capture-outage weeks. A rule whose input does not
exist is reported in `rules_unevaluable`, which is not the same as passing.
