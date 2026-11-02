#!/usr/bin/env python3
"""
compute_analysis.py — base rates, bet-outcome correlations, backtests, luck/skill tables.

INPUT (pinned):
  data/raw/spreadspoke_scores.csv — tobycrabtree/spreadspoke @ 1d309cb7f8f58a9eceb36293979dbcb1af70db94
    (community dataset of NFL scores and closing lines; NOT an official NFL source — see docs/flagged.md)
OUTPUT (derived, reproducible by re-running this script):
  data/base_rates.csv, data/correlation_bets.csv, data/correlation_parlays.csv,
  data/backtest_results.csv, data/luck_skill.csv

Conventions (validated in session log, 2026-11-02):
  spread_favorite < 0  => favorite 'laying' |spread| points
  favorite covers  <=> fav_margin + spread_favorite > 0 (== 0 is a push)
  over hits        <=> total_points > over_under_line (== is a push)
"""
import json
import numpy as np
import pandas as pd
from scipy import stats

RAW = "data/raw/spreadspoke_scores.csv"
OUT = "data/"
SRC_DATASET = "https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv"
SRC_SCRIPT = "https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_analysis.py"

NAME2ABBR = {
    'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Colts': 'IND', 'Baltimore Ravens': 'BAL',
    'Boston Patriots': 'NE', 'Buffalo Bills': 'BUF', 'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE', 'Dallas Cowboys': 'DAL', 'Denver Broncos': 'DEN',
    'Detroit Lions': 'DET', 'Green Bay Packers': 'GB', 'Houston Oilers': 'TEN', 'Houston Texans': 'HOU',
    'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX', 'Kansas City Chiefs': 'KC',
    'Las Vegas': 'LV', 'Las Vegas Raiders': 'LV', 'Los Angeles Chargers': 'LAC', 'Los Angeles Raiders': 'LV',
    'Los Angeles Rams': 'LAR', 'Miami Dolphins': 'MIA', 'Minnesota Vikings': 'MIN',
    'New England': 'NE', 'New England Patriots': 'NE', 'New Orleans Saints': 'NO',
    'New York': 'AMBIG', 'New York Giants': 'NYG', 'New York Jets': 'NYJ', 'New York Jets (1p, ': 'NYJ',
    'Oakland Raiders': 'LV', 'Philadelphia Eagles': 'PHI', 'Phoenix Cardinals': 'ARI', 'Pittsburgh Steelers': 'PIT',
    'San Diego Chargers': 'LAC', 'San Francisco 49ers': 'SF', 'Seattle Seahawks': 'SEA', 'St. Louis Cardinals': 'ARI',
    'St. Louis Rams': 'LAR', 'Tampa Bay': 'TB', 'Tampa Bay Buccaneers': 'TB', 'Tennessee Oilers': 'TEN', 'Tennessee Titans': 'TEN',
    'Washington Commanders': 'WAS', 'Washington Football Team': 'WAS', 'Washington Redskins': 'WAS',
}

DIVISIONS = {
    'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'], 'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
    'AFC South': ['HOU', 'IND', 'JAX', 'TEN'], 'AFC West': ['DEN', 'KC', 'LAC', 'LV'],
    'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'], 'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
    'NFC South': ['ATL', 'CAR', 'NO', 'TB'], 'NFC West': ['ARI', 'LAR', 'SEA', 'SF'],
}
ABBR2DIV = {a: d for d, teams in DIVISIONS.items() for a in teams}


def wilson_ci(wins, n, z=1.959963984540054):
    if n == 0:
        return (np.nan, np.nan)
    p = wins / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (center - half, center + half)


