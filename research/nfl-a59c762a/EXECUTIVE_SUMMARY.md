# NFL Decision Console — Executive summary

**Session:** `a59c762a` · **Branch:** `arena/a59c762a-own5` · **Official reads:** 2026-11-19 (UTC)
**Desk:** [`nfl-desk-a59c762a/`](../../nfl-desk-a59c762a/index.html)

---

## What this session did

It answered the reviewer's brief line by line, against the official NFL record, and
published the answer as a decision console with one row per requirement.

It did three things that no other desk in this repository had done:

1. **Built the master requirement register** — one row per line of the brief, with the
   gate that blocks it, the number that would clear it, what is observed now, and a
   link to the evidence and to the official page. The repository previously held four
   partial registers in four different formats; the integration hub had already logged
   this as the gap to close (`nfl-integration-a620f5a5/data/suggestions.csv`, SG-A62-01).
2. **Made a dated, first-hand official capture** of the Week-11 availability record and
   published the **delta** against the repository's earlier partial read.
3. **Reconciled the whole results corpus against the official standings** and found a
   material defect in the repository's primary feed.

---

## The four findings that change a decision

### 1. The repository's primary results feed has a stale row, and it is not the only one

`nfl-desk-35a1feb2/data/results_feed_2026.csv` holds 150 rows. The row
`2026_10_LAC_BAL` — Los Angeles Chargers at Baltimore Ravens, Week 10 — has blank
scores and the status `SCHEDULED - NOT KICKED OFF AT READ TIME`.

