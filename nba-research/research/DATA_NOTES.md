# Frozen evidence protocol — 2026-11-05

This workspace is additive. It does not overwrite the other sessions' datasets.

## Collection and verification

- NBA team tables: all 30 rows were transcribed from the complete official 2026–27 advanced and traditional tables. Records were compared across advanced, traditional and standings renderings. The 2025–26 advanced table supplies an 82-game prior. Arithmetic checks are in `engine.py`; they are not a substitute for source comparison.
- Player sample: the 61 Edwards and 64 Dončić rows in session 6d508fee's CSV were re-reviewed line by line against freshly fetched official NBA logs. Edwards required the unfiltered page plus the 2025-10-01–2025-11-20 window. Dončić's unfiltered requests initially returned no table; the 2025-10-01–2025-12-14 (19 rows) and 2025-12-15–2026-04-30 (45 rows) windows returned all 64. No cell discrepancy was found in the re-reviewed fields. The new CSV retains the official log URL and individual game URL, and normalizes the ASCII name to Dončić. Season totals/rounded means are checked against the official leaders page.
- **Correction:** the official leaders page ranks Dončić first (33.5), Gilgeous-Alexander second (31.1), Edwards third (28.8). This is a two-player high-usage sample, **not** the top two scorers. Gilgeous-Alexander's full log was not collected.
- Schedule: the official dated schedule returned exactly two games for November 5. Both game IDs, home teams, arenas and ET tip times were transcribed. No other games were inferred.
- Injuries: the official November 5, 12:00 PM ET PDF was read. Eleven current-game rows are retained, including two `NOT YET SUBMITTED` team rows. Blank player/reason cells on those rows are intentional. Absence of a player from this report is not evidence of availability. Later reports were not substituted into this frozen snapshot.
- Market: the official FanDuel NBA board rendered 12 prices (spread, moneyline and total, both sides, both games). The Miami–Golden State event page independently rendered the same six prices. The Orlando–Phoenix event page returned a location check, so its six prices have only the board rendering. `observed_before_utc` is an upper bound recorded after retrieval, not a fabricated exact quote timestamp. Exact retrieval time, jurisdiction and ticket-specific terms are blank and flagged. These are archived observations, not executable quotes.
- Rules/definitions: official NBA glossary, injury-policy index and 2026–27 rules PDF were opened. The page fetcher parses only the first 30 PDF pages; the full rules PDF was not exhaustively parsed. No unobserved rule text is quoted.
- Methods: NIST's binomial-confidence reference and the authors' own Deflated Sharpe Ratio and PBO manuscripts were opened. PubMed's abstract and bibliographic metadata were returned by official-domain search; direct page retrieval failed twice with HTTP 500. That access limitation is flagged; the abstract is used only as a hypothesis source, not an NBA effect-size estimate.

## Provenance limitations

The platform fetcher returns rendered text, not response headers or a byte-for-byte HTML archive. Source URLs and the retrieval date are recorded; response-body hashes are not invented. Dynamic pages may change after retrieval. CI rebuilds the frozen CSVs and checks internal consistency, schema, calculations and links; it does **not** claim to re-fetch live NBA or sportsbook pages.

Every raw factual row has an official source URL. Calculated rows link to their underlying official inputs and are labeled `Derived`. Model parameters and competition policies link to official context but are explicitly labeled analyst choices, not NBA facts. Unknown market, performance, rank and prize values remain empty. See `FLAGS.md` and the Flagged for Review page.
