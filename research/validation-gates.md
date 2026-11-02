# Validation Gates (T4)

Status: done | Owner: session arena-f1d30421 | Verified: 2026-11-02

A strategy must pass **every gate** to be marked `Validated`. Gates are evaluated mechanically by
[`scripts/compute_analysis.py`](../scripts/compute_analysis.py); thresholds below are pre-registered
(design choices where noted). Statistical machinery references are listed per gate.

| Gate | Requirement | Threshold (pre-registered) | Basis / source | Rationale |
|---|---|---|---|---|
| G0 Data provenance | Every input pinned (repo@SHA) or official URL; unknown values blank + flagged | 100% of rows sourced | Project policy; NFL official sources ([nfl.com](https://www.nfl.com/)) | No inferred numbers, ever |
| G1 Sample size | n ≥ 200 graded bets per strategy | n ≥ 200 | Power analysis in `data/luck_skill.csv`: detecting a true 55% skill at 80% power needs ~2,243 bets; 200 is the *entry* floor, not proof | Below 200, variance dominates |
| G2 Statistical significance | one-sided binomial vs break-even rate, **Bonferroni-corrected** for the pre-registered family of k=8 variants | p < 0.05/8 = 0.00625 | Binomial test (standard); multiple-testing correction per Bailey, Borwein, López de Prado & Zhu 2014, [Notices AMS 61(5)](https://www.davidhbailey.com/dhbpapers/overfit-tools-at.pdf) | The winner of many trials is inflated by selection — see "False Strategy Theorem", Bailey & López de Prado 2014, [JPM 40(5)](https://doi.org/10.3905/jpm.2014.40.5.094) |
| G3 Closing line value | Live-tracked entries must beat the closing number on ≥ 55% of bets | CLV hit rate ≥ 55%, measured on ≥ 100 live picks | CLV as leading skill indicator — documented review in betting research ([example](https://bodog.com/sports-betting/why-clv-matters)); closing line ≈ sharp consensus (Kaunitz et al. 2017, [arXiv:1710.02824](https://arxiv.org/abs/1710.02824)) | ROI is noisy; CLV isolates decision quality |
| G4 Out-of-sample / era stability | Win rate > 50% in ≥ 3 of 4 pre-registered era splits (1980–99, 2000–09, 2010–19, 2020–24) | sign-consistent | Standard OOS discipline (walk-forward), cf. backtest-overfitting literature above | Kills single-era flukes (rule changes, market learning) |
| G5 Correlation accounting | Parlay legs priced with measured correlation; same-game legs use empirical joint probabilities | No naive independence when measured \|phi\| > 0.05 | Measured values in `data/correlation_bets.csv` / `data/correlation_props.csv` | Same-game prop legs measured up to r = 0.76 |
| G6 Robustness | Signal survives ±10% parameter perturbation and removal of best single season | ≥ 80% of variants same sign | Standard sensitivity analysis | Prevents parameter-fitting |
| G7 Capacity & execution | Strategy specifies minimum acceptable price and max stake; results graded at realistic prices | recorded per entry | Kelly sizing discipline, Thorp 2011 ([record](https://ideas.repec.org/h/wsi/wschap/9789814293501_0054.html)) | Paper ROI at −110 ≠ achievable ROI |

## How gates map to states

* `Research`: any catalog entry, results published regardless of outcome (anti-selection-bias).
* `Candidate`: passes G0, G1 (n ≥ 200) and has sign-consistent era direction.
* `Validated`: passes G0–G7.
* `Live-tracked`: `Validated` + forward record with G3 active; reverts to `Research` if G3 fails
  over ≥ 100 live picks.

## Current gate outcomes (computed 2026-11-02, full rows in [`data/backtest_results.csv`](../data/backtest_results.csv))

| Strategy | G1 | G2 | G4 | State |
|---|---|---|---|---|
| S1 home underdog | PASS | FAIL (p=0.404) | PASS | Candidate |
| S2 home dog ≥7 | PASS | **FAIL (p=0.0134 > 0.00625)** | PASS | Candidate |
| S3 home fav ≥7 | PASS | FAIL | FAIL | Research |
| S4 low total over | PASS | FAIL | FAIL | Research |
| S5 high total under | PASS | FAIL (p=0.216) | PASS | Research |
| S6 divisional home dog | PASS | FAIL | FAIL | Research |
| S7 road dog ≥7 | PASS | FAIL | FAIL | Research |
| S8 SGP fav+over | PASS | FAIL (p=1.0) | n/a | Research |

**No strategy is `Validated` in the opening catalog.** That is the system working: luck is removed
by construction, and promotion requires live evidence (G3) plus corrected significance.
