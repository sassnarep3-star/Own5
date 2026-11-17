# Methodology — NFL Season Desk (`941fe39f`)

Every number on the site is produced by `tools/season_desk_941fe39f/build.py`.
Nothing is typed by hand. This file explains how, so a reader can decide whether
to believe it.

---

## 1. The corpus, and why it is pinned

One tarball, `data/corpus/raw/nfldata_e045566e.tar.gz`, fetched from a single
commit of the nfverse release set and committed. Its SHA-256 is
`9a6a736819bd6587f135d0995778c23ef9e51a9587d9e901f5dc84072504462c`.
`build.py` recomputes the hash on every run and refuses to proceed if it differs.

Why this matters: the corpus is the only dataset with enough history to fit a
model and grade it out of sample (7,239 games, 1999–2026). Anything less than a
pinned, hashed snapshot would make every downstream number unreproducible.

**What the corpus is not.** It is a *single-snapshot* price set. It carries one
spread and one total per game, apparently at close. It does **not** carry an
opening price. That single fact decides several gates (see §6) and it is why CLV
is recorded as failed-by-construction rather than quietly skipped.

---

## 2. Feature handling

| Input | Treatment |
|---|---|
| Numeric columns | coerced from strings before any arithmetic; a blank stays blank, never zero |
| Team codes | normalised on every join. The corpus writes `LA`, `ARI`, `WAS`, `JAX`; official feeds write `LAR`, `AZ`, `WSH`, `JAC`. Both directions are mapped |
| Weather | `wind_mph`, `temp_f`; missing values drop the row from the correlation, never impute zero |
| Rest | computed from the game log, not read from a column |

The team-code trap is worth its own note because it has already caused one wrong
answer in this repo: an unmatched code that is silently treated as "no games"
looks identical to a genuine zero. `crosscheck.py` now diagnoses every unmatched
code rather than skipping it.

---

## 3. The model

A ridge-shrunk rating model, fit separately for each game on data strictly before
that game:

```
margin_home = hfa + rating[home] - rating[away]
total       = base_total + pace[home] + pace[away]
                 + wind_effect + temp_effect + rest_effects
```

- `HALF_LIFE_DAYS = 365` — a game a year old carries half the weight of today's.
- `RIDGE_RATING = 2.0` — shrinks thin records toward the mean rather than letting
  a 2-0 team look elite.
- `MIN_GAMES_TO_FIT = 60` — below this the model refuses to originate.
- `sigma = 11.52` — by probit maximum likelihood, used to turn the margin into a
  win probability. It is recomputed per fit and stored on every row.

**Walk-forward is structural, not procedural.** `Fit(games, cutoff)` discards every
game on or after the cutoff, and `originate()` records the cutoff it used on each
row. A test asserts that no row's gameday precedes its fit cutoff. That test is
the single most important one in the suite: it is what makes the holdout a
holdout.

---

## 4. Origination order

Side first, then total, then moneyline — the order the brief asks for, and the
order that matters. Moneyline is a *function* of the side model and sigma
(`Phi(margin / sigma)`), so originating it first would mean deriving the side
from the moneyline, which is backwards.

Every market is stored as four separate things: the **fair** value, the **market**
value, the **difference**, and the **probability** (plus the inputs that produced
it). They are never combined into a single "edge" column, because that would hide
which of the two moved.

---

## 5. Strategies, windows, and pre-registration

Windows are disjoint and fixed before evaluation:

| Window | Seasons | Purpose |
|---|---|---|
| train | 1999–2012 | fitting |
| validation | 2013–2019 | sign check (G7) |
| holdout | 2020–2025 | the only window that can certify |
| prospective | 2026– | untouched |

`prereg.py` writes `data/strategy/prereg.json` containing every rule text, its
SHA-256, the windows, the gates, and **the git commit that introduced them**.
It refuses to write while `strategies.py`, `model.py` or `stats.py` is
uncommitted — a registration made against dirty code proves nothing, so the
refusal is the feature.

Amendments are new strategies with new ids. The superseded id stays visible,
marked retired. This is the only mechanism that prevents a quiet re-tune.

---

## 6. The nine gates, and the honest one

| Gate | Tests | Threshold |
|---|---|---|
| G1_SAMPLE | evaluation sample | n ≥ 300 |
| G2_PRICE | two-sided price at one clock time | required |
| G3_CLV | beat the close | **unmeasurable here** |
| G3B_ALPHA | residual alpha, interval excludes 0 | > 0 |
| G4_BSS | Brier skill vs de-vigged close | > 0 |
| G5_CALIBRATION | calibration slope, intercept | [0.8, 1.25], \|a\| < 0.05 |
| G6_MULTIPLICITY | Holm-adjusted p | < 0.05 |
| G7_SURVIVAL | validation sign = holdout sign | same sign |
| G8_DECAY | max single-season profit share | ≤ 40% |

