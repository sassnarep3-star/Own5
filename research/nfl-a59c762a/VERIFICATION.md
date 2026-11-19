# Verification log — NFL Decision Console (session a59c762a)

Every read below was performed in this session on 2026-11-19 (UTC). "Read first-hand"
means the value was transcribed from the official page read at the stated clock, not
inherited from a prior session.

---

## 1. Line-by-line verification of the official reads

| # | Item | How it was verified | Result |
|---|---|---|---|
| 1.1 | League standings, 32 clubs | Read the official standings page in 2 chunks. Extracted W, L, T, PF, PA, NET. Checked that NET = PF − PA on every row. | **PASS** on all 32 rows |
| 1.2 | Sum of the standings | ΣW = 149, ΣT = 2, so Σ games = 150. ΣPF = ΣPA = 6 923, which is what a closed league requires. | **PASS** |
| 1.3 | Games played per club | The 32 game counts sum to 300 = 2 × 150 games | **PASS** |
| 1.4 | Week-11 injury report | Read the official report in all 7 chunks. Transcribed every player row: club, player, position, injury text, practice status, game status | **PASS** — 253 rows, 24 clubs, 9 `Out`, 7 `Questionable`, 237 rows with no game status |
| 1.5 | Clubs with no listed injuries | The report prints `No Injuries Reported` for the Bengals and the Commanders | **PASS** — recorded, not turned into zero rows |
| 1.6 | Week-11 schedule | Read the official by-week page in 3 chunks | **PASS** — 13 games, each with date, kickoff time and network |
| 1.7 | Week-10 finals | Read the official by-week page in 2 chunks | **PASS** — all 14 games read, with the four Week-10 bye clubs listed |
| 1.8 | Week-10 bye clubs | The page prints CHI, DEN, PHI, TB | **PASS** |
| 1.9 | Official Game Book | Read the official PDF for Washington at New York | **PASS** — 22 expected starters, 22 actual starters, 6 WAS and 7 NYG players Not Active, 3 and 1 Did Not Play, the weather and surface line, and the final score 24–21 |
| 1.10 | Game Book contains snap counts | Searched the read document | **Absent** — the Game Book publishes no snap count |
| 1.11 | Colts at Texans game centre | Read the official game centre | **PASS** — venue `HOUSTON, TX`, stadium `RELIANT STADIUM` |
| 1.12 | 2026 Schedule Release | Read the landing page in 2 chunks | **PASS** on the content; the page prints **no publication date** → the date cell is blank and flagged (F-A59-11) |
| 1.13 | Week-11 neutral site | The release page lists Week 11 Vikings at 49ers at Estadio Banorte | **PASS** |
| 1.14 | International games through Week 10 | The release page lists nine; eight fall in weeks 1–10 and one in week 11. The corpus carries exactly eight neutral rows | **PASS** |
| 1.15 | Next Gen Stats snap series | Read the official glossary | **Absent** — the glossary documents tracking metrics and no public per-player play series |

## 2. Reconciliation of the repository's own artefacts

