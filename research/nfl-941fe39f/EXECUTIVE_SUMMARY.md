# Executive summary — NFL Season Desk (session `941fe39f`)

**Live site:** https://sassnarep3-star.github.io/Own5/nfl-season-941fe39f/
**Branch:** `arena/941fe39f-own5`
**Data as of:** 2026-11-17
**Rebuild:** `python3 tools/season_desk_941fe39f/build.py && python3 tools/season_desk_941fe39f/site.py` (25 s, no network)

---

## The question, and the answer

**Can a model built here beat the NFL closing line?**

On this evidence: **no.** Not yet, and the desk can say by how much.

| Test | Result | Reading |
|---|---|---|
| Residual alpha, holdout 2020–25 | **+0.0019**, 95% CI −0.047 to +0.051, n=1,615 | interval straddles zero — no demonstrated information |
| Residual alpha, full 1999–25 | +0.0245, CI +0.0009 to +0.0480, n=6,895 | small, and not present out of sample |
| Mean absolute error, side | ours **10.71** vs market **10.27** | the market is better |
| Mean absolute error, total | ours **10.93** vs market **10.63** | the market is better |
| Strategies certified | **0 of 14** | by rule, so the leaderboard holds nothing |
| Backtest rows on the leaderboard | **0** | the brief's prohibition, enforced in code |

The full-sample result is the interesting one for honesty: `r = +0.0245` with an
interval that excludes zero looks like a finding until it meets the holdout and
becomes `+0.0019` with an interval that does not. That is what a small edge
leaking out of a big sample looks like. The desk publishes both numbers side by
side and ranks nothing on either.

---

## What was built

| Layer | What exists | Where |
|---|---|---|
| Corpus | 7,239 games, 7,116 graded, 1999–2026, one pin `e045566e…fae2`, SHA-256 `9a6a7368…462c` re-proved on every build | `data/corpus/` |
| Price store | Opening and closing per market, **two series kept separate** because they disagree on 958 of 2,969 joinable games | `data/derived/price_snapshots.csv` |
| Origination | 7,058 markets, side → total → moneyline, fair line, market line and difference as separate columns, each row carrying its own fit cutoff | `data/derived/origination.csv` |
| Model | Ridge ratings, 365-day half-life, probit sigma = 11.52, `MIN_GAMES_TO_FIT=60`, n_fit 7,116 | `tools/season_desk_941fe39f/model.py` |
| Strategies | 14 pre-registered with frozen rule text, 9 gates, two-sided falsifiers, disjoint windows | `data/derived/strategies.csv`, `data/strategy/prereg.json` |
| Availability | 113 depth slots from 5 clubs, 250 player rows, 1 shared rank-1 slot stored as a group, 0 empty | `data/derived/depth_slots.csv` |
| Snapshots | 8 captures, one ledger row per read, SHA-256 per file, point-in-time replay | `data/derived/snapshot_ledger.csv` |
| Registers | 80 requirements (50 met / 21 partial / 9 blocked), 18 questions, 16 suggestions, 16 flags, 16 audit rows | `data/derived/*.csv` |
| Site | 22 pages, 465 table rows, **465 with a source link or an explicit UNVERIFIED badge** | `nfl-season-941fe39f/` |

---

## Four findings worth acting on

**1. The market is the benchmark, and it wins.** Not one of the nine
non-control families shows positive Brier skill against the de-vigged close on
the holdout. The best of them is `S10` at −0.0921. Judging a strategy against a
coin flip instead would have made several of these look strong.

**2. The two price series are not interchangeable.** `games.spread_line_home` and
`closing.csv` agree exactly on 2,011 of 2,969 joinable games. On 17 they sit on
opposite sides of zero with at least a half-point gap, so they disagree about
which side is favoured. Any ROI computed on one and checked against the other
would change on 32% of games. Every table on the site names its series.

**3. Availability is the unexplored edge, and it is blocked.** The injury report
and depth charts are readable at club level, but the inactives list returns 404
and Houston's depth chart is a single image with no text. Without inactives a
replacement can be inferred but never confirmed. That is 3 of the 9 blocked
requirements.

**4. The luck panel is large enough to explain most of a season.** Denver sits at
7-2 against an expected 0.537; Tampa Bay at 3-6 against 0.574. At the measured
exponent of 2.37, a 9-game record carries roughly ±2 wins of luck. That is why
the leaderboard ranks on Brier skill and not on record.

---

## What is blocked, and what would unblock it

| Blocked | Why | What clears it |
|---|---|---|
| CLV / G3 | no opening price exists anywhere in the corpus | one book's opening *and* closing price per market, same clock time |
| Inactives | `nfl.com/inactives/.../reg10` returns 404 | a dated inactives feed, or a game book |
| Houston depth | chart is an image; `static.clubs.nfl.com` is TLS-blocked here | a text chart, or OCR with a human check against the image |
| Certified strategy | 0 clear the gates | one family with positive Brier skill and a positive alpha interval on 2020–25 |
| 32/32 clubs | 5 clubs re-read this session | 27 club depth pages, or one league-wide depth feed |

None of these block publication. All of them block a stronger claim than the
site makes, which is the point of publishing them next to the numbers.

---

## Where to look first

- **Landing** — decision-readiness table: one row per requirement, the gate that blocks it, the number that clears it.
- **Flagged for review** — 16 flags, each with a source link; 5 blocking, 9 for review, 2 informational.
- **Strategies and gates** — the pre-registration, the registration commit, and the hash of every rule text.
- **Removal of luck** — expected vs actual for all 32 clubs, with the power calculation for how many bets a real edge would need.
- **Questions** — 18 questions, each with *what we have*, *what is missing*, and *the route to it*.

Nothing here is a betting recommendation. No bets were placed. Zero strategies are certified.
