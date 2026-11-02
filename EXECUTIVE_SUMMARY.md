# Own5 — Executive Summary

**Project:** originate and analyze our own NFL lines and betting-style strategies using only verified official sources, framed as a leaderboard competition, and publish the results as a GitHub Pages dashboard.
**As-of date:** 2026-11-02 (UTC). 2026 NFL season is live through Week 8; the Week 9 target slate begins Thursday 2026-11-05.
**Branch / session:** `arena/09d847e1-own5` (session `arena-09d847e1-own5`). Analytics only — no wagering advice; see the legal note in `data/flagged.json` (F15).

---

## 1. What was built

| Component | Location | Contents |
|---|---|---|
| Verified raw datasets | `data/` (9 files) | 2025 + 2026 standings, 2026 W1–W8 game results (121 games, 120 final), 2026 W9 schedule (15 games), 2025 + 2026 player-stat leaders, season facts, source registry (18 official sources), flagged-items register (F01–F15) |
| Analysis engine | `scripts/analyze.py` | Line-by-line verification checks, walk-forward model, backtest, correlations, strategies + gates, leaderboard, Week 9 originated lines |
| Analysis outputs | `analysis/` (6 JSON) | `verification_report.json`, `backtest_2026.json`, `model_lines_2026_w9.json`, `correlations.json`, `strategies.json`, `leaderboard.json` |
| Docs | `EXECUTIVE_SUMMARY.md`, `docs/repo-review.md`, `docs/sources.md` | This summary; line-by-line repo review with links and irregularities; official source registry |
| Live site | repo root `index.html` + `pages/*.html` + `assets/` | Dashboard landing + category subpages; every table row carries an official-source link; flagged items on a dedicated page |

## 2. Data verification (line by line, official sources only)

All raw values were transcribed from official NFL properties (`nfl.com` standings/schedules/stats/game pages, `media.nfl.com`, `operations.nfl.com`) — registry with URLs in `data/sources.json` and `docs/sources.md`. Every value is traceable; nothing was inferred. **All 10 automated consistency checks pass** (`analysis/verification_report.json`):

- 2025: all 32 teams W+L+T = 17; sum(W)=sum(L)=271; PCT=(W+½T)/17; NET=PF−PA; HOME+ROAD=17, DIV=6, CONF=12.
- 2026 W1–W8: per-team games played, W/L/T, PF/PA, HOME/ROAD records re-derived from the 120 final game entries match the official standings table for **all 32 teams exactly**; sum(W)=sum(L)=119 decided games, 1 tie (NYG@WAS 27–27, Week 5).
- The one pending game (CHI@SEA, Week 8 MNF, 2026-11-02) is excluded from the backtest and flagged (F05).

**Verification rule applied throughout:** every table row on the site links to an official source; anything not confirmable from an official source is left **blank** and listed on the **Flagged for Review** page (`data/flagged.json`, F01–F15) — never inferred. Headline example: sportsbook market lines do not exist in any official source (F01), so no market/CLV column is populated anywhere.

## 3. Originated lines — 2026 Week 9 (target slate, 15 games)

Method (no lookahead): each team's power rating = pooled (points for − points against)/game over the verified 2025 full season plus 2026 final games through Week 8; model margin (home perspective) = rating(home) − rating(away) + empirical HFA (mean home margin of the 120 final 2026 games = **+0.72 pts**, home win rate 62/120 = 51.7%); model total = sum of expected team scores, expected = (own PF/G + opponent PA/G)/2. Full table with per-game official links: `analysis/model_lines_2026_w9.json` and the site's Week 9 page.

| Game | Originated spread | Model total | Total pick vs league ref (46.0) |
|---|---|---|---|
| JAX @ BAL (Thu 11/05, TNF) | JAX 8.5 | 47.4 | Over |
| CIN @ ATL (Sun 11/08, Madrid 9:30a) | CIN 0.7 | 48.7 | Over |
| DEN @ CAR | DEN 6.7 | 43.1 | Under |
| DAL @ IND | IND 1.8 | 53.5 | Over |
| NYJ @ KC | KC 12.5 | 43.8 | Under |
| DET @ MIA | DET 8.9 | 48.9 | Over |
| CLE @ NO | NO 1.5 | 41.2 | Under |
| NYG @ PHI | PHI 2.6 | 44.7 | Under |
| LA @ WAS | LA 12.1 | 48.4 | Over |
| HOU @ LAC | HOU 5.6 | 42.0 | Under |
| LV @ SF | SF 13.9 | 46.3 | Over |
| GB @ NE | NE 6.9 | 44.8 | Under |
| AZ @ SEA | SEA 18.3 | 47.4 | Over |
| TB @ CHI (SNF) | CHI 3.5 | 47.0 | Over |
| BUF @ MIN (Mon 11/09, MNF) | BUF 3.9 | 45.2 | Under |

**QB passing-yards prop lines** (originated, not backtested — flagged F03/F06/F07): line = 0.65×(2026 YDS ÷ team GP) + 0.35×(2025 YDS ÷ 17). 17 of 30 QB slots have a line (e.g., Stafford LA 271.3, Goff DET 276.3, Prescott DAL 260.0, Lawrence JAX 239.4); BAL/MIA/PHI/AZ slots are blank because the Week 9 starters are not confirmed from an official source (Lamar Jackson is on IR per official nfl.com news, 2026-11-01), and a few 2026 totals are outside the fetched top-24 table (blank, flagged).

