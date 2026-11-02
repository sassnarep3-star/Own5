#!/usr/bin/env python3
"""
originate_lines.py — originate our own NFL lines for 2026 Week 9 from official inputs.

INPUTS (all official NFL sources, transcribed 2026-11-02 — see data/raw/*.csv source_url columns):
  data/raw/standings_2026_reg.csv   — official standings (W-L-T, PF, PA) through week 8
  data/raw/schedule_2026_wk9.csv    — official week-9 schedule
  data/base_rates.csv               — historical home-field advantage estimate (derived from pinned dataset)

MODEL (fully transparent — documented in docs/research/line-origination.md):
  rating(team)   = (PF - PA) / G                         # net points per game
  shrunk(team)   = rating * G / (G + 4)                  # empirical-Bayes shrinkage toward league avg (0)
  model_margin   = shrunk(home) - shrunk(away) + HFA     # HFA = 2.0 pts (2002-2024 mean home margin, rounded)
                                                       # HFA = 0 for neutral-site games (Madrid)
  model_total    = (PF_h/G_h + PA_a/G_a + PF_a/G_a + PA_h/G_h) / 2
  Lines rounded to nearest 0.5. Market line columns are intentionally BLANK — no official
  public source publishes market lines (see docs/flagged.md).

OUTPUT:
  data/model_lines_2026_wk9.csv
"""
import numpy as np
import pandas as pd

SRC_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
SRC_SCRIPT = "https://github.com/sassnarep3-star/Own5/blob/main/scripts/originate_lines.py"


def rhalf(x):
    return float(np.round(x * 2) / 2)


def main():
    st = pd.read_csv('data/raw/standings_2026_reg.csv')
    sc = pd.read_csv('data/raw/schedule_2026_wk9.csv')
    br = pd.read_csv('data/base_rates.csv')
    hfa_row = br[(br.metric == 'mean_home_margin_pts') & (br.window == 'modern_2002_2024')].iloc[0]
    HFA = rhalf(float(hfa_row.value))  # 2.0

    st['g'] = st.w + st.l + st.t
    st['rating'] = (st.pf - st.pa) / st.g
    st['shrunk'] = st.rating * st.g / (st.g + 4)
    st['ppg_scored'] = st.pf / st.g
    st['ppg_allowed'] = st.pa / st.g
    t = st.set_index('team_name')  # schedule uses full team names

    rows = []
    for _, g in sc.iterrows():
        away, home = g.away_team, g.home_team
        if away not in t.index or home not in t.index:
            raise KeyError(f'schedule team not found in standings: {away} / {home}')
        a = t.loc[away]
        h = t.loc[home]
        neutral = str(g.site_type).startswith('neutral')
        hfa = 0.0 if neutral else HFA
        margin = rhalf(h.shrunk - a.shrunk + hfa)  # >0 => home expected to win
        total = rhalf((h.ppg_scored + a.ppg_allowed + a.ppg_scored + h.ppg_allowed) / 2)
        if margin > 0:
            fav, dog, line = home, away, f'{home} -{margin:g}'
        elif margin < 0:
            fav, dog, line = away, home, f'{away} -{abs(margin):g}'
        else:
            fav, dog, line = 'pick', 'pick', 'PK'
        rows.append(dict(
            game_date=g.game_date, away_team=away, home_team=home,
            site_type=g.site_type, kickoff_et=g.kickoff_et,
            model_home_margin=margin, model_spread=line, model_total=total,
            model_favorite=fav, model_underdog=dog,
            market_spread='', market_total='',  # BLANK: no official market-line source exists
            inputs=f'official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA={HFA:g} (derived 2002-2024 mean home margin)',
            source_url=g.source_url, source_schedule=g.source_url, source_standings=SRC_STANDINGS, source_script=SRC_SCRIPT,
            verification_status='Model output (derived); market columns UNVERIFIED (blank per policy)',
        ))
    out = pd.DataFrame(rows)
    out.to_csv('data/model_lines_2026_wk9.csv', index=False)
    print(out[['game_date', 'away_team', 'home_team', 'model_spread', 'model_total']].to_string(index=False))
    print('\nHFA used:', HFA)


if __name__ == '__main__':
    main()
