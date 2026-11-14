# Verification & irregularities (853c0074)

Verification date for fresh page checks: **2026-11-14 UTC**. Scope: only `nfl-price-results-853c0074/**` and its isolated workflow.

## Row-level rules

- Each published NFL result row in `data/official_results.csv` retains its own exact NFL.com game-center URL, `FINAL` status, score cells and inherited `source_verified_on` date.
- `verify.py` checks all 136 rows have integer final scores, distinct event keys, a dated inherited verification marker and direct `https://www.nfl.com/games/…` source URL. The source row URLs are preserved in the dashboard, not replaced with a general league link.
- Fresh re-fetch was **not** performed for all 136 historical game pages in this session. The values were normalized from `nfl-b34253a1/data/games_2026_w1_w9.csv`, whose existing coordination record says 136 source-linked results reconciled against official standings. This desk does not represent those 136 pages as freshly re-certified. The official sources remain directly linked row-by-row for review.
- `data/unclassified_market_quotes.csv` retains 28 metadata records only. All numeric prices are blank; all retrieval UTC timestamps are blank; rows carry F01 or F07. The validator rejects any nonblank legacy price value.
- Empty opening/closing, settlement and graded-bet ledgers are intentional. No inferred price, grade or performance result is published.
- Questions, suggestions, flags and source-register rows each carry a direct official source URL; these links provide source context and are not claims that every proposed design is endorsed by that source.

## Fresh official-source spot checks performed

1. [NFL.com Patriots at Seahawks 2026 REG 1 game center](https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1), fetched 2026-11-14: page shows final **New England 10, Seattle 13**, matching the inherited Week 1 feed row. The NFL page's game header is the source for the displayed final score; the row remains flagged for its day-label note.
2. [NFL.com Week 9 schedule](https://www.nfl.com/schedules/2026/by-week/week-9), fetched 2026-11-14: schedule page showed Week 9 finals and direct game links. Used as league-source cross-check context; not substituted for per-row game links.
3. [FanDuel Indiana House Rules](https://www.fanduel.com/fanduel-sportsbook-house-rules-in), fetched 2026-11-14: displayed an effective date of October 15, 2026 and jurisdiction-specific terms. This confirms why a user/operator jurisdiction cannot be assumed; this is an example source only, not a default grading profile.
4. [FanDuel NFL market board](https://sportsbook.fanduel.com/navigation/nfl), fetched 2026-11-14: live board displayed side, moneyline and total markets. This is a mutable current market page, not a timestamped historical price archive; its quotes were not copied into the open/close store.
5. [DraftKings WSH–NYG legacy event quote URL](https://sportsbook.draftkings.com/event/was-commanders-%40-ny-giants/34118102), fetched 2026-11-14: the operator returned its **404 Not Found** page. No historic quote screenshot/body is retained. Numeric values for every inherited quote row were therefore blanked in this desk; the failed event URL is F07. The current market-board link is listed separately for future prospective capture, not as a replacement verification of that old quote.

## Automated checks

- `python3 nfl-price-results-853c0074/seed_results.py` and `seed_quotes.py`: deterministic normalization from existing repo files; neither contacts the network.
- `python3 nfl-price-results-853c0074/build.py`: deterministic nine-page GitHub Pages site.
- `python3 nfl-price-results-853c0074/verify.py`: validates row source domains, exact result row counts/keys, quote blanks/flags, page existence and internal links.
- `python3 -m unittest discover -s nfl-price-results-853c0074/tests -v`: store validation, duplicate prevention, timezone enforcement, settlement-source gating, ROI arithmetic, and blank-source quote handling.

These automated checks validate structure and arithmetic, not the continuing availability or correctness of dynamic external pages. Exact inaccessible/uncertain items remain on `flagged.html`.
