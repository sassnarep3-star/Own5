# Methodology - NBA Desk

All inputs are CSVs in `nba-desk/data/`, transcribed from official NBA pages; each row has `source_url`. `python3 nba-desk/analysis.py` runs the integrity checks, fits the model and writes `data/derived/`; `python3 nba-desk/build.py` writes the site and these documents.

## Data
- Team seasons 2024-25, 2025-26 (82 games) and 2026-27 to date (214 team-games): games, W, L, PTS per game, +/- per game.
- 2025-26 home/road/neutral splits (MEM, SAC, UTA column order unconfirmed, flag F07).
- 22 team-box-score games (44 rows), 10/31-11/02, chosen by visibility rule (flag F03).
- Schedule 11/04-11/05 (16 games); injury report 5:00 PM ET 11/03 (verbatim).

## Model
1. beta = OLS slope of 2025-26 margin on 2024-25 margin = 0.542 (n = 30). Same for total deviations: 0.415.
2. sigma = RMSE of the prior-only margin model on the 22 games = 14.09 (conservative; in-sample).
3. Home-court advantage = sigma x inverse-normal(home win %) = 1.92 points; home win % = 679/1225.
4. K = sigma^2 / tau^2 = 7.46, tau^2 = training residual variance - sigma^2/82 = 26.64. Rating = (G x margin + K x beta x last-season margin)/(G + K).
5. Own margin = rating(home) - rating(away) + HFA; win probability = Phi(margin/sigma); total = 2026-27 league level + shrunk total deviations (K_T = 30.1).

## Validation
- Training pair 2024-25 to 2025-26; test pair 2025-26 to 2026-27 to date (n = 30) and 22 played games walk-forward (prior-only inputs).
- Gates G1-G9 (site page *Validation gates*) fail closed. Strategies S1-S6 are pre-registered; none can be evaluated without market quotes.
- Luck: exact binomial tables (site page *Luck vs skill*), parlay joint-probability formula pq + phi sqrt(p(1-p)q(1-q)).

## Limits
Small samples, no injury or rest adjustment, no market data, hand transcription. See the *Flagged for Review* page (14 flags).

## Reproduce
```
python3 nba-desk/analysis.py && python3 nba-desk/build.py
python3 -m unittest discover -s nba-desk/tests -q
python3 nba-desk/check.py
python3 nba-desk/settle.py        # after filling official final scores in the ledger
```
