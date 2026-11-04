# Methodology — NBA Signal Lab (session 6d508fee)

Everything here is implemented in `nba-signal-lab/compute.py` (stdlib-only, deterministic) and
covered by `nba-signal-lab/test_lab.py`. Parameters were fixed before looking at any result
(holdout discipline, gate G07) and are listed at the bottom with flags.

## 1. Team strength blend and model lines

For team i with `n_i` current-season games:

```
w_i      = n_i / (n_i + K_BLEND)                    # K_BLEND = 20
S_i      = w_i · net_cur_i + (1 − w_i) · net_pri_i  # net = +/- per game (official)
Tot_i    = w_i · (PF/g + PA/g)_cur + (1 − w_i) · (PF/g + PA/g)_pri
PF/g     = official PTS per game
PA/g     = PTS/g − (+/−)/g                          # documented derivation, ±0.1 rounding
```

For a game with home team h and away team a:

```
model home spread = S_h − S_a + HFA                 # HFA = 2.5 pts (flagged constant)
model total       = (Tot_h + Tot_a) / 2
```

Sensitivity: spreads are also published at HFA ∈ {2.0, 2.5, 3.0}. The empirical evidence for
HFA is the league home-win% computed from official HOME/ROAD splits (both seasons); no official
NBA source publishes HFA in points, so the constant is flagged (F-HFA). Market columns exist in
the schema but stay null (F-MARKET).

## 2. Correlation engine

Unit of analysis = player-game (n = 125). Pooled rows across the two tracked players; per-player
breakdowns always published so pooling is auditable.

- **Pearson r** with **Fisher-z 95% CI** for continuous pairs (PTS/REB/AST/3PM/MIN).
- **Point-biserial r** for PTS × WIN.
- **Phi** for pre-registered 0/1 prop thresholds (PTS≥25 & AST≥5, PTS≥25 & REB≥5,
  PTS≥25 & 3PM≥3, AST≥5 & REB≥5) + the 3-leg set PTS≥25 & AST≥5 & REB≥5.
  Each combo publishes P(A), P(B), P(A∩B), the independence product P(A)P(B), and the lift
  ratio — the same-game dependence input for parlay/SBP pricing (gate G06).
- **Lag-1 autocorrelation** of PTS in chronological order per player — the cross-game
  independence probe for multi-game parlays (gate G05).

Thresholds were chosen before computing (typical market prop lines: 25 pts, 5 ast, 5 reb,
3 threes) — they are not optimized on the data.

## 3. Luck-vs-skill engine

- **Break-even rate** p₀ = 110/210 = 0.5238 at a −110 price (arithmetic).
- **Power/sample size**: normal approximation to the binomial (documented; the exact-tail
  version is used for small-n checks and is computed in-repo in the log domain).
  Required n at α=0.05 one-sided, power 0.8: 55% → 2,243 bets; 57% → 719; 60% → 263.
- **Exact binomial tails** for concrete records (30-20, 28-22, 23-17, 60-40, 56-44) —
  P(X ≥ w | n, p₀).
- **Deflated scoring** (leaderboard): score = (wins + p₀·25) / (n + 25) − style; raw and
  deflated win rates both published; z vs break-even = (p̂ − p₀)/√(p₀(1−p₀)/n).
- **Multiple testing**: Šidák α* = 1−(1−0.05)^(1/m) and Bonferroni 0.05/m for m ∈ {5, 10, 25, 50}
  candidate strategies. Any future certification must survive the correction for the full m.

## 4. Validation gates (G01–G10)

| Gate | Rule | Enforced by |
|---|---|---|
| G01 Source | every input row has an official URL; unverified = blank+flag | tests + build |
| G02 Sample size | n ≥ 50 graded bets before skill claims | power table |
| G03 Break-even | deflated rate > 0.5238 at corrected α | luck engine |
| G04 Multiple testing | m counted, Šidák/Bonferroni applied | luck engine |
| G05 Independence | parlay independence only where lag checks support | correlations |
| G06 Correlation | same-game combos priced with phi, not marginals | correlations |
| G07 Holdout | parameters fixed pre-fit; no retuning on graded results | this document |
| G08 Market | grading only vs verified closing lines | BLOCKED (F-MARKET) |
| G09 Audit | pipeline reproducible; tests green | test_lab.py |
| G10 Luck-stripping | returns must survive deflation | luck engine |

## 5. Competition desk

Entries = the strategy catalog (singles, parlay, prop combos). Scoring: unit profit at −110
baseline; deflated score breaks ties by larger n then lower α consumed. Reward tiers 50/30/20
of the prize pool. Prize pool value is intentionally null (F-ODDS).

## 6. Parameters (all flagged as model choices)

| Name | Value | Role | Flag |
|---|---|---|---|
| K_BLEND | 20 | shrinkage prior weight in games | model choice |
| HFA_PTS | 2.5 | home advantage points | F-HFA |
| BREAK_EVEN | 0.5238 | −110 arithmetic | derived |
| DSR_PRIOR_N | 25 | deflation prior weight in bets | model choice |
| MARGIN_SIGMA | 11.2 | reserved for probit conversions | model constant |

## 7. Reproducibility

```
python3 nba-signal-lab/compute.py      # writes data/outputs.json (deterministic)
python3 nba-signal-lab/build.py        # writes the 11 site pages (deterministic)
python3 nba-signal-lab/test_lab.py     # 13 tests: determinism, identities, link coverage,
                                       # blank+flag discipline, structure
```

Integrity identities enforced on every run: PTS scoring identity, REB split identity,
W-L cross-page agreement, split sums, league Σ(W)=Σ(L), Σ(net×GP)=0, per-player checksums
against the official leaders page.
