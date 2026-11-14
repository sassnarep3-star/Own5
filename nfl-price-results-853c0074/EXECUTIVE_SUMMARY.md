# Executive summary — NFL price snapshots and verified results

## Decision status

**No betting-performance conclusion is justified from the currently available data.** The repository now has an append-only opening/closing snapshot contract and a verified-source results ingestion format, but historical price values and market settlements are not present in the scoped store. ROI and closing-line value (CLV) are deliberately unreported rather than inferred.

## Verified / source-linked evidence

- The normalized results feed contains **136** 2026 Week 1–9 final-score rows, each preserving an exact NFL.com game-center URL and the source-check date inherited from the earlier repository ledger. The source URL and values are available row by row in [`results.html`](results.html). This session freshly checked the Patriots–Seahawks Week 1 game center, which shows New England 10, Seattle 13, matching that row: [NFL.com game page](https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1). **All 136 pages were not freshly re-fetched in this session**; see [`VERIFICATION.md`](VERIFICATION.md).
- The official FanDuel NFL board is a live, mutable market page showing current game markets; it did not provide a historical timestamped quote archive in the fetched page: [FanDuel NFL board](https://sportsbook.fanduel.com/navigation/nfl).
- FanDuel Indiana's official rules page is state-specific (the fetched version showed an effective date of October 15, 2026): [FanDuel Indiana house rules](https://www.fanduel.com/fanduel-sportsbook-house-rules-in). It is an example only, not the user's applicable rule profile.

## Missing data and flagged irregularities

- The 28 inherited Week 10 quote records lack UTC capture times and retained page captures. Numeric prices are blanked in this subsite; none is classified as open or close.
- A linked DraftKings WSH–NYG event page returned the operator's 404 page on 2026-11-14; no archived quote evidence is available (F07).
- The opening/closing store has **0** records, the market-settlement ledger has **0**, and the graded-bet ledger has **0**. `store.py roi` returns `roi_pct: null` for zero bets.
- Market grading needs the applicable sportsbook, jurisdiction and dated rule URL. No player's prop result or post-game correction feed is imported. Existing Week 1 source notes also flag a schedule/game-page day-label discrepancy (F06).
- No skill leaderboard, ROI, CLV, parlay return, prop-combo performance or validated edge is claimed. Existing strategy material elsewhere in the repo does not make those results available to this store.

See [`flagged.html`](flagged.html) for the nonblocking review register and [`questions.html`](questions.html) for known facts, missing information, bounded answers and discovery actions.

## Recommended decision path

1. Select the authorized operator and jurisdiction; retain the rules version applicable to each accepted ticket.
2. Select a lawful, durable source for timestamped market prices or begin prospective capture. Define opening, closing and cutoff semantics before counting CLV.
3. Use stable event, market and selection keys. Keep official NFL outcomes distinct from sportsbook settlements and ticket accepted prices.
4. Verify result/stat corrections, preserve raw evidence and source hashes, and publish sample sizes with each result.
5. Keep predictive signal metrics separate from staking ROI. Lock holdout, multiple-testing, reward and live-to-paper demotion gates before a strategy can rank or be funded.

The dashboard implements a storage and review framework; it does not ingest authenticated account data, scrape an operator, or certify that source links remain available.
