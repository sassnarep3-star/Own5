# Methodology

## 1. Source boundary

The engine reads only `nba-strategy-lab/data/raw/*.csv`. Every raw row must carry an HTTPS URL on `www.nba.com`. Official inputs are NBA traditional team statistics, team box scores, player box scores, and the NBA schedule. NBA Official's injury-report page supplies availability-review context, not an inferred player status.

The raw files are frozen transcriptions inherited from earlier reviewed repository snapshots. This session did not freshly fetch NBA pages (flag F06). It recomputes arithmetic and relational identities and provides direct links for manual source comparison.

## 2. Own-line model

For team `t`, with current games `G`, current points margin `M`, and 2025-26 margin `P`:

`rating(t) = (G × M + 20 × P) / (G + 20)`.

The value 20 is a disclosed analyst regularization choice, not an NBA-published parameter. Model home margin is `rating(home) − rating(away)`. Home-court advantage is zero by convention (F04).

A team's total environment is `2 × PTS/G − margin/G`. Current and prior deviations are shrunk with the same 20-game weight. Model total is current league mean total plus the two shrunk team deviations.

The 22 frozen 2026-27 games are predicted using only 2025-26 margin differences. The resulting home-margin RMSE, 14.3454 points, supplies the scale in `P(home win) = Φ(model margin / 14.3454)`. Using this diagnostic scale does not validate calibration. Fair American prices are direct probability conversions, not market quotes.

## 3. Strategy tracks

- **S01:** prior-season favorite on every frozen game.
- **S02:** prior-season favorite only when absolute rating difference is at least 3 points.
- **S03:** whether prior total and realized total are on the same side of 231.22, the 2025-26 unweighted league mean; this is not an over/under bet test.
- **S04:** daily two-leg parlay of the largest absolute prior-margin favorites; all legs must win.
- **S05/S06:** fixed 25+ point thresholds for Luka Dončić and Anthony Edwards.
- **S07/S08/S09:** fixed 25+ points combined with 5+ rebounds, 3+ made threes, or 5+ assists.

Player rows are sorted chronologically within player and split 60% development / 40% holdout. Team diagnostics use the frozen 22-game sample and a 0.5 directional null. These are retrospective diagnostics, not prospective bet results.

## 4. Dependence

Continuous stat pairs use Pearson correlation; points × team win is point-biserial. Binary threshold pairs use φ, mathematically Pearson correlation on 0/1 indicators. Fisher-z intervals use `1/sqrt(n−3)` and 1.96 standard errors. For a combo, empirical joint hit rate is compared with `p(A) × p(B)`; lift is their ratio. The parlay correlation cell is blank because three joint observations do not support a useful φ estimate.

## 5. Luck and qualification

Each strategy receives an exact one-sided binomial upper-tail test against its development hit rate (props) or 0.5 directional null (team tracks). Holm step-down correction is applied across all nine candidates. Wilson 95% intervals describe holdout hit-rate uncertainty.

G01–G08 require official provenance, a frozen rule and chronological holdout, at least 200 holdout events, Holm-adjusted p < 0.05, CI lower bound above the null, timestamped market/settlement evidence, independent prospective replication, and combo-dependence robustness where applicable. All gates must pass. No candidate qualifies.

## 6. Leaderboard and rewards

Only qualified entries can be scored. The proposed score is `100 × max(0, CI lower bound − null rate) × ln(1+n)`. Ties would require a preregistered prospective CLV/calibration comparison; no such data exists. A future separately funded pool may allocate 50% / 30% / 20% to the top three eligible entries. Current rank, score, ROI, and reward cells are blank.

## 7. Reproduction

```bash
python3 nba-strategy-lab/engine.py
python3 nba-strategy-lab/build.py
python3 nba-strategy-lab/check.py
python3 -m unittest discover -s nba-strategy-lab/tests -v
```

The implementation uses only the Python standard library. Outputs are deterministic.
