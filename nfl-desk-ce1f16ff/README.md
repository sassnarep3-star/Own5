# Own5 NFL desk — session `ce1f16ff`

Origination, verification and gating for the 2026 season. The desk originates its own
lines, keeps every price it ever quoted, and refuses to promote anything it cannot
defend. It currently promotes nothing, and the reason is on the front page.

Read the site first: [`index.html`](index.html) (published at
`https://sassnarep3-star.github.io/Own5/nfl-desk-ce1f16ff/`).

## Run it

```bash
cd nfl-desk-ce1f16ff
python3 run.py            # rebuild every table and every page, from the committed inputs
python3 -m unittest discover -s tests   # 82 tests: arithmetic, gates, chains, site contract
python3 verify.py         # 32 checks: chains, determinism, citation coverage, links, fail-closed gates
```

Python 3.11+, standard library only — no numpy, no pandas, no network. Every input is a
pinned file in this repository, so the build is reproducible byte-for-byte: `verify.py`
rebuilds everything and compares digests, and CI fails on drift.

`python3 run.py --check` rebuilds into a scratch copy and compares, for when you want the
working tree left alone.

## What each file is

| File | Produces | Promise it keeps |
|---|---|---|
| `statslib.py` | — | Every statistic the desk quotes, stdlib-only, unit-tested against hand-computable cases |
| `inputs.py`, `vendor.py` | `data/input_register.csv` | Reads pinned mirrors only; verifies each file's digest against the owning session's record and says so |
| `results_feed.py` | `data/results_feed.csv`, `results_checks.csv`, `game_conditions.csv` | Hash-chained; 13 self-checks; a scheduled game carries no score, ever |
| `originate.py` | `data/fair_lines.csv`, `model_ratings.csv`, `backtest_predictions.csv`, `derivation.csv` | Side, then total, then moneyline, from one fit with no look-ahead; refusals written to stderr, never to a table |
| `grade.py` | `data/settled_legs.csv` | A push returns the stake and leaves the denominator |
| `ledger.py` | `data/leaderboard_signal.csv`, `leaderboard_staking.csv`, `exposure.csv`, `calibration.csv`, `validation.csv`, … | Break-even read from the price actually taken; Holm over every registered variant; DSR with the trial count |
| `depth.py` | `data/replacement_depth.csv`, `depth_by_team.csv`, `absence_vs_depth.csv`, `depth_rules.csv` | Depth graded from the replacement's own measured snaps; a peer's score stays in a separate labelled column |
| `availability.py` | `data/availability_base_rates.csv`, `availability_impact.csv`, `availability_wk10_official.csv`, `availability_source_diff.csv` | Exact-name joins only, with every rejected join counted; a source disagreement stays visible |
| `markets.py`, `store.py` | `data/price_snapshots.csv`, `line_sheet.csv`, `market_gaps.csv`, `store_meta.csv` | Hash-chained store; every row carries provider, URL, method, timestamp; a missing cell becomes a gap row |
| `leaderboard.py` | `data/leaderboard.csv`, `rewards.csv`, `scoring_rules.csv`, `multiplicity.csv` | Signal rank and staking rank published side by side; no division awarded unless it is worth awarding |
| `gate.py` | `data/demotion_gate.csv`, `gate_rules.csv`, `gate_integrity.csv` | Fail-closed demotion; an unmeasurable rule is `unevaluable`, not passed |
| `correlate.py` | `data/correlations.csv` | No `r` without `n`, a confidence interval and a source; refusals printed as refusals |
| `registers.py` | `data/suggestions.csv`, `questions.csv`, `flags.csv`, `sources.csv`, `strategy_states.csv` | Options and costs, not implementations; every register row is `PROPOSED` |
| `capture_job.py` | `data/capture_log.csv`, `data/captured_<date>.csv` | The only thing here that touches the network, and it runs in CI, not from a laptop |
| `build_site.py` | 13 HTML pages, `assets/desk.css` | A blank cell is marked "not published"; a truncated table says how many rows it left out |

## Conventions that are not negotiable

- **No price here is official.** Odds come from an aggregator page attributing one
  sportsbook. They are tier-labelled `OPERATOR` everywhere they appear.
- **Closing lines do not exist yet in this build** (0 rows in a 148-row store), so no
  closing-line-value claim is made anywhere. `market_gaps.csv` carries all 56 absent
  cells; `capture_job.py` on its weekly schedule is what changes that.
- **A gap is a result.** Blank plus a reason plus a route to an answer beats a number
  that looks complete.
- **`data/live_bets.csv` ships empty on purpose.** The demotion gate is *armed*, not
  *passed*; `verify.py` fails if anything writes rows into it.
- Scores are regulation plus overtime. Tie rate is measured (1 of 137 games) and used
  to split the moneyline's tie mass rather than assumed away.

## Known limits, in one place

See [`flagged.html`](flagged.html) (12 flags, 2 high). The high ones: three pinned
upstream mirrors were republished after this desk pinned them (so the pin holds and the
drift is logged rather than chased), and the model loses to the market as a forecaster —
`r=0.2901` for the model against `r=0.453` for the posted line on the identical fixture
list, which is the honest reason nothing is promoted.
