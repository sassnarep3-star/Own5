# Verification log — 2026-11-14

Everything below was executed in this session on branch `arena/39086ec8-own5`. Commands are
reproducible from the repository root.

## 1. Deterministic build

```
$ cd nfl-engine-39086ec8 && python3 build_data.py
built: {'price_snapshots': 78, 'games_priced': 13, 'games_unpriced': 1, 'results': 137,
        'recon_checks': 192, 'recon_mismatches': 0, 'origination_rows': 14, 'depth_slots': 78,
        'depth_exposed_slots': 3, 'depth_exhausted_slots': 0, 'correlations_official': 4,
        'demotion_rules': 5, 'demotion_scenarios': 6, 'audit_checks': 37, 'audit_irregular': 7,
        'suggestions': 12, 'questions': 13}
recon mismatches: 0 of 192

$ python3 build_site.py
wrote 14 pages
```

Rebuilt twice; `git status` reports no change to any tracked file. The build reads no network.

## 2. Unit tests

```
$ python3 -m unittest discover -s tests
Ran 68 tests in 0.007s
OK
```

Coverage by area: odds conversion and de-vig (incl. a push at exactly the line), normal/binomial
tails against closed forms, Wilson, Fisher-z, SPRT and Holm, the price store's reject/conflict
paths, settlement (push ≠ half-win), every origination stage and its isolation rules, the
signal/staking split and the in-sample block, depth rungs and exhaustion, all five demotion rules,
correlation reproduction at published precision, and one test per official-data transcription.

Tolerances are set to published precision, not to floating-point precision: correlations are
published to 4 dp so `reproduce` uses 1e-3, and the binomial boundary uses the exact break-even
0.95·11/21 rather than a rounded 0.5.

`statslib.z_from_p` is checked against `norm_sf` out to z = 8 and agrees to ~1e-14.

## 3. Verification harness

```
$ python3 verify.py
1215 checks run, 0 failed
```

| Category | What it asserts |
|---|---|
| Structure | every page has exactly one `<h1>` and a `<title>`; no `TODO`, no rendered `None` |
| Links | every internal `href` resolves on disk; every external link is `https` and on the allow-list |
| Row sourcing | every non-header table row carries a source link, a definition chip, or an explicit blank |
| Snapshots | each of the 13 archived raw blocks recomputes to its stored `sha256` |
| Store | every price row passes `PriceStore` validation; all 78 append |
| Reconciliation | 192 checks, 0 mismatches; 137 games; feed total = official total (6,291) |
| Determinism | rebuild `build_data` + `build_site`, assert byte-identical output |
| Invariants | one and only one `UNPRICED` game, and it has a blank market; a blank market never yields a numeric difference; in-sample entries never pass; an exhausted slot is never filled; no suggestion is marked implemented; every question states have/lack/how |

## 4. Spot checks against the live pages

| Claim | Checked how | Result |
|---|---|---|
| Price store does not fabricate an opening line | `grep` summary + page audit | `event=open` rows = 0; page states it |
| WAS@NYG is not silently dropped | row count = 14, `price_status` | 14 rows, 1 `UNPRICED` |
| R3 cannot pass | leaderboard CSV | `NOT_ELIGIBLE_IN_SAMPLE` |
| Depth metric is not the old 0/1 column | units CSV | index per unit; 3 exposed slots carry rungs |
| No external asset is loaded | `grep 'src="'` over all HTML/CSS | no matches; CSS is inlined into `assets/style.css` |

## 5. Corrections made during the session (and why)

| Correction | Detected by | Fix |
|---|---|---|
| `z_from_p` returned the wrong sign and diverged past z = 3.5 | own test vs `norm_sf` | Acklam seed + bisection on [0, 10] |
| Ledger join dropped LAR and ARI | reconciliation short by 2 clubs | canonical alias map (`canon()`), unit test |
| Staking growth could mask a failing signal | masking scenario asserted the wrong way | split into two scoreboards with separate verdicts |
| `masking_example()` asserted a 20-long pattern | build crash | interleaved sequences; assert on the realised pattern |
| A stale path to the official slate | audit crash | `official_slate_2026_wk10.csv` |
| Correlations compared at 5e-5 | 4-dp publication rounding | tolerance 1e-3, documented |
| 5-of-10 at −110 classified as FAIL | Wilson bound | relabelled INCONCLUSIVE |

## 6. Known-unverified, published rather than hidden

`data/repo_audit.csv` carries 7 IRREGULAR and 3 REVIEW verdicts; `flagged.html` lists every item
with its source link. The desk's own gaps (no opening price, no prop prices, 28 clubs without a
chart, no CLV) are enumerated on the same page. Merge was not gated on them, per the standing
rule that flagged items are published, not blocking.
