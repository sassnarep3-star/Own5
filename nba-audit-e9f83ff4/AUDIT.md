# Independent NBA sample audit — 2026-11-03 UTC

## Scope and verification

This is an additive, bounded audit, not a line-by-line verification of the whole repository. Compared the ten existing CSV rows, in order, to the first ten entries in the [NBA 2025–26 Anthony Edwards box-score log](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26). Checked each row's game ID, date, opponent, result, displayed integer minutes, points, three-pointers made, rebounds, and assists. All matched the displayed source. The published sample links both the game and the log; the latter is the exact player-level evidence. These are not a random sample. The NBA table displayed 61 rows; this audit checked only the first ten.

Recomputed existing Pearson coefficients using `nba-2026-lab/compute.py`; these are derived sample statistics, not official NBA-published coefficients. They do not establish leg-hit dependence or profitable parlay prices. Three-pointers form part of points, so that association is partly mechanical. No current odds, sportsbook rule set, settled ledger, or funded prize was verified. Removing luck altogether is not possible. The [NBA injury index](https://official.nba.com/nba-injury-report-2026-27-season/) describes changing reports; no historical point-in-time injury join was verified.

## Checks and limitations

Run `python3 -m unittest discover -s nba-audit-e9f83ff4 -v` and `python3 -m unittest discover -s nba-2026-lab -p 'test*.py' -v`. The structural test checks local targets and official-domain link presence, not source entailment, live availability, or every repository page. NBA log is dynamic; verification reflects the accessible display at audit time. This audit is not a complete registry of NBA games, players, bookmakers, or strategies. The existing dashboard's broader historical assertions remain outside the scope of this independent audit. No prospective strategy validation or automated market data feed was established. These and other limitations are disclosed in `review.html`.