## 4. Backtest — walk-forward, 2026 Weeks 1–8 (120 final games)

The same model was re-run walk-forward: each game predicted using only 2025 aggregates + earlier 2026 weeks. Calibration: model-vs-actual margin Pearson **r = 0.289** (n=120), margin MAE 10.5 pts; model total r = 0.232.

| Strategy | Type | Bets | Win rate | ROI | Binomial p vs breakeven | Gates | Tier |
|---|---|---|---|---|---|---|---|
| **S2 Spread direction, selective abs(line)≥6** | single (SU) | 51 | **68.6%** | +37.3% | 0.0055 | all pass | **Gold** |
| **S4 Same-game 2-leg parlay (spread dir + total dir)** | parlay | 120 | 38.7% (breakeven 27.4%) | +40.5% | 0.0052 | all pass | **Gold** |
| **S3 Total direction vs league reference** | single (SU) | 120 | **63.3%** | +26.7% | 0.0022 | all pass | **Gold** |
| **S1 Spread direction, all games** | single (SU) | 120 | 58.0% | +16.0% | 0.0493 | all pass | Gold |
| S5 Weekly top-2 spread parlay | parlay | 8 | 62.5% | +127.8% | 0.0403 | **G1 fails (n<30)** | Not approved |
| S6 Negative control: own line at −110 | single (−110) | 120 | 37.5% / 46.7% | −28.4% / −10.9% | ~1.0 | fails | Not approved |
| S7 W9 QB prop lines | props | — | blank (unverified) | — | — | G1/G3 unmet | Unrated — flagged |

Validation gates (all must pass; `analysis/strategies.json`): G1 ≥30 graded bets · G2 win rate ≥ breakeven (50% SU / 52.38% at −110 / 27.44% for a 2-leg −110 parlay — the −110 convention is labeled assumption F02) · G3 one-sided binomial p<0.05 vs breakeven (skill vs luck) · G4 Weeks 7–8 holdout ≥ breakeven (S1 70.4%, S2 60.0%, S3 70.4%, S4 48.2% — all pass) · G5 max drawdown ≤15 units · G6 parlay correlation guard |r|<0.35.

**Luck removed / skill isolated:** the SU strategies are graded at even money against a 50% null, so the vig is not the source of any win rate; significance is binomial, and the W7–W8 holdout was not used for fitting. The negative control (S6) shows the honest counterpoint: paying −110 on self-originated lines without a market price loses money — which is exactly why no market/CLV column exists (F01) and why approval requires the binomial gate, not raw ROI.

**Correlation values determined from verified data** (`analysis/correlations.json`): 2025 NET vs win% r=**0.919** (n=32); 2026 NET vs win% r=**0.831** (n=32); model vs actual margin r=**0.289** (n=120); same-game margin vs total r=**−0.164**; same-game spread-leg vs total-leg result r=**+0.087** (passes the G6 parlay guard <0.35, which is why the S4 same-game parlay is allowed while its legs are still priced honestly at parlay odds); 2025 differential vs 2026 win% persistence r=**0.397** (n=32); empirical HFA = **+0.72** pts/game, home win rate 51.7%.

**Leaderboard scoring** (project-defined, labeled as such): score = 100×ROI + 10×Sharpe + 50×(win rate − breakeven). Rewards go only to gate-approved strategies: S2 (75.2), S4 (71.3), S3 (63.7), S1 (37.6) — all Gold tier. S5 has the highest raw score (165.8) but is **not approved** because 8 bets < 30 (G1) — a deliberate guard against small-sample luck.

## 5. Repo review & irregularities

Line-by-line review with per-file links is in `docs/repo-review.md`. Irregularities flagged: the repo's `README.md` was **empty (0 bytes)** at review time (F14) — fixed by this project; chunk-boundary truncation during capture cut two values mid-string (2025 Tyler Shough INT/RATING/LNG set to null, F-row note; W2 WAS@DAL game link re-confirmed via its own game page); standings table columns that could not be mapped (e.g., streak/last-5 semantics) are stored but marked unmapped rather than guessed (F11).

## 6. Site & deployment

Static site at the repo root (`index.html` dashboard + `pages/` subpages + inline styles only — no external assets, so it renders in a no-network iframe; `.nojekyll` disables Jekyll processing). GitHub Pages is configured to serve from **main / root**. The integration step re-verified all combined data line-by-line, built the site, opened the PR to `main`, merged it, and confirmed the Pages deploy; the PR link and merge result are recorded in `COORDINATION.md`.

## 7. How to reproduce

```bash
python3 scripts/analyze.py     # reads data/*.json -> analysis/*.json (pure stdlib, no network)
python3 scripts/build_site.py  # reads data/ + analysis/ -> index.html, pages/*.html, assets/
```

## 8. Limitations (all flagged, none blocking)

No official market odds exist (F01) so no CLV; −110 is a labeled convention (F02); QB GP approximated by team GP (F03); two 2026 backup QB teams unconfirmed (F04); CHI@SEA pending at cutoff (F05); BAL/MIA/PHI/AZ W9 starters unconfirmed (F06); 2026 leaders table is top-24 only, so a few QB totals are blank (F07); cross-game parlay independence assumed (F08); HFA is empirical (F09); 2025 data is team-level only (F10); no injury/weather modeling beyond the Jackson IR note (F12); analytics only — sports wagering legality varies by jurisdiction, including South Korea where it is generally prohibited (F15).