**G3 cannot be passed with this corpus.** It needs an opening *and* a closing
price from the same book to sign CLV. With one snapshot, the only computable
"CLV" is model-minus-close, which is the selection rule itself — circular. So G3
is recorded as failed by construction on every strategy, and **G3B** carries the
measurable substitute: does our disagreement with the close predict the result
relative to the close?

That substitution is a real weakening and is stated as one. G3B is a weaker
statement than CLV, but it is the strongest one a one-snapshot corpus can
support.

**No strategy is certified, and a family that fails a gate is not dropped.** It
still counts in the multiplicity family (G6), so testing more rules cannot buy a
better p-value.

---

## 7. Scoring

**Brier skill vs the de-vigged close** is the ranking axis. ROI is published
because the brief asks for it and is never used to rank — the brief explicitly
rejects season-long ROI as a ranking rule, and the code enforces that by ranking
on `bss_holdout` only.

Uncertainty is a **game-cluster bootstrap**, not an i.i.d. bootstrap: bets on the
same game are correlated, so resampling bets independently would understate the
interval. Clusters are games.

Multiplicity is **Holm**, not Bonferroni. Holm is uniformly more powerful and
never gives an adjusted p below the raw one, so it is strictly better here.

---

## 8. Availability: depth, injuries, replacements

- **Depth comes from the clubs' own charts.** Never from jersey number, salary or
  experience — the brief rejects all three, and the parser has no code path for
  any of them.
- **A shared rank-1 cell is a group.** Seattle publishes "Cooper Kupp | Rashid
  Shaheed". Storing one name would fabricate a starter the club never named. The
  group is stored, counted, and published as a group.
- **An empty rank-1 cell stays empty.** It is never filled by promoting rank 2.
  Green Bay prints one unlabelled continuation row under its RB row; that joins
  the slot above it and makes it a genuine four-deep chain rather than inventing
  an empty fifth slot.
- **A replacement carries his depth rank**, not just "a replacement happened". A
  rank-2 guard replacing a rank-1 guard is a different event from an unnamed
  practice-squad call-up, and the table shows which.
- **The injury signal is surprise, not level.** The desk computes the delta
  between two dated reads (2026-11-15T23:27Z → 2026-11-17T00:57Z). This session's
  delta was **0 changed rows**, and it is published as zero rather than dressed
  up as a finding.
- **Injury effects are ablations, not point penalties.** The brief rejects fixed
  point penalties, so there is no "+3 points for a starting QB out" constant
  anywhere in the code.

---

## 9. Snapshots and point-in-time replay

Every official capture is hashed and entered in an append-only ledger with a
clock time. The ledger has **one row per read**, not one per file: the injury
report was read at two clock times, and collapsing them would make replay return
the wrong capture for a given moment.

Replay is exact: `SNAP.replay(rows, unit, as_of)` returns the capture in force at
that instant, and returns `None` before the first capture rather than guessing.
A schema contract per parser fails the build if a field disappears from a source
page. An alarm reports freshness.

---

## 10. What is deliberately not here

| Not done | Why |
|---|---|
| Season-long ROI ranking | rejected by the brief; enforced in `leaderboard_graded.csv` |
| Depth order from jersey/salary/experience | rejected by the brief; no code path |
| Fixed point penalties for injuries | rejected by the brief; ablations instead |
| Imputing a missing price | a blank is published instead, with a flag |
| Passing G3 by redefining CLV | would be circular; recorded as failed |
| Publishing a backtest number on the leaderboard | prohibited by the brief |
| Guessing Houston's depth chart from an image | would be a fabricated reading |

---

## 11. Reproducing this

```bash
python3 tools/season_desk_941fe39f/build.py    # 28 derived files + manifest, ~25 s, no network
python3 tools/season_desk_941fe39f/site.py     # 22 pages
python3 tools/season_desk_941fe39f/verify.py   # row provenance, links, corpus pin
python3 -m unittest discover -s tests -p "test_season_desk*"   # 48 tests
python3 tools/season_desk_941fe39f/prereg.py   # refuses if the rules are uncommitted
```

CI (`.github/workflows/nfl-season-941fe39f.yml`) runs all of this and then asserts
`git diff --exit-code` over `nfl-season-941fe39f/`, so a committed site that does
not match a clean rebuild fails the build.
