# NFL Command Desk — methodology and provenance rules

## 1. Why this desk exists

The repository contains 32 NFL desk folders, each valid in its own namespace. A reader cannot
tell which one is current, which numbers are read and which are assumed, or what is still
missing. This desk answers three questions on one site:

1. What is **proven**, with the official page that proves it?
2. What is **missing**, what gate does it block, and what number would clear it?
3. What would change our mind?

It edits nothing in another session's namespace.

## 2. Provenance rule (hard)

* A value may be published **only** if this session read it from an official publisher and
  stamped the read; or if it is a deterministic computation over rows that individually pass
  the reconciliation check.
* A value that cannot be confirmed is **blank** and, where it matters, listed on the Flagged
  for Review page. It is never inferred, never carried over from an aggregator, and never
  filled in "conservatively".
* Derived numbers say what they were derived from, on the same row.
* Model output is labelled model output. It is not mixed into a column of read values.

## 3. Source classes

| Class | Meaning | Example |
|---|---|---|
| `official` | Published by the NFL or a league entity | nfl.com, media.nfl.com |
| `repository` | A fact about this repository, not about football | GitHub API |

Aggregators (Pro Football Reference, ESPN, spotrac, overthecap, etc.) are **not** admissible
sources at this desk. Two earlier desks used them for kickoff times and tie notes; those notes
travel with the row they came from and are marked in the corpus `note` column, never upgraded to
a read value.

## 4. The corpus merge rule

A game row is admitted to `results_corpus.csv` only after the **whole corpus** reproduces the
official standings: wins, losses, ties, points for and points against for all 32 clubs.

Why this test: points-for and points-against are additive over the season. A single incorrect
scoreline changes the total of two clubs, so the check is 32 independent constraints on 150
rows rather than 150 isolated spot checks. It cannot detect a pair of compensating errors (two
games wrong by the same amount in opposite directions), which is a known limitation and is
recorded as such.

The check runs in `corpus.reconcile()`, is re-run by `verify.py` (`V03`, `V04`), and has a unit
test that plants a one-point error and a flipped result and requires both to fail.

## 5. Windows and leakage control

| Window | Weeks | Games | Use |
|---|---|---|---|
| Train | 1-4 | 64 | Ratings only |
| Validation | 5-8 | 57 | Gates |
| Holdout | 9-10 | 29 | Read once, reported separately |

No row crosses a boundary. Every Week 11 line uses ratings from weeks 1-4 only. A unit test
adds a holdout game to the training set and requires the ratings to change, proving the split
is load-bearing rather than decorative.

**Known leakage risk that is not present but could appear later.** The corpus is scored with
final results. A correct point-in-time model needs a capture of the schedule, the standings and
the availability report *as they stood before each kickoff*. The repository holds one such
capture (2026-11-12) for one week only. Until a hashed multi-day capture exists (FLAG-A4),
"point-in-time" here means "training data restricted to earlier weeks", which is weaker than a
true pre-kickoff snapshot and is labelled as such.

## 6. The model

    rating(club)      = mean own margin over the games it played inside the train window
    fair home margin  = rating(home) - rating(away) + HFA
    fair total A      = points scored/game (home) + points scored/game (away)
    fair total B      = league mean total over the train window
    p(home win)       = sigmoid(fair home margin / 6.0)

`HFA = 2.0` points is an **assumption**, published as such. The 2026 observed home margin over
150 games is −0.98 (95% CI −3.07 to +1.13), so the assumption is not supported by this season's
sample; it is retained because it was registered before the season's numbers were seen. It is a
review question (Q07), not a fitted value.

The logistic scale of 6.0 was registered with the model. It is a convention that maps a margin
to a probability; it has not been calibrated (G04 is not met: 85 forecasts is far short of 500).

## 7. Metrics and why these

* **Brier score** — a proper scoring rule. Lower is better; it rewards calibration and sharpness
  together and cannot be gamed by abstaining on hard games the way accuracy can.
* **Brier Skill Score** — `1 − Brier(model)/Brier(flat 0.5)`. Positive means better than a coin.
* **Bootstrap over games** — one forecast per game, so the game is the natural resampling unit.
  2,000 draws, fixed seed, 95% percentile interval. Clustering by game rather than by bet avoids
  the false precision of treating two bets on one game as independent.
* **Exact binomial p, then Holm** — the registered family is small enough for exact tests, and
  Holm controls the multiplicity that comes from looking at several strategies.

Two things are deliberately **not** computed: **ROI** and **CLV**. Both need a market price. No
official price exists in the repository, so publishing either would be inventing the most
decision-relevant number on the page.

## 8. Leaderboard divisions and the demotion gate

Divisions: singles, game parlay, same-game parlay, prop combo. Parlays and prop combos sit
behind G09 (a directly validated joint probability plus the operator's void and push rules)
because multiplying marginal probabilities is invalid under dependence.

Demotion rule (R08): a live strategy returns to paper immediately when any of the following
happens —

* its rolling 100-bet Brier skill lower bound falls below 0;
* its calibration slope leaves 0.8-1.2 on the rolling sample;
* its realised CLV is negative for two consecutive four-week blocks;
* a required data source fails its drift alarm (a pinned row count or a required field).

No strategy is live, so the rule has nothing to demote yet. It is published so that it cannot
be negotiated later.

## 9. Availability: the surprise rule

The injury signal must be a **surprise**, not a level: what matters is the change between two
timestamps, not the status on any one day. That requires at least two dated captures. The
repository has one. The desk therefore publishes a single diff (2026-11-12 vs 2026-11-18) for
the four clubs that could be re-read, and states plainly that no delta exists for the other 28.

Depth is never modelled from jersey order, experience or salary. Those are recorded as
rejected (R48, Q-list). Depth needs a published depth chart with a date and a source per row
(FLAG-D1) or a playing-time source (snap counts, FLAG-A2). Neither exists for 2026.

## 10. Reproducing everything

```
python3 nfl-command-desk/generate.py    # data/*.csv from committed inputs
python3 nfl-command-desk/build.py       # 11 pages
python3 nfl-command-desk/verify.py      # 46 fail-closed checks
python3 -m unittest discover -s nfl-command-desk/tests -v
```

CI (`.github/workflows/nfl-command-desk.yml`) runs all four and fails on any diff between the
committed tree and a clean rebuild.
