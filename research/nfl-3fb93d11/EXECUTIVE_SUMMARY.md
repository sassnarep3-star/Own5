# NFL Price-Snapshot & Verified-Results Desk — Executive Summary

**Session:** `3fb93d11` · **Branch:** `arena/3fb93d11-own5` · **Official data retrieved:** 2026-11-14T21:33:19Z
**Live site:** https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/
**Build script:** `nfl-desk-3fb93d11/run.py` (deterministic; 51 unit tests; row-level source verifier `verify.py`)
**Scope:** `nfl-desk-3fb93d11/**` and `research/nfl-3fb93d11/**` only. No other desk's files were touched.

---

## 1. The short version

This session was asked for eight things. All eight are built, published and testable:

| # | Requirement | Result |
|---|---|---|
| 1 | Price-snapshot store with opening **and** closing numbers | 390 rows (78 markets × 5 snapshot types); **156 populated, 234 empty and flagged** |
| 2 | Verified results feed | 137 official 2026 finals; rebuilt standings reproduce nfl.com **32/32, 0 mismatches** |
| 3 | Originate side → total → moneyline | Every game records steps 1, 2, 3 in order; the moneyline is **derived** from the other two |
| 4 | Model / market / difference as separate columns | Three columns for all 78 markets; the market column is labelled AGGREGATOR |
| 5 | Separate signal from staking in the leaderboard | Two ranks per family from disjoint inputs; ranking happens inside a board, never across universes |
| 6 | Track the **depth** of a replacement | 705 slots over 31 clubs; 7 currently filled by a backup, each naming which string and whether the loss compounds |
| 7 | Correlations from official numbers only, with n | 9 pairs, each with r, p, 95% CI, n and an n-definition; 7 previously published values **withheld** |
| 8 | Demotion gate to paper | 6 triggers, evaluated against every family; all armed, none fired |

**The finding that governs everything else:** nfl.com publishes no betting prices. There is no
official opening price and no official closing price for any market. That single fact is why the
price store's opening and closing rows are empty, why gate G2 (price provenance) fails for every
strategy family, and why the certified count on the leaderboard is **0**. The store now records the
gap explicitly instead of leaving it implicit.

**Nothing here is certified. No family has demonstrated an edge.** On the larger research sample the
best family hits 51.5% against a 52.38% break-even.

---

## 2. Verified inputs

| Input | Source | Result |
|---|---|---|
| 2026 schedule, weeks 1–11 | https://www.nfl.com/schedules/2026/by-week/ | 137 finals + 26 scheduled (W10 remainder, W11) |
| 2026 league standings | https://www.nfl.com/standings/league/2026/REG | 32 clubs; **32/32 reproduce exactly** from the game feed |
| Week 10 injury report | https://www.nfl.com/injuries/league/2026/reg10 | 326 player rows; 301 have no game status yet this week |
| Week 11 injury report | https://www.nfl.com/injuries/league/2026/reg11 | **does not exist — the URL serves Week 10** (F-04) |
| Club depth charts | club pages via https://www.nfl.com/teams/ | 31 clubs; Houston publishes only a raster chart (F-05) |
| Pinned results mirror, 1999–2025 | nflverse `games.csv.gz` (AGGREGATOR) | 6,967 rows; agrees with the official feed on 136/137 |

Two rules govern every number on the site:

* **OFFICIAL** inputs (nfl.com, club pages) are the only ones a fact may be asserted from.
* **AGGREGATOR** inputs (the mirror) are used for cross-checks and as an untimestamped market
  reference only. They are never called an opening or a closing price, and never used to assert a fact.
* **DERIVED** values are computed here by a committed, re-runnable script from OFFICIAL inputs.

---

## 3. What the results feed proves

137 games were transcribed week by week from the official schedule pages. Rebuilding every club's
win–loss–tie, points for and points against from those games reproduces the official standings page
with **zero mismatches across all 32 clubs**. Three examples:

