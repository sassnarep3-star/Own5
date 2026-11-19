# Model, gates and governance — desk 715e2cd4

## 1. The model is deliberately small

```
hp = mu + h/2 + off_H + def_A
ap = mu - h/2 + off_A + def_H
```

32 offence parameters, 32 defence parameters, two plug-in moments (`mu`, `h`) and one plug-in scale
(`sigma`). Five hundred words of theory are not needed to justify it; what is needed is that it is
frozen before scoring, that its inputs are official, and that its failures are published.

Why these choices:

* **Ridge, not a free fit.** Nine weeks is 136 games and 64 parameters. Unpenalised, the design would
  fit noise. `lambda = 5.0` points² is pre-registered and the sensitivity at 1/10/25 is published
  alongside so a reader can see the result is not a hyper-parameter artefact.
* **Opponent-aware by construction.** Each game contributes the home club's offence against the away
  club's defence, and vice versa. A rating is therefore the average residual against the defences (or
  offences) that club actually faced, which is what "opponent-aware" means in practice.
* **Plug-in moments, not fitted ones.** `mu`, `h` and `sigma` are computed directly from the training
  corpus. Fitting them inside the ridge would make the test set influence the fit.
* **Moneyline from the margin.** `P(home) = Phi(margin / sigma)`. This is a mapping, not a second
  model, and it is labelled as such everywhere.
* **Two totals.** `A` = sum of fitted expected points; `B` = mean of the two clubs' average combined
  game total. Both are published until one wins, and on the current holdout neither does.

## 2. What the model does not contain, and why that is a limitation not a choice

| Missing input | Why it is missing | Consequence |
|---|---|---|
| Injuries / availability | No verified depth or snap source for 32 clubs | No injury penalty at all; a fixed penalty would be an unsourced guess |
| Depth and replacements | Same | The deficiency matrix cannot be built honestly |
| Weather, roof, surface | Not captured | Totals ignore environment entirely |
| Rest, travel, short weeks | Rest is derivable from official dates; travel is not | Only bye status is published as fixture context |
| Line movement | No price feed | No CLV, no steam, no residual |

A model that adds an unsourced injury penalty is worse than a model that admits it has none: the first
produces a confident number with no evidence behind it. Requirement R14 asks for **ablations**, not
penalties, precisely so the effect of personnel is measured rather than assumed. That ablation is
currently impossible (G6 blocked) because there is no verified availability feature to remove.

## 3. Gate status in one line each

| Gate | Status | The observation that sets it |
|---|---|---|
| G0 pre-registration | **passed** | `PREREGISTRATION.md` committed 2026-11-19, before any Week 11 fixture was scored |
| G1 minimum sample | **failed** | 0 scored bets against a 300-bet provisional floor; 5,773 for a 55%-vs-52.4% claim |
| G2 walk-forward | **partial** | side +21.96% MAE vs baseline, both totals negative (−12.1%, −8.4%) on 14 games |
| G3 proper-score qualification | **failed** | no strategy has a qualifying sample; game-cluster bound not estimable at n=14 |
| G4 price provenance | **failed** | 0 of 39 markets have any price |
| G5 depth-source verification | **failed** | 0 of 32 clubs verified; jersey/experience/salary route rejected in writing |
| G6 ablation reproducibility | **blocked** | no availability feature exists to ablate |
| G7 demotion | **not triggered** | no strategy is live; four numeric triggers are written and frozen |
| G8 joint evidence for combos | **blocked** | no validated joint probability and no operator void/push rules |
| G9 designation calibration | **blocked** | 0 archived seasons; 16 of 253 report rows carry a designation |

## 4. Why signal and staking are separate (LB-03)

A staking run can be lucky while the signal is noise, and a good signal can lose money on a bad stake
plan. Ranking on realised return conflates the two and rewards whichever lucky sequence happened to
land. The desk therefore carries two columns that are never derived from each other:

* **Signal score** — benchmark-relative Brier skill, game-cluster lower bound, multiplicity-adjusted.
* **Staking score** — closing-line value and staked-return observations, scored only after G4 exists.

Neither column has a value, because neither has data. That is the honest state, not an empty table.

## 5. Why combos are gated (G8)

Multiplying marginal probabilities assumes independence. Across games that assumption is nearly true
(the margin/total correlation in the 136-game corpus is −0.122 with a 95% interval of −0.285 to 0.047,
so independence is not rejected), but *within* a game it is false by construction: a quarterback's
yards and his receiver's yards share a driver. A combo may only be ranked when a directly validated
joint probability exists **and** the operator's void and push rules are known, because a void leg
changes the payout structure in a way a probability alone cannot express. Neither condition holds for
any of the 13 fixtures, so S4, S5 and S6 carry no numbers.

## 6. Governance rules that bind this desk

1. **P-01** No operator odds page is fetched before that operator's terms are read and recorded.
2. **P-05** A residual is never published without the market value it was subtracted from.
3. **LB-01** No backtest performance figure appears on the leaderboard, in any column, ever.
4. **LB-02** Ranking uses benchmark-relative Brier skill with a game-cluster lower bound and a
   multiplicity adjustment; win rate and ROI are not ranking metrics.
5. **LB-03** Signal and staking are scored separately and neither may be inferred from the other.
6. **D-01** A live strategy returns to paper when any demotion trigger fires.
7. **Rejections, in writing:** depth from jersey number, experience or salary; ranking by season-long
   ROI; a backtest number on the leaderboard; an inferred replacement presented as a named one.

## 7. Reproducibility contract

`python3 pipeline.py && python3 build.py && python3 verify.py && python3 -m unittest discover -s tests`
reproduces every page byte-for-byte from the raw extracts. The builder has no clock, no network and no
git access. `verify.py` runs 3,000+ checks including nine negative controls that prove it fails when a
market price is injected, a depth rank is invented, a row disappears, a source URL is blanked, a
performance figure is put on the leaderboard, or an internal link breaks.
