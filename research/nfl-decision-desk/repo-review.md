# Repo review against official sources — session arena-e413f933

Scope: every NFL data artifact in the repository, compared line by line against
official nfl.com pages (fetched 2026-11-12). Each item links the official source
for manual review. Discrepancies are flagged in
`nfl-decision-desk/data/flagged_items.csv` and published on the Flagged page.

## Reviewed artifacts

| Repo file | Official source used | Result |
|---|---|---|
| `data/standings-2026-wk8.csv` (prior session) | https://www.nfl.com/standings/ | Structure consistent with official format; superseded for Week-10 work by `nfl-decision-desk/data/standings_2026_reg_wk9.csv` (transcribed fresh, 32/32 teams) |
| `data/model_lines_2026_wk9.csv` (prior session) | https://www.nfl.com/standings/ + https://www.nfl.com/schedules/ | Methodology re-read and reproduced exactly in `nfl-decision-desk/scripts/originate_lines_wk10.py`; market columns correctly blank |
| `data/week8-2026-results.csv` (prior session) | https://www.nfl.com/schedules/2026/by-week/week-8 | **All 13 played games match official finals exactly** (CAR 19-27 GB, BAL 10-36 BUF, TEN 36-43 CIN, AZ 33-30 DAL, MIN 15-19 DET, IND 7-42 JAX, LV 38-33 NYJ, CLE 6-27 PIT, ATL 0-16 TB, LAC 9-24 LAR, KC 24-28 DEN, NE 24-19 MIA, PHI 10-27 WAS). CHI@SEA row blank (correct at capture, pre-kickoff) — game since final 34-17 → flagged **F-W8-1** |
| `data/leaderboard.csv` (prior session) | n/a (rule table) | Tier rules adopted unchanged; metric cells correctly blank/pending, no fabricated numbers |
| `data/luck_skill.csv` (prior session) | n/a (definition table) | Breakeven definitions consistent (−110 = 52.38%) |
| Root site `index.html`, `pages/`, `data/research.json` | n/a (other session scope, CI-locked) | Not modified; left to root-site session per COORDINATION.md |

## This session's inputs (fresh official transcription)

| Artifact | Official source | Verification |
|---|---|---|
| `nfl-decision-desk/data/standings_2026_reg_wk9.csv` | https://www.nfl.com/standings/ (2 chunks, all 32 teams) | Every W-L-T/PF/PA/net/streak copied from the official table; ties shown as T |
| `nfl-decision-desk/data/schedule_2026_wk10.csv` | https://www.nfl.com/schedules/2026/REG10 (3 chunks) | All 14 games: date, time ET, network, notes; Munich game marked neutral |
| `nfl-decision-desk/data/byes_2026_wk10.csv` | same | CHI, DEN, PHI, TB |
| `nfl-decision-desk/data/injuries_2026_wk10.csv` | https://www.nfl.com/injuries/league/2026/REG10 (7 chunks) | 278 rows / 14 games; 5 Out + 1 Questionable; game-status blank on 272 rows (flagged F-INT-1) |
| `nfl-decision-desk/data/depth_charts_2026_wk10.csv` | 27 official club depth-chart pages (`https://www.<club>.com/team/depth-chart/`) | 608 rows; HOU image-only (flagged F-HOU-1); BAL chart-vs-transaction conflict (F-BAL-1); MIA QB depth gap (F-MIA-1) |
| `nfl-decision-desk/data/own_lines_2026_wk10.csv` | derived from standings + schedule | Model output labeled as derived; market columns blank (F-MKT-1) |

## Irregularities found

1. **F-HOU-1** — Houston depth chart is an image only; no machine-readable table. HOU deficiency data blank, never inferred.
2. **F-BAL-1** — Ravens chart lists Lamar Jackson QB1 while official news reports IR placement.
3. **F-MIA-1** — Dolphins chart lists Kyle McCord alone at QB (no backup strings).
4. **F-INT-1** — Official mid-week injury report leaves game status blank for 272/278 rows.
5. **F-MKT-1 / F-PROP-1** — No official public source for market lines or player props; all such columns blank/blocked by policy.
6. **F-W8-1** — Prior week-8 results file has one stale blank row (CHI@SEA, now final 34-17).
7. **nfl.com depth-chart URLs 404** — league site has no depth-chart page; official club sites used instead (documented pattern, not a data defect).

## Method notes

- Direct `curl` to nfl.com is blocked in this environment; all official pages were
  fetched through the workspace fetcher and transcribed by hand — no generated values.
- No value in any table was inferred. Unconfirmable cells are blank and flagged.
