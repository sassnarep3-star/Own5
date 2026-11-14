# Repo audit: line-by-line review of the existing NFL desks

Scope of this audit: every NFL desk already in the repository, reviewed for the properties this
session was asked to deliver - official-source provenance, price snapshots, verified results,
publication ordering, leaderboard separation, replacement depth, correlations with `n`, a demotion
gate and per-row source links. Findings are recorded with file paths so they can be re-checked by
hand.

Desks reviewed: `nfl-desk-864d5668`, `nfl-desk-26d4cafb`, `nfl-hub-28431d9c`, `nfl-b34253a1`,
`nfl-decision-desk`, `nfl-decision-desk-38a1fc27`, `nfl-decision-desk-e413f933`, `nfl-strategy-lab`,
`line-lab`, `own5-desk`, plus the shared `data/` tree.

## Findings

| ID | Desk | Path | Finding | Impact | Recommendation |
|---|---|---|---|---|---|
| RA-01 | `nfl-desk-864d5668` | `data/depth_crosscheck.csv` | The `practice_status` column contains character-exploded strings (`L / i / m / i / t / e / d ...`) instead of the published practice designation. The same rows carry the correct text in the `issue` column. | A published column is unreadable; anything computed from it is wrong | Fix the writer that split the string per character; see SUG-08 |
| RA-02 | `nfl-desk-864d5668` | `data/injury_summary.csv`, `data/injuries.csv` | The official injury source is pinned to `https://www.nfl.com/injuries/league/2026/reg10` and the capture is dated 2026-11-13, with 326 rows. This session captured the same official page on 2026-11-14 and transcribed 347 rows. | Two desks publish different counts for the same official report; a reader cannot tell which is current | Pin one capture date per page and print it next to every count |
| RA-03 | `nfl-desk-864d5668` | `data/leaderboard.csv` | A single ranking mixes staking results (`units_per_bet_at_-110`, `roi_pct`, `deflated_sharpe`) with the signal name, and the ROI is computed at an assumed flat -110 rather than at a published price. | A lucky staking run can dominate the ranking, and the ROI column is not a market ROI | Split the leaderboard into signal and staking tables, as this desk does |
| RA-04 | `nfl-desk-864d5668` | `data/flags.csv` F-01 | Correctly records that no official market prices exist and that every market column is left blank. | None - this is the correct behaviour and it is the precedent this desk follows | Keep |
| RA-05 | `nfl-desk-26d4cafb` | `data/oos_week9.csv` | Market lines and prices are taken from an "ESPN/DraftKings -- THIRD PARTY" scrape and published beside official scores. | A third-party price is published on a site whose rule is that every row needs an official source | Label third-party prices in the row itself and keep them out of official-source tables |
| RA-06 | `nfl-desk-26d4cafb` | `data/flagged.csv` FLG-01 | The desk itself records that "the repo's market numbers are an ESPN/DraftKings scrape" and leaves its market columns blank. | Consistent within the desk; the inconsistency is across desks | Consolidate on one rule (SUG-07) |
| RA-07 | `nfl-desk-26d4cafb` | `registers.py` (VALIDATION_GATES G-01..G-10) | Ten fail-closed validation gates exist, but every failure action is "reject / unranked / ineligible"; there is no explicit live-to-paper state transition. | A live strategy has no defined demotion path | Adopt this desk's gate, which computes a `PAPER` decision and a reason for every strategy on every build |
| RA-08 | `nfl-decision-desk-e413f933` | `scripts/originate_lines_wk10.py` | The home-field term is a module constant (`HFA`) rather than an estimate, and it is not surfaced as a flagged assumption in the published output. | A reviewer cannot tell an assumption from a sourced number | Publish model parameters next to the lines and flag them |
| RA-09 | `nfl-hub-28431d9c` | `verify.py`, `data/` | The hub reconciles desks against one official snapshot, but it has no price-snapshot store, no verified-results feed and no leaderboard, so it cannot detect drift in those areas | Drift in price and results handling stays invisible | Point the hub verifier at this desk's `price_snapshots.jsonl` and `results_verified.csv` |
| RA-10 | shared `data/` | `data/correlation_bets.csv`, `data/decision-desk/parlay_correlations.csv` | Historical correlations use third-party archives (`github.com/tobycrabtree/spreadspoke`, `github.com/nflverse/nflverse-data`), not official NFL publications. | Valuable for long samples, but not "officially sourced numbers"; must not be presented as official | Label the provenance per row; this desk restricts itself to official NFL sources and publishes `n` for every value |
| RA-11 | shared `data/` | `data/correlations.csv` | Carries `n_teams` and the input file, which is the right shape, but the computed column and the source URL are stored in separate columns with no per-value note | A reader has to join columns to check a number | Keep the `n`, the input and the note in one row, as `data/correlations.csv` does here |
| RA-12 | `nfl-strategy-lab`, `line-lab` | `lines-2026-wk9.html`, `data/` | The oldest labs are frozen at 2026-11-02 and still publish Week 9 lines and ledgers computed on a stale game list | Their rankings are computed on fewer games than the current official record | Re-run or clearly date-stamp them as historical |
| RA-13 | `own5-desk` | `data/derived_lines.json` | Legacy snapshot records carry `"empirical_home_advantage": null` and `"home_advantage_assumption": 0.0` | The home-field treatment differs between snapshots and the same field is null in one and 0.0 in another | Normalise the field and record which estimate produced each snapshot |
| RA-14 | repo-wide | `index.html`, `README.md` | The root landing page and README describe several NFL desks with different dates and different counts, with no single canonical NFL entry point | A reviewer landing on the root sees conflicting numbers for the same league week | Final integration session publishes one canonical NFL landing page (SUG-07, D-09) |

