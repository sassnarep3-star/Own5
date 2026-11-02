# Requirements traceability

| Requirement | Implementation / evidence | Release status |
|---|---|---|
| Review the repo line by line | `docs/SOURCE_AUDIT.md`; starting tree was one README line | Complete |
| Coordinate claims and scopes | Root `COORDINATION.md`; small commits; fixed-branch exception documented | Complete |
| Collect and organize NFL information | Frozen official excerpts, typed snapshot, source register, fact table | Complete for declared snapshot; not a full historical archive |
| Originate own NFL lines | Shrunken PF/PA baseline and Poisson distribution; separate research-line page | Complete as research; not validated market prices |
| Single bets | ST01/ST02/ST06 registry and push-aware EV engine | Implemented; qualification blocked by missing market history |
| Parlays | ST03; joint bounds, dependence sensitivity, settlement-aware returns | Implemented; no verified ticket prices |
| Player-prop combinations | ST04/ST05; 17 paired official Burrow–Chase observations | Descriptive study; current props blank |
| Determine correlations | Pearson, Spearman, binary phi, empirical joint lift, bootstrap intervals | Complete for declared historical sample; not universal SGP estimates |
| Remove luck / selective skill | Uncertainty-aware gates, walk-forward protocol, multiplicity, CLV, joint calibration | Framework complete; no strategy passes yet; finite-sample luck cannot be eliminated |
| Leaderboard competition and rewards | Eligibility-first ranking; non-cash 100/60/40 research points | Empty qualified field; no invented ranking |
| Validation gates for every strategy | G00–G10; unknown never passes; automated tests | Complete |
| Official link on every table row | Fact rows link official sources; derived rows link official inputs and method; review rows link official lookup sources | Enforced by build audit |
| Unsupported values blank and flagged | `null` data contract; blank renderer; Flagged for Review | Complete |
| Executive summary | `docs/EXECUTIVE_SUMMARY.md` and site summary | Complete after integration |
| Clean dashboard and category subpages | Static site: overview, lines, strategies, parlays, props, correlations, validation, leaderboard, data, sources, review, methodology | Complete after integration |
| No manual user input | Agent performs research, implementation, validation, PR, merge and publication | Complete when publication record is written |
| Verify combined data and no broken links | Source audit, reconciliation, unit tests, deterministic build, internal-link and asset checks | Complete after integration |
| GitHub Pages live site | Pages workflow and deployment verification | Publication attempted by final integration; result recorded in board |
| PR and merge without waiting | PR from the platform-fixed integration branch to main; merge only after checks | Result recorded in board |
| Publish irregularities without blocking | Dedicated Flagged for Review page | Complete |

## Interpretation boundaries

“Official source” means the NFL, an official club/league system, an official operator for its own rules, or an official scholarly publisher for methodology. A source link beside a model estimate identifies its inputs; it does not falsely imply that the NFL published the estimate. “Useful signal” requires out-of-sample evidence, not an attractive backtest. “No hallucinations” is implemented as explicit evidence, missing-value preservation, reconciliation, and refusal to claim unavailable results.