| # | Artefact | Check | Result |
|---|---|---|---|
| 2.1 | `nfl-desk-35a1feb2/data/results_feed_2026.csv` | Per-club W, L, T, PF, PA against the official standings | **FAIL for 2 clubs** — Baltimore (4-6-0, 209/259 vs 4-5-0, 189/236) and the Chargers (1-8-0, 144/239 vs 0-8-0, 121/219). Flag **F-A59-01** |
| 2.2 | `nfl-c98c6270/data/results_feed.csv` | Same reconciliation | 150 rows but the Rams at Cardinals row is absent and the Chargers at Ravens row is `NOT FINAL`. Flag F-A59-03 |
| 2.3 | `nfl-command-desk/data/results_corpus.csv` | Same reconciliation | 150 rows, the Rams at Cardinals row absent. Flag F-A59-03 |
| 2.4 | `nfl-market-desk/data/results_feed.csv` | Same reconciliation | 145 rows, five Week-10 games absent. Flag F-A59-03 |
| 2.5 | `nfl-desk-e46fb855/data/results_feed.csv` | Same reconciliation | 145 rows, five Week-10 games absent. Flag F-A59-03 |
| 2.6 | `nfl-price-results-853c0074/data/official_results.csv` | Same reconciliation | 136 rows, all of Week 10 absent. Flag F-A59-03 |
| 2.7 | `nfl-desk-e46fb855/data/depth_slots.csv` | Per-club parse status | 30 clubs `parsed`, **Houston `NOT PARSED`** (image only), **Patriots partial**. Flag F-A59-05 |
| 2.8 | `nfl-c98c6270/data/depth_slots.csv` | Row and slot counts | 890 rows, 32 clubs, Houston a single `image_only` row, **14 shared rank-1 slots**, **5 empty first strings** |
| 2.9 | `data/nfl-desk-f2e20e96/availability_wk11_preview.csv` | Compared row by row against the new capture | 10 rows from game pages; the Minnesota and San Francisco club statements are **superseded** by 10 and 15 named rows respectively. Flag F-A59-04 |
| 2.10 | The desk's own corpus | Same reconciliation | **0 mismatches across all 32 clubs** |

## 3. What was computed, and how it was checked

| # | Quantity | Check | Result |
|---|---|---|---|
| 3.1 | Home field | Fitted, not assumed; must be positive and inside a plausible band | 1.488 points |
| 3.2 | Residual sigma | Must be inside a plausible band | 14.079 points |
| 3.3 | Rating vector | Must sum to zero | sums to 0 within 1e-6 |
| 3.4 | Line ordering | Every game must emit side, then total, then moneyline | 13 games × 3 markets = 39 rows, ordered |
| 3.5 | Probabilities | Every published probability must be strictly between 0 and 1 | **PASS** |
| 3.6 | Correlations | Every value must publish n, an interval and a p-value | 8 rows, all complete |
| 3.7 | Lookahead | No availability read may be dated after the kickoff it informs | the Week-11 read at 06:45Z precedes the 8:15 PM ET kickoff |
| 3.8 | Leaderboard | No cell may hold a backtest-derived number | all blank |
| 3.9 | Blank cells | Every blank factual cell must carry a flag | enforced by V10 |
| 3.10 | Price cells | A price cell may only hold a value if the row records that an operator price was captured | enforced by V14; all 39 rows are blank and flagged |

## 4. Negative controls

Eight defects were injected into throwaway copies of the desk. The verifier must reject
each one, and does:

| # | Injected defect | Expected rejection | Result |
|---|---|---|---|
| 4.1 | Stripped source link and flag from a requirement row | V2 | **rejected** |
| 4.2 | A market price filled in with the flag removed | V14 | **rejected** |
| 4.3 | Every flag deleted from the per-team view | V10 | **rejected** |
| 4.4 | A backtest score written onto the leaderboard | V7 | **rejected** |
| 4.5 | An internal link pointed at a missing page | V3 | **rejected** |
| 4.6 | A row deleted from the results corpus | V5 | **rejected** |
| 4.7 | A non-official host substituted for a source link | V2 and V11 | **rejected** |
| 4.8 | A tampered sigma and home-field value in the backtest table | V13 | **rejected** |

## 5. Regularity of the committed tree

`verify_desk.py` runs 14 check families (1 371 checks) and re-runs the three build
scripts to prove the committed pages and CSVs reproduce byte for byte. The unit test
suite runs 23 tests. All green.

## 6. Things that could not be verified in this session

- The exact server bytes behind any page (limitation L-01).
- Per-player play counts from an official source (F-A59-07).
- A venue string for 11 of the 13 Week-11 fixtures, because those game centres were not
  read (F-A59-10 covers the one conflict that was found).
- The publication date of the 2026 schedule release (F-A59-11).
- Any market price, and therefore any residual, closing-line value or return (F-A59-02).
