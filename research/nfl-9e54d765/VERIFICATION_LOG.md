# Verification log — session 9e54d765

Every check below was run in this session on the committed tree. A check that did not pass
would have stopped publication; `verify.py` exits non-zero and the CI job fails.

## Machine checks (run last: 165 pass / 0 fail, 99 unit tests OK)

### Structure
- Every expected table exists and holds the expected row count (22 tables pinned).
- No CSV has a row whose field count differs from its header.
- 71 requirement rows; 14 questions; 14 suggestions; 15 flags; 13 sources.

### Provenance — the rule that every factual row links out
- All 52 originated rows carry both a schedule URL and an operator URL, plus a 64-hex input
  hash.
- `market_order` is the clean sequence 1..52, and the market column cycles
  side → total → moneyline → moneyline for all 13 fixtures.
- `difference = fair − market` holds to 2 dp on every row; every probability is strictly
  inside (0, 1).
- All 255 availability rows carry the official injury URL and a UTC read clock.
- All 560 delta rows carry two **different** read clocks.
- All 5 correlations carry n and a source; every flag carries evidence and an https link;
  every question names a route and a source; every suggestion has a two-sided falsifier and a
  review status.

### Integrity
- The sha256 of `preregistration.json` matches the value in `build_manifest.json`.
- All 5 transcribed inputs and all 5 repository inputs still hash to their recorded values.
- `engine.py` and `build_data.py` are unchanged since the build that produced the CSVs.

### Pre-registered rules (the ones a careless edit could break)
- No backtest column exists on the leaderboard; no row has a non-zero `n_settled`; nothing is
  certified; every row says where the backtest lives instead.
- The three combo divisions are BLOCKED, each with a demotion trigger and a clearing
  condition.
- Closing cells are empty on all 156 snapshot rows and are explained by a policy row with a
  clearing condition.
- Exactly one sign convention is chosen; it is the one with the lower MAE **and** a positive
  correlation with the realised margin.
- 32/32 clubs reconcile on all five columns.
- The availability effect is published as estimated coefficients plus a with-minus-without
  difference; no fixed point penalty exists anywhere in the pipeline.
- The headline interval is wholly below zero and is published that way; both controls are
  scored beside the model.
- No team row claims a confirmed replacement (all read `NOT CONFIRMED`).

### Site
- 12 pages, no `TODO`/`FIXME`/placeholder text, no silently empty `<td>`.
- No broken internal link.
- Every page that shows a table also links out to a source.
- Every flag id appears on the flagged page.

## Manual / first-hand checks (this session)

| What | How it was checked | Result |
|---|---|---|
| Standings | Re-read all 32 clubs from nfl.com and recomputed W-L-T, PF, PA against the corpus aggregate | 30/32 from the pinned file alone; **32/32** after appending the 14 official Week 10 finals |
| Week 11 slate | Re-read the schedule page; 13 games + 6 byes, codes as printed (`LAR`, `ARI`) | matches the transcription; alias map `LAR→LA`, `ARI→AZ` published |
| Week 10 finals | Re-read the results page and matched each final to its Game Center URL | 14/14 |
| Week 11 injuries | Re-read the full report; 253 player rows + 2 "No Injuries Reported" clubs | 255 rows published; blank game-status cells left blank |
| Prices | Two operators read at 11:00Z / 11:01Z for all 13 fixtures | 156 snapshot rows; no third-source confirmation (F15) |
| Sign convention | Measured both readings against realised margins | home-favoured **positive** chosen, MAE 3.4127 vs 8.2237 |
| Prior capture identity | Compared `requested_url` against `source_url` on the 2026-11-18T03:55:13Z file | requested `/reg11`, served `/reg10` → F02 |

## What could not be verified, and is therefore blank and flagged

- Closing prices (do not exist yet) — F12.
- A confirmed replacement player for any absence (no official inactive list) — F10.
- A third-party confirmation of either operator's print — F15.
- Venue detail beyond one stadium — F07.
- Any 2026 week 10–18 score from the pinned dataset (it prints none) — F01.
