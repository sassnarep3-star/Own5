# NFL line origination — executive summary

**Session** `39086ec8` · **Branch** `arena/39086ec8-own5` · **Data captured** 2026-11-14 (UTC)
**Desk**: `nfl-engine-39086ec8/` · **Site**: 14 pages, self-contained · **Verification**: 1,215 checks, 0 failures

---

## The one-paragraph version

Eight engine requirements were each built and each verified against something outside the code
that produced them. Two of them changed what the repository believes. First, **official market
prices are readable**: a prior desk concluded that no official price exists and left every market
column blank, but the operator's public event pages served a full Game Lines block for 13 of the
14 Week 10 games. The repository now has its first price-snapshot store — 78 rows, hash-addressed,
one capture point each — and the store's first honest finding is that it cannot compute a
closing-line value, because no opening number was ever captured. Second, **the strongest published
correlation in the repo is a scheduling artefact**: rest differential vs home margin is published
at r = −0.4257; remove the 16 games where either side came off a bye and it is +0.0387 (p = 0.72).
The results layer is the part that is fully settled: 137 finals, 192 reconciliation checks against
official standings, zero mismatches. The model is *built* and *not calibrated* — a 1.76-point mean
absolute disagreement on the side, with a systematic −0.844-point bias, which is an information
gap rather than an edge.

---

## Requirement matrix

| # | Requirement | Built | Evidence | Honest limit |
|---|---|---|---|---|
| 1 | Price store, open **and** close, every market | ✅ | 78 snapshots, 13 games, 6 markets, sha256 on every raw block | `event=open` is **empty**; no opening price was captured and none is reconstructed |
| 2 | Verified results feed for backtests and ROI | ✅ | 137 finals, 192 checks, **0** mismatches, 6,291 points both ways | Settlement is final score only; no in-play or grading feed |
| 3 | Originate side → total → moneyline | ✅ | Staged in code; each stage may not read a later stage or any market price | Stage 1 uses an in-sample rating, so it cannot be a live edge |
| 4 | Fair / market / difference as separate columns | ✅ | 14 rows × 3 markets; missing market ⇒ blank, difference ⇒ `UNPRICED` | 13 of 14 games priced; WAS@NYG unpriced (kicked off before capture) |
| 5 | Signal separate from staking on the leaderboard | ✅ | Two independent scoreboards; in-sample entry force-flagged | No entry has a verified CLV, so no staking number is publishable as skill |
| 6 | Depth **of** replacement, not the fact of it | ✅ | 78 slots: rungs down, cascade count, exhaustion flag | Only 4 of 32 club charts are published; the rest are blank, not assumed |
| 7 | Correlations from official numbers, with **n** | ✅ | 4 official values + n, CI, p; 13 prior claims reproduced | Player-market correlations remain third-party and are tagged as such |
| 8 | Demotion gate back to paper | ✅ | 5 executable rules, 6 scenarios, each rule shown firing | D2/D4 need price history the repo does not have |

---

## What the data actually says

**Results.** 137 games, 32 clubs, 6,291 total points, 0 mismatches against
[nfl.com standings](https://www.nfl.com/standings/). This is the one layer with no caveat.

**Model.** Ridge (λ = 5.0) on 137 games, fitted HFA 0.179. Side: mean bias −0.844, mean |error|
1.764, max 3.212. Total: bias +1.185, mean |error| 4.001, max 7.833. The side error is small
enough to be interesting and the total error is large enough to be a warning: the model is
missing information, not making a mistake.

**Leaderboard.** Four entries scored on two separate boards.

| Entry | n | Hit rate | Edge | z | Signal verdict | Flat units | Staking growth |
|---|---|---|---|---|---|---|---|
| R1 home ML | 136 | 0.4926 | −0.0311 | −0.73 | INCONCLUSIVE | −8.09 | 0.9165 |
| R2 away ML | 136 | 0.5073 | −0.0164 | −0.38 | INCONCLUSIVE | −4.27 | 0.9522 |
| R3 better-margin ML | 136 | 0.7500 | +0.2262 | 5.28 | **NOT_ELIGIBLE_IN_SAMPLE** | +58.73 | 1.7884 |
| R4 under 45.5 | 137 | 0.5109 | −0.0128 | −0.30 | INCONCLUSIVE | −3.36 | 0.9609 |

R3 is the demonstration the requirement exists for: a 5.3σ hit rate built from the same games
the rating was fitted on, refused a pass rather than rewarded.

**Masking.** A 20-bet sequence with 5 wins (25%, a clear signal failure) still grows a 1%-stake
bankroll by +31.8% with 2.67% max drawdown. Staking and signal are reported apart for exactly
this reason.

**Demotion.** Six scenarios; S1 holds live sampling, S2–S6 each trip a different rule
(D1 insufficient sample → keep sampling; D2 CLV reversal; D3 drawdown; D4 no price; D5 data
integrity). Every rule fires on evidence the desk can actually read.

**Correlations.** Published values (CORR01–06: 0.6136, −0.5796, 0.8391, 0.0705, 0.8313, −0.0117)
reproduce from the prior desks' own declared inputs. The one substantive correction is C-03:
−0.4257 → **+0.0387** with byes removed.

---

## Repo audit

37 checks: **26 MATCH**, **7 IRREGULAR**, **3 REVIEW**, **1 NOT CHECKED**. Full detail on the
[audit page](../../nfl-engine-39086ec8/audit.html) and in `data/repo_audit.csv`.

Irregularities, in order of consequence:

1. **B11** — prior desks asserted no official price exists. 13 games exposed readable prices.
2. **B6** — a published correlation is a bye-week artefact.
3. **D2** — the inherited depth metric is 0 for 698 of 705 slots; it cannot rank anything.
4. **B10** — the Week 10 origination omitted WAS@NYG entirely rather than marking it unpriced.
5. **C5** — prior quotes are `DATE_ONLY`; CAR@NO moved −2.5 → −1.5 between desks.
6. **B2** — club-code joins drop LAR/ARI unless canonicalised.
7. **B7** — a cited source does not contain the quantity attributed to it.

Review items: a hard-coded "00/08" stat in the root page, and two prior correlation values
(C2, C3) that do not reproduce from the inputs the repo declares. C6 was **withdrawn** by C7
(the sign was correct) and is recorded as NOT CHECKED rather than silently deleted.

---

## Deliverables

| Artifact | Path |
|---|---|
| Site (14 pages) | `nfl-engine-39086ec8/*.html` |
| Price store | `nfl-engine-39086ec8/data/price_snapshots.csv` + `archive/` |
| Verification harness | `nfl-engine-39086ec8/verify.py` |
| Tests (68) | `nfl-engine-39086ec8/tests/test_engine.py` |
| Suggestions (12) / Questions (13) | `data/suggestions.csv`, `data/questions.csv` |
| Audit | `data/repo_audit.csv` |
| This document | `research/nfl-39086ec8/` |

## What is *not* claimed

No closing-line value. No prop prices. No ROI figure presented as skill. No opening line. No
depth chart for 28 clubs. No correlation implying prediction. Every one of these is published as
blank or `UNPRICED` and carried on the Flagged for Review page rather than filled in.
