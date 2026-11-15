# Methodology — NFL market desk (session 83a7d6a8)

Everything below is a decision that was fixed before the numbers were looked at, or a rule
that the build enforces mechanically. Where a decision is a stipulation rather than a
measurement, it says so.

## 1. Data tiers

| Tier | Meaning | What it may be used for |
|---|---|---|
| OFFICIAL | A league or club page, read directly, with its clock time | Anything |
| AGGREGATOR | A third-party mirror with undocumented provenance (no book, jurisdiction or quote time) | Benchmarking, research ROI, residual studies — never certification or CLV |
| DERIVED | Computed here from published inputs, reproducible from committed files | Any claim whose derivation is published |
| UNVERIFIED | Could not be confirmed | Nothing. Published as a blank with a flag |

## 2. The chronological split

Weeks 1–4 are burn-in (ratings only, never graded). Weeks 5–8 are validation. Weeks 9–10
are the final holdout and were **not** used to choose anything. Every forecast records
`train_last_week` and `train_games`, and gate G3 fails the build if any forecast was trained
on its own week or a later one.

## 3. The model

A joint least-squares attack/defence rating with a home-field term, fitted on completed
games only. Because both sides of every game enter the same fit, every rating is
opponent-adjusted by construction. The margin distribution is normal with a fitted
σ_margin; the moneyline is **not** fitted separately — it is Φ(side / σ) of the same margin
model, so the two markets cannot disagree in direction.

## 4. Origination order

Side → total → moneyline. The side is a points forecast, the total is a separate points
forecast from a separate σ, and the moneyline is a probability derived from the side. This
order is stored in `origination_order` so a reader never has to guess which number came
from which.

## 5. Prices

- The league publishes no price. This was checked on the schedule, standings and injury pages.
- Operator pages are outside the capture environment's network allowlist, so the operator
  route is recorded as **blocked**, not as pending.
- The only prices in the repository are the mirror's. They are AGGREGATOR tier everywhere.
- Two-way markets are de-vigged **proportionally**. That is a stipulation, published as a
  method assumption (P-07), not a fact about any book.
- A market with no price keeps an empty snapshot row with a flag id. No substitution, no
  interpolation, no carry-forward.
- Opening and closing snapshots require two observations. One capture produces neither, so
  those rows are empty with flag OWN-03.

## 6. Statistics

- **Proper score:** Brier. Reported against the market's own de-vigged probability, against
  climatology, and against a coin flip — never against nothing.
- **Clustering:** game-level cluster bootstrap (2,000 resamples, seeded), because two bets on
  the same game are not independent.
- **Multiplicity:** Holm adjustment across all nine registered families, not across the
  families that happen to look good.
- **Market-state rules** carry no probability, so ranking them on Brier was an artefact.
  They are ranked on hit rate against the null rate implied by the price they paid.
- **Ranking is never by ROI.** ROI is published, with its n and its price tier, in a separate
  column with a separate rank.

## 7. Personnel

The brief asks for ablations with uncertainty, not fixed penalties. The coefficient is
estimated from Week 10 games where a personnel difference exists and is published with its
standard error. It spans zero, so **no points penalty is applied anywhere**. The
replacement-depth table is evidence, not an adjustment.

## 8. Depth charts

Read from each club's own page. Shared slots (two players at rank 1) and empty slots are
preserved as published. Jersey numbers are parsed and stored, and used for nothing: the
brief explicitly rejects deriving depth from jersey number, experience or salary. Where a
club publishes an image instead of a table, the chart is recorded as unreadable rather than
transcribed by eye.

## 9. What the build enforces

`verify.py` fails on: a table row with no source and no explicit UNVERIFIED marker; a broken
internal link; a requirement whose evidence file is missing or empty; a duplicate or
unnamespaced flag id; a published number that does not match its file; a required field
disappearing from a core table; a registration hash that does not match its rule file; a
backtest number appearing in the leaderboard universe; and a rebuild that is not
byte-identical.

## 10. Reproducing

```
cd nfl-market-desk
python3 capture_injuries.py     # official injury report (network)
python3 build_results.py        # results feed + reconciliation from the pinned mirror
python3 build_model.py          # forecasts, accuracy, ablation, originated markets
python3 build_prices.py         # policy + snapshot store
python3 build_strategies.py     # pre-registration, grading, leaderboard, gates
python3 build_availability.py   # injuries + depth + announcements
python3 build_registers.py      # requirements, readiness, questions, suggestions
python3 build.py                # the 13 pages
python3 verify.py               # all checks
```

Stdlib only. No package is installed by this desk.
