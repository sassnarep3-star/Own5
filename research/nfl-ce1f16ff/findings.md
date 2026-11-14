# Findings — session `ce1f16ff` (2026 season, week 10 snapshot)

Every number here is regenerable from the committed inputs (`python3 run.py` in
`nfl-desk-ce1f16ff/`) and carries its own `n` and interval. Nothing in this file is
advice; nothing here is promoted.

## The headline

**The model loses to the market as a forecaster, so the desk promotes nothing.**

| Quantity | model | posted line | same games |
|---|---|---|---|
| Home margin — Pearson r | **0.2901** | **0.4530** | n = 1,274 |
| Home margin — MAE (points) | 10.574 | 9.808 | n = 1,274 |
| Home margin — RMSE (points) | 13.610 | 12.688 | n = 1,274 |
| Total — Pearson r | 0.0551 | 0.2978 | n = 1,274 |
| Total — MAE (points) | 11.242 | 10.326 | n = 1,274 |

Walk-forward, one model per week, no look-ahead. Model reliability over seven bins of
`P(home wins)` sits inside ±0.045 of realized frequency (Brier 0.2356), so the model is
*calibrated* — it is simply **less informative than the line**. Being well-calibrated
about a weaker signal is exactly what a desk must not mistake for an edge.

## Gate state (11 promotion gates)

| | |
|---|---|
| PASS | V-01 results coverage · V-02 price coverage · V-03 break-even computed per bet · V-04 sample floor honoured · V-07 push handling · V-09 provenance per row |
| FAIL | V-05 survives multiplicity (Holm p = 1.0000 for every strategy) · V-06 forecast skill ≥ market · V-08 closing-line value (0 closing snapshots) · V-11 promotion authority (no live record) |
| BLOCKED | V-10 stability across seasons (2026 window too short to split) |

Promoted strategies: **0 of 12**. Leaderboard rewards: `parlays → NOT AWARDED`,
`singles → NOT AWARDED`, `prop-combos → BLOCKED`.

## Results and schedule

- 151 feed rows: **137 FINAL**, 14 scheduled rows carrying no score (by design), 0
  disagreements with the pinned mirror, 32/32 clubs reconciling W/L/T/PF/PA against the
  official standings.
- 2026 home-field advantage measured **+0.47 points** (n = 130 non-neutral, 95% CI
  −1.81 … +2.75) versus the **+2.0** constant several other boards assume. The desk uses
  the measured value and publishes the interval, because "the assumed constant is
  4× the point estimate and outside its CI" is a finding about the other boards.
- 2026 tie rate **1 / 137 = 0.00730** — used to split the moneyline tie mass instead of
  assuming ties are impossible.
- 9 neutral-site games in 2026, verified against the mirror's `location` field; those
  games carry no home-field term.

## Signals, with the luck test attached

| strategy | settled | hit rate | break-even of its own prices | raw p | Holm p | verdict |
|---|---|---|---|---|---|---|
| S6 take the model's side at any size | 1,224 | 0.4845 | 0.5187 | 0.0176 | 0.1936 | below break-even, not a signal |
| S4 over when our total ≥ 3 pts above market | 317 | 0.4448 | 0.5208 | 0.0069 | 0.0828 | strongest raw p in the desk, still not < 0.05 adjusted |
| S8 moneyline away when model p_home ≤ 0.38 | 87 | 0.6322 | 0.7342 | 0.0384 | 0.3840 | under-powered, needs n ≈ 2,243 |
| S7 moneyline home when model p ≥ 0.62 | 372 | 0.6882 | 0.7186 | 0.2046 | 1.0000 | indistinguishable from luck |
| P1 home side + over (parlay) | 299 | 0.2475 | 0.2702 | 0.3978 | 1.0000 | indistinguishable from luck |

Break-even for a −110 bet is 52.38%; proving a 55% handicapper against that at 80%
power needs roughly **2,243 bets**. The desk's largest strategy has 1,224 and its
typical one has fewer than 400, so *every* row here is an under-powered result rather
than evidence of no edge — a distinction the table states in words, because a reader
who sees "p = 0.3978" alone will write "no edge" and be wrong in a different way.

Signal rank and staking rank disagree on purpose. The four parlay strategies hold
signal ranks 1-4 and staking ranks 3, 6, 7, 8; the best staking rank overall belongs to
`S5` (signal 9) and the second-best to `S8` (signal 12), while `S6` — the largest
strategy in the desk, 1,255 bets — is 10th on signal and **12th last** on units. Every
one of the twelve earns 2 points, because the two rank orderings answer different
questions and neither is allowed to launder the other. Merging them into a single score
would hide exactly the thing worth looking at.