The official [NFL Week 10 schedule page](https://www.nfl.com/schedules/2026/by-week/week-10),
read on 2026-11-19, shows that game **FINAL on Monday 16 November, Chargers 23, Ravens 20**.
The official [league standings](https://www.nfl.com/standings/league/2026/REG) include it.

Reconciling every feed against the standings, club by club, on all five fields
(wins, losses, ties, points for, points against):

| Feed | Rows | Week-10 discrepancies against the official read |
|---|---|---|
| `nfl-desk-35a1feb2/data/results_feed_2026.csv` | 150 | **1** — the Chargers at Ravens row is blank |
| `nfl-c98c6270/data/results_feed.csv` | 150 | 2 — Rams at Cardinals missing, Chargers at Ravens `NOT FINAL` |
| `nfl-command-desk/data/results_corpus.csv` | 150 | 1 — Rams at Cardinals missing |
| `nfl-market-desk/data/results_feed.csv` | 145 | 5 — five Week-10 games missing |
| `nfl-desk-e46fb855/data/results_feed.csv` | 145 | 5 — five Week-10 games missing |
| `nfl-price-results-853c0074/data/official_results.csv` | 136 | 14 — all of Week 10 missing |

The true corpus size is verifiable from the official standings alone: the 32 clubs sum
to **149 wins and 2 ties, which is 150 games**. The desk publishes its own 150-game
feed, reconciled with **0 mismatches**.

*Decision impact:* any backtest, rating fit or availability join that reads one of the
shorter feeds computes on an incomplete corpus, and the stale row mis-states two clubs.

### 2. The removal-of-luck panel shows exactly what the brief was worried about

The pre-registered singles-only model was fitted on weeks 1–8 only and evaluated on two
untouched chronological splits:

| Split | n | Accuracy | Brier | Climatology Brier | Brier skill | MAE (points) |
|---|---|---|---|---|---|---|
| Validation, week 9 | 15 | 0.8667 | 0.14349 | 0.25429 | **0.4357** | 9.649 |
| Final holdout, week 10 | 14 | 0.7143 | 0.25067 | 0.25547 | **0.0188** | 12.124 |

On the same 29 out-of-sample games, the **favourites-only control won 79.3 %** while the
model itself won **71.4 %**. The random control's analytic Brier is 0.25 and the
climatology control's is 0.25486.

A leaderboard that ranked on the validation week alone would have declared skill. The
final holdout says the validation week was mostly luck.

*Decision impact:* no strategy may be staked or rewarded on a single split. The
leaderboard therefore publishes prospective scores only, and the shadow numbers live on
their own page with the split visible on every row.

### 3. The depth-order source is verified for 31 of 32 clubs, and route (b) is unproven

The brief said not to build the backup-deficiency feature until one route is verified
for all 32 clubs. Neither route is:

- **Route (a), the club depth pages.** `nfl-desk-e46fb855/data/depth_slots.csv` holds
  702 rows. Thirty clubs are `parsed`. **Houston is a single row marked `NOT PARSED`**
  because the club publishes the depth chart as an image. The Patriots carry 19 parsed
  rows and 7 partial rows. A second capture in `nfl-c98c6270` holds 890 rows across 32
  clubs with the same Houston exception, plus **14 shared rank-1 slots and 5 empty first
  strings** recorded faithfully.
- **Route (b), play time.** The official [NFL Game Book](https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books)
  for Washington at New York was read in full. It publishes the starting lineups, the
  substitutions, the players who did not play, the **Not Active** list and the game-day
  weather and surface — and **no snap counts**. The official
  [Next Gen Stats glossary](https://nextgenstats.nfl.com/glossary) publishes tracking
  metrics and documents no public per-player play series.

*Decision impact:* the backup-deficiency feature, the off-versus-defence matchup matrix
and the starters-out count are left **unbuilt and blank**, as the brief instructs.

### 4. The earlier availability read was not a league report, and the club statements do not survive

The repository's Week-11 availability read
(`data/nfl-desk-f2e20e96/availability_wk11_preview.csv`, 10 rows, read 2026-11-18T03:46Z)
came from two **game pages**, which expose four rows per club. It carried club statements
that Minnesota and San Francisco had no active injuries.

The full league report, read 2026-11-19T06:45Z, carries **253 named rows across 24 clubs**,
with 9 `Out` and 7 `Questionable` designations, and a no-injuries-reported line for the
Bengals and the Commanders. It names **10 Minnesota rows** (including Jordan Addison, who
did not participate) and **15 San Francisco rows**.

*Decision impact:* a game page is not an availability source. The desk publishes the
**delta** with both read clocks on every row and never publishes a level.

---

## What the model actually produced

- Opponent-adjusted least squares on the 150-game corpus, fitted on weeks 1–8 only:
  `margin = HFA + rating_home − rating_away`, rating vector constrained to sum to zero,
  ridge penalty 1.0 on the ratings, home field fitted rather than assumed.
- **Home field 1.488 points; residual sigma 14.079 points.**
- 39 originated lines: 13 Week-11 games at three markets each, in the order
  **side → total → moneyline**, each row carrying the model line, the market line and
  the difference as three separate columns, plus the probability and the full input state.
- The total is published **twice** — estimator A (league mean) and estimator B (shrunk
  offense plus shrunk opponent defense) — with the gap, and neither is retired.
- 8 correlations, computed only from officially sourced numbers, each publishing n, a
  95 % interval and a two-sided p-value.

---

## What is blocked, and why

| Blocked thing | Gate | What would clear it |
|---|---|---|
| Market line, residual, closing-line value, ROI | No admitted price source (P-01, an open decision) | One permitted source with a quote timestamp per market |
| Parlay and prop-combo divisions | G-A59-10 joint evidence | A directly validated joint probability **and** the operator's void and push rules |
| Replacement depth, starters out, matchup matrix | G-A59-12 depth source | A verified depth order for all 32 clubs, or a verified official play-time source |
| Any leaderboard score | No prospective game played | The Week-11 slate, which kicks off 2026-11-19 at 8:15 PM ET |
| Injury and personnel ablations | No verified availability feature to ablate | The depth and play-time prerequisites above |

---

## What is on the site

13 pages: dashboard (with the full decision-readiness table), requirements, availability,
originated lines, leaderboard, gates, backtest and removal of luck, correlations,
questions, suggestions, flagged for review, sources, executive summary.

The verifier is fail-closed and runs **14 check families** (1 371 checks) plus **23 unit
tests**, eight of which are **negative controls**: each injects one deliberate defect
into a throwaway copy of the desk — a stripped source link, a filled blank without a
flag, a deleted flag, a backtest score on the leaderboard, a broken internal link, a
wrong row count, a non-official source, a tampered model output — and requires the
verifier to reject every one.

**No manual input was used.** Every artefact is produced by three scripts from the dated
raw captures, and the rebuild is byte-for-byte deterministic.

---

## The one thing to decide first

**The price-data policy (requirement R-02).** It is the single gate that blocks the
market residual, closing-line value, realised ROI, the parlay and prop-combo divisions,
and three of the fourteen gates. The desk deliberately keeps the price store empty and
publishes every money cell as blank and flagged until that decision is made. The
suggestion register states the options, the recommendation and both sides of the
what-would-change-our-mind field.
