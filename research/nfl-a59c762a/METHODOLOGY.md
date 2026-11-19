# Methodology — NFL Decision Console (session a59c762a)

Everything below is reproducible from the repository with the standard library only.
No third-party package, no credentials, no sportsbook API.

---

## 1. Sources and the read clock

| Source | URL | Read (UTC) |
|---|---|---|
| 2026 league standings | `https://www.nfl.com/standings/league/2026/REG` | 2026-11-19T06:38Z |
| Official Week 11 injury report | `https://www.nfl.com/injuries/league/2026/reg11` | 2026-11-19T06:45Z |
| Week 11 schedule | `https://www.nfl.com/schedules/2026/by-week/week-11` | 2026-11-19T06:41Z |
| Week 10 schedule and finals | `https://www.nfl.com/schedules/2026/by-week/week-10` | 2026-11-19T06:44Z |
| Colts at Texans game centre | `https://www.nfl.com/games/colts-at-texans-2026-reg-11` | 2026-11-19T06:50Z |
| 2026 NFL Schedule Release | `https://www.nfl.com/nfl-schedule-release/` | 2026-11-19T06:49Z |
| Official Game Book, WAS at NYG | `https://static.www.nfl.com/image/upload/v1794570519/gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf` | 2026-11-19T06:47Z |
| NFL Game Books index | `https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books` | 2026-11-19T06:47Z |
| NFL Next Gen Stats glossary | `https://nextgenstats.nfl.com/glossary` | 2026-11-19T06:52Z |

**Limitation L-01.** The sandbox fetches the *processed text* of a page, not the server
bytes. The stored extracts are hashed, so the hash proves the text was not altered after
capture; it does **not** prove the bytes on the server are identical. Every capture row
records the method, the read clock and the chunk count so a reader can judge it.

**Limitation L-02.** `https://www.nfl.com` is not reachable over TLS from this sandbox
with `curl`; the reads were made through the sandbox document fetcher. The
`nfl.com` pages are the source of record regardless of transport.

---

## 2. The corpus

- Weeks 1–9 of the 2026 regular season are carried forward from
  `nfl-desk-35a1feb2/data/results_feed_2026.csv`, which already carries the official
  `nfl.com` source URL on every row. Those rows are marked
  `evidence_class = REPOSITORY_SOURCE_LINKED` and keep their original verification note.
- All **14 Week-10 finals were read first-hand** on 2026-11-19 and are marked
  `evidence_class = READ_FIRST_HAND_2026-11-19`.
- The corpus is **150 games**. That number is not asserted, it is reconciled: the
  official standings sum to 149 wins and 2 ties, so 149 + 2/2 = 150 games, and the
  per-club sums of wins, losses, ties, points for and points against agree for all
  **32 clubs with 0 mismatches**. The check is `V9` in the verifier and
  `test_results_feed_reconciles_with_the_official_standings` in the tests.
- The one row that the carried-forward feed left blank (Chargers at Ravens, Week 10) is
  filled from the first-hand read and the defect is logged as **F-A59-01** with a
  cross-session request to the owning session. The owning session's file is not edited.

## 3. The model

`m1-2026-11-19-opponent-adjusted-ls`, fitted on weeks 1–8 only.

```
margin_home = HFA * (1 if the game is not neutral else 0) + rating_home - rating_away + e
```

- The rating vector is constrained to sum to zero by eliminating the last club's rating
  in the design matrix, not by a penalty.
- A ridge penalty of 1.0 is applied to the ratings only, never to the home-field term.
- **The home field is fitted, not assumed.** This session's fit gives **1.488 points**
  with a residual standard deviation of **14.079 points**.
- Normal equations are solved by Gaussian elimination with partial pivoting, in pure
  Python (`build_data.fit_ratings`).
- The eight international games through Week 10 carry `neutral_site` set, so the
  home-field term is switched off for them. The ninth, Vikings at 49ers at
  **Estadio Banorte**, is a Week-11 neutral game, confirmed from the Schedule Release
  page.
- Probability: `P(home win) = Φ(margin / sigma)`. Fair American odds are printed without
  vig on both sides.

**Totals.** Two estimators, published together with their gap, neither retired:

- **A** — the league mean total points per game in the training window (46.107).
- **B** — shrunk team offense plus shrunk opponent defense:
  `pred_home = mean + 0.5 * (adj_off_home - adj_def_away)`, where each adjustment is
  shrunk toward the league mean with weight `gp / (gp + 11)`.

## 4. Splits

| Window | Weeks | Games | Use |
|---|---|---|---|
| Train | 1–8 | 121 | The only window the model is fitted on |
| Validation | 9 | 15 | Model selection |
| Final holdout | 10 | 14 | Touched once, after the rule was frozen |

The split is chronological, never random.

## 5. Scoring

- **Brier score** for binary home-win forecasts.
- **Brier skill score** against a climatology baseline: always predict the training
  window's home-win rate (0.5124).
- **95 % interval** by the Fisher z transform; **two-sided p-value** by the normal
  approximation on z.
- **Multiplicity**: 3 trials are declared, so the Bonferroni-adjusted significance level
  is `0.05 / 3 = 0.01667`.
- **Controls** on every run: a random pick (analytic Brier 0.25 for a fair coin) and a
  favourites-only pick (the higher-rated team).

## 6. What is deliberately not modelled

- **No injury term.** The model has no availability feature, so the injury ablation is
  a no-op rather than a measurement. That is recorded (R-17, R-18) rather than faked.
- **No depth term.** The depth-order source is verified for 31 of 32 clubs.
- **No market term.** No price source is admitted, so no residual is computed.

## 7. Availability and the delta

The Week-11 league report is stored as 253 rows with the practice status and the game
status exactly as printed. The delta is computed against the repository's earlier read
of the same report (2026-11-18T03:46Z, ten rows from two game pages) and carries, on
every row: the previous value, the current value, the change type, and **both read
clocks**. The level is never published in place of the delta.

The three blank Lions game-status cells (Kerby Joseph, Cade Mays, D.J. Reed) are the
publisher's timing, not a parsing failure: the Lions play on Sunday 22 November and the
report was read on Thursday morning. Flagged as **F-A59-08, resolved**.

## 8. Determinism

`build_registers.py` (authored registers) → `build_data.py` (computed data) →
`build_desk.py` (pages). No clock, no network, no git inside any of them. The verifier
re-runs all three and fails if any committed byte changes: check `V6`.

## 9. Verification families

| Check | What it enforces |
|---|---|
| V1 | Every CSV parses with a matching header and a constant field count |
| V2 | Every row carries a source link or an explicit flag, and cites an official host |
| V3 | Every internal link resolves, in both quote styles |
| V4 | No plain-`http` external link |
| V5 | Pinned row counts on every table |
| V6 | The committed tree reproduces from a clean rebuild, byte for byte |
| V7 | No leaderboard cell holds a backtest-derived number |
| V8 | No input is dated after the kickoff it informs |
| V9 | The corpus reconciles with the official standings for all 32 clubs |
| V10 | Every blank factual cell carries a flag |
| V11 | Every external URL is official or a repository link |
| V12 | The requirement register covers every category and has no duplicate ids |
| V13 | The published model numbers match a recomputation from the raw captures |
| V14 | A market price cell may only hold a value when an operator price was captured |

Plus 23 unit tests, eight of which are negative controls that inject one defect each and
require the verifier to reject it.
