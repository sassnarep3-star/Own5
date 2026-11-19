# Verification log

## What runs

```
python3 nfl-af9a1ada/tools/build_data.py     # deterministic data build, ~20 s
python3 nfl-af9a1ada/tools/build_site.py     # 14 pages, no JS
python3 nfl-af9a1ada/verify.py               # 1,898 fail-closed checks
python3 -m unittest discover -s nfl-af9a1ada/tests -t nfl-af9a1ada   # 30 tests
```

All four exit 0 at HEAD.

## The twelve check families in `verify.py`

1. Every input in the manifest still hashes to its recorded value.
2. The shipped registration is byte-identical to the committed one, and every leaderboard row carries its hash.
3. No performance number appears while there are zero settled bets.
4. No requirement claims MET without an observed value; every row names a gate, a clearing number and a source (official URL, or a shipped artefact that exists).
5. Every originated row has fair, market, difference and a 64-character inputs hash; the difference equals fair minus market.
6. **No published side difference is large enough to be a convention artefact**, and the two columns agree on the favourite in at least 7 of 13 games.
7. Every price row names a book, a UTC clock, a URL, and carries a parseable line.
8. A depth rank implies a club chart source; a blank rank implies no source, so nothing is implied.
9. The site builds; 14 pages; every internal link resolves.
10. No empty numeric cell anywhere — a value that was not read renders as a labelled BLANK.
11. Every flag has a unique id, a valid severity, at least one source and a detail.
12. Every question has a route to an answer; every suggestion states its risk.

## Identities that hold

| Identity | Value | Why it matters |
|---|---|---|
| league wins = losses | 149 = 149 | the standings read is complete |
| league PF = PA | 6,923 = 6,923 | every point is attributed |
| sum(offence) = 0 | 0.000 | the rating is centred |
| hfa > 0 | +1.17 | a negative home edge would be a defect |
| corr(offence, PF/g) | +0.786 | the rating describes scoring |
| corr(defence, PA/g) | −0.750 | defence points the right way |
| mean(pred total) = mean(actual total) | yes | the totals equation is identified |
| Week 10 finals vs pinned corpus | 14/14 | the third-party data matches today's official results |

## What the verifier cannot check

- That an official page said what a transcription says. The transcribed raw captures sit beside the transcriptions in `captures/`, and the manifest hashes both, but a human must diff them once.
- That the corpus is right. It is third-party; the only cross-check available is the 14-game Week 10 reconciliation.
- Anything about the operators' terms, which were not reachable.
