# Source review and verification boundary

## Retrieval and frozen data

The following official pages were opened through the platform page fetcher on **2026-11-05 UTC**, approximately 21:21–21:27 UTC. The sandbox cannot directly reach NBA hosts, and the NBA pages are dynamic. The CSVs are reviewed transcriptions, not immutable raw official extracts. Source links allow manual review; later displayed values can change.

- [NBA 2026–27 advanced team table](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season), both text chunks: independently compared the 18 selected team names, team IDs, games played, offensive rating, defensive rating, net rating and pace with `nba-integrity-lab/data/team_snapshot.csv`. The Dallas aggregate row crossed a text-chunk boundary, so the [official Dallas team advanced page](https://www.nba.com/stats/team/1610612742/advanced?Season=2026-27) was also opened and compared. The displayed ratings are rounded separately: e.g. Oklahoma City and Utah net ratings need not equal subtraction of the rounded display columns. We did not alter the official displayed value.
- [Official NBA injury report, 2026-11-05 4:00 p.m. ET](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf): checked the nine Nov 6 matchups and team-report statuses. The text extraction omits the date/time on the Utah–Dallas continuation rows; [Utah's official schedule](https://www.nba.com/jazz/schedule) separately confirms the Nov 6 away game and displays 6:00 PM MST. [Dallas's schedule](https://www.nba.com/mavs/schedule) labels its 7:00 PM entry PDT, so the displayed source labels differ and no ET time is inferred. The [NBA games calendar](https://www.nba.com/games?date=2026-11-06) shows nine games on November 6. The other tip strings are transcribed exactly in the PDF's own format, without assuming AM/PM.
- [Official Edwards 2025–26 player box-score log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26), chunks 0–2: independently compared the 25 selected rows from April 10 through January 25 with `nba-integrity-lab/data/edwards_sample.csv`: date, matchup, game ID, W/L, minutes, points, made threes, rebounds and assists. The remaining 36 Edwards rows and all Dončić rows in earlier datasets were not independently re-verified by this session. The sample conditions on appearances and was chosen after the season.
- [Official NBA glossary](https://www.nba.com/stats/help/glossary): checked it is the NBA statistics glossary; it does not establish the statistical quality of our model.
- [NIST binomial reference](https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm) and [NIST confidence limits](https://www.itl.nist.gov/div898/handbook/prc/section2/old.prc271.htm): reviewed the fixed-p binomial distribution and the distinction between exact and normal-approximation confidence methods. The desk's power examples are computed locally under explicit assumptions, not copied as official NBA facts.
- [DraftKings same-game parlay page](https://sportsbook.draftkings.com/same-game-parlay): checked the operator describes combining same-game outcomes, combinations across games, and dynamic odds. No specific odds, payout, jurisdiction, house-rule version or executable quote was obtained. This is an operator example, not a claim about every book.
- [Official NBA injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/): reviewed its notice that reports are continually updated. No point-in-time player-by-player availability join is constructed.
- [NBA 2025–26 scoring leaders](https://www.nba.com/stats/leaders?Season=2025-26): checked Dončić (33.5), Gilgeous-Alexander (31.1) and Edwards (28.8) appear in ranks 1–3 respectively. An earlier report's top-two claim is incorrect (R17).
- [DraftKings NBA spread explanation](https://sportsbook.draftkings.com/page/nba-finals-odds): checked that the operator uses a negative spread for the favorite and a positive spread for the underdog. The earlier Signal Lab code labels a home-margin expression as the spread without reversing the sign (R16). This does not verify any current quote.
- Both `https://www.nba.com/mavericks/schedule` and the recorded `https://www.nba.com/mavs/schedule` resolve through the page fetcher to the same Mavericks schedule; the latter is the URL returned by the fetcher.

Reviewed input-file SHA-256 hashes (computed locally, integrity seals for the transcription, not official NBA signatures):

- `team_snapshot.csv`: `c57a90a7365a59998a91cd298d5446df7e1177b3491121a42d5602b6f6c5eaa1`
- `schedule_snapshot.csv`: `bad032f126e4675e691fa7494602df4980e63e07e600bd77da1c516d1f65af22`
- `edwards_sample.csv`: `8df444e39ed148782f3d5d1ead307c29413e8ad75c030c605934bdbbc3d442c3`

The 25 player rows were also compared field-by-field with the earlier `nba-signal-lab/data/game_logs_2025_26.csv` transcription. Agreement is an additional consistency check, not independent evidence of NBA correctness. Source-page access and the limited field-by-field review are the verification basis.

## Mathematical and design boundaries

All model lines, Pearson and phi coefficients, joint hit frequencies, binomial tails, and proposed gate thresholds are **locally calculated or analyst-chosen**, not NBA-published facts. The full formulas are in `nba-integrity-lab/model.py`. The model parameters were selected after inspecting the data; they were not prospectively registered, fitted, calibrated or validated. A legitimate source link is not evidence that a profitable strategy exists.

The hypothetical exact binomial examples assume independent Bernoulli trials with a common fixed win probability, a fixed −110 price, no pushes and no fees. Those assumptions generally need separate validation for any real ledger. Multiplicity is illustrated with the Bonferroni α/m threshold; no false-discovery or power guarantee is asserted for arbitrary dependent betting data.

## Prior repository review

`nba-integrity-lab/legacy_audit.py` enumerates all tracked static HTML files from the immutable [session-start tree](https://github.com/sassnarep3-star/Own5/tree/54e8dee596d49731c3da535a1f77b01cd0c295d5), counts table rows containing data cells, and checks whether each has an HTTPS link on a conservative allowlist of official/context domains. The resulting `data/legacy-audit.json` contains every file and each missing-link row ordinal. Domain match is only a presence check; it neither verifies sports values nor proves that unlisted domains are unofficial. The scan excludes dynamic content and non-HTML files, and it is not repository-wide line-by-line factual verification.

Material findings about earlier work are preserved on the new review page and requested from their owners in `COORDINATION.md`. Earlier session source files and generated sites were not modified during the independent audit.