## Cross-desk drift summary

| Area | State across the repo | State in this desk |
|---|---|---|
| Market prices | Blank in the desks that follow the official-only rule; third-party ESPN/DraftKings values in `nfl-desk-26d4cafb` | Blank everywhere, flagged, with the manual-review link |
| Price snapshots | No opening/closing store found in any desk | Append-only store, opening + closing for every originated market |
| Verified results | Ledgers exist but are per-desk copies with different cut-off dates | One feed, 137 official final scores, reconciled against the official standings |
| Publication order | Not enforced as a rule | `MARKET_ORDER` enforced in code and in the published order of every game's rows |
| Leaderboard | Single mixed ranking in `nfl-desk-864d5668` | Two separate leaderboards, signal and staking |
| Depth | Depth charts are tracked, but the tracker does not always reach the *replacement tier*; `depth_crosscheck.csv` is corrupted (RA-01) | Per-player replacement tier and depth-deficiency flag for every injury row |
| Correlations | Most carry `n`; the root shared data mixes official and third-party inputs | Official inputs only, `n` on every row |
| Gate | Ten fail-closed criteria but no live-to-paper transition | Fail-closed gate with an explicit demotion decision and reason |
| Source links | Present on most rows; some legacy JSON rows carry a source field that is null | Every published row carries a source link, enforced by the verifier |

## Manual review links for the audit

- Official standings used for reconciliation: https://www.nfl.com/standings/league/2026/REG
- Official schedules used for every result: https://www.nfl.com/schedules/2026/by-week/week-10
- Official injury report behind the injury tables: https://www.nfl.com/injuries/
- Example club depth chart behind the depth tables: https://www.packers.com/team/depth-chart
- The third-party price provenance seen in `nfl-desk-26d4cafb`: https://www.espn.com/nfl/odds
- The third-party archives seen in the shared correlation files:
  https://github.com/tobycrabtree/spreadspoke , https://github.com/nflverse/nflverse-data

## Conclusion

The repository already contains strong pieces - fail-closed validation gates, official-source
discipline, injury and depth work, per-row `n` in correlations. The gaps are cross-desk: duplicated
inputs that drift, one corrupted column, one leaderboard that mixes luck with skill, and no shared
price-snapshot or verified-results layer. This desk is deliberately standalone and does not edit any
file owned by another session's claim; the consolidation work is proposed as SUG-07 for a final
integration session.
