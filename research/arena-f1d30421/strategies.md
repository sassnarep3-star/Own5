# Strategy Catalog — Singles, Parlays, Player-Prop Combos (T3)

Status: done | Owner: session arena-f1d30421 | Verified: 2026-11-02

Every strategy below is *pre-registered* (rule written before the backtest ran), backtested on the
pinned dataset (1980–2024 regular seasons, n recorded per row), and scored against the validation
gates in [validation-gates.md](validation-gates.md). Backtest outputs:
[`data/backtest_results.csv`](../../data/backtest_results.csv) (each row carries dataset + script links).
Prices are not present in the source dataset, so modeled ROI assumes flat −110 (flagged in every row).

## A. Single bets (game lines)

| ID | Strategy | Signal | Backtest result (1980–2024) | Gate verdict |
|---|---|---|---|---|
| S1 | Home underdog ATS | bet home dog +points | 52.59% (n=3,740), modeled ROI +0.45% | FAIL G2 (p=0.404) |
| S2 | Large home dog ATS | home dog getting ≥7 | 56.37% (n=793), modeled ROI +8.37% | **FAIL G2** (p=0.013 > α=0.00625) |
| S3 | Home favorite ≥7 ATS | bet favorite laying ≥7 | 48.58% (n=2,394), modeled ROI −7.98% | FAIL G2, G4 |
| S4 | Low-total over | over when total ≤ 42 | 50.02% (n=5,382), modeled ROI −4.96% | FAIL G2, G4 |
| S5 | High-total under | under when total ≥ 49 | 53.72% (n=942), modeled ROI +2.80% | FAIL G2 (p=0.216) |
| S6 | Divisional home dog | divisional home dog +points | 52.38% (n=1,279), modeled ROI +0.01% | FAIL G2, G4 |
| S7 | Road dog ≥7 ATS | dog side of S3 games | 51.42% (n=2,394), modeled ROI −2.02% | FAIL G2, G4 |

**Headline finding (luck removed):** S2 is the strongest-looking signal in the catalog and *still
fails* the pre-registered multiple-comparisons gate (α = 0.05/8 = 0.00625; measured p = 0.013).
Under our own rules, no single-bet strategy is certified as skill-based yet. S1 and S2 are
consistent in sign with published findings (home underdogs covered ~53.5% in 2002–2011 per
Szalkowski et al., [ResearchGate](https://www.researchgate.net/publication/233427163_The_Performance_of_Betting_Lines_for_Predicting_the_Outcome_of_NFL_Games);
Paul & Weinbach report significant returns to underdog strategies with large closing lines,
[J Sport Econ](https://www.researchgate.net/publication/329796231_NFL_Betting_Biases_Profitable_Strategies_and_the_Wisdom_of_the_Crowd)),
so they remain on the leaderboard as *Candidate* entries for live out-of-sample tracking — where
CLV and further seasons can promote them.

## B. Parlays (cross-game)

| ID | Strategy | Construction | Finding |
|---|---|---|---|
| P1 | 2-leg cross-game parlay | two qualifying singles, different games | Leg outcomes are statistically independent: measured same-week cross-game cover correlation ratio = 0.9836 (n=9,479 pairs, `data/correlation_parlays.csv`). Parlay EV = product of leg EVs — a parlay cannot create edge that the legs lack. |
| P2 | Fixed-payout parlay audit | 2-leg at −110/−110 pays +264 | Break-even joint rate 27.47%; two break-even legs combine to only ~23.6% → fixed parlays are **worse** than straight bets unless legs carry real edge or strong positive correlation (`data/luck_skill.csv`) |

Rule adopted: parlay legs must be (a) individually gate-passing, (b) from different games (or, if
same-game, priced with empirical joint probabilities), (c) bankrolled at parlay-level variance
(bankroll rules in [luck-vs-skill.md](luck-vs-skill.md)).

## C. Player-prop combos (same-game)

| ID | Strategy | Construction | Finding |
|---|---|---|---|
| X1 | QB over + WR over (same team) | QB passing yards over + top WR receiving yards over | Strong positive leg correlation measured: **r = 0.76** (n=3,852 team-games, `data/correlation_props.csv`). Naive multiplication of leg probabilities massively overstates/understates true joint odds — must use empirical joint pricing. |
| X2 | RB over + game under | rush yards over + game total under | Mild positive correlation of RB yards with margin (r=0.21) and weak with game total (r=0.07): "winning script runs the ball" — leg correlation is real but small; combine only with script-adjusted projections. |
| X3 | QB over + game over | QB yards over + game total over | Leg correlation r = 0.35 with game total — moderate; acceptable 2-leg combo *only* at joint pricing (see correlation.md). |

Status: **framework defined, market lines required for live entries** (prop market lines have no
official source — blank + flagged per policy). Backtest of X-legs on closing prop lines is pending a
verifiable prop-line data source; the correlation values above are computed and reproducible now.

## D. Leaderboard entry states

`Research` → `Candidate` (passes G1 sample + direction sanity) → `Validated` (passes G1–G7) →
`Live-tracked` (promoted to forward tracking with CLV gate active). Current catalog states:
S1, S2 = Candidate; S3–S7 = Research (negative/neutral results published anyway — selection-bias
control); P1/P2/X1–X3 = framework entries. See [leaderboard.md](leaderboard.md).

## Sources for methodology

* Multiple-testing discipline: Bailey, Borwein, López de Prado & Zhu, *Pseudo-Mathematics and
  Financial Charlatanism*, Notices of the AMS 61(5), 2014 ([link](https://www.davidhbailey.com/dhbpapers/overfit-tools-at.pdf));
  Bailey & López de Prado, *The Deflated Sharpe Ratio*, J. Portfolio Management 40(5), 2014.
* Market efficiency context: Kaunitz, Zhong & Kreiner 2017, [arXiv:1710.02824](https://arxiv.org/abs/1710.02824).
* Bankroll: Thorp, *The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market*,
  World Scientific, 2011 ([bibliographic record](https://ideas.repec.org/h/wsi/wschap/9789814293501_0054.html)).
