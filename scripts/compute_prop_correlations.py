#!/usr/bin/env python3
"""
compute_prop_correlations.py — same-game player-prop style correlations from archived play-by-play.

INPUT (pinned):
  /tmp/pbp/{2002..2012}_nfl_pbp_data.csv and /tmp/pbp2013.csv
  — brianfoshee/nfl-play-by-play-data @ 352c9c9b0bce0ffa8ce85681cf9ed50c0398f462
    (mirror of the advancedfootballanalytics.com play-by-play archive; community source, NOT official NFL — see docs/flagged.md)
  Fetch via scripts/download_data.sh (release CDN unreachable from sandbox; files live in repo tree).

OUTPUT (derived, reproducible):
  data/correlation_props.csv

Method notes (all documented in docs/research/correlation.md):
  * passing yards = sum of "for N yards" on completed pass plays (sacks excluded, per NFL convention)
  * rushing yards = sum of "for N yards" on rush/kneel plays
  * receiving yards = sum of "for N yards" credited to pass receiver
  * player-game aggregates restricted to team-games; QB = team's passer with most yards that game
  * 2-point conversions and no-gain plays handled conservatively (no-gain = 0 yards, 2pt excluded)
"""
import glob
import re
import numpy as np
import pandas as pd
from scipy import stats

SRC_DATA = "https://github.com/brianfoshee/nfl-play-by-play-data/blob/352c9c9b0bce0ffa8ce85681cf9ed50c0398f462/"
SRC_SCRIPT = "https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_prop_correlations.py"

PLAYER = r"([A-Z]\.[A-Za-z\.\'\-]+)"
YARDS = r"for (-?\d+) yards"
NOGAIN = r"for no gain"
PASS_RE = re.compile(PLAYER + r" pass .*? to " + PLAYER + r" .*?(?:" + YARDS + "|" + NOGAIN + r")")
SACK_RE = re.compile(PLAYER + r" sacked .*?(?:" + YARDS + "|" + NOGAIN + r")")
RUSH_RE = re.compile(PLAYER + r" (?:rushes|up the middle|left end|right end|left tackle|right tackle|left guard|right guard|scrambles|kneels).*?(?:" + YARDS + "|" + NOGAIN + r")")


def parse_plays(df):
    rows = []
    for gameid, off, desc in zip(df.gameid, df.off, df.description.fillna('')):
        if 'TWO-POINT CONVERSION' in desc or 'extra point' in desc.lower():
            continue
        m = PASS_RE.search(desc)
        if m:
            qb, wr = m.group(1), m.group(2)
            yds = int(m.group(3)) if m.group(3) else 0
            rows.append((gameid, off, qb, 'pass_yds', yds))
            rows.append((gameid, off, wr, 'rec_yds', yds))
            continue
        if SACK_RE.search(desc):
            continue  # excluded from pass & rush yardage
        m = RUSH_RE.search(desc)
        if m:
            pl = m.group(1)
            yds = int(m.group(2)) if m.group(2) else 0
            rows.append((gameid, off, pl, 'rush_yds', yds))
    return rows


