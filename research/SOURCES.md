# Source register and verification

Reviewed on 2026-11-02 UTC. Only primary/official publishers are used for factual data and technical references. Links are also carried into the generated website tables.

## NFL game results

- NFL Football Operations, Big Data Bowl, [2017 game-level data, pinned revision](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv). The local file `data/raw/nfl_2017_games.csv` is a byte-for-byte copy, SHA-256 `f5bbd13d9c711c07e3d4a5b674eb25c1f5f9ced099729337bfd366b5229199ed`; the source schema describes season, week, date, teams and final scores. The source contains 91 rows, from weeks 1–6 only.
- NFL Football Operations, [data schema, pinned revision](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/schema.md). Check column semantics here; a designated home team is not necessarily playing in its home stadium.
- NFL.com, [2017 Week 1 schedule](https://www.nfl.com/schedules/2017/by-week/week-1): additional spot check, not the source for all 91 games. The pinned data retains historical team display names.

The GitHub API reported no repository license in its metadata. Permission to redistribute the source data has not been established; this is flagged for review, not represented as legal advice.

## NFL player logs

The four NFL.com regular-season game-log tables were opened and the date, week, opponent, result, QB passing yards, receiver yards, and receptions in `data/raw/player_pair_games.csv` were checked against the corresponding rows. The local CSV is a *transcription*, not a byte copy or an official NFL publication. The logs can be revised after retrieval and are not version-pinned.

- [Joe Burrow, 2024 game log](https://www.nfl.com/players/joe-burrow/stats/logs/2024/)
- [Ja’Marr Chase, 2024 game log](https://www.nfl.com/players/ja-marr-chase/stats/logs/2024/)
- [Patrick Mahomes, 2025 game log](https://www.nfl.com/players/patrick-mahomes/stats/logs/2025/)
- [Travis Kelce, 2025 game log](https://www.nfl.com/players/travis-kelce/stats/logs/2025/)

Pair only on matching season, week, date, opponent and result. Kelce's 2025 Weeks 16–18 have no corresponding Mahomes row in the retrieved game log; the QB value is blank, and these rows are excluded from paired calculations. A missing row is not assumed to be zero or to indicate a particular reason.

## Measurement and settlement references

- NOAA National Weather Service, [Brier score and mean absolute error definitions](https://vlab.ncep.noaa.gov/web/mdl/ndfd-verification-score-definitions). Brier is a proper probability accuracy measure; lower is better. The baseline and gate thresholds in this project are our policy, not NOAA's.
- NIST, [sample Pearson correlation definition](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/correlat.htm). For two binary indicators, Pearson's r is the phi coefficient.
- UK Gambling Commission, [bet acceptance and settlement rules](https://www.gamblingcommission.gov.uk/licensees-and-businesses/lccp/condition/4-2-6-display-of-rules-betting). Rules are jurisdiction/operator-specific; this source is a reminder to verify the relevant rules, not a claim about any particular wager.
- FTC, [risk of loss and addictive gambling](https://www.ftc.gov/news-events/news/press-releases/2002/06/ftc-warns-consumers-about-online-gambling-children). The page is U.S.-specific and not a statement of the user's local law.

No timestamped sportsbook odds, actual prop thresholds, execution records, terms, injuries, or current-season predictions were verified. Those values remain absent rather than estimated as facts. Model outputs and arithmetic calculations are the project's work, not figures published or endorsed by the NFL or NOAA.
