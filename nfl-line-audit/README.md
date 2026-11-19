# NFL verified line desk — session `d6c404d4`

**Live:** https://sassnarep3-star.github.io/Own5/nfl-line-audit/
**Desk root:** `nfl-line-audit/` · **Research notes:** `research/nfl-d6c404d4/`

## The finding, first

Our own line loses to the closing line. Over 744 walk-forward games the model's Brier skill against the
de-vigged closing price is **−0.0782**; it is behind in the tune window (2023–24, −0.1064) and in the
holdout (2025–26, −0.0561). No strategy family certifies; two are significantly worse than the market after
Holm correction. Nothing is on the leaderboard because no prospective bet has settled.

One baseline reads positive — betting every over at the close returns +0.33% — because the closing total
sits 1.26 points below realised scoring (cluster CI 0.40–2.05). That is a market quirk, and the screen that
found it used the holdout, so it is published as a hypothesis to pre-register, not as a strategy.

## What is here

| File | What it is |
|---|---|
| `data/preregistration.json` | `REG-D6C404D4-V1`: frozen strategy families, gate, demotion triggers, data policy P-01. Hash-pinned by the verifier. |
| `engine/common.py`, `engine/model.py` | Statistics helpers and the opponent-adjusted, recency-weighted points-per-drive model. |
| `build_data.py` | Corpus, reconciliation, log audit, ratings, price snapshots, origination, walk-forward backtest, line-bias study, luck panel, availability delta, usage ranks, correlations, registers. ~33 s, deterministic. |
| `build_registers.py` | 71 requirements, 18 questions, 12 suggestions, 9 research rows, 14 sources, 15 flags. |
| `build_site.py`, `style.css` | 15 static pages. No JavaScript, no CDN, no build-time network. |
| `verify.py` | 80 checks: row counts, preregistration hash, 12 pinned-input hashes, per-row source links, no blanks where a blank would be an inference, no broken internal links, no placeholder text. |
| `captures/` | Timestamped official and operator reads. Never overwritten. |
| `../research/nfl-d6c404d4/` | Model card, backtest narrative, availability method, sources. |

## Reproduce

```
python3 nfl-line-audit/build_data.py
python3 nfl-line-audit/build_registers.py
python3 nfl-line-audit/build_site.py
python3 nfl-line-audit/verify.py        # exit 1 on any drift
```

## Rules this desk enforces in code, not prose

- No backtest column on the leaderboard (the verifier fails the build if one appears).
- No settled bet before kickoff (the verifier fails if any division claims one).
- No origination row without an input hash, a source link and an opening clock.
- No depth from jersey number, salary or experience: usage rank comes from playing time.
- No fixed points penalty for an absent starter; ablations instead.
- No marginal multiplication for parlays: same-game legs correlate at 0.513 (n=1,523).

## Data policy P-01

Row-level official NFL data is not republished. The desk publishes derived aggregates and links to the
official page; operator prices are quoted with the operator named and the read clock. Basis:
[NFL.com Terms §1.3](https://www.nfl.com/legal/terms/), read 2026-11-19.
