# data/ — provenance & regeneration

Every file here is either **transcribed from an official NFL page** (with per-row source links) or
**derived by a script from a pinned input** (reproducible). Community (non-official) inputs are
flagged — see [../docs/flagged.md](../docs/flagged.md).

## Transcribed (official NFL sources)

| File | Source | Method |
|---|---|---|
| `raw/standings_2026_reg.csv` | https://www.nfl.com/standings/league/2026/REG (fetched 2026-11-02) | transcribed; every row carries `source_url` |
| `raw/schedule_2026_wk9.csv` | https://www.nfl.com/schedules/2026/by-week/week-9 (fetched 2026-11-02) | transcribed; every row carries `source_url` (official game page) |
| `verified_official_results.csv` | nfl.com game pages (2025 Week 1: 16 games; 2026 Week 8: 13 finals) | transcribed from official schedule pages; every row carries the official game URL |

## Pinned community inputs (flagged F1/F2)

| File | Pin |
|---|---|
| `raw/spreadspoke_scores.csv` (1966–2025 wk5) | tobycrabtree/spreadspoke @ `1d309cb7f8f58a9eceb36293979dbcb1af70db94` — [file](https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv) |
| `raw/spreadspoke_teams.csv` | same repo/commit |
| play-by-play 2002–2013 (kept out of git; refetch via `../scripts/download_data.sh`) | brianfoshee/nfl-play-by-play-data @ `352c9c9b0bce0ffa8ce85681cf9ed50c0398f462` — [repo](https://github.com/brianfoshee/nfl-play-by-play-data) |

## Derived (regenerate with the scripts)

| File | Script | Contents |
|---|---|---|
| `base_rates.csv` | `scripts/compute_analysis.py` | cover/over/SU base rates, HFA, spread buckets, era splits |
| `correlation_bets.csv` | `scripts/compute_analysis.py` | same-game phi/Pearson correlations of bet outcomes |
| `correlation_parlays.csv` | `scripts/compute_analysis.py` | joint vs independent probabilities (SGP + cross-game) |
| `correlation_props.csv` | `scripts/compute_prop_correlations.py` | player-prop style correlations (QB/WR/RB/team) |
| `backtest_results.csv` | `scripts/compute_analysis.py` | pre-registered strategy backtests with gate verdicts |
| `luck_skill.csv` | `scripts/compute_analysis.py` | break-even rates, luck probabilities, power analysis |
| `model_lines_2026_wk9.csv` | `scripts/originate_lines.py` | our originated lines for 2026 Week 9 (market cols blank/flagged) |

## Data-integrity verification (2026-11-02)

* Dataset 2025 Week 1 scores vs official nfl.com game pages: **16/16 exact match** (sample check,
  see `verified_official_results.csv` and F6 in flagged list).
* Sign conventions validated statistically (favorite SU win rate 65.6%, favorite cover 48.1% excl.
  pushes — consistent with published NFL market behavior; pushes 2.8%).
* Ambiguous/malformed team-name rows excluded (never guessed) — F3 in flagged list.
* Non-numeric `over_under_line` values coerced out (never imputed) — F4 in flagged list.