| Club | Official | From the feed |
|---|---|---|
| Buffalo Bills | 7-1, 256 PF / 187 PA | 7-1, 256 / 187 |
| New York Giants | 5-3-1 | 5-3-1 |
| Los Angeles Chargers | 0-8 | 0-8 |

The pinned mirror agrees on 136 of the 137 and disagrees on none. It has simply not yet published a
final for one game (Week 10 WAS@NYG, final on nfl.com) — a lag, not a contradiction.

The feed also self-checks: 137 rows × (home margin = home − away, total = home + away) all reconcile,
and 137 weekday labels recomputed from the ISO dates match the weekday printed by nfl.com.

---

## 4. What the model can and cannot do

Out of sample on 2026 weeks 5–10 (73 predictions, σ = 12.92 points):

| Measure | Value |
|---|---|
| Margin forecast vs actual margin | r = **0.3187**, p = 0.0060, n = 73 |
| Straight-up winner | 49 of 72 = **68.1%** |
| Margin MAE | 10.02 pts vs 10.81 for "predict a tie" |
| Totals MAE | 11.00 pts vs **11.02** for "predict the league average" |
| Brier / log loss | 0.2302 / 0.6523 |

The side model is real but modest — about 0.79 points a game better than the naive baseline. The
totals model is not yet worth anything: it beats predicting the league average every time by 0.02
points. Because the moneyline is derived from the side *and* the total, that weakness flows into the
moneyline. Fixing the totals model is suggestion **S-02** and question **Q-02**.

Home-field advantage comes out at **+0.21 points**, which is not separable from zero on 137 games
(F-11). It is still applied, because shrinking it to zero on this sample would be fitting noise.

---

## 5. The nine strategies

Nine families were pre-registered before any result was inspected, then graded walk-forward
(parameters always fitted on periods strictly earlier than the period being graded). Two universes:

* **CERTIFICATION** — the official results feed. Small (4–51 graded bets per family) but the only
  board that can ever certify anything.
* **RESEARCH** — the pinned mirror, 1999–2025. Thousands of bets; useful for asking whether a signal
  exists at all. It cannot certify or reward anything.

Every bet is graded at a flat −110 (52.38% break-even), because the mirror carries no per-leg prices
for 2026 (F-07). Pushes are excluded from the hit rate and reported separately.

**Certification board — official results, 8 families with graded bets:**

| Family | n | Hit rate | ROI | Signal rank | Staking rank |
|---|---|---|---|---|---|
| Rest edge ≥ 3 days | 24 | 62.5% | +19.3% | **1** | 3 |
| Model total edge ≥ 3 pts | 33 | 42.4% | −19.0% | 2 | 5 |
| Model side edge ≥ 3 pts | 29 | 44.8% | −14.4% | 3 | 4 |
| Same-game side+total parlay | 8 | 37.5% (BE 27.4%) | +36.7% | 4 | 2 |
| **Fade large home favourite ≥ 10** | **4** | **75.0%** | **+43.2%** | **5** | **1** |
| Divisional home underdog | 8 | 37.5% | −28.4% | 6 | 6 |
| Moneyline value ≥ 5 pp | 51 | 21.6% | −58.8% | 7 | 8 |
| Home underdog ≥ 2.5 | 25 | 24.0% | −54.2% | 8 | 7 |
| Same-game prop combination | 0 | — | — | — | — |

**"Fade large home favourite ≥ 10" is the reason the leaderboard was split.** It is first on realised
money — 75% on 4 bets, +43.2% — and **fifth of eight** on signal. Under a single-score board that run
would have been rewarded. Here the staking axis cannot certify or reward anything, and the row is
labelled *staking-only* in plain English.

**The moneyline family is significantly worse than break-even** (21.6% on 51 bets, Holm p =
5.8×10⁻⁵), not merely inconclusive. That is a real finding about that rule, and the signal score
penalises the direction rather than rewarding the strength of the evidence.

