# NFL Price & Results Lab

A self-contained, additive GitHub Pages subsite and standard-library Python store for two gaps in the existing NFL research desk: historical opening/closing prices and market-keyed, sourced settlements. It does not modify shared navigation or any other session's files.

## Status now

- `data/official_results.csv`: 136 final-score rows normalized from the repository's existing NFL.com-linked 2026 Week 1–9 results ledger. Every row preserves its exact NFL.com game-page URL and inherited source-check date. This task did not re-fetch each historical game page; the source URLs remain available for review. One inherited page-label/date irregularity remains flagged.
- `data/unclassified_market_quotes.csv`: 28 inherited Week 10 quote metadata records from official DraftKings/FanDuel market pages. Historical numeric price fields are intentionally blank because there are no retained source captures for re-verification; retrieval UTC times are also blank, so none are opening or closing prices. All carry F01 or F07. One direct DraftKings event URL was fetched on 2026-11-14 and returned the operator's 404 page (F07).
- `data/price_snapshots.csv`, `data/market_settlements.csv`, `data/graded_bets.csv`: valid header-only, append-only ledgers. Their emptiness is intentional; no prices, settlements or performance values were invented.
- Nine static pages: overview, executive summary, price snapshots, official results, ROI/backtests, questions, suggestions, flagged review and sources. The complete executive summary is also in `EXECUTIVE_SUMMARY.md`.

## Add data prospectively

Initialize the ledgers:

```sh
python3 nfl-price-results-853c0074/store.py init
```

`store.py` exposes validated append functions for a price event and market settlement. A price row requires stable origin/event/market/selection keys, a phase (`opening`, `intermediate`, `closing`), a non-zero American price, book, jurisdiction, an explicit UTC capture timestamp and an HTTPS source URL. An optional source update time must also be UTC. Duplicate natural keys are rejected. The store never infers a timestamp from a date.

Settlement rows require both an official outcome URL and the actual applicable sportsbook-rule URL, a settlement state, an explicit jurisdiction, UTC settlement time and `verified` status. Do not label a source verified solely because it is linked; a reviewer must check it. The included FanDuel rule links are state-specific examples and are not a default profile.

The price ledger keys permit opening, closing and intervening snapshots for side, total, moneyline, player-prop, parlay and prop-combo markets. A consuming strategy should originate side, then total, then moneyline, with the same stable IDs carried to price and outcome records. Never report a closing-line result when either timestamp or price is missing.

## Backtest / ROI boundary

`python3 nfl-price-results-853c0074/store.py roi` computes unit ROI only from rows in `graded_bets.csv` marked verified and linked to a settlement source. Net return for a single wager is reconciled to stake, accepted American odds and explicit settlement state. A sportsbook result/rule profile is necessary: a league score alone cannot settle every operator's spread, total, moneyline, prop or parlay ticket. The current feed has zero graded rows, so there is no ROI or skill claim. Parlays should be expanded to sourced constituent legs and graded under the chosen operator's rules before scoring.

Each graded wager also carries book, jurisdiction, accepted-price evidence URL, exact verified market settlement source, and applicable rules URL; the join requires an exact origin/event/market/selection/book/jurisdiction match. The evaluator is a fail-closed arithmetic tool, not an independent source verifier or evidence of statistical significance. Keep predictive signal scoring (probability calibration, Brier/log loss, sample size) separate from staking ROI. Do not rank/reward until pre-registered holdout, uncertainty, multiple-testing and demotion gates exist.

## Build and verify

```sh
python3 nfl-price-results-853c0074/seed_results.py
python3 nfl-price-results-853c0074/seed_quotes.py
python3 nfl-price-results-853c0074/build.py
python3 nfl-price-results-853c0074/verify.py
python3 -m unittest discover -s nfl-price-results-853c0074/tests -v
```

`seed_*` are deterministic normalizers of the already linked repository snapshot files; they do not access the network or certify that dynamic source pages remain unchanged. The scoped CI repeats feed and HTML structure checks and unit tests.

## Official source links

- NFL game center/result source attached row-by-row: [NFL.com games](https://www.nfl.com/games/steelers-at-eagles-2026-reg-11)
- Schedule and official player statistics: [NFL schedule](https://www.nfl.com/schedules/2026/by-week/week-9), [NFL player stats](https://www.nfl.com/stats/player-stats/)
- Live operator boards: [DraftKings NFL](https://sportsbook.draftkings.com/leagues/football/nfl?category=games&subcategory=game-lines&nav_1=all-games), [FanDuel NFL](https://sportsbook.fanduel.com/navigation/nfl)
- Example rule pages only: [FanDuel Indiana](https://www.fanduel.com/fanduel-sportsbook-house-rules-in), [FanDuel Ohio](https://www.fanduel.com/fanduel-sportsbook-house-rules-oh)

Rules and market boards are dynamic and jurisdiction-specific. See `sources.html`, `questions.html` and `flagged.html` before relying on any table.