def main():
    files = sorted(glob.glob('/tmp/pbp/2*_nfl_pbp_data.csv')) + ['/tmp/pbp2013.csv']
    all_rows = []
    finals = {}
    for f in files:
        df = pd.read_csv(f, usecols=['gameid', 'off', 'def', 'description', 'offscore', 'defscore'])
        all_rows.extend(parse_plays(df))
        # final score per game = last row's running scores
        last = df.groupby('gameid').tail(1)
        for gid, off, dfe, os_, ds_ in zip(last.gameid, last.off, last['def'], last.offscore, last.defscore):
            finals[gid] = {'off': off, 'def': dfe, 'off_score': float(os_), 'def_score': float(ds_)}
    plays = pd.DataFrame(all_rows, columns=['gameid', 'team', 'player', 'stat', 'yds'])
    agg = plays.groupby(['gameid', 'team', 'player', 'stat']).yds.sum().unstack(fill_value=0).reset_index()

    # final scores as team-game table
    tg = []
    for gid, v in finals.items():
        tg.append((gid, v['off'], v['off_score'], v['def_score']))
        tg.append((gid, v['def'], v['def_score'], v['off_score']))
    tg = pd.DataFrame(tg, columns=['gameid', 'team', 'points', 'opp_points'])
    tg['margin'] = tg.points - tg.opp_points
    tg['game_total'] = tg.points + tg.opp_points
    tg['team_pass_yds'] = pd.to_numeric(tg.set_index(['gameid', 'team']).index.map(
        plays[plays.stat == 'pass_yds'].groupby(['gameid', 'team']).yds.sum()), errors='coerce').astype(float)
    tg['team_rush_yds'] = pd.to_numeric(tg.set_index(['gameid', 'team']).index.map(
        plays[plays.stat == 'rush_yds'].groupby(['gameid', 'team']).yds.sum()), errors='coerce').astype(float)
    tg['team_pass_yds'] = tg['team_pass_yds'].fillna(0.0)
    tg['team_rush_yds'] = tg['team_rush_yds'].fillna(0.0)

    # QB / top WR / top RB per team-game
    qb = agg[agg.pass_yds > 0].sort_values('pass_yds').groupby(['gameid', 'team']).tail(1)
    qb = qb.rename(columns={'player': 'qb', 'pass_yds': 'qb_pass_yds'})[['gameid', 'team', 'qb', 'qb_pass_yds']]
    wr = agg[agg.rec_yds > 0].sort_values('rec_yds').groupby(['gameid', 'team']).tail(1)
    wr = wr.rename(columns={'player': 'wr', 'rec_yds': 'wr_rec_yds'})[['gameid', 'team', 'wr', 'wr_rec_yds']]
    rb = agg[agg.rush_yds > 0].sort_values('rush_yds').groupby(['gameid', 'team']).tail(1)
    rb = rb.rename(columns={'player': 'rb', 'rush_yds': 'rb_rush_yds'})[['gameid', 'team', 'rb', 'rb_rush_yds']]

    m = tg.merge(qb, on=['gameid', 'team'], how='left').merge(wr, on=['gameid', 'team'], how='left').merge(rb, on=['gameid', 'team'], how='left')
    m = m.fillna({'qb_pass_yds': 0, 'wr_rec_yds': 0, 'rb_rush_yds': 0})

    def corr(x, y, label, note='', min_filter=None):
        d = m
        if min_filter:
            col, thr = min_filter
            d = d[d[col] >= thr]
        a, b = d[x].values, d[y].values
        r, p = stats.pearsonr(a, b)
        return dict(pair=label, pearson_r=round(float(r), 4), p_value=float('%.3g' % p), n_team_games=len(d),
                    note=note, source_url=SRC_DATA, source_dataset=SRC_DATA, source_script=SRC_SCRIPT)

    rows = [
        corr('qb_pass_yds', 'points', 'QB_pass_yds_vs_team_points', 'QB passing prop vs team total', ('qb_pass_yds', 100)),
        corr('qb_pass_yds', 'game_total', 'QB_pass_yds_vs_game_total', 'QB passing prop vs game total', ('qb_pass_yds', 100)),
        corr('qb_pass_yds', 'margin', 'QB_pass_yds_vs_team_margin', 'game-script effect (negative when team trails -> more passing)', ('qb_pass_yds', 100)),
        corr('qb_pass_yds', 'wr_rec_yds', 'QB_pass_yds_vs_topWR_rec_yds', 'same-game prop combo legs (QB over + WR over)', ('qb_pass_yds', 100)),
        corr('wr_rec_yds', 'points', 'topWR_rec_yds_vs_team_points', 'WR receiving prop vs team total', ('wr_rec_yds', 50)),
        corr('rb_rush_yds', 'margin', 'topRB_rush_yds_vs_team_margin', 'RB rushing prop vs team margin (positive = winning script)', ('rb_rush_yds', 50)),
        corr('rb_rush_yds', 'game_total', 'topRB_rush_yds_vs_game_total', 'RB rushing prop vs game total', ('rb_rush_yds', 50)),
        corr('rb_rush_yds', 'points', 'topRB_rush_yds_vs_team_points', 'RB rushing prop vs team total', ('rb_rush_yds', 50)),
        corr('team_pass_yds', 'team_rush_yds', 'team_pass_yds_vs_team_rush_yds', 'negative: passing vs rushing game scripts'),
        corr('points', 'opp_points', 'team_points_vs_opponent_points', 'game-flow correlation for same-game team legs'),
        corr('team_pass_yds', 'points', 'team_pass_yds_vs_team_points', 'aggregate passing vs scoring'),
    ]
    pd.DataFrame(rows).to_csv('data/correlation_props.csv', index=False)
    print(pd.DataFrame(rows)[['pair', 'pearson_r', 'n_team_games']].to_string(index=False))
    print('team-games parsed:', len(m))


if __name__ == '__main__':
    main()
