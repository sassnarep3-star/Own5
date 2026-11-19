# Executive summary — Own5 NFL Signal Board

**Session** `1fab8a48` · **Branch** `arena/1fab8a48-own5` · **Built** 2026-11-19 UTC
**Live:** https://sassnarep3-star.github.io/Own5/nfl-signal-board/
**Evidence:** every number below is reproduced by `data/nfl-signal-board/build_data.py` and re-checked by
`nfl-signal-board/verify.py` (1,773 checks, 0 failures) on inputs that are hashed in
`data/nfl-signal-board/derive_summary.json`.

---

## The one thing to read

**Our model does not beat the market, and the site says so on the landing page.**

| What was asked | What the evidence says | Where it is published |
|---|---|---|
| Originate our own lines | 13 Week 11 fixtures × 3 markets = **78 rows**, side → total → moneyline, with the fair line, the operator's line and the difference in three separate columns | `origination.html` |
| Remove the luck | Side **Brier skill −0.0354** (95% week-cluster CI −0.0508 to −0.0202) vs *a coin flip at the closing line*, n=2,951; moneyline **−0.0579** vs the de-vigged close, n=3,030 | `model.html` |
| Build strategies that are selectively skill-based | **0 certified.** All 8 registered strategies start at 0 settled bets. No backtest number appears on the leaderboard | `leaderboard.html` |
| Track injuries and depth deficiencies | 253 official report rows across 24 clubs captured and counted. **No replacement is named and no depth order is published**, because no official source available here supplies one | `availability.html` |
| Tell me what is missing | **18 questions**, each with a discovery route, plus **15 flags** and a **10-item list of information we do not have** | `questions.html`, `flagged.html` |

## Why the model loses, stated precisely

1. **It is over-confident by an order of magnitude.** A logistic calibration fitted on the training window
   (2015–2024, n=2,550) has a **slope of 0.110**. A raw model probability of 0.92 corresponds to roughly 0.55
   on the evidence. Every headline "edge" on the origination page is therefore an artefact, and the site prints
   the calibrated probability beside the raw one and blocks staking.
2. **The holdout is worse than the training window** (−0.0617 vs −0.0313 on the side), which is what a model
   fitted to noise looks like out of sample.
3. **The controls behave exactly as they must**, which is the check that the benchmark is not rigged: a constant
   0.5 predictor scores **0.0000** against the coin-flip benchmark, and a train-estimated base-rate predictor
   scores **+0.0009** (CI −0.0009 to +0.0027).

## Two errors this build found in itself, and published

These are recorded rather than quietly replaced, because a number that changed without a note is indistinguishable
from a hallucination.

- **A sign error worth +0.038 skill.** `closing_spread_home` in the pinned corpus is home-favoured-**positive**
  (mean absolute error 10.25 points read one way, 14.62 the other). The first pass read it the other way and
  produced a *positive* skill with an interval excluding zero. Fixed; the skill is negative.
- **A wrong benchmark.** The second pass scored the side against the de-vigged *moneyline* probability. The
  constant-0.5 control beat that benchmark by 0.139 — impossible if it were a cover probability. The control
  caught it. The benchmark is now a coin flip at the closing line, and the control returns exactly 0.0000.

## What is genuinely verified today

| Item | Result | Official source |
|---|---|---|
| 2026 standings reconciliation | **32/32 clubs** exact on W-L-T, PF and PA | [nfl.com standings](https://www.nfl.com/standings/league/2026/REG) |
| Week 10 finals | 14 games, all matching the reconciled corpus | [Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) |
| Week 11 slate | 13 fixtures, 6 byes, kickoffs, networks, venues | [Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11) |
| Week 11 injury report | 253 rows, 24 clubs, **16** game-status cells (9 Out, 7 Questionable) | [injury report](https://www.nfl.com/injuries/league/2026/reg11) |
| The 136-row log named in the brief | **117 agree, 16 blank, 3 absent, 0 disagree** on a posted score | [games_2026.json](https://github.com/sassnarep3-star/Own5/blob/main/data/games_2026.json) |
| Operator prices | 78 prices across 13 fixtures, one operator, clocked at 11:10 UTC | [DraftKings NFL](https://sportsbook.draftkings.com/leagues/football/nfl) |
| Correlations | 4 coefficients, **n=32 each**, from the standings page only | [correlations page](https://sassnarep3-star.github.io/Own5/nfl-signal-board/correlations.html) |

## What is deliberately blank

Every blank below has a gate and a route on `questions.html`; none is filled by inference.

- **Closing prices** — readable only at kickoff. Stored as open snapshots; the close column is empty and says why.
- **Replacement names and depth order** — need an official inactive list, a game book or a structured depth source.
- **Starter claims** — need a game book. None was read.
- **What "Questionable" predicts** — needs designations joined to official inactive lists over seasons.
- **Parlay-leg correlations and joint probabilities** — need play-by-play.
- **A second and third operator price** — one book is not a consensus.
- **The dated 2026 schedule announcement** — not re-read this session, so the date is flagged (SBF-06) rather than recalled.

## The decision the owner has to make

The binding constraint is **not data volume** — it is that the model's probabilities are not calibrated enough to
carry a stake. Two inputs would change what is possible, in this order:

1. **An official inactive list capture** (≈90 minutes before kickoff). It converts "a player is out" into
   "this named backup is playing" — the whole depth feature the brief asks for. Suggested first step: SUG04.
2. **The game book as the starter record.** Published, dated, and it removes the depth-chart parsing problem
   entirely for actual starters. Suggested second step: SUG05.

Until then the honest position is: originate, publish, publish the errors in the market column, and do not bet.

---

*Policy P-01: the public site carries derived aggregates, our own model outputs and operator-attributed prices.
Row-level official data stays private. No bets are placed. No strategy is certified. This is research, not betting advice.*
