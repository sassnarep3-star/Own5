# NFL Verified Origination Desk v4 — session 9e54d765

**Live site:** https://sassnarep3-star.github.io/Own5/nfl-desk-9e54d765/
**Flagged for review:** https://sassnarep3-star.github.io/Own5/nfl-desk-9e54d765/flagged.html
**Read clock for every external value in this desk:** 2026-11-19T11:10:00Z

This file is the written record behind the site. The site is the deliverable; the CSVs in
`nfl-desk-9e54d765/data/` are the evidence; this note explains what was done and what it left
unfinished.

---

## 1. The headline

The model **loses to the closing line**, and the result is not noise:

| Family | Brier skill vs de-vigged close | 95% cluster interval | n |
|---|---|---|---|
| F2_RANDOM (control) | −0.1855 | [−0.2120, −0.1601] | 6,591 |
| F1_LEAGUE_BASE (control) | −0.1724 | [−0.1973, −0.1495] | 6,591 |
| F3_FAVOURITE_ONLY (control) | −0.0441 | [−0.0544, −0.0333] | 6,591 |
| F4_OPPONENT_AWARE (model) | −0.0855 | [−0.1034, −0.0686] | 6,591 |
| F5_MARKET_LINE_BENCHMARK | −0.0021 | [−0.0058, +0.0013] | 6,591 |

Totals model F6: Brier 0.25797 vs 0.25010 de-vigged, skill −0.03146 [−0.04373, −0.02008].

No family is certified. Every leaderboard row is PAPER with `n_settled = 0`.

## 2. What was built

- `build_data.py` — every CSV from the committed inputs and the pinned datasets. Stdlib only.
- `engine.py` — the numerics: ridge ratings, de-vig, Brier, cluster bootstrap, Holm, Wilson,
  Pearson. No numpy, no scipy.
- `verify.py` — 165 fail-closed checks across structure, provenance, hashes, pre-registered
  rules and site links. Non-zero exit = do not publish.
- `build_site.py` — 12 table-first pages, no JavaScript required to read anything.
- `tests/` — 99 unit tests, including numeric negative controls (a flipped sign convention, a
  fabricated positive skill row and a settled-bet row must all fail their rules).
- `preregistration.json` — frozen before the evaluation ran; its sha256 is in
  `data/build_manifest.json` and re-checked by the verifier.
- `.github/workflows/nfl-desk-9e54d765-verify.yml` — rebuild → diff → verify → test → Pages
  smoke check.

Reproduce:

```
python3 nfl-desk-9e54d765/build_data.py
python3 nfl-desk-9e54d765/verify.py
python3 nfl-desk-9e54d765/build_site.py
python3 -m unittest discover -s nfl-desk-9e54d765/tests -v
```

## 3. Sources read first-hand this session

All five were transcribed verbatim into `nfl-desk-9e54d765/inputs/` and hashed.

1. `https://www.nfl.com/standings/league/2026/REG` — all 32 clubs.
2. `https://www.nfl.com/schedules/2026/by-week/week-11` — 13 games, 6 byes.
3. `https://www.nfl.com/schedules/2026/by-week/week-10` — 14 finals, one URL per game.
4. `https://www.nfl.com/injuries/league/2026/reg11` — the full Week 11 report (253 player rows).
5. `https://sportsbook.draftkings.com/leagues/football/nfl` and
   `https://sportsbook.fanduel.com/navigation/nfl` — two named operators, all 13 fixtures,
   read at 11:00Z and 11:01Z.

Plus one Game Center page (`https://www.nfl.com/games/colts-at-texans-2026-reg-11`) for the
TNF matchup detail.

## 4. Where the honest gaps are

Everything below is published on the site; none of it is worked around silently.

1. **The pinned 2026 dataset prints no score for weeks 10–18** (136 blank rows). Only weeks
   1–9 are usable. This desk appends the 14 official Week 10 finals and publishes the gap
   week by week in `corpus_coverage.csv`.
2. **A prior capture asked for Week 11 and served Week 10.** It is stamped
   2026-11-18T03:55:13Z with `requested_url` ending `/reg11` and `source_url` ending `/reg10`.
   The delta table therefore compares two different weeks and is labelled as such.
3. **No closing prices exist.** Every fixture kicks off after the build. The closing columns
   are empty by policy, with a clearing condition in `closing_policy.csv`.
4. **No prospective results.** `n_settled = 0` everywhere.
5. **No third-party price confirmation** of either operator's print.
6. **Only one venue page was read** of thirteen.

## 5. Corrections made to this desk's own first passes

Recorded rather than quietly fixed (also published as F14):

- the spread-to-probability benchmark was first built unsigned, making the market benchmark
  look far worse than the close;
- the sign convention was first reported as "flipped" before being **measured** — the stored
  spread is home-favoured **positive** (MAE 3.4127 vs 8.2237; corr with realised margin
  +0.4314, n=7,087), and both readings are now published side by side;
- the sign-convention table originally printed one correlation twice; each row now carries the
  correlation under **its own** reading of the sign (+0.4314 vs −0.4314), which is what makes
  the table a test rather than a label.

## 6. What the owner should decide

The desk's own recommendation, published on the site and not implemented:

- keep everything on paper; promote nothing;
- treat the origination residual as a research series, not picks;
- unblock in this order: closing prices (Q01), operator terms (Q02), official inactive lists
  (Q03), then re-evaluate;
- two suggestions (S05, S13) are deliberately left as drafts for the owner to accept or reject.

Nothing here is a betting recommendation.