**Research board (mirror):** the largest samples land at 51.2–51.5% against a 52.38% break-even.
The same-game parlay needs 27.44% and delivered **26.32% over 1,953 bets** — independent leg pricing
is not free money, it is an assumption that costs about 4% of turnover here. Prop combinations (S9)
produced **no graded bets at all**, because no prop lines exist from any source in this repo (F-08).

**Certified families: 0.** Every family fails G2 (price provenance). Certification-board families
also fail G1 (300-bet minimum). Parlay families fail G7 (leg correlation not measurable). All rows
stay `PAPER`.

---

## 6. The demotion gate

A strategy promoted to live is returned to paper the moment any of six triggers fires, automatically,
without waiting for a review:

| Trigger | Condition |
|---|---|
| D1a | Rolling 200-bet closing-line value ≤ 0 |
| D1b | Drawdown from peak ≥ 20% of the reference bankroll |
| D1c | Last 100 graded bets fail to beat break-even at p < 0.10 one-sided |
| D1d | Any parameter or rule changed from the pre-registered commit |
| D1e | Any graded bet without a verified opening or closing snapshot |
| D1f | The official results feed falls more than a week behind |

**Current state: armed.** Nothing has ever been promoted, so no trigger has fired. The triggers are
evaluated against every family anyway, so the day a promotion happens the gate is already wired.

---

## 7. Injuries and replacement depth

705 published position slots across 31 clubs, offence and defence recorded separately (a defence on
its third cornerback is never pooled with an offence on its backup left tackle). For every slot where
a backup is expected to start, the tracker records:

* which string steps in (2nd / 3rd / 4th);
* whether that replacement is himself on the official injury report, so the loss compounds;
* whether the loss therefore cascades to a third name, and whether a third name is even published;
* how many rungs down the chart the club has been forced to go.

**7 slots are currently being filled by a backup — all second-string, none compounding.** 14 players
the league lists as Out were cross-checked against their club's own chart; **0 irregularities** this
build.

Two honest limits: game status is empty for 301 of the 326 injury rows, because statuses fill in
later in the week, so the tracker under-counts Out players early (F-12); and the Week 11 injury
report does not exist yet, so every Week 11 market here is originated with no injury adjustment at
all (F-04).

---

## 8. Correlations

9 pairs are published, every one computed from numbers nfl.com publishes (the 32-row standings page,
or the 137 official game results). Each row states r, p, a 95% interval, n, and what n counts.

7 values previously published elsewhere in this repository were **moved to a withheld register**.
Three of them — including the widely quoted QB-passing-yards vs WR1-receiving-yards figure of 0.76
(n = 3,852) — were computed from the third-party mirror and are not admissible under the
official-only rule. Four were computed from official inputs but are superseded by this desk's own
recomputation. They are listed with their previous value, their previous n, the session that
published them, and the basis that disqualifies or supersedes them.

**The correlation that matters most cannot be computed at all.** Two player-prop legs in the same
game — what actually prices a same-game parlay — has no official source at that granularity. Gate
G7 therefore fails for every parlay and prop family, and the desk refuses to price a leg pair it
cannot measure (F-08).

---

## 9. Repo audit

150 checks re-ran earlier desks' headline claims against the official pages fetched for this build.
**150 matched, 0 disagreed, 0 could not be run.** The audit covers the cross-desk hub's 2026
standings (32 clubs × record and points), `nfl-desk-864d5668`'s standings reconciliation, its
completed-game count (137), the home-field sample size (130 non-neutral / 7 neutral), the Week 8
desk's row count, the injury row counts (276 on 2026-11-12 vs 326 on 2026-11-13 — the report filling
in, not a contradiction), and the depth-chart counts (31 clubs, 705 slots).

One item is reported rather than reconciled: session 864d5668's COORDINATION entry says 707 depth
slots while its committed table holds 705. Only the file can be checked, so both numbers are shown.

*A full line-by-line read of all 1,000-plus files in this repository is more than one session can
honestly claim to have done.* This audit re-checks headline claims; it is not a complete audit of the
repo.

---

## 10. What is missing

14 items are flagged. **4 are blocking:**