## Prices

- 148 chained snapshots: 100 `pre_game`, 48 `opening`, **0 closing**, 16 games with an
  operator snapshot. 14 line-sheet rows; 126 gap rows.
- Largest fair-vs-market differences on the live slate (points, signed fair − market).
  Totals: `SEA@LV` **+8.0**, `MIA@IND` **+7.0**, `LAR@ARI` **+6.5**, `LAC@BAL` **+5.5**,
  `MIN@GB` **−4.0**, `SF@DAL` **−4.0**. Side: `IND@HOU` **+5.0**, `LAR@ARI` **−4.5**,
  `MIA@IND` **+4.0**. Moneyline (probability points): `LAR@ARI` **+0.1219**,
  `CAR@NO` **−0.0903**, `HOU@CLE` **+0.0576**, `BUF@NYJ` **+0.0571**.
- The `LAR@ARI` row is the one to look at first, because its side and total differences
  point in opposite directions from the same two numbers: fair side 5.0 against a posted
  9.5, fair total 46.0 against a posted 39.5. A posted total 6.5 points below the model
  and 8 points below the *other* posted number on the same page is a capture or
  transcription hazard, not a find.
- Those differences are **not** claims of value. Four of the source's own line moves are
  implausible (MIA@IND 47.5 → 37.5, LAR@ARI 47.5 → 39.5, JAX@TEN −2.5 → −10.5,
  IND@HOU −5.5 → −10.0), which is why MK-F-03 says the biggest apparent edges in this
  build are more likely to be capture artefacts than alpha.
- No opening moneyline exists on the source page at all (MK-Q-01), so the moneyline gap
  cells are `ABSENT FROM SOURCE` rather than estimated.

## Availability and depth

- Base rates, week 1–9 2026, official report × play records, exact-name join:
  **Questionable** n = 590, played **346** (58.64%, Wilson 54.63–62.55%), median snap
  share when played 0.54; **Out** n = 588, played **0** (upper bound 0.0065);
  **Doubtful** n = 43, played **0** (upper bound 0.082).
  "Questionable means out" is therefore false, and so is using the status as a point
  estimate for an individual — it is a base rate over 590 player-weeks.
- Week 10 official report vs mirror: **326 vs 276 rows** across the 28 clubs that have a
  report (4 are on bye); 18 clubs disagree on row count, `BAL` the most sharply (8 vs 0). That is a vintage disagreement, kept visible rather than
  reconciled by picking a side (MK-F-06).
- Replacement depth: **705** published position groups across 31 clubs — TESTED 90,
  PARTIALLY TESTED 423, UNTESTED 116, NO NAME PUBLISHED 76. Graded from the named
  replacement's own measured snap share, not from the fact that a name exists.
- Of 96 week-10 absences joined to the depth charts, many resolve to
  `NO MEASURED BACKUP at this position in the snap records`. Offence and defence snaps
  removed are published against their own bases (256.5% and 328.0% are the maximums, and
  they are not clamped: several full-time players at one position can remove more snaps
  than one unit produces). 25 club-weeks carry the impact, `players_unmatched` says how
  many listed names were absent from the snap records, and those names contribute zero
  rather than an estimate.
- Another session's `deficiency_points` is carried as a separate, labelled peer column
  and never blended into the desk's own measurement.

## Correlations (officially sourced only)

| pair | r | n | tier |
|---|---|---|---|
| \|margin\| vs total | 0.0478 | 1,411 | OFFICIAL |
| home points vs away points | −0.0262 | 1,411 | OFFICIAL |
| weekly mean margin → next week | −0.2591 | 89 | OFFICIAL |
| same, 2026 only | −0.0157 | 137 | OFFICIAL |
| φ(home winner ∧ total ≥ 45) | −0.0796 | 1,411 | OFFICIAL |

The last row is what licenses pricing a same-game home+over parlay by multiplying two
legs at all — the legs are *slightly* negatively associated, so the product is not a
fabricated independence. Five further pairs are published as `NOT COMPUTED` with a blank
`r` and a reason (QB ↔ top-WR being the notable one: the only available figure, r = 0.76,
is a third party's, and this desk will not launder it into an official-tier row).

## Demotion gate, as shipped

`integrity_ok = True`, 0 outage weeks, 0 live bets → all 12 rows read **`STAYS ON PAPER`**
with `rules_unevaluable: D3`. That is reported as **armed, not passed**: a gate that
"passed" on an empty ledger would be a gate that passes on nothing.
