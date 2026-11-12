# Requirements matrix

Derived line by line from the 2026-11-12 brief. Status: **Met**, **Partially met** (analysis done,
gap named) or **Blocked** (cannot progress without a decision or a paid feed).

| ID | Requirement | Status | Artefact | Remaining gap |
|---|---|---|---|---|
| R01 | Collect, organise and analyse against a full list of requirements | Met | This file; `data/decision-desk/requirements.csv`; site Requirements page | — |
| R02 | Suggestions to improve decision-making, in a dedicated reviewable section | Met | `suggestions.html`; `data/decision-desk/suggestions.csv` (16 items, each with a decision state and a review test) | — |
| R03 | Clear list of questions, information and answers needed before a decision; suggestions to find missing information | Met | `questions.html`; `data/decision-desk/questions.csv` (18 questions, 4 blocking) | Four cannot be closed from public data |
| R04 | Originate own NFL lines | Met | `lines.html`; `data/decision-desk/model_lines_wk10.csv` (14 games) | Market comparison is aggregator-sourced (F01) |
| R05 | Research strategies that generate useful signals | Partially met | `strategies.html`; `data/decision-desk/strategy_ledger.csv` (7 families, 1980–2026) | No family passes every gate |
| R06 | Leaderboard competition with rewards for top strategies | Partially met | `strategies.html#leaderboard`; reward tiers proposal | No certified entrant; funding/jurisdiction open (Q04/Q05) |
| R07 | Singles, parlays, player-prop combos | Met | `strategies.html`, `correlations.html`, SGP pricing table | No official prop lines (F03) |
| R08 | Every strategy must pass validation gates | Met | `validation.html`; `gate_matrix.csv` (G0–G12) | G4 and G8 objectively unpassable today |
| R09 | Determine correlation values | Met | `correlations.html`; `prop_correlations.csv`, `parlay_correlations.csv` | — |
| R10 | Remove luck; selectively skill-based strategies | Partially met | Exact binomial tests, Bonferroni, holdouts, permutation nulls | Skill cannot be certified without CLV data |
| R11 | Track injuries | Met | `injuries.html`; `injuries_wk10_players.csv` (276 official rows) | Game statuses publish later in the week (F04) |
| R12 | Defensive depth: 2nd/3rd/4th string replacing starters | Met | `team_deficiency_wk10.csv` (defence drop column) | Depth inferred from snap share (F05) |
| R13 | Same for the offence | Met | `team_deficiency_wk10.csv` (offence drop column) | — |
| R14 | Executive summary | Met | `summary.html`; `EXECUTIVE_SUMMARY.md` | — |
| R15 | No manual input | Met | `.github/workflows/decision-desk.yml`; `build_all.py` | Requires runner network access |
| R16 | Verify line by line from official sources, link, flag, no hallucinations | Partially met | `verification.html`; `standings_crosscheck.csv`; `claim_checks.csv` | Market/prop/CLV data has no official publisher |
| R17 | GitHub Pages site: clean landing page, category subpages, tables | Met | `nfl-decision-desk/` (14 pages) | — |
| R18 | Coordinate with parallel sessions | Met | `COORDINATION.md` (session 38a1fc27 block) | — |
| R19 | PR, autonomous merge, verified Pages deployment | Met | `COORDINATION.md` D9 record | — |
