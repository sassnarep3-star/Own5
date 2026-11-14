# Suggestions: options for review and the recommended path

This section exists so a decision can be taken **before** implementation. Each option lists what it
changes, the evidence behind it, the options that compete with it, the recommendation, the effort and
how easily it can be reversed.

## Option set

| ID | Title | Area | What changes | Evidence | Options considered | Recommendation | Effort | Reversible |
|---|---|---|---|---|---|---|---|---|
| SUG-01 | Establish a primary market price feed | data | Market line, market price, difference, CLV and market ROI become real; gate criteria 9 and 10 become testable; S4 becomes runnable | Every market column in this desk is blank; `nfl.com/betting/` returns 404; no operator feed reachable from this environment | A: keep everything blank and fail closed. B: use the repo's third-party ESPN/DraftKings scrape. C: license a primary feed | **C**, with A as the interim state. B is rejected: a third-party scrape cannot satisfy "every row has an official source", and it silently changes the meaning of every ROI column | Commercial | Low (append-only store) |
| SUG-02 | Archive each week's official injury report inside this desk | data | Enables a walk-forward depth backtest, which is the only way to know whether S5 has value | No official historical injury archive exists on nfl.com; the official page is current-week only | A: keep one snapshot. B: archive weekly from now on | **B**. The archive starts empty and grows; that is the honest answer to Q-04 | Low, automated | Yes (additive files) |
| SUG-03 | Estimate the 2026 home-field effect instead of assuming 2.0 | model | Replaces the only non-official number in the engine with an official-data-derived value and an interval | HFA = 2.0 is flagged in `data/flagged_for_review.csv`; the older desk estimates it empirically in `nfl-desk-864d5668/data/hfa.csv` | A: keep the constant and flag it. B: estimate it from the official results | **B**, published as an estimate with `n` and an interval, keeping the constant as the fallback | Low | Yes (one parameter) |
| SUG-04 | Parse the official Game Book PDFs into a player table | data | Unlocks player-prop research and per-player replacement analysis | NFL Game Center publishes an official Game Book PDF per game | A: skip props. B: parse the PDFs | **B**, with a verification script that checks parsed totals against the official box score | Medium | Yes (additive) |
| SUG-05 | Publish the leaderboards as two permanently separate tables | reporting | A lucky staking run can never hide a weak signal, and a strong signal is never credited for luck | `data/leaderboard_signal.csv` and `data/leaderboard_staking.csv`; gate rows 7 and 8 | A: one combined ranking. B: two separate tables | **B**. Already implemented in this desk | Done | Yes |
| SUG-06 | Keep the fail-closed demotion gate | reporting | A criterion that cannot be evaluated can never be silently passed; nothing is promoted on luck | `data/gate_decisions.csv`: all six strategies are `PAPER` | A: allow promotion with missing data. B: fail closed | **B**. The cost is that nothing is live today, which is the correct description of the evidence | Done | Yes |
| SUG-07 | Consolidate the six existing NFL desks into one family with a shared data layer | repo | Removes duplicated, drifting inputs and conflicting numbers in the same repository | The audit found four desks with their own copied inputs and different injury counts for the same official page | A: keep all desks. B: shared data layer, separate studies. C: one canonical desk | **B**: one shared official data layer (`raw_inputs.py`, `injuries_raw.py`, `depth_raw.py` promoted to a shared package), separate study pages that import it. C would delete work that other sessions still own | Medium | Partly |
| SUG-08 | Repair the data defects found in the existing desks | repo | Removes corrupted columns and stale ledgers from published pages | `nfl-desk-864d5668/data/depth_crosscheck.csv` contains character-exploded practice statuses; several desks are frozen at 2026-11-02 while this desk is current to 2026-11-14 | A: leave them. B: fix in a follow-up session | **B**, but **not in this session**: those files belong to other sessions' claims. Logged as a cross-session request instead | Low per file | Yes |

## Recommended path

1. **Now (done in this session):** publish a complete, self-contained, officially sourced desk that
   fails closed on prices, separates signal from luck, tracks replacement depth, publishes `n` with
   every correlation, and keeps a live demotion gate.
2. **Next (highest value, low effort):** SUG-03 (estimate HFA), D-04/D-02 (weekly archives and a
   growing calibration sample), D-05/D-06 (close the flagged data gaps).
3. **Then (highest value, higher effort):** SUG-01 (price feed) and SUG-04 (player tables). These two
   unlock the three strategies that are currently blocked and turn the desk from a model study into a
   betting record with measurable ROI and CLV.
4. **Separately (repo-wide, other sessions):** SUG-07 and SUG-08, coordinated through
   `COORDINATION.md` and finished in a final integration session.

## What we are deliberately not doing

* Not importing third-party price scrapes to fill the market columns.
* Not promoting any strategy to live while a required criterion is not evaluable.
* Not editing files owned by other sessions' claims.