def phi_binary(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def load_games():
    df = pd.read_csv(RAW)
    df['home_abbr'] = df.team_home.map(NAME2ABBR)
    df['away_abbr'] = df.team_away.map(NAME2ABBR)
    df['ou'] = pd.to_numeric(df.over_under_line, errors='coerce')
    df['spread'] = pd.to_numeric(df.spread_favorite, errors='coerce')
    df['is_playoff'] = df.schedule_playoff.map(lambda x: str(x).strip().upper() in ('TRUE', '1', 'YES'))
    g = df.dropna(subset=['score_home', 'score_away', 'spread', 'team_favorite_id', 'home_abbr', 'away_abbr']).copy()
    g = g[(g.home_abbr != 'AMBIG') & (g.away_abbr != 'AMBIG') & (g.team_favorite_id != 'PICK')].copy()
    g['margin_home'] = g.score_home - g.score_away
    g['total_points'] = g.score_home + g.score_away
    g['fav_is_home'] = g.team_favorite_id == g.home_abbr
    g['fav_margin'] = np.where(g.fav_is_home, g.margin_home, -g.margin_home)
    g['ats_margin'] = g.fav_margin + g.spread          # >0 favorite covers
    g['fav_cover'] = (g.ats_margin > 0).astype(int)
    g['fav_su'] = (g.fav_margin > 0).astype(int)
    g['home_su'] = (g.margin_home > 0).astype(int)
    g['home_dog'] = (~g.fav_is_home).astype(int)
    g['div_game'] = [ABBR2DIV.get(h) == ABBR2DIV.get(a) for h, a in zip(g.home_abbr, g.away_abbr)]
    g['tot_diff'] = g.total_points - g.ou
    g['over_hit'] = (g.tot_diff > 0).astype(int)
    return g


def sample_masks(g):
    """Pre-registered analysis windows (recorded in docs/research/validation-gates.md)."""
    base = g[(g.schedule_season >= 1980) & (g.schedule_season <= 2024) & (~g.is_playoff)]
    return {
        'full_1980_2024': base,
        'era_1980_1999': base[base.schedule_season <= 1999],
        'era_2000_2009': base[(base.schedule_season >= 2000) & (base.schedule_season <= 2009)],
        'era_2010_2019': base[(base.schedule_season >= 2010) & (base.schedule_season <= 2019)],
        'era_2020_2024': base[base.schedule_season >= 2020],
        'modern_2002_2024': base[base.schedule_season >= 2002],
    }


def main():
    g = load_games()
    S = sample_masks(g)
    full = S['full_1980_2024']

    # ---------------- base rates ----------------
    rows = []

    def add(metric, val, n, window, note=""):
        rows.append(dict(metric=metric, value=round(float(val), 4) if val == val else "",
                         n=int(n), window=window, note=note,
                         source_url=SRC_DATASET, source_dataset=SRC_DATASET, source_script=SRC_SCRIPT))
    for wname, w in S.items():
        nb = len(w)
        w_nopush = w[w.ats_margin != 0]
        t_nopush = w[w.tot_diff != 0]
        add('favorite_su_win_rate', w.fav_su.mean(), nb, wname)
        add('favorite_ats_cover_rate_excl_push', w_nopush.fav_cover.mean(), len(w_nopush), wname)
        add('ats_push_rate', (w.ats_margin == 0).mean(), nb, wname)
        add('over_rate_excl_push', t_nopush.over_hit.mean(), len(t_nopush), wname)
        add('total_push_rate', (w.tot_diff == 0).mean(), nb, wname)
        add('home_underdog_share', w.home_dog.mean(), nb, wname)
        hd = w[(w.home_dog == 1) & (w.ats_margin != 0)]
        add('home_underdog_ats_cover_rate', (hd.ats_margin < 0).mean(), len(hd), wname)
        rd = w[(w.home_dog == 0) & (w.ats_margin != 0)]
        add('home_favorite_ats_cover_rate', (rd.ats_margin > 0).mean(), len(rd), wname)
        add('mean_home_margin_pts', w.margin_home.mean(), nb, wname, 'HFA estimate (points)')
        add('mean_total_points', w.total_points.mean(), nb, wname)
        add('mean_closing_total_line', w.ou.mean(), nb, wname)
    buckets = [(-60, -9.5), (-9.5, -6.5), (-6.5, -3.5), (-3.5, -0.5)]
    for lo, hi in buckets:
        w = full[(full.spread >= lo) & (full.spread < hi) & (full.ats_margin != 0)]
        add(f'favorite_cover_rate_spread_[{lo},{hi})', w.fav_cover.mean(), len(w), 'full_1980_2024')
    pd.DataFrame(rows).to_csv(OUT + 'base_rates.csv', index=False)

    # ---------------- bet-outcome correlations (same game) ----------------
    crows = []

    def cadd(pair, value, n, window, kind, note=''):
        crows.append(dict(pair=pair, value=round(float(value), 4) if value == value else "",
                          n=int(n), window=window, kind=kind, note=note,
                          source_url=SRC_DATASET, source_dataset=SRC_DATASET, source_script=SRC_SCRIPT))
    for wname, w in S.items():
        sub = w[(w.ats_margin != 0) & (w.tot_diff != 0)]
        cadd('fav_cover_vs_over', phi_binary(sub.fav_cover, sub.over_hit), len(sub), wname, 'phi')
        cadd('fav_su_vs_over', phi_binary(sub.fav_su, sub.over_hit), len(sub), wname, 'phi')
        cadd('fav_cover_vs_fav_su', phi_binary(sub.fav_cover, sub.fav_su), len(sub), wname, 'phi')
        cadd('home_su_vs_over', phi_binary(sub.home_su, sub.over_hit), len(sub), wname, 'phi')
        cadd('home_dog_vs_over', phi_binary(sub.home_dog, sub.over_hit), len(sub), wname, 'phi')
        cadd('margin_home_vs_total_points', stats.pearsonr(sub.margin_home, sub.total_points)[0], len(sub), wname, 'pearson')
        cadd('ats_margin_vs_tot_diff', stats.pearsonr(sub.ats_margin, sub.tot_diff)[0], len(sub), wname, 'pearson')
    sub = full[(full.ats_margin != 0) & (full.tot_diff != 0)]
    for lbl, m in [('home_favorite', sub.fav_is_home), ('away_favorite', ~sub.fav_is_home)]:
        s = sub[m]
        cadd(f'fav_cover_vs_over|{lbl}', phi_binary(s.fav_cover, s.over_hit), len(s), 'full_1980_2024', 'phi')
    pd.DataFrame(crows).to_csv(OUT + 'correlation_bets.csv', index=False)

    # ---------------- parlay / SGP joint probabilities ----------------
    prows = []

    def padd(leg_a, leg_b, pa, pb, pab, n, window):
        prows.append(dict(leg_a=leg_a, leg_b=leg_b, p_a=round(pa, 4), p_b=round(pb, 4),
                          p_joint=round(pab, 4), p_independent=round(pa * pb, 4),
                          joint_over_independent=round(pab / (pa * pb), 4) if pa * pb > 0 else "",
                          n=int(n), window=window,
                          source_url=SRC_DATASET, source_dataset=SRC_DATASET, source_script=SRC_SCRIPT))
    for wname, w in S.items():
        sub = w[(w.ats_margin != 0) & (w.tot_diff != 0)]
        n = len(sub)
        hd_covers = ((sub.home_dog == 1) & (sub.ats_margin < 0)).astype(float)
        combos = [
            ('favorite_covers', 'over', sub.fav_cover, sub.over_hit),
            ('favorite_covers', 'under', sub.fav_cover, 1 - sub.over_hit),
            ('favorite_wins_su', 'over', sub.fav_su, sub.over_hit),
            ('home_underdog_covers', 'over', hd_covers, sub.over_hit),
            ('home_underdog_covers', 'under', hd_covers, 1 - sub.over_hit),
        ]
        for la, lb, ia, ib in combos:
            ia = np.asarray(ia, dtype=float)
            ib = np.asarray(ib, dtype=float)
            padd(la, lb, ia.mean(), ib.mean(), (ia * ib).mean(), n, wname)
    # cross-game independence check (2-leg parlay across different games, same week)
    sub = full[(full.ats_margin != 0) & (full.tot_diff != 0)].copy()
    sub['week_key'] = sub.schedule_season.astype(str) + '_' + sub.schedule_week.astype(str)
    pair_a, pair_b = [], []
    for _, wk in sub.groupby('week_key'):
        v = wk.fav_cover.values
        for i in range(len(v) - 1):
            pair_a.append(v[i])
            pair_b.append(v[i + 1])
    pair_a, pair_b = np.array(pair_a), np.array(pair_b)
    padd('favorite_covers(game_i)', 'favorite_covers(game_i+1)', pair_a.mean(), pair_b.mean(),
         (pair_a * pair_b).mean(), len(pair_a), 'full_1980_2024 (cross-game same-week pairs)')
    pd.DataFrame(prows).to_csv(OUT + 'correlation_parlays.csv', index=False)

    # ---------------- backtests (pre-registered signals) ----------------
    BREAKEVEN = 110 / 210  # 0.52381 at -110
    k_tests = 8            # pre-registered strategy variants (Bonferroni family)
    alpha_adj = 0.05 / k_tests

    def eval_strategy(name, s, win_cond, bet_side_desc, price_desc, win_expr):
        """win_cond: boolean Series aligned with s — True if the BET wins (pushes removed by caller)."""
        n = len(s)
        win = win_cond.values.astype(bool)
        wins = int(win.sum())
        losses = n - wins
        p = wins / n if n else np.nan
        unit = 1.10  # -110 flat
        roi = (wins * 1.0 - losses * unit) / n if n else np.nan
        lo, hi = wilson_ci(wins, n)
        pval = stats.binomtest(wins, n, BREAKEVEN, alternative='greater').pvalue if n else np.nan
        eras = {}
        for loy, hiy, lbl in [(1980, 1999, '1980-1999'), (2000, 2009, '2000-2009'), (2010, 2019, '2010-2019'), (2020, 2024, '2020-2024')]:
            e = win[(s.schedule_season >= loy).values & (s.schedule_season <= hiy).values]
            eras[lbl] = round(float(e.mean()), 4) if len(e) else ''
        gates = {
            'G1_sample_n_ge_200': n >= 200,
            'G2_significance_bonferroni': bool(pval == pval and pval < alpha_adj),
            'G4_sign_consistent_across_eras': all(v == '' or v > 0.5 for v in eras.values()),
        }
        return dict(
            strategy=name, bet_side=bet_side_desc, win_condition=win_expr,
            window='full_1980_2024 regular season',
            n_bets=n, wins=wins, losses=losses,
            win_rate_excl_push=round(p, 4) if p == p else '',
            win_rate_ci95_low=round(lo, 4) if lo == lo else '',
            win_rate_ci95_high=round(hi, 4) if hi == hi else '',
            modeled_roi_flat_stake=round(roi, 4) if roi == roi else '',
            breakeven_rate=round(BREAKEVEN, 4),
            binomial_p_vs_breakeven=round(float(pval), 5) if pval == pval else '',
            alpha_bonferroni_k8=round(alpha_adj, 5),
            era_win_rates=json.dumps(eras),
            gates_G1_G2_G4=('PASS' if all(gates.values()) else 'FAIL: ' + ','.join(k for k, v in gates.items() if not v)),
            assumption_price=price_desc,
            source_url=SRC_DATASET, source_dataset=SRC_DATASET, source_script=SRC_SCRIPT,
        )

    def subset(mask):
        s = full[mask].copy()
        return s

    strategies = []
    # S1: home underdog +points
    s1 = subset(full.home_dog == 1)
    s1p = s1[s1.ats_margin != 0]
    strategies.append(eval_strategy('S1_home_underdog_ats', s1p, (s1p.ats_margin < 0),
                                    'bet home underdog +points', '-110 flat (price not in source dataset)',
                                    'home underdog covers: ats_margin < 0'))
    # S2: home dog getting 7+
    s2 = subset((full.home_dog == 1) & (full.spread <= -7))
    s2p = s2[s2.ats_margin != 0]
    strategies.append(eval_strategy('S2_home_dog_ge7_ats', s2p, (s2p.ats_margin < 0),
                                    'bet home underdog getting 7+', '-110 flat (price not in source dataset)',
                                    'home underdog covers: ats_margin < 0'))
    # S3: home favorite laying 7+ (bet favorite)
    s3 = subset((full.home_dog == 0) & (full.spread <= -7))
    s3p = s3[s3.ats_margin != 0]
    strategies.append(eval_strategy('S3_home_fav_ge7_ats', s3p, (s3p.ats_margin > 0),
                                    'bet home favorite laying 7+', '-110 flat (price not in source dataset)',
                                    'favorite covers: ats_margin > 0'))
    # S4: over on low totals
    s4 = subset((full.ou <= 42) & full.ou.notna())
    s4p = s4[s4.tot_diff != 0]
    strategies.append(eval_strategy('S4_low_total_le42_over', s4p, (s4p.tot_diff > 0),
                                    'bet OVER when closing total <= 42', '-110 flat (price not in source dataset)',
                                    'total_points > over_under_line'))
    # S5: under on high totals
    s5 = subset((full.ou >= 49) & full.ou.notna())
    s5p = s5[s5.tot_diff != 0]
    strategies.append(eval_strategy('S5_high_total_ge49_under', s5p, (s5p.tot_diff < 0),
                                    'bet UNDER when closing total >= 49', '-110 flat (price not in source dataset)',
                                    'total_points < over_under_line'))
    # S6: divisional home dog
    s6 = subset((full.home_dog == 1) & full.div_game)
    s6p = s6[s6.ats_margin != 0]
    strategies.append(eval_strategy('S6_divisional_home_dog_ats', s6p, (s6p.ats_margin < 0),
                                    'bet divisional home underdog +points', '-110 flat (price not in source dataset)',
                                    'home underdog covers: ats_margin < 0'))
    # S7: road underdog getting 7+
    s7 = subset((full.home_dog == 0) & (full.spread <= -7))
    s7p = s7[s7.ats_margin != 0]
    strategies.append(eval_strategy('S7_road_dog_ge7_ats', s7p, (s7p.ats_margin < 0),
                                    'bet away underdog getting 7+', '-110 flat (price not in source dataset)',
                                    'favorite fails to cover: ats_margin < 0'))
    # S8: SGP combo — favorite covers AND over (2-leg same-game parlay)
    sub8 = full[(full.ats_margin != 0) & (full.tot_diff != 0)]
    n8 = len(sub8)
    win8 = ((sub8.fav_cover == 1) & (sub8.over_hit == 1)).values
    wins8 = int(win8.sum())
    p8 = wins8 / n8
    roi8 = (wins8 * 2.64 - (n8 - wins8) * 1.0) / n8
    lo8, hi8 = wilson_ci(wins8, n8)
    pval8 = stats.binomtest(wins8, n8, 100 / 364, alternative='greater').pvalue
    strategies.append(dict(
        strategy='S8_sgp_fav_covers_and_over', bet_side='2-leg same-game parlay: favorite ATS + over',
        win_condition='both legs hit: ats_margin>0 AND tot_diff>0',
        window='full_1980_2024 regular season', n_bets=n8, wins=wins8, losses=n8 - wins8,
        win_rate_excl_push=round(p8, 4), win_rate_ci95_low=round(lo8, 4), win_rate_ci95_high=round(hi8, 4),
        modeled_roi_flat_stake=round(roi8, 4), breakeven_rate=round(100 / 364, 4),
        binomial_p_vs_breakeven=round(float(pval8), 5), alpha_bonferroni_k8=round(alpha_adj, 5),
        era_win_rates=json.dumps({}), gates_G1_G2_G4=('PASS' if (n8 >= 200 and pval8 < alpha_adj) else 'FAIL: see p-value/sample'),
        assumption_price='2-leg parlay -110/-110 => +264 modeled payout (price not in source dataset)',
        source_url=SRC_DATASET, source_dataset=SRC_DATASET, source_script=SRC_SCRIPT))
    pd.DataFrame(strategies).to_csv(OUT + 'backtest_results.csv', index=False)

    # ---------------- luck vs skill ----------------
    lrows = []

    def ladd(**kw):
        lrows.append(dict(**kw, source_url=SRC_SCRIPT, source_script=SRC_SCRIPT))
    for price in [-105, -110, -115, -120, -125, -130]:
        be = abs(price) / (abs(price) + 100)
        ladd(table='breakeven_win_rate', parameter=f'price {price}', value=round(be, 4),
             detail=f'win rate needed to break even at {price}', basis='exact definition')
    ladd(table='breakeven_win_rate', parameter='2-leg parlay -110/-110 (+264)', value=round(100 / 364, 4),
         detail='joint hit rate needed to break even', basis='exact definition')
    ladd(table='breakeven_win_rate', parameter='3-leg parlay -110 x3 (+596)', value=round(100 / 696, 4),
         detail='joint hit rate needed to break even', basis='exact definition')
    for n in [50, 100, 200, 300, 500, 1000]:
        p_lucky = stats.binom.sf(int(np.ceil(0.55 * n)) - 1, n, BREAKEVEN)
        ladd(table='luck_probability', parameter=f'P(win_rate>=55% given true p=52.38%, n={n})',
             value=float('%.6g' % p_lucky),
             detail='probability a break-even bettor looks like a 55% handicapper',
             basis='exact binomial')
    for p_true in [0.53, 0.54, 0.55, 0.56]:
        p0 = BREAKEVEN
        z_a = stats.norm.ppf(0.95)
        z_b = stats.norm.ppf(0.80)
        num = (z_a * np.sqrt(p0 * (1 - p0)) + z_b * np.sqrt(p_true * (1 - p_true))) ** 2
        n_req = int(np.ceil(num / (p_true - p0) ** 2))
        ladd(table='required_sample_size', parameter=f'detect true p={p_true} vs {p0:.4f}',
             value=n_req, detail='one-sided alpha=0.05, power=0.80, normal approximation',
             basis='statistical power analysis (computed)')
    pd.DataFrame(lrows).to_csv(OUT + 'luck_skill.csv', index=False)

    print('base_rates rows:', len(rows))
    print('correlation rows:', len(crows), '+ parlays:', len(prows))
    print('strategies evaluated:', len(strategies))
    print('luck_skill rows:', len(lrows))
    print('HFA modern_2002_2024 (mean home margin):', round(S['modern_2002_2024'].margin_home.mean(), 3))


if __name__ == '__main__':
    main()
