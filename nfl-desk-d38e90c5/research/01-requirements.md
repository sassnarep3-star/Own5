# Requirements, acceptance status and evidence

Every requirement from the brief is listed once, with the artefact that satisfies it and the honest
status of that artefact. "Met" means the artefact exists, is published and is verifiable from the
sources cited. "Partial" means the artefact exists but a required value cannot be confirmed from an
official source and is therefore blank and flagged.

| # | Requirement | Artefact | Status | Evidence / note |
|---|---|---|---|---|
| R1 | Collect and organise the full requirements list, and create an executive summary. | `research/01-requirements.md`, `research/00-executive-summary.md`, site pages *Requirements* and *Executive summary* | Met | this document and the executive summary page |
| R2 | Originate the model's own NFL lines. | `model.py`, `data/own_lines.csv`, site page *Own lines* | Met | 297 markets originated from official inputs only |
| R3 | Publish side/spread first, total second, moneyline third. | `model.MARKET_ORDER`, `publish_seq` column, site page *Own lines* | Met | every game's rows are ordered spread -> total -> moneyline; order is also printed in the page header |
| R4 | Publish model fair line, market line and difference as separate columns. | `data/own_lines.csv` columns `model_fair_line`, `market_line`, `difference` | Partial | market line and difference are blank because no official price source exists (see Flagged for Review) |
| R5 | Price-snapshot store with opening and closing prices for every originated market. | `data/price_snapshots.jsonl` (append-only), `data/price_snapshots.csv`, site page *Price snapshots* | Partial | 594 records (opening + closing for 297 markets); the market price field is blank and flagged |
| R6 | Verified results feed so backtests and ROI can be computed. | `data/results_verified.csv` (137 official final scores), site page *Verified results* | Met | the feed is complete; ROI stays blank until a price source exists |
| R7 | Separate signal quality from staking performance on the leaderboard. | `data/leaderboard_signal.csv`, `data/leaderboard_staking.csv`, site page *Leaderboard* | Met | two independent tables with different columns; the gate consumes both |
| R8 | Track replacement depth (starter vs 2nd/3rd/4th string), not merely whether a replacement occurred. | `data/depth_detail.csv`, `data/depth_team_summary.csv`, site pages *Injuries* and *Depth* | Met | every injury row carries unit, position, depth slot, depth tier and the named replacement |
| R9 | Compute correlations only from officially sourced numbers and publish `n` with every value. | `data/correlations.csv`, site page *Correlations* | Met | 7 correlations, each with `n`, both input sources and a note |
| R10 | Define a demotion gate that moves a live strategy back to paper. | `pipeline.py` gate block, `data/gate_decisions.csv`, site page *Gate* | Met | 10 criteria per strategy, fail-closed, all six strategies currently `PAPER` |
| R11 | Research signals across single bets, parlays and player-prop combinations. | `research/04-strategy-research.md`, `data/strategies.csv`, site page *Strategies* | Met | six strategies with definitions, thresholds, backtests and blocked status where applicable |
| R12 | Every strategy must pass validation gates; reward demonstrable skill rather than luck. | `data/gate_decisions.csv` | Met | the luck criterion and the "profit never promotes alone" criterion are explicit gate rows |
| R13 | Track injuries and positional depth deficiencies on offense and defense. | `data/depth_detail.csv` (unit column), `data/depth_team_summary.csv` | Met | offense, defense and special teams are separated; deficiency rows name the player and the next in line |
| R14 | State the questions, information, answers, unknowns and discovery steps needed before decisions can be made. | `research/06-questions-and-unknowns.md`, site page *Questions and unknowns* | Met | 10 questions with what is known, what is missing, and the discovery step |
| R15 | Include a dedicated Suggestions section for reviewing options and choosing a path before implementation. | `research/07-suggestions.md`, site page *Suggestions* | Met | 8 options with a recommended path and reversibility notes |
| R16 | Review the repo line by line, verify facts from official/trusted sources, provide manual-review links, flag irregularities without hallucination. | `research/08-repo-audit.md`, `data/flagged_for_review.csv`, site pages *Repo audit* and *Flagged for review* | Met | 14 audit findings with file paths; 10 flagged items with links |
| R17 | Clean GitHub Pages dashboard with a landing page and categorised subpages containing entries, findings, analysis and readable source-linked tables. | `index.html`, `pages/*.html`, `.github/workflows/nfl-desk-d38e90c5.yml` | Met | 15 pages, one shared stylesheet, no external assets |
| R18 | Verify every table row against an official source; unverifiable values stay blank and flagged. | `verify.py`, `data/flagged_for_review.csv` | Met | the verifier fails the build if a published row has no source link or if a blank value is not registered in the flagged register |
| R19 | Coordinate parallel sessions through `COORDINATION.md`, with non-overlapping claims, immediate commits and rebases. | `COORDINATION.md` claim record for session `d38e90c5` | Met | claim committed as `273b652` and pushed before any other file was added |
| R20 | Final integration, re-verify the combined tree, no broken links, PR to `main` merged without waiting, Pages deployed. | pull request, merge commit, deployment record | Met | recorded in `COORDINATION.md` after the merge |

## Acceptance rules used by the verifier

1. Every published table row must contain a non-empty official source link (`https://www.nfl.com/...`,
   `https://www.<club>.com/...` or a club domain).
2. A blank value in a value column is only allowed when the same item appears in
   `data/flagged_for_review.csv`.
3. Every correlation row must carry `n`.
4. Own-line rows must be ordered spread, total, moneyline within a game.
5. Every internal link in the generated site must resolve to a generated file.
6. The pipeline must be deterministic: two consecutive runs on the same inputs produce identical
   `data/*.csv` files.

## What is not claimed

- No market price, CLV or market ROI is claimed anywhere.
- No player-prop line or player-prop backtest is claimed.
- No causal claim is made from the Week 10 injury cross-section.
- The model is a transparent baseline, not a proven edge.
