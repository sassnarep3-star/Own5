# Verification log — NFL market desk (session 83a7d6a8)

What was checked, what it found, and where the evidence lives. A check that failed is listed with what it cost, not removed.

| Check | Result | File | Source |
|---|---|---|---|
| Results feed | 145 finals, 32/32 reconcile | data/results_feed.csv, data/standings_reconciliation.csv | nfl.com/schedules/2026/by-week/week-10 and nfl.com/standings/league/2026/REG |
| Mirror comparison | 127 agree, 0 disagree, 18 absent | data/results_feed.csv | pinned nflverse games.csv.gz |
| Injury capture | 347 rows across 28 clubs | data/injuries_wk10.csv | nfl.com/injuries/league/2026/reg10 |
| Week 11 report | not published; reg11 serves Week 10 | flags.csv OWN-07 | nfl.com/injuries/league/2026/reg11 |
| Depth charts | 11 of 12 captured clubs parsed; Houston is an image | data/depth_coverage.csv | each club's own depth-chart page |
| Depth divergence | 17 rows | data/depth_compare.csv | live chart vs inherited register |
| Venues | 12 of 13 stadiums named on the official page; 1 host city only | data/venues.csv | nfl.com/schedules/2026/by-week/week-11 |
| Schedule language | 4 dated statements quoted verbatim | data/schedule_announcements.csv | nfl.com/schedules/2026/by-week/week-11 footer |
| Standings | 32 rows transcribed | data/standings_official.csv | nfl.com/standings/league/2026/REG |
| Correlations | 5 published, 5 withheld | data/correlations_official.csv | nfl.com/standings/league/2026/REG |
| Price policy | 10 decisions, all with a URL | data/price_policy.csv | mixed, see each row |
| Price store | 195 rows, 78 populated | data/price_snapshots.csv | mirror release page |
| Pre-registration | 9 hashed rule files | data/preregistration/ | this build, hash published |
| Flags | 34: 14 INH-, 20 OWN- | data/flags.csv | each row's source_url |
| Ledger corrections | 2 counts corrected and kept visible | data/raw/sources_captured.csv, OWN-20 | the generated files themselves |

## Checks that failed during the build and what changed

| Failure | Cause | Fix |
|---|---|---|
| `build_prices.py` KeyError `matchup` | the origination file carries `away`/`home`, not `matchup` | compose the fixture from the two club fields |
| `build_prices.py` NameError `prob_to_american` | helper not imported | import it |
| Verify C: 78 requirements "missing evidence" | paths were resolved against the repository root while they are written relative to the desk | resolve both forms explicitly |
| Verify A: 168 unsourced rows | several tables had no source column at all | added an evidence column to readiness, withheld correlations, leaderboard, luck, demotion, questions, suggestions, and the registration table |
| Verify B: 10 broken links | policy rows cited "internal policy" and flags cited repo-relative paths | policy rows now link the policy file; repo paths are rewritten to absolute blob URLs |
| Totals wrong: 14 games / 254 rows | typed from memory instead of from the file | counts are now copied from the generated files; OWN-20 records the error |
| Market-implied margin σ of 42.9 points | dividing a line by a z-score from a symmetric price | the field is now blank by construction and the mistake is documented in the code |
| Controls all scored 0.25 against the home outcome | control rows reused the home result | each control is now graded against its own outcome |
