# Verification log — 2026-11-12

## 1. Retrieval

`tools/decision_desk/fetch_sources.py` records, for every input: URL, HTTP status, byte count,
SHA-256 and UTC timestamp (`data/decision-desk/raw/provenance.json`). A failed fetch writes a status
row — it never writes a value.

Snapshot used by this build: **2026-11-12T16:29Z** (12/12 pinned datasets and 3/3 official pages
returned HTTP 200).

## 2. Row-level checks

| Check | Method | Result |
|---|---|---|
| Official standings vs independent game log | parse nfl.com standings, re-derive W-L-T/PF/PA from nflverse results | **32/32 exact** |
| Official injury report vs mirror | match 276 rows on team + player + position + practice + game status | **276/276** |
| Injury report completeness | count clubs and statuses | 26 clubs listed; 6 report no injuries; 6 rows carry a game status (Thursday report) |
| CSV provenance | every published table must have a per-row source link | 19 tables, 0 unsourced rows |
| Site rows | every `<tr>` on every page must contain a link | 26 tables / 494 rows / 0 without a link |
| Internal links | every relative href must resolve | 246 pages, 4,182 links, **0 broken** |
| Schedules | Week 10 games and kickoff times vs official schedule page | 14 games, matches |

## 3. The sign-convention error (documented, not hidden)

The first injury backtest computed the against-the-spread residual as `margin + spread`, treating the
spread as a handicap applied to the home team. The pinned source stores the **expected home margin**.

- Wrong sign: fade-the-more-injured-team = 57.4% ATS over 798 bets, "p = 0.0046".
- Correct sign: the same rule = **51.4% over 782 bets, p = 1.0**.

The erroneous result is preserved in `claim_checks.csv` and on the site so the correction can be
audited. Suggested control: S02 (synthetic fixture + ten known-answer games in CI).

## 4. Re-derivation of previously published claims

Eleven numeric claims were recomputed from the pinned inputs using the conventions above.

| Claim (published earlier) | Prior | Recomputed | Verdict |
|---|---|---|---|
| Favourites cover ATS | 48.1% | 48.49% (n = 10,423) | agrees |
| Overs | 49.1% | 49.08% (n = 10,530) | agrees |
| Home underdogs cover ATS | 52.6% | 49.72% (n = 3,626) | does not reproduce |
| Home dogs +7 or more | 56.37% (n = 793) | 53.97% (n = 730) | does not reproduce |
| Favourite SU win rate | 65.63% | 66.14% (n = 10,729) | minor difference |
| QB ↔ WR1 correlation | 0.76 (n = 3,852) | 0.50 (n = 1,255) | does not reproduce (different sample) |
| 110+ wins in 200 bets at break-even | 20.8% | 25.13% | does not reproduce |
| Bets to prove 55% at 80% power | 2,243 | 2,241 | agrees |
| Two-leg −110 parlay break-even | 27.47% | 27.44% | agrees |
| ATS vs total legs independent | phi ≈ 0.01 | 0.006 | agrees |
| Injury signal beats the market | 57.4% (this session, first pass) | 51.4% | rejected and corrected |

## 5. Reproduce

```sh
python3 tools/decision_desk/fetch_sources.py    # official pages + pinned mirrors + provenance
python3 tools/decision_desk/build_all.py        # parse, compute, audit
python3 tools/decision_desk/export_registers.py # registries -> CSV with source links
python3 tools/decision_desk/build_site.py       # render nfl-decision-desk/
python3 tools/decision_desk/verify.py           # fails on any unsourced row or broken link
```

## 6. Known limitations of this verification

- The sandbox that produced this branch can reach only GitHub; official pages and release assets are
  reached by GitHub Actions runners and by the page-fetch tool. The runner-side fetch is the
  authoritative path and is recorded in `provenance.json`.
- Aggregator data is verified against the official page only where both exist.
- Market prices, prop lines and closing lines have no official public source: they remain flagged,
  not verified.
