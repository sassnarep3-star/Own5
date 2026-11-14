# Executive summary - NFL line origination and strategy desk (session d38e90c5)

**Status:** published as a standalone GitHub Pages desk. Every published table row carries an
official source link. Values that cannot be confirmed from an official source are blank and listed on
the **Flagged for Review** page.

**Data as of 2026-11-14 (official NFL.com).** 137 completed games transcribed from the official Week
1-9 schedule pages plus the completed Week 10 Thursday game; 26 upcoming games (Week 10 and Week 11)
with kickoff times, networks and venues; the complete official Week 10 injury report (347 rows); and
the official depth chart of all 32 clubs (31 transcribed, Houston published as an image only).

## What this desk does

1. **Originates its own NFL lines** with a transparent model built only from official numbers:
   alternating least-squares offensive and defensive ratings, small-sample shrinkage, and a
   walk-forward logistic calibration. 297 markets originated (99 spreads, 99 totals, 99 moneylines).
2. **Publishes in the required order** - side/spread first, total second, moneyline third - with
   **model fair line, market line and difference as three separate columns**.
3. **Keeps a price-snapshot store** with an opening and a closing record for every originated market
   (594 records, append-only).
4. **Keeps a verified results feed** (137 official final scores) so backtests and ROI can be computed
   the moment a price source exists.
5. **Separates signal quality from staking performance** on two leaderboards, so a lucky staking run
   cannot hide a weak signal (and a strong signal is not credited for a lucky run).
6. **Tracks replacement depth**, not just "did a replacement happen": every official injury row is
   matched to the club's official depth chart and labelled 1st / 2nd / 3rd / 4th string on offense and
   on defense.
7. **Computes correlations only from officially sourced numbers** and publishes `n` with every value.
8. **Runs a fail-closed demotion gate**: every strategy is currently `PAPER`, because no required
   criterion may be silently skipped.
9. **Researches single bets, parlays and player-prop combinations**, and records what blocks each
   one.

## Headline findings

| # | Finding | Evidence |
|---|---|---|
| 1 | The model is a usable but unremarkable baseline: 73 walk-forward out-of-sample predictions, MAE 10.24 points, Brier 0.2291 vs a 0.2443 base-rate baseline, log loss 0.6480 vs 0.6818, winner hit rate 60.3%, calibration slope 0.869. | `data/backtest_predictions.csv`, `data/leaderboard_signal.csv` |
| 2 | **NFL.com publishes no betting prices.** `nfl.com/betting/` returns 404 and no operator price feed was reachable from this environment. Every market line, market price, difference, CLV and market ROI is therefore blank and flagged. | `data/flagged_for_review.csv`, https://www.nfl.com/betting/ |
| 3 | 26 of the 28 clubs playing in Week 10 have at least one **starter Out** on the official injury report; the substitution depth behind each absence is published per player. | `data/depth_detail.csv`, `data/depth_team_summary.csv` |
| 4 | Offensive starters out in Week 10 show essentially no relationship to the season point differential (Pearson r = 0.034, n = 28); defensive starters out show a weak negative relationship with points allowed per game (r = -0.1587, n = 28). One injury week cannot separate injury effect from team quality. | `data/correlations.csv` |
| 5 | Staking results priced at the model's own fair price are **pure luck** (expected profit is zero by construction). The leaderboard therefore reports them separately from signal quality and the gate never lets them promote a strategy. | `data/leaderboard_staking.csv`, `data/gate_decisions.csv` |
| 6 | The Houston Texans publish their depth chart as an image only, so all 16 Texans depth values are blank pending manual review. | `data/flagged_for_review.csv`, https://www.houstontexans.com/team/depth-chart |

## What is deliberately blank

Market line, market price, difference, closing-line value, market ROI, player-prop lines and the
player-prop backtest. They are not estimated, not filled from a third-party scrape, and not carried
over from an older desk. Each one has an entry on the Flagged for Review page with the manual-review
link and the action needed to close it.

## Read next

- Requirements and acceptance status: `research/01-requirements.md`
- Model and parameters: `research/02-methodology.md`
- Strategy research: `research/04-strategy-research.md`
- Questions, unknowns and discovery steps: `research/06-questions-and-unknowns.md`
- Options and recommended path: `research/07-suggestions.md`
- Repo-wide audit and irregularities: `research/08-repo-audit.md`