| Flag | What is missing |
|---|---|
| F-01 | No official NFL price publisher exists — the store's open/close slots cannot be filled |
| F-04 | The Week 11 injury report does not exist; the URL serves Week 10 |
| F-08 | No prop lines exist from any source, so prop combinations cannot be priced or graded |
| F-10 | The certification universe (4–51 bets per family) is far short of gate G1's 300 |

The other 10 are review items that do not block anything: the mirror lagging by one game (F-02),
MODEL_CLOSE not yet observed (F-03), Houston's depth chart published only as an image (F-05), the
flat −110 grading convention (F-07), the totals model's lack of edge (F-09), home-field advantage not
separable from zero (F-11), 301 of 326 injury rows carrying no game status (F-12), inadmissible
previously published correlations (F-13), and the untimestamped aggregator line (F-14).

14 questions are open; **5 are blocking**: which price is the benchmark for beating the market
(Q-01); whether the aggregator line is an opening, a closing, or neither (Q-02); what bankroll and
staking rule apply, without which D1b cannot fire (Q-03); whether rewards are cash, points or nothing
(Q-04); and which jurisdictions and who is eligible (Q-05).

---

## 11. Suggestions — awaiting your decision

12 suggestions, each with two or three costed options, a recommended path, the evidence behind it and
the test that would change the recommendation. **All 12 are AWAITING DECISION. Nothing on that page
has been implemented.**

The seven rated High impact:

* **S-01 — solve the price gap.** Either license a price feed (Option A), run the desk's own
  timestamped logger and treat logged quotes as the authoritative close (Option B, recommended), or
  publish a no-prices-ever statement and delete the open/close slots (Option C). Everything else is
  downstream of this one.
* **S-02 — rebuild the totals model.** It is worth about 0.02 points over a constant right now, and
  the moneyline inherits that weakness.
* **S-03 — grade parlays against an empirical joint, never against independent legs.** Independent
  pricing costs about 4% of turnover on 1,953 mirror bets.
* **S-05 — budget how many new families a season, and publish the count.** Nine families tested
  against one season is a multiplicity problem, and it is why the Deflated Sharpe ratio is on every row.
* **S-06 — extend the official results feed backwards.** One season cannot certify anything; gate G1
  needs 300 graded bets.
* **S-07 — publish a market-efficiency scorecard next to every signal**, so a reader can see how much
  of a gap the market already prices.
* **S-08 — make the demotion gate automatic rather than advisory.** Today it is evaluated but nothing
  is live, so it has never actually fired.

---

## 12. Reading the site

| Page | What is on it |
|---|---|
| [Overview](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/) | Headline counts and where to go next |
| [Executive summary](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/executive-summary.html) | The eight requirements and what each produced |
| [Verified results feed](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/results.html) | 137 finals, the 32-club reconciliation, the mirror cross-check |
| [Price snapshot store](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/price-store.html) | 390 rows; every empty cell named |
| [Originated lines](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/lines.html) | 78 markets, side → total → moneyline |
| [Strategies](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/strategies.html) | Nine families, two universes |
| [Validation & demotion](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/gates.html) | Nine gates plus the six demotion triggers |
| [Leaderboard](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/leaderboard.html) | Signal and staking ranked separately |
| [Correlations](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/correlations.html) | 9 admissible pairs, 7 withheld |
| [Injuries & depth](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/depth.html) | 705 slots, offence and defence split |
| [Suggestions](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/suggestions.html) | 12 proposals, none implemented |
| [Questions](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/questions.html) | 14 open, 4 blocking |
| [Repo audit](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/repo-audit.html) | 150 checks against earlier desks |
| [Flagged for review](https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/flagged.html) | 14 flags, 7 blocking |

Every table row on every page links to the source that produced it. A value that cannot be sourced is
rendered **blank with an UNVERIFIED badge** that links to the flagged register — never inferred,
never filled in.

---

*Research only. Nothing here is betting advice, and no bet has been placed. Not affiliated with the NFL.*
