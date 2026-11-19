# PREREGISTRATION — desk 715e2cd4

**Status:** frozen. This file is committed to git *before* the evaluation window opens.
**Registration:** the commit that first added this file is the registration. Its hash is recorded
in `COORDINATION.md` and in `data/captures.csv`-adjacent notes; the file itself must never be edited
after the first scoring result is known.

| Field | Value |
|---|---|
| Rule set | `M1-ridge-offdef` plus strategies `S1`–`S6` |
| Registered at (UTC) | 2026-11-19T07:00Z |
| Evaluation window opens | 2026-11-22T18:00Z (Week 11 kickoff, Colts at Texans is 2026-11-19 — see note) |
| First scoring allowed | after the Week 11 finals are published as official |
| Holdout already consumed | Week 10, 2026 (14 finals) — scored once, results published, window closed |
| Variants registered | 6 strategies, 1 model spec, 4 ridge values (sensitivity only, 1 pre-registered) |
| Number of trials for multiplicity | 6 strategies + 1 model = 7 primary; 3 ridge sensitivity fits are reported and are not candidates |

> **Note on the window.** The first Week 11 fixture (Colts at Texans) kicks off 2026-11-19 20:15 ET,
> a few hours after this file was committed. Any origination for that fixture was therefore made
> *before* kickoff but also before the rest of the slate. The window is declared as the whole slate
> (2026-11-19 through 2026-11-23) and no fixture in it has been scored at registration time.

## Model `M1-ridge-offdef`

```
hp = mu + h/2 + off_H + def_A
ap = mu - h/2 + off_A + def_H
```

* `mu` = mean team points per game over the training corpus (plug-in moment, not fitted).
* `h`  = mean home margin over the training corpus (plug-in moment, not fitted).
* `off`, `def` = 32 + 32 parameters solved jointly by ridge regression with `lambda = 5.0` points²,
  using only the game graph (each game contributes the home club's offence against the away club's
  defence and vice versa).
* `sigma` = sd of the margin residuals on the training corpus. Moneyline: `P(home win) = Phi(margin/sigma)`.
* Origination order: **side → total → moneyline**.
* Totals are published twice: `A` = sum of the two fitted expected points, `B` = mean of the two clubs'
  average combined game total. **Decision rule:** an estimator may be dropped only after it loses to
  the other over ≥ 100 scored totals in the prospective window.

## Frozen gates (no gate may be moved after a result is seen)

| Gate | Requirement |
|---|---|
| G1 | 300 scored bets before provisional listing; ~5,773 to separate 55% from 52.4% at 80% power |
| G2 | The model beats its own pre-registered baseline on a chronological holdout |
| G3 | Benchmark-relative Brier skill with a game-cluster lower bound and a multiplicity adjustment over 7 trials |
| G4 | A dated, licensed operator price for every market claimed |
| G8 | A directly validated joint probability plus the operator's void/push rules before any combo is ranked |

## Frozen strategies

| ID | Division | Definition (verbatim, frozen) | Window | Gates |
|---|---|---|---|---|
| S1 | Singles | Bet the side when the model fair spread differs from the market spread by ≥ 1.5 pts | 2026 Wk 12–18 | G0,G1,G3,G4 |
| S2 | Singles | Home dog ≥ +7 and model total differs from market total by ≥ 3 pts → take the side on the total | 2026 Wk 12–18 | G0,G1,G3,G4 |
| S3 | Singles | Club off a bye when the model margin exceeds the market by ≥ 2 pts | 2026 Wk 12–18 | G0,G1,G3,G4 |
| S4 | Game parlays | Two-leg cross-game parlay, ranked only with a validated joint probability | after G8 | + G8 |
| S5 | Same-game parlays | Same-game legs (QB yards with a receiver's yards) | after G8 | + G8,G9 |
| S6 | Prop combos | Two-player prop combo from official box scores | after G8 | + G8,G9 |

**Demotion (also frozen):** a rolling 200-bet benchmark-relative lower bound of ≤ 0, mean CLV ≤ 0 over
100 consecutive bets, two consecutive calibration bins outside their intervals, or a parser drift alarm
each send a live strategy back to paper the same day.

## What is deliberately *not* registered

Nothing about depth, starters, replacements, snap counts, weather or injuries is in the model. There is
no verified availability feature to register, so registering one would be a promise the desk cannot keep.
Adding any such feature requires a **new** pre-registration and a new window; the frozen spec above must
not be silently extended.
