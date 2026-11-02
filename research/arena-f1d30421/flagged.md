# Flagged for Review (irregularities & unverified items)

Status: published (non-blocking) | Owner: session arena-f1d30421 | Date: 2026-11-02

Policy: any value that cannot be confirmed from an official source is left blank and listed here.
Nothing on this list blocks use or merge. Items are numbered for easy follow-up requests.

| ID | Item | Where | Evidence / observation | Severity | Status |
|---|---|---|---|---|---|
| F1 | Historical betting lines have **no official public source** | `data/raw/spreadspoke_scores.csv`, all backtest/base-rate rows that use `spread_favorite`, `over_under_line` | The NFL does not publish closing lines; the only reachable historical line dataset is the community "spreadspoke" dataset ([pin](https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv)). Values used verbatim from that file, never inferred. | Medium | Open — needs licensed odds feed for official-grade verification |
| F2 | Play-by-play source is a community mirror, 2002–2013 only | `data/correlation_props.csv` | `brianfoshee/nfl-play-by-play-data` @ `352c9c9` mirrors the advancedfootballanalytics.com archive ([pin](https://github.com/brianfoshee/nfl-play-by-play-data/blob/352c9c9b0bce0ffa8ce85681cf9ed50c0398f462/)). Era-caveat: modern pass volumes differ; correlations labeled derived. Release-CDN nflverse data unreachable from build sandbox (documented in COORDINATION.md). | Medium | Open — re-run with nflverse data when infrastructure allows |
| F3 | Dataset team-name inconsistencies | `data/raw/spreadspoke_scores.csv` team columns | 49 distinct name strings incl. `New York` (ambiguous: 1 row — excluded from analysis), `New York Jets (1p, ` (malformed), `Las Vegas` vs `Las Vegas Raiders`, short/long forms (`New England`/`New England Patriots`, `Tampa Bay`/`Tampa Bay Buccaneers`). Handled via explicit mapping in `scripts/compute_analysis.py`; the ambiguous row is dropped, not guessed. | Low | Resolved-in-code (mapping is auditable) |
| F4 | Mixed-type `over_under_line` field | `data/raw/spreadspoke_scores.csv` | Column contains non-numeric strings; coerced with `pd.to_numeric(errors='coerce')` — coerced-out rows excluded from totals analysis (never imputed). | Low | Resolved-in-code |
| F5 | Dataset 2025 season is partial | base-rate windows | File (last commit 2025-10-01) has 78 rows for 2025 with 64 scored (weeks 1–5). 2025 excluded from analysis windows (which end at 2024). Score spot-verification against nfl.com passed (see F6). | Low | Resolved-by-exclusion |
| F6 | Historical scores verified on a sample, not the full 61-year file | `data/verified_official_results.csv` | All 16 games of 2025 Week 1 (dataset rows + nfl.com game pages) matched exactly, incl. BUF 41–40 BAL. Full-file official verification is impossible from the sandbox (official pages cover recent seasons only) — sampled verification documented instead. | Medium | Open — sample passed (16/16) |
| F7 | Market lines for 2026 Week 9 model lines | `data/model_lines_2026_wk9.csv` `market_spread`, `market_total` columns | Blank by policy — no official source publishes market lines. | Medium | Open — needs licensed odds feed |
| F8 | Backtest ROI assumes flat −110 (or +264 for 2-leg) | `data/backtest_results.csv` `assumption_price` | Prices are not in the source dataset. ROI values are modeled at standard prices and labeled as assumptions in every row. | Medium | Open — needs licensed odds feed |
| F9 | Reward pool amounts | `research/leaderboard.md` §4 | Competition reward *mechanics* are specified; pool size/funding/currency are owner decisions — left blank, not invented. | Low | Open — awaiting owner decision |
| F10 | GB streak-column anomaly on official standings page | transcription of 2026 standings | The standings page streak field for GB appeared inconsistent with week-8 results (display possibly stale/misread). Streaks were **not** used anywhere (model uses W-L-T/PF-PA only) and are excluded from the transcribed CSV. | Low | Resolved-by-exclusion |
| F11 | Model limitations (not errors, disclosed) | `data/model_lines_2026_wk9.csv` | v1 ratings are net-points based: no opponent adjustment, no injuries/QB news, league-wide HFA constant. Sensitivity to these is gate G6 territory; CLE@NO week-9 line is a visible example of record-vs-point-differential tension. | Low | Disclosed |

Manual review aid: each site table row carries its own source link; this page groups the items whose
*entire column class* cannot be officially sourced (F1, F2, F7, F8) plus data-quality notes (F3–F6,
F10) and design disclosures (F9, F11).
