#!/usr/bin/env python3
"""build_data.py — deterministic, stdlib-only data layer for desk 9e54d765.

Every output derives from
  (a) the transcriptions in inputs/ (each carrying the official URL and read stamp), or
  (b) committed repository inputs (the pinned games / snap-count / injury datasets and other
      desks' stamped captures), each named with its source class and hash.

No value is invented. Where a value cannot be read it stays empty and appears on
data/flagged.csv.
"""
import csv
import gzip
import hashlib
import json
import os

import engine as E
import registers_data as RD

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(HERE, 'data')
INPUTS = os.path.join(HERE, 'inputs')
os.makedirs(DATA, exist_ok=True)

READ_UTC = '2026-11-19T11:10:00Z'
STANDINGS_URL = 'https://www.nfl.com/standings/league/2026/REG'
SLATE_URL = 'https://www.nfl.com/schedules/2026/by-week/week-11'
WK10_URL = 'https://www.nfl.com/schedules/2026/by-week/week-10'
INJURY_URL = 'https://www.nfl.com/injuries/league/2026/reg11'
DK_URL = 'https://sportsbook.draftkings.com/leagues/football/nfl'
FD_URL = 'https://sportsbook.fanduel.com/navigation/nfl'
GAME_URL = 'https://www.nfl.com/games/{slug}'
CORPUS_PATH = os.path.join(REPO, 'data/decision-desk/raw/games.csv.gz')
SNAP_PATH = os.path.join(REPO, 'data/decision-desk/raw/snap_counts_2026.csv.gz')
PINNED_INJURY = {s: os.path.join(REPO, f'data/decision-desk/raw/injuries_{s}.csv.gz')
                 for s in (2023, 2024, 2025, 2026)}
CAP_1118 = os.path.join(REPO, 'data/nfl-desk-6cbf25fa/injury_reads/'
                              'capture_injuries_2026-11-18.csv')
CAP_1119_06 = os.path.join(REPO, 'data/nfl-desk-6e13b9ff/wk11_tnf_injury_2026-11-19.csv')
CAP_WK10_1112 = os.path.join(REPO, 'data/decision-desk/official/official_injuries_wk10.csv')
# The captured Week 10 file's own source_url column, verbatim — never a local path.
CAP_WK10_URL = 'https://www.nfl.com/injuries/'
CORPUS_URL = ('https://github.com/nflverse/nflverse-data/releases/download/schedules/'
              'games.csv.gz')

# Club print codes used by nfl.com standings: LA (Rams) and AZ (Cardinals). The pinned
# dataset prints LAR and ARI. The alias is applied once, here, and published so a reviewer
# can undo it.
ALIAS = {'LAR': 'LA', 'ARI': 'AZ'}


def unalias(code):
    return ALIAS.get(code, code)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_obj(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write_csv(name, fieldnames, rows):
    path = os.path.join(DATA, name)
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fieldnames})
    print(f'  wrote {name}: {len(rows)} rows')
    return path


# ------------------------------------------------------------------ input transcriptions
def load_standings():
    rows = []
    with open(os.path.join(INPUTS, 'standings_2026-11-19.txt')) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            p = line.split()
            rows.append({'club': p[0], 'w': int(p[1]), 'l': int(p[2]), 't': int(p[3]),
                         'pct': p[4], 'pf': int(p[5]), 'pa': int(p[6]), 'net': int(p[7])})
    return rows


def load_slate():
    rows = []
    with open(os.path.join(INPUTS, 'slate_week11_2026-11-19.txt')) as fh:
        for line in fh:
            line = line.rstrip('\n')
            if not line.strip() or line.startswith('#'):
                continue
            away, home, kick, net, neutral = line.split(',')
            rows.append({'away': away, 'home': home, 'kickoff': kick, 'network': net,
                         'neutral': neutral})
    return rows


def load_markets():
    out = {}
    with open(os.path.join(INPUTS, 'markets_week11_2026-11-19.txt')) as fh:
        for line in fh:
            if not line.strip() or line.startswith('#'):
                continue
            game, market, dk_a, dk_h, fd_a, fd_h = [x.strip() for x in line.split('|')]
            out.setdefault(game, {})[market] = {'DK': (dk_a, dk_h), 'FD': (fd_a, fd_h)}
    return out


def load_injuries():
    rows = []
    with open(os.path.join(INPUTS, 'injuries_week11_2026-11-19.txt')) as fh:
        for line in fh:
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.rstrip('\n').split('|')
            club, player, pos, inj, practice, status = parts[:6]
            rows.append({'club': club, 'player': player, 'position': pos, 'injury': inj,
                         'practice': practice, 'status': status})
    return rows


def load_week10_results():
    rows = []
    with open(os.path.join(INPUTS, 'results_week10_2026-11-19.txt')) as fh:
        for line in fh:
            if not line.strip() or line.startswith('#'):
                continue
            away, home, a, h, url = line.strip().split(',')
            rows.append({'away': away, 'home': home, 'away_score': int(a),
                         'home_score': int(h), 'url': url})
    return rows


def load_corpus():
    """REG games from the pinned dataset. Rows with no score are counted, never guessed."""
    games, blank = [], []
    with gzip.open(CORPUS_PATH, 'rt') as fh:
        for r in csv.DictReader(fh):
            if r['game_type'] != 'REG':
                continue
            try:
                a = int(r['away_score'])
                h = int(r['home_score'])
                week = int(r['week'])
                season = int(r['season'])
            except (TypeError, ValueError):
                blank.append({'season': r['season'], 'week': r['week'], 'date': r['gameday'],
                              'away': unalias(r['away_team']),
                              'home': unalias(r['home_team']),
                              'spread': r['spread_line'], 'total': r['total_line']})
                continue
            games.append({
                'season': season, 'week': week, 'date': r['gameday'],
                'away': unalias(r['away_team']), 'home': unalias(r['home_team']),
                'raw_away': r['away_team'], 'raw_home': r['home_team'],
                'away_score': a, 'home_score': h,
                'spread': r['spread_line'], 'total_line': r['total_line'],
                'away_ml': r['away_moneyline'], 'home_ml': r['home_moneyline'],
                'over_odds': r['over_odds'], 'under_odds': r['under_odds'],
                'away_spread_odds': r['away_spread_odds'],
                'home_spread_odds': r['home_spread_odds'],
                'div_game': r['div_game'], 'roof': r['roof'], 'surface': r['surface'],
                'temp': r['temp'], 'wind': r['wind'],
            })
    return games, blank


# ------------------------------------------------------------------------------ sources
def build_sources():
    rows = [
        dict(id='S01', name='NFL official league standings, 2026 regular season',
             url=STANDINGS_URL, read_utc=READ_UTC, source_class='OFFICIAL',
             used_for='32-club W/L/T and PF/PA reconciliation of the results log'),
        dict(id='S02', name='NFL official Week 11 schedule page',
             url=SLATE_URL, read_utc=READ_UTC, source_class='OFFICIAL',
             used_for='13 fixtures, kickoff as printed, network, neutral-site flag, bye clubs'),
        dict(id='S03', name='NFL official Week 10 schedule and results page',
             url=WK10_URL, read_utc=READ_UTC, source_class='OFFICIAL',
             used_for='14 Week 10 final scores, read today and appended to the log'),
        dict(id='S04', name='NFL official Week 11 injury report',
             url=INJURY_URL, read_utc=READ_UTC, source_class='OFFICIAL',
             used_for='253 designation rows, 24 clubs, 2 clubs printed "No Injuries Reported"'),
        dict(id='S05', name='DraftKings Sportsbook NFL game lines',
             url=DK_URL, read_utc='2026-11-19T11:00:00Z', source_class='NAMED-OPERATOR',
             used_for='spread, total and moneyline for the 13 Week 11 fixtures'),
        dict(id='S06', name='FanDuel Sportsbook NFL odds',
             url=FD_URL, read_utc='2026-11-19T11:01:00Z', source_class='NAMED-OPERATOR',
             used_for='second named-operator quote for the same 13 fixtures'),
        dict(id='S07', name='nflverse-data games.csv.gz (pinned in-repo dataset)',
             url=CORPUS_URL, read_utc='2026-11-19T11:22:00Z', source_class='PINNED-DATASET',
             used_for='7,103 scored REG games 1999-2026 for fitting and walk-forward '
                      'evaluation; reconciled to S01 for 2026'),
        dict(id='S08', name='nflverse-data snap counts 2026 (pinned in-repo dataset)',
             url='https://github.com/nflverse/nflverse-data/releases/download/snap_counts/'
                 'snap_counts.csv.gz', read_utc='2026-11-19T11:22:00Z',
             source_class='PINNED-DATASET',
             used_for='playing-time share as the depth/starter proxy and the join that tests '
                      'designation reliability'),
        dict(id='S09', name='nflverse-data injury reports 2023-2026 (pinned in-repo dataset)',
             url='https://github.com/nflverse/nflverse-data/releases/download/injuries/'
                 'injuries_{season}.csv.gz', read_utc='2026-11-19T11:22:00Z',
             source_class='PINNED-DATASET',
             used_for='multi-season designation rows for the reliability study and the '
                      'availability counts'),
        dict(id='S10', name='NFL Game Center, Colts at Texans, Week 11',
             url=GAME_URL.format(slug='colts-at-texans-2026-reg-11'), read_utc=READ_UTC,
             source_class='OFFICIAL',
             used_for='venue and stadium as printed (HOUSTON, TX / RELIANT STADIUM) and the '
                      'club injury blocks printed on the game page'),
        dict(id='S11', name='desk 6cbf25fa stamped capture (2026-11-18T03:55:13Z)',
             url=INJURY_URL, read_utc='2026-11-18T03:55:13Z', source_class='PRIOR-CAPTURE',
             used_for='the prior read for the two-clock delta; the file records that it '
                      'asked for reg11 and received reg10 content'),
        dict(id='S12', name='desk 6e13b9ff stamped capture (2026-11-19T06:57:28Z)',
             url=INJURY_URL, read_utc='2026-11-19T06:57:28Z', source_class='PRIOR-CAPTURE',
             used_for='the earlier read of the same day, used to measure intra-day drift'),
        dict(id='S13', name='decision-desk stamped Week 10 capture (2026-11-12T16:52:39Z)',
             url='https://www.nfl.com/injuries/league/2026/reg10',
             read_utc='2026-11-12T16:52:39Z', source_class='PRIOR-CAPTURE',
             used_for='the Week 10 designation set stamped before that week\'s first kickoff'),
    ]
    write_csv('sources.csv', ['id', 'name', 'url', 'read_utc', 'source_class', 'used_for'], rows)
    return rows


# ------------------------------------------------------------------------------ results
def build_results(games, official_standings, week10, blank):
    """The 2026 log: official finals where they exist, pinned scores elsewhere."""
    g26 = [g for g in games if g['season'] == 2026]
    rows = []
    for g in sorted(g26, key=lambda x: (x['week'], x['date'], x['away'])):
        res = 'home' if g['home_score'] > g['away_score'] else (
            'away' if g['away_score'] > g['home_score'] else 'tie')
        rows.append({
            'season': g['season'], 'week': g['week'], 'date': g['date'],
            'away': g['away'], 'home': g['home'], 'away_score': g['away_score'],
            'home_score': g['home_score'],
            'home_margin': g['home_score'] - g['away_score'],
            'total': g['home_score'] + g['away_score'], 'winner': res,
            'closing_spread_home': g['spread'], 'closing_total': g['total_line'],
            'score_source_class': 'PINNED-DATASET',
            'source_url': CORPUS_URL, 'score_source_url': CORPUS_URL,
            'reconciled_to': STANDINGS_URL,
            'note': 'pinned dataset score; the combined 2026 log is reconciled club by club '
                    'to the official standings in standings_reconciliation.csv'})
    for r in week10:
        rows.append({
            'season': 2026, 'week': 10, 'date': '2026-11-12..16',
            'away': r['away'], 'home': r['home'], 'away_score': r['away_score'],
            'home_score': r['home_score'],
            'home_margin': r['home_score'] - r['away_score'],
            'total': r['home_score'] + r['away_score'],
            'winner': 'home' if r['home_score'] > r['away_score'] else (
                'away' if r['away_score'] > r['home_score'] else 'tie'),
            'closing_spread_home': '', 'closing_total': '',
            'score_source_class': 'OFFICIAL',
            'source_url': WK10_URL, 'score_source_url': r['url'],
            'reconciled_to': STANDINGS_URL,
            'note': 'official Week 10 final read today; the pinned dataset prints no score for '
                    'this fixture at the pinned commit'})
    rows.sort(key=lambda r: (r['week'], r['date'], r['away']))
    write_csv('results_2026.csv',
              ['season', 'week', 'date', 'away', 'home', 'away_score', 'home_score',
               'home_margin', 'total', 'winner', 'closing_spread_home', 'closing_total',
               'score_source_class', 'source_url', 'score_source_url', 'reconciled_to',
               'note'], rows)

    # coverage of the pinned corpus, so the holes are published rather than discovered
    cov = {}
    for g in games:
        if g['season'] == 2026:
            d = cov.setdefault(g['week'], {'pinned_scored': 0, 'official_added': 0,
                                           'no_score_at_all': 0})
            d['pinned_scored'] += 1
    for b in blank:
        if b['season'] == '2026':
            d = cov.setdefault(int(b['week']), {'pinned_scored': 0, 'official_added': 0,
                                                'no_score_at_all': 0})
            d['no_score_at_all'] += 1
    for _ in week10:
        d = cov.setdefault(10, {'pinned_scored': 0, 'official_added': 0,
                                'no_score_at_all': 0})
        d['official_added'] += 1
        d['no_score_at_all'] -= 1
    crows = []
    for wk in sorted(cov):
        d = cov[wk]
        crows.append(dict(week=wk, pinned_scored=d['pinned_scored'],
                          official_added=d['official_added'],
                          no_score_at_all=d['no_score_at_all'],
                          total_games=d['pinned_scored'] + d['official_added']
                          + d['no_score_at_all'], source_url=CORPUS_URL))
    write_csv('corpus_coverage.csv',
              ['week', 'pinned_scored', 'official_added', 'no_score_at_all', 'total_games',
               'source_url'], crows)

    # reconciliation of the combined log against the official standings
    w, l, t, pf, pa, n = {}, {}, {}, {}, {}, {}
    for r in rows:
        for club, mine, theirs in ((r['home'], r['home_score'], r['away_score']),
                                   (r['away'], r['away_score'], r['home_score'])):
            n[club] = n.get(club, 0) + 1
            pf[club] = pf.get(club, 0) + mine
            pa[club] = pa.get(club, 0) + theirs
            if mine > theirs:
                w[club] = w.get(club, 0) + 1
            elif mine < theirs:
                l[club] = l.get(club, 0) + 1
            else:
                t[club] = t.get(club, 0) + 1
    srows, exact = [], 0
    for s in official_standings:
        c = s['club']
        got = (w.get(c, 0), l.get(c, 0), t.get(c, 0), pf.get(c, 0), pa.get(c, 0))
        want = (s['w'], s['l'], s['t'], s['pf'], s['pa'])
        ok = got == want
        exact += ok
        srows.append({'club': c, 'games_in_log': n.get(c, 0),
                      'log_w': got[0], 'official_w': want[0],
                      'log_l': got[1], 'official_l': want[1],
                      'log_t': got[2], 'official_t': want[2],
                      'log_pf': got[3], 'official_pf': want[3],
                      'log_pa': got[4], 'official_pa': want[4],
                      'pf_minus_official': got[3] - want[3],
                      'pa_minus_official': got[4] - want[4],
                      'match': 'yes' if ok else 'NO', 'source_url': STANDINGS_URL})
    srows.sort(key=lambda r: r['club'])
    write_csv('standings_reconciliation.csv',
              ['club', 'games_in_log', 'log_w', 'official_w', 'log_l', 'official_l', 'log_t',
               'official_t', 'log_pf', 'official_pf', 'log_pa', 'official_pa',
               'pf_minus_official', 'pa_minus_official', 'match', 'source_url'], srows)
    print(f'  reconciliation of the combined 2026 log: {exact}/{len(official_standings)} exact')

    prow, pexact = [], 0
    for s in official_standings:
        c = s['club']
        pw = pl = pt = ppf = ppa = 0
        for g in g26:
            if g['home'] == c:
                ppf += g['home_score']; ppa += g['away_score']
                pw += g['home_score'] > g['away_score']
                pl += g['home_score'] < g['away_score']
                pt += g['home_score'] == g['away_score']
            elif g['away'] == c:
                ppf += g['away_score']; ppa += g['home_score']
                pw += g['away_score'] > g['home_score']
                pl += g['away_score'] < g['home_score']
                pt += g['away_score'] == g['home_score']
        ok = (pw, pl, pt, ppf, ppa) == (s['w'], s['l'], s['t'], s['pf'], s['pa'])
        pexact += ok
        prow.append(dict(club=c, pinned_w=pw, official_w=s['w'], pinned_l=pl,
                         official_l=s['l'], pinned_pf=ppf, official_pf=s['pf'],
                         pinned_pa=ppa, official_pa=s['pa'],
                         match='yes' if ok else 'NO', source_url=STANDINGS_URL))
    write_csv('standings_pinned_only.csv',
              ['club', 'pinned_w', 'official_w', 'pinned_l', 'official_l', 'pinned_pf',
               'official_pf', 'pinned_pa', 'official_pa', 'match', 'source_url'], prow)
    print(f'  the pinned dataset alone reproduces {pexact}/{len(official_standings)} clubs')

    wrows = []
    corpus_wk10 = {f"{g['away']}_{g['home']}": g for g in g26 if g['week'] == 10}
    for r in week10:
        c = corpus_wk10.get(f"{r['away']}_{r['home']}")
        wrows.append(dict(away=r['away'], home=r['home'],
                          official_away_score=r['away_score'],
                          official_home_score=r['home_score'],
                          corpus_away_score=c['away_score'] if c else '',
                          corpus_home_score=c['home_score'] if c else '',
                          verdict='pinned dataset prints no score for this fixture' if c
                          else 'fixture absent from the pinned dataset',
                          source_url=r['url'], schedule_url=WK10_URL, read_utc=READ_UTC))
    write_csv('week10_reread.csv',
              ['away', 'home', 'official_away_score', 'official_home_score',
               'corpus_away_score', 'corpus_home_score', 'verdict', 'source_url',
               'schedule_url', 'read_utc'], wrows)
    print(f'  week-10 re-read: {len(week10)} official finals; the pinned dataset scored '
          f'{sum(1 for c in corpus_wk10.values() if c)} of them')
    return rows, exact, len(official_standings)


# ------------------------------------------------------------------------------ markets
def summarize_market(m):
    """Median-across-operators view of one fixture plus de-vigged market probabilities."""
    out = {}
    out['dk_home_spread'] = float(m['spread']['DK'][1].split()[0])
    out['fd_home_spread'] = float(m['spread']['FD'][1].split()[0])
    out['median_home_spread'] = (out['dk_home_spread'] + out['fd_home_spread']) / 2
    dk_total = float(m['total']['DK'][0].replace('O', '').split()[0])
    fd_total = float(m['total']['FD'][0].replace('O', '').split()[0])
    out['dk_total'], out['fd_total'] = dk_total, fd_total
    out['median_total'] = (dk_total + fd_total) / 2
    out['dk_home_ml'] = float(m['ml']['DK'][1])
    out['fd_home_ml'] = float(m['ml']['FD'][1])
    out['median_home_ml'] = (out['dk_home_ml'] + out['fd_home_ml']) / 2
    out['dk_away_ml'] = float(m['ml']['DK'][0])
    out['fd_away_ml'] = float(m['ml']['FD'][0])
    out['median_away_ml'] = (out['dk_away_ml'] + out['fd_away_ml']) / 2
    pk = E.devig_two_way(E.american_to_prob(out['dk_home_ml']),
                         E.american_to_prob(out['dk_away_ml']))
    pf = E.devig_two_way(E.american_to_prob(out['fd_home_ml']),
                         E.american_to_prob(out['fd_away_ml']))
    out['market_p_home'] = (pk + pf) / 2
    out['dk_spread_price_home'] = m['spread']['DK'][1].split()[1]
    out['dk_spread_price_away'] = m['spread']['DK'][0].split()[1]
    out['dk_total_price_over'] = m['total']['DK'][0].split()[1]
    out['dk_total_price_under'] = m['total']['DK'][1].split()[1]
    out['fd_total_price_over'] = m['total']['FD'][0].split()[1]
    out['fd_total_price_under'] = m['total']['FD'][1].split()[1]
    over_p = E.devig_two_way(E.american_to_prob(out['dk_total_price_over']),
                             E.american_to_prob(out['dk_total_price_under']))
    over_p2 = E.devig_two_way(E.american_to_prob(out['fd_total_price_over']),
                              E.american_to_prob(out['fd_total_price_under']))
    out['market_p_over'] = (over_p + over_p2) / 2
    return out


def build_slate_and_markets(slate, markets):
    snap_rows, consensus = [], {}
    for s in slate:
        gid = f"{s['away']}_{s['home']}"
        m = markets.get(gid, {})
        for market in ('spread', 'total', 'ml'):
            if market not in m:
                raise SystemExit(f'missing {market} for {gid} in the market transcription')
            for op, url, stamp in (('DK', DK_URL, '2026-11-19T11:00:00Z'),
                                   ('FD', FD_URL, '2026-11-19T11:01:00Z')):
                vals = m[market][op]
                if market == 'spread':
                    for side, raw in (('away', vals[0]), ('home', vals[1])):
                        num, price = raw.split()
                        snap_rows.append(dict(fixture=gid, market='side', side=side,
                                              operator=op, line=num, price=price,
                                              value_as_printed=raw, snapshot_role='OPEN',
                                              read_utc=stamp, source_url=url,
                                              closing_line='', closing_price=''))
                elif market == 'total':
                    for side, raw in (('over', vals[0]), ('under', vals[1])):
                        parts = raw.replace('O', '').replace('U', '').split()
                        snap_rows.append(dict(fixture=gid, market='total', side=side,
                                              operator=op, line=parts[0], price=parts[1],
                                              value_as_printed=raw, snapshot_role='OPEN',
                                              read_utc=stamp, source_url=url,
                                              closing_line='', closing_price=''))
                else:
                    for side, raw in (('away', vals[0]), ('home', vals[1])):
                        snap_rows.append(dict(fixture=gid, market='moneyline', side=side,
                                              operator=op, line='', price=raw,
                                              value_as_printed=raw, snapshot_role='OPEN',
                                              read_utc=stamp, source_url=url,
                                              closing_line='', closing_price=''))
        consensus[gid] = summarize_market(m)
    write_csv('market_snapshots.csv',
              ['fixture', 'market', 'side', 'operator', 'line', 'price', 'value_as_printed',
               'snapshot_role', 'read_utc', 'source_url', 'closing_line', 'closing_price'],
              snap_rows)
    write_csv('closing_policy.csv',
              ['snapshot_role', 'status', 'reason', 'clear_by', 'source_url'],
              [dict(snapshot_role='CLOSE', status='NOT READ',
                    reason='the closing number exists only at kickoff; the 13 fixtures kick off '
                           'from 2026-11-19T20:15 ET onward, after this build',
                    clear_by='one capture at kickoff minus 10 minutes per fixture, stamped and '
                             'hashed; the column stays empty until then',
                    source_url=SLATE_URL)])
    return consensus


def ratings_ref(ratings):
    return {'fit': 'ridge additive ratings on REG games 2020-2026 strictly before week 11 of '
                   '2026', 'n_games': ratings.n_games, 'mu': round(ratings.mu, 4),
            'home_field': round(ratings.hfa, 4),
            'sigma_margin': round(ratings.sigma_margin, 4),
            'sigma_total': round(ratings.sigma_total, 4)}


def build_origination(slate, consensus, ratings):
    rows, order = [], 0
    for s in slate:
        gid = f"{s['away']}_{s['home']}"
        c = consensus[gid]
        home, away = s['home'], s['away']
        margin_model = ratings.expected_margin(home, away)
        total_model = ratings.expected_total(home, away)
        fair_spread_home = -round(margin_model * 2) / 2      # printer's convention
        fair_total = round(total_model * 2) / 2
        p_home = ratings.p_home_win(home, away)
        fair_ml_home = E.prob_to_american(p_home)
        fair_ml_away = E.prob_to_american(1 - p_home)
        p_over = ratings.p_over(home, away, c['median_total'])
        inputs = {'fixture': gid, 'home': home, 'away': away,
                  'ratings_ref': ratings_ref(ratings), 'market_total': c['median_total']}
        base = dict(game_id=gid, week=11, away=away, home=home, neutral_site=s['neutral'],
                    kickoff_as_printed=s['kickoff'], network_as_printed=s['network'],
                    market_n_books=2,
                    market_source='median of 2 named operators (DraftKings, FanDuel)',
                    inputs_sha256=sha256_obj(inputs), opened_utc='2026-11-19T11:30:00Z',
                    source_url=SLATE_URL, market_url=f'{DK_URL} ; {FD_URL}')
        for mkt, side, fair, prob, mline in (
                ('side', 'home', fair_spread_home, p_home, c['median_home_spread']),
                ('total', 'over', fair_total, p_over, c['median_total']),
                ('moneyline', 'home', fair_ml_home, p_home, c['median_home_ml']),
                ('moneyline', 'away', fair_ml_away, 1 - p_home, c['median_away_ml'])):
            order += 1
            note = {
                'side': "fair spread is the model's expected home margin sign-flipped into the "
                        "printer's convention (favourite negative); market_line is the median "
                        "operator home spread; difference is fair minus market in points",
                'total': "fair total from the same ratings; probability is P(total above the "
                         "operator total) under the measured total dispersion",
                'moneyline': "fair moneyline is the model probability converted to an American "
                             "price; market_line is the median operator price; difference is "
                             "fair minus market in American points",
            }[mkt]
            rows.append(dict(base, market_order=order, market=mkt, side=side,
                             fair_line=fair, probability=round(prob, 6), market_line=mline,
                             difference_fair_minus_market=round(fair - mline, 2), note=note))
    write_csv('origination_week11.csv',
              ['game_id', 'week', 'away', 'home', 'neutral_site', 'kickoff_as_printed',
               'network_as_printed', 'market_n_books', 'market_source', 'inputs_sha256',
               'opened_utc', 'source_url', 'market_url', 'market_order', 'market', 'side',
               'fair_line', 'probability', 'market_line', 'difference_fair_minus_market',
               'note'], rows)
    return rows


def build_ratings_table(ratings, source_url):
    rows = []
    for club in sorted(ratings.teams):
        rows.append(dict(club=club, off_points=round(ratings.off[club], 3),
                         def_points_allowed=round(ratings.deff[club], 3),
                         off_minus_def=round(ratings.off[club] - ratings.deff[club], 3),
                         source_url=source_url,
                         note='fitted in-repo from the pinned scored game log; not an official '
                              'NFL rating; positive def_points_allowed means points allowed '
                              'above the league mean'))
    write_csv('ratings_2026.csv',
              ['club', 'off_points', 'def_points_allowed', 'off_minus_def', 'source_url',
               'note'], rows)


# ------------------------------------------------------------------------ walk forward
BENCHMARK_URL = CORPUS_URL
FIELDS_WF = ['season', 'week', 'date', 'away', 'home', 'away_score', 'home_score', 'home_win',
             'p_model', 'p_base_rate', 'p_random', 'p_market_ml', 'p_market_spread',
             'p_favourite_only', 'p_model_total_over', 'p_market_over', 'total_result_over',
             'sigma_margin', 'n_fit_games', 'closing_spread_home', 'closing_total', 'cluster']


def expanding_home_rate(games, season, week):
    hw = n = 0
    for g in games:
        if (g['season'], g['week']) < (season, week):
            if g['home_score'] == g['away_score']:
                continue
            n += 1
            hw += g['home_score'] > g['away_score']
    return hw / n if n else 0.5


def unscored(g):
    return {'season': g['season'], 'week': g['week'], 'date': g['date'], 'away': g['away'],
            'home': g['home'], 'away_score': g['away_score'], 'home_score': g['home_score'],
            'home_win': '', 'p_model': '', 'p_base_rate': '', 'p_random': 0.5,
            'sigma_margin': '', 'n_fit_games': '', 'closing_spread_home': g['spread'],
            'closing_total': g['total_line'], 'p_market_ml': '', 'p_market_spread': '',
            'p_favourite_only': '', 'p_model_total_over': '', 'p_market_over': '',
            'total_result_over': '', 'cluster': f"{g['season']}-W{int(g['week']):02d}"}


def walk_forward(games):
    """Score every game from 2006 on with parameters fitted only on prior weeks."""
    teams = sorted({g['away'] for g in games} | {g['home'] for g in games})
    by_season = {}
    for g in games:
        by_season.setdefault(g['season'], []).append(g)
    rows = []
    for season in sorted(by_season):
        prior = [g for g in games if g['season'] < season]
        if len(prior) < 400:
            for g in by_season[season]:
                rows.append(unscored(g))
            continue
        fits = {}
        for g in sorted(by_season[season], key=lambda x: (x['week'], x['date'])):
            wk = g['week']
            if wk not in fits:
                train = prior + [p for p in by_season[season] if p['week'] < wk]
                fits[wk] = E.fit_ratings(train, teams, ridge=3.0, seasons_used=6)
            r = fits[wk]
            rec = {'season': season, 'week': wk, 'date': g['date'], 'away': g['away'],
                   'home': g['home'], 'away_score': g['away_score'],
                   'home_score': g['home_score'],
                   'home_win': 1 if g['home_score'] > g['away_score'] else (
                       0 if g['home_score'] < g['away_score'] else ''),
                   'p_model': round(r.p_home_win(g['home'], g['away']), 6),
                   'p_base_rate': round(expanding_home_rate(games, season, wk), 6),
                   'p_random': 0.5, 'sigma_margin': round(r.sigma_margin, 3),
                   'n_fit_games': r.n_games, 'closing_spread_home': g['spread'],
                   'closing_total': g['total_line'],
                   'cluster': f'{season}-W{wk:02d}'}
            if g['home_ml'] and g['away_ml']:
                try:
                    rec['p_market_ml'] = round(E.devig_two_way(
                        E.american_to_prob(float(g['home_ml'])),
                        E.american_to_prob(float(g['away_ml']))), 6)
                except (ValueError, ZeroDivisionError):
                    rec['p_market_ml'] = ''
            else:
                rec['p_market_ml'] = ''
            if g['spread']:
                sp = float(g['spread'])
                # spread_line is stored HOME-FAVOURED POSITIVE (measured in sign_convention.csv)
                rec['p_market_spread'] = round(E.norm_cdf(sp / r.sigma_margin), 6)
                rec['p_favourite_only'] = 0.75 if sp >= 3 else (0.25 if sp <= -3 else 0.5)
                rec['p_model_total_over'] = round(
                    r.p_over(g['home'], g['away'], float(g['total_line'])), 6) \
                    if g['total_line'] else ''
            else:
                rec['p_market_spread'] = ''
                rec['p_favourite_only'] = ''
                rec['p_model_total_over'] = ''
            if g['over_odds'] and g['under_odds'] and g['total_line']:
                try:
                    rec['p_market_over'] = round(E.devig_two_way(
                        E.american_to_prob(float(g['over_odds'])),
                        E.american_to_prob(float(g['under_odds']))), 6)
                except (ValueError, ZeroDivisionError):
                    rec['p_market_over'] = ''
                tot = g['home_score'] + g['away_score']
                line = float(g['total_line'])
                rec['total_result_over'] = 1 if tot > line else (0 if tot < line else '')
            else:
                rec['p_market_over'] = ''
                rec['total_result_over'] = ''
            rows.append(rec)
    return rows


def rows_brier(rows, idx):
    return E.brier([r[idx] for r in rows], [r[3] for r in rows])


def stake_moneyline(scored, col='p_model'):
    """Flat 1-unit bets at the de-vigged fair price when the model disagrees by > 2 points."""
    bets = []
    for r in scored:
        if r['p_market_ml'] == '' or r.get(col) in ('', None):
            continue
        p, pm = float(r[col]), float(r['p_market_ml'])
        edge = p - pm
        if abs(edge) < 0.02:
            continue
        side_home = edge > 0
        price = 1.0 / pm if side_home else 1.0 / (1 - pm)
        win = (r['home_win'] == 1) if side_home else (r['home_win'] == 0)
        bets.append((r['cluster'], (price - 1.0) if win else -1.0))
    if not bets:
        return {'n': 0, 'roi': 0.0, 'lo': 0.0, 'hi': 0.0}
    groups = {}
    for k, v in bets:
        groups.setdefault(k, []).append(v)
    point = sum(v for _, v in bets) / len(bets)
    rng = E.Lcg(20261119)
    keys = list(groups)
    stats = []
    for _ in range(2000):
        acc = []
        for _ in range(len(keys)):
            acc.extend(groups[keys[rng.below(len(keys))]])
        stats.append(sum(acc) / len(acc))
    return {'n': len(bets), 'roi': point, 'lo': E.quantile(stats, 0.025),
            'hi': E.quantile(stats, 0.975)}


def build_backtest(wf):
    scored = [r for r in wf if r['home_win'] != '' and r['p_model'] != '']
    seasons = sorted({r['season'] for r in scored})
    holdout = seasons[-2:]
    print(f'  scored games: {len(scored)}; holdout {holdout}')
    families = [
        ('F2_RANDOM', 'p_random', 'P = 0.5 on every game — control',
         'nothing; this is the definition of no skill'),
        ('F1_LEAGUE_BASE', 'p_base_rate', 'expanding league home-win rate — control',
         'the league drifts away from its long-run home-win rate'),
        ('F3_FAVOURITE_ONLY', 'p_favourite_only', 'take the side of the closing spread — control',
         'large closing favourites stop winning at the rate the spread implies'),
        ('F4_OPPONENT_AWARE', 'p_model', 'opponent-aware ridge ratings (offence, defence, '
                                         'home field) fitted on prior weeks only',
         'opponent adjustment stops adding information beyond the league base rate'),
        ('F5_MARKET_LINE_BENCHMARK', 'p_market_spread',
         'the closing spread turned into a probability with the model dispersion — benchmark',
         'the market view of the same game is mis-scaled by the measured dispersion'),
    ]
    out = []
    for name, col, desc, mind in families:
        rows = [(r['cluster'], float(r[col]), float(r['p_market_ml']), float(r['home_win']))
                for r in scored if r.get(col) not in ('', None) and r['p_market_ml'] != '']
        skill = E.cluster_bootstrap_skill(rows)
        rows2 = [(r['cluster'], float(r[col]), float(r['p_base_rate']), float(r['home_win']))
                 for r in scored if r.get(col) not in ('', None)]
        skill2 = E.cluster_bootstrap_skill(rows2, reps=1000)
        hold_rows = [t for t in rows if int(t[0].split('-W')[0]) in holdout]
        hold_skill = E.cluster_bootstrap_skill(hold_rows, reps=1000) if hold_rows else None
        bets = stake_moneyline(scored, col) if name == 'F4_OPPONENT_AWARE' else None
        out.append({'family': name, 'description': desc, 'market': 'side (P home win)',
                    'n_games': skill['n_games'], 'n_clusters': skill['n_clusters'],
                    'brier_model': round(rows_brier(rows, 1), 6),
                    'brier_benchmark': round(rows_brier(rows, 2), 6),
                    'brier_skill_vs_close': round(skill['point'], 6),
                    'skill_lo95': round(skill['lo'], 6), 'skill_hi95': round(skill['hi'], 6),
                    'brier_skill_vs_base_rate': round(skill2['point'], 6),
                    'skill_vs_base_lo95': round(skill2['lo'], 6),
                    'holdout_seasons': ' '.join(str(s) for s in holdout),
                    'holdout_brier_skill': round(hold_skill['point'], 6) if hold_skill else '',
                    'holdout_lo95': round(hold_skill['lo'], 6) if hold_skill else '',
                    'n_bets': bets['n'] if bets else '',
                    'staking_roi': round(bets['roi'], 6) if bets else '',
                    'staking_roi_lo95': round(bets['lo'], 6) if bets else '',
                    'staking_roi_hi95': round(bets['hi'], 6) if bets else '',
                    'what_would_change_our_mind': mind,
                    'source_url': BENCHMARK_URL})
    pvals = []
    for r in out:
        se = (r['skill_hi95'] - r['skill_lo95']) / (2 * 1.96)
        z = r['brier_skill_vs_close'] / se if se > 0 else 0.0
        pvals.append(E.normal_two_sided_p(z))
    adj = E.holm(pvals)
    for r, p, pa in zip(out, pvals, adj):
        r['p_value_vs_close'] = round(p, 6)
        r['p_holm'] = round(pa, 6)
        r['certified'] = 'no'
    write_csv('backtest_families.csv',
              ['family', 'description', 'market', 'n_games', 'n_clusters', 'brier_model',
               'brier_benchmark', 'brier_skill_vs_close', 'skill_lo95', 'skill_hi95',
               'brier_skill_vs_base_rate', 'skill_vs_base_lo95', 'holdout_seasons',
               'holdout_brier_skill', 'holdout_lo95', 'n_bets', 'staking_roi',
               'staking_roi_lo95', 'staking_roi_hi95', 'p_value_vs_close', 'p_holm',
               'certified', 'what_would_change_our_mind', 'source_url'], out)

    trows = [(r['cluster'], float(r['p_model_total_over']), float(r['p_market_over']),
              float(r['total_result_over'])) for r in scored
             if r['p_model_total_over'] != '' and r['p_market_over'] != ''
             and r['total_result_over'] != '']
    tskill = E.cluster_bootstrap_skill(trows, reps=1000)
    write_csv('backtest_totals.csv',
              ['family', 'market', 'n_games', 'brier_model', 'brier_benchmark',
               'brier_skill_vs_close', 'skill_lo95', 'skill_hi95',
               'what_would_change_our_mind', 'source_url'],
              [{'family': 'F6_TOTAL_OPPONENT_AWARE', 'market': 'total (P over)',
                'n_games': tskill['n_games'],
                'brier_model': round(rows_brier(trows, 1), 6),
                'brier_benchmark': round(rows_brier(trows, 2), 6),
                'brier_skill_vs_close': round(tskill['point'], 6),
                'skill_lo95': round(tskill['lo'], 6), 'skill_hi95': round(tskill['hi'], 6),
                'what_would_change_our_mind': 'the total model stops losing to the de-vigged '
                                              'over price',
                'source_url': BENCHMARK_URL}])

    per = []
    for s in seasons:
        sub = [r for r in scored if r['season'] == s and r['p_market_ml'] != '']
        if not sub:
            continue
        m = E.brier([r['p_model'] for r in sub], [float(r['home_win']) for r in sub])
        b = E.brier([r['p_market_ml'] for r in sub], [float(r['home_win']) for r in sub])
        per.append({'season': s, 'n_games': len(sub), 'brier_model': round(m, 6),
                    'brier_market': round(b, 6), 'brier_skill': round(1 - m / b, 6),
                    'holdout': 'yes' if s in holdout else 'no', 'source_url': BENCHMARK_URL})
    write_csv('backtest_by_season.csv',
              ['season', 'n_games', 'brier_model', 'brier_market', 'brier_skill', 'holdout',
               'source_url'], per)
    return out, holdout


def build_luck(wf, families):
    scored = [r for r in wf if r['home_win'] != '']
    n = len(scored)
    wins = sum(1 for r in scored if r['home_win'] == 1)
    p, lo, hi = E.wilson(wins, n)
    be = E.devig_two_way(E.american_to_prob(-110), E.american_to_prob(-110))
    z_a, z_b = E.norm_ppf(0.975), E.norm_ppf(0.80)

    def n_needed(p1, p0):
        return ((z_a * ((p0 * (1 - p0)) ** 0.5) + z_b * ((p1 * (1 - p1)) ** 0.5))
                / (p1 - p0)) ** 2

    f4 = next(f for f in families if f['family'] == 'F4_OPPONENT_AWARE')
    rows = [
        dict(panel='A_home_win_base_rate', value=round(p, 6), lo=round(lo, 6),
             hi=round(hi, 6), n=n, method='Wilson interval on the empirical home-win rate',
             interpretation='at this n the interval is about one point wide, so a season-long '
                            'win rate cannot separate a good process from a lucky one',
             source_url=BENCHMARK_URL),
        dict(panel='B_breakeven_probability', value=round(be, 6), lo='', hi='', n='',
             method='two-way -110 de-vigged proportionally',
             interpretation='the probability a flat bettor must exceed to break even at -110',
             source_url='https://sportsbook.draftkings.com/help/general-betting-rules/'
                        'general-rules'),
        dict(panel='C_bets_to_prove_55pct', value=round(n_needed(0.55, be)), lo='', hi='',
             n='', method='two-proportion power calculation, 95% one-sided, 80% power',
             interpretation='this many settled bets are needed before a 55% win rate is '
                            'distinguishable from break-even',
             source_url='https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5496353/'),
        dict(panel='D_bets_to_prove_54pct', value=round(n_needed(0.54, be)), lo='', hi='',
             n='', method='same calculation at 54%',
             interpretation='the sample a leaderboard needs before its ranking means anything',
             source_url='https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5496353/'),
        dict(panel='E_model_vs_close_skill', value=f4['brier_skill_vs_close'],
             lo=f4['skill_lo95'], hi=f4['skill_hi95'], n=f4['n_games'],
             method='game-cluster bootstrap of the Brier skill ratio (2,000 resamples)',
             interpretation='the whole interval lies below zero, so the model is worse than the '
                            'close rather than merely unlucky',
             source_url=BENCHMARK_URL),
        dict(panel='F_signal_vs_staking_disagreement',
             value=f4['staking_roi'], lo=f4['staking_roi_lo95'], hi=f4['staking_roi_hi95'],
             n=f4['n_bets'],
             method='signal (Brier skill) and staking (flat ROI) published as two columns and '
                    'never blended',
             interpretation='here the staking ROI interval covers zero while the signal '
                            'interval sits below zero: the same strategy looks harmless on '
                            'staking and is clearly bad on signal, which is exactly why the '
                            'two must be separated',
             source_url=BENCHMARK_URL),
    ]
    write_csv('luck_panel.csv',
              ['panel', 'value', 'lo', 'hi', 'n', 'method', 'interpretation', 'source_url'],
              rows)
    return rows


def build_correlations(games, ratings, official_standings):
    rows = []
    pf = [s['pf'] for s in official_standings]
    pa = [s['pa'] for s in official_standings]
    net = [s['net'] for s in official_standings]
    r1, ci1, n1 = E.pearson(pf, pa)
    rows.append(dict(id='C01', pair='points_for vs points_against (club totals)',
                     r=round(r1, 4), ci_lo=round(ci1[0], 4), ci_hi=round(ci1[1], 4), n=n1,
                     source_class='OFFICIAL', source_url=STANDINGS_URL,
                     interpretation='no material relationship at n=32: a club scoring more does '
                                    'not systematically concede more'))
    r2, ci2, _ = E.pearson(net, pf)
    rows.append(dict(id='C02', pair='net_points vs points_for (club totals)', r=round(r2, 4),
                     ci_lo=round(ci2[0], 4), ci_hi=round(ci2[1], 4), n=len(official_standings),
                     source_class='OFFICIAL', source_url=STANDINGS_URL,
                     interpretation='net points is dominated by offence this season'))
    g26 = [g for g in games if g['season'] >= 2021]
    margins = [g['home_score'] - g['away_score'] for g in g26]
    totals = [g['home_score'] + g['away_score'] for g in g26]
    r3, ci3, n3 = E.pearson(margins, totals)
    rows.append(dict(id='C03', pair='game margin vs game total (same game)', r=round(r3, 4),
                     ci_lo=round(ci3[0], 4), ci_hi=round(ci3[1], 4), n=n3,
                     source_class='PINNED-DATASET', source_url=CORPUS_URL,
                     interpretation='small but not zero at n>1,000: the side and the total of '
                                    'one game are not independent, so a side+total parlay '
                                    'cannot be priced by multiplying marginals'))
    x = [ratings.off[g['home']] for g in g26]
    y = [ratings.off[g['away']] for g in g26]
    r4, ci4, n4 = E.pearson(x, y)
    rows.append(dict(id='C04', pair='home offence rating vs away offence rating (matchup)',
                     r=round(r4, 4), ci_lo=round(ci4[0], 4), ci_hi=round(ci4[1], 4), n=n4,
                     source_class='PINNED-DATASET', source_url=CORPUS_URL,
                     interpretation='the schedule pairs good offences with good offences about '
                                    'as often as chance allows; no dependence to exploit'))
    seasons = sorted({g['season'] for g in games})
    hv = []
    for s in seasons:
        gg = [g for g in games if g['season'] == s and g['home_score'] != g['away_score']]
        if gg:
            hv.append((s, sum(1 for g in gg if g['home_score'] > g['away_score']) / len(gg)))
    r5, ci5, n5 = E.pearson([s for s, _ in hv], [v for _, v in hv])
    rows.append(dict(id='C05', pair='season vs home-win rate (league, 1999-2026)',
                     r=round(r5, 4), ci_lo=round(ci5[0], 4), ci_hi=round(ci5[1], 4), n=n5,
                     source_class='PINNED-DATASET', source_url=CORPUS_URL,
                     interpretation='home advantage is drifting down in this window; it is a '
                                    'measured trend with n=28 seasons, not a stable constant'))
    write_csv('correlations.csv',
              ['id', 'pair', 'r', 'ci_lo', 'ci_hi', 'n', 'source_class', 'source_url',
               'interpretation'], rows)
    return rows


def build_sign_convention(games):
    """Measure which sign convention the pinned spread uses and publish the measurement."""
    g26 = [g for g in games if g['season'] == 2026 and g['spread']]
    teams = sorted({g['away'] for g in games} | {g['home'] for g in games})
    r = E.fit_ratings([g for g in games if g['season'] < 2026], teams)
    mae_pos = mae_neg = 0.0
    for g in g26:
        pm = r.expected_margin(g['home'], g['away'])
        sp = float(g['spread'])
        mae_pos += abs(sp - pm)        # H1: positive stored value = home favoured
        mae_neg += abs((-sp) - pm)     # H2: negative stored value = home favoured
    n = len(g26)
    allg = [g for g in games if g['spread'] and g['home_score'] != g['away_score']]
    rr, cci, nn = E.pearson([float(g['spread']) for g in allg],
                            [g['home_score'] - g['away_score'] for g in allg])
    rr_neg, cci_neg, nn_neg = E.pearson([-float(g['spread']) for g in allg],
                                        [g['home_score'] - g['away_score'] for g in allg])
    chosen = ('as_stored(home_favoured_positive)' if mae_pos < mae_neg
              else 'flipped(home_favoured_negative)')
    rows = [
        dict(convention='as_stored(home_favoured_positive)',
             interpretation='a positive stored value means the home club is favoured',
             mean_abs_error=round(mae_pos / n, 4), n=n),
        dict(convention='flipped(home_favoured_negative)',
             interpretation='a negative stored value means the home club is favoured',
             mean_abs_error=round(mae_neg / n, 4), n=n),
    ]
    for row in rows:
        as_stored = row['convention'].startswith('as_stored')
        row['chosen'] = 'yes' if row['convention'] == chosen else 'no'
        # the correlation under THIS row's own reading of the sign, not one number twice
        row['corr_stored_line_realised_home_margin'] = round(rr if as_stored else rr_neg, 4)
        row['corr_n'] = nn if as_stored else nn_neg
        c = cci if as_stored else cci_neg
        row['corr_ci'] = f'{c[0]:.4f} to {c[1]:.4f}'
        row['source_url'] = CORPUS_URL
    write_csv('sign_convention.csv',
              ['convention', 'interpretation', 'mean_abs_error', 'n', 'chosen',
               'corr_stored_line_realised_home_margin', 'corr_n', 'corr_ci', 'source_url'],
              rows)
    print(f'  sign convention: {chosen} (MAE {min(mae_pos, mae_neg) / n:.3f}, '
          f'corr {rr:.3f})')
    return chosen


# ------------------------------------------------------------------------ availability
def build_availability(injuries, prior_1118, prior_0619):
    rows = []
    for r in injuries:
        if r['player'] == '__NO_INJURIES_REPORTED__':
            rows.append(dict(club=r['club'], player_as_printed='(none printed)',
                             position_as_printed='', injury_as_printed='',
                             practice_status_as_printed='', game_status_as_printed='',
                             read_utc=READ_UTC, source_url=INJURY_URL,
                             note='nfl.com prints "No Injuries Reported" for this club on this '
                                  'page; that is a statement about the page, not about health'))
            continue
        rows.append(dict(club=r['club'], player_as_printed=r['player'],
                         position_as_printed=r['position'],
                         injury_as_printed=r['injury'],
                         practice_status_as_printed=r['practice'],
                         game_status_as_printed=r['status'], read_utc=READ_UTC,
                         source_url=INJURY_URL,
                         note='transcribed from the official report; an empty game-status cell '
                              'is printed empty by nfl.com and is left empty here'))
    write_csv('availability_week11.csv',
              ['club', 'player_as_printed', 'position_as_printed', 'injury_as_printed',
               'practice_status_as_printed', 'game_status_as_printed', 'read_utc',
               'source_url', 'note'], rows)

    summary = {}
    for r in injuries:
        if r['player'] == '__NO_INJURIES_REPORTED__':
            summary.setdefault(r['club'], {'out': 0, 'doubtful': 0, 'questionable': 0,
                                           'blank': 0, 'rows': 0, 'no_injuries': 'yes'})
            continue
        d = summary.setdefault(r['club'], {'out': 0, 'doubtful': 0, 'questionable': 0,
                                           'blank': 0, 'rows': 0, 'no_injuries': 'no'})
        d['rows'] += 1
        st = (r['status'] or '').strip()
        d['out'] += st == 'Out'
        d['doubtful'] += st == 'Doubtful'
        d['questionable'] += st == 'Questionable'
        d['blank'] += st not in ('Out', 'Doubtful', 'Questionable')
    srows = []
    for club in sorted(summary):
        d = summary[club]
        srows.append(dict(club=club, rows_in_report=d['rows'], out=d['out'],
                          doubtful=d['doubtful'], questionable=d['questionable'],
                          no_game_status=d['blank'], printed_no_injuries=d['no_injuries'],
                          read_utc=READ_UTC, source_url=INJURY_URL))
    write_csv('availability_summary.csv',
              ['club', 'rows_in_report', 'out', 'doubtful', 'questionable', 'no_game_status',
               'printed_no_injuries', 'read_utc', 'source_url'], srows)

    mine = {(r['club'], r['player']): r for r in injuries
            if r['player'] != '__NO_INJURIES_REPORTED__'}
    prior = {}
    with open(prior_1118, newline='') as fh:
        for r in csv.DictReader(fh):
            prior[(r['team_code'], r['player'])] = r
    delta = []
    for key, r in sorted(mine.items()):
        p = prior.get(key)
        if not p:
            delta.append(dict(change='appeared_in_report', club=key[0], player=key[1],
                              field='row', prior_value='', this_value='present',
                              prior_read_utc='2026-11-18T03:55:13Z', this_read_utc=READ_UTC,
                              source_url=INJURY_URL,
                              page_note='the prior file asked for reg11 but recorded reg10 as '
                                        'its source_url; this read is the real Week 11 page'))
            continue
        for field, mk, pk in (('game_status', 'status', 'game_status'),
                              ('practice_status', 'practice', 'practice_status'),
                              ('injury', 'injury', 'injuries')):
            a, b = (p.get(pk) or '').strip(), (r.get(mk) or '').strip()
            if a != b:
                delta.append(dict(change='changed', club=key[0], player=key[1], field=field,
                                  prior_value=a, this_value=b,
                                  prior_read_utc='2026-11-18T03:55:13Z',
                                  this_read_utc=READ_UTC, source_url=INJURY_URL,
                                  page_note='prior read served Week 10 content; the difference '
                                            'is page-to-page, not day-to-day'))
    for key, p in sorted(prior.items()):
        if key not in mine:
            delta.append(dict(change='absent_from_report', club=key[0], player=key[1],
                              field='row', prior_value='present', this_value='',
                              prior_read_utc='2026-11-18T03:55:13Z', this_read_utc=READ_UTC,
                              source_url=INJURY_URL,
                              page_note='prior read served Week 10 content'))
    write_csv('injury_delta.csv',
              ['change', 'club', 'player', 'field', 'prior_value', 'this_value',
               'prior_read_utc', 'this_read_utc', 'source_url', 'page_note'], delta)

    early = {}
    with open(prior_0619, newline='') as fh:
        for r in csv.DictReader(fh):
            early[(r['team'], r['player'])] = r
    drift = []
    for key, e in sorted(early.items()):
        m = mine.get(key)
        if not m:
            drift.append(dict(club=key[0], player=key[1], field='row',
                              value_at_0657='present', value_at_1110='',
                              note='row no longer printed'))
            continue
        if (e.get('game_status') or '') != (m.get('status') or ''):
            drift.append(dict(club=key[0], player=key[1], field='game_status',
                              value_at_0657=e.get('game_status', ''),
                              value_at_1110=m.get('status', ''),
                              note='designation changed inside the four-hour window'))
    write_csv('injury_drift_intraday.csv',
              ['club', 'player', 'field', 'value_at_0657', 'value_at_1110', 'note'], drift)
    return srows, delta, drift


def build_designation_reliability():
    """P(a snap record exists | designation), 2023-2026, from the pinned datasets."""
    out = []
    for season in sorted(PINNED_INJURY):
        snap_path = os.path.join(REPO, f'data/decision-desk/raw/snap_counts_{season}.csv.gz')
        if not os.path.exists(snap_path):
            continue
        snaps = {}
        with gzip.open(snap_path, 'rt') as fh:
            for r in csv.DictReader(fh):
                played = (int(r['offense_snaps'] or 0) + int(r['defense_snaps'] or 0)
                          + int(r['st_snaps'] or 0)) > 0
                if played:
                    snaps.setdefault((r['team'], r['week']), set()).add(r['player'])
        counts = {}
        with gzip.open(PINNED_INJURY[season], 'rt') as fh:
            for r in csv.DictReader(fh):
                wk = str(r.get('week') or '')
                if not wk.isdigit():
                    continue
                st = (r.get('report_status') or '').strip() or 'no designation'
                d = counts.setdefault(st, [0, 0])
                d[0] += 1
                if r['full_name'] in snaps.get((r['team'], r['week']), set()):
                    d[1] += 1
        for st, (nn, k) in sorted(counts.items()):
            p, lo, hi = E.wilson(k, nn)
            out.append(dict(season=season, designation=st, designated_rows=nn, played_rows=k,
                            play_rate=round(p, 4), ci_lo=round(lo, 4), ci_hi=round(hi, 4),
                            source_class='PINNED-DATASET',
                            source_url='https://github.com/nflverse/nflverse-data/releases/'
                                       'download/snap_counts/snap_counts.csv.gz',
                            note='"played" means a snap-count record exists for that club-week; '
                                 'an official inactive list is not in the repository, so a '
                                 'player cut before kickoff is indistinguishable from one who '
                                 'dressed and never took a snap'))
    pool = {}
    for r in out:
        d = pool.setdefault(r['designation'], [0, 0])
        d[0] += r['designated_rows']
        d[1] += r['played_rows']
    for st, (nn, k) in sorted(pool.items()):
        p, lo, hi = E.wilson(k, nn)
        out.append(dict(season='2023-2026 pooled', designation=st, designated_rows=nn,
                        played_rows=k, play_rate=round(p, 4), ci_lo=round(lo, 4),
                        ci_hi=round(hi, 4), source_class='PINNED-DATASET',
                        source_url='https://github.com/nflverse/nflverse-data/releases/download/'
                                   'snap_counts/snap_counts.csv.gz',
                        note='pooled across the four seasons present in the repository'))
    write_csv('designation_reliability.csv',
              ['season', 'designation', 'designated_rows', 'played_rows', 'play_rate',
               'ci_lo', 'ci_hi', 'source_class', 'source_url', 'note'], out)
    return out


def build_depth_usage(snap_path):
    """Usage rank inside each club x position group, from offensive snap share only."""
    by = {}
    with gzip.open(snap_path, 'rt') as fh:
        for r in csv.DictReader(fh):
            if not r['offense_snaps'] or int(r['offense_snaps']) == 0:
                continue
            key = (r['team'], r['position'])
            by.setdefault(key, {}).setdefault(r['player'], []).append(float(r['offense_pct']))
    rows = []
    for (team, pos), players in sorted(by.items()):
        ranked = sorted(players.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))
        for rank, (player, pcts) in enumerate(ranked, 1):
            rows.append(dict(club=team, position_group=pos, usage_rank=rank, player=player,
                             games_with_offence=len(pcts),
                             mean_offensive_snap_share=round(sum(pcts) / len(pcts), 4),
                             method='mean offensive snap share over the club games present in '
                                    'the pinned file; jersey number, draft slot and salary are '
                                    'never used',
                             source_class='PINNED-DATASET',
                             source_url='https://github.com/nflverse/nflverse-data/releases/'
                                        'download/snap_counts/snap_counts.csv.gz'))
    write_csv('depth_usage_2026.csv',
              ['club', 'position_group', 'usage_rank', 'player', 'games_with_offence',
               'mean_offensive_snap_share', 'method', 'source_class', 'source_url'], rows)
    groups = {}
    for r in rows:
        groups.setdefault((r['club'], r['position_group']), []).append(r)
    rep = []
    for (club, pos), rs in sorted(groups.items()):
        r1 = [x for x in rs if x['usage_rank'] == 1]
        r2 = [x for x in rs if x['usage_rank'] == 2]
        if not r1:
            continue
        rep.append(dict(club=club, position_group=pos, rank1_player=r1[0]['player'],
                        rank1_share=r1[0]['mean_offensive_snap_share'],
                        rank2_player=r2[0]['player'] if r2 else '',
                        rank2_share=r2[0]['mean_offensive_snap_share'] if r2 else '',
                        depth_gap=round(float(r1[0]['mean_offensive_snap_share'])
                                        - float(r2[0]['mean_offensive_snap_share']), 4)
                        if r2 else '',
                        field='offence', source_class='PINNED-DATASET',
                        source_url='https://github.com/nflverse/nflverse-data/releases/download/'
                                   'snap_counts/snap_counts.csv.gz',
                        note='the gap is the measured drop from the club usage leader to the '
                             'next player at the position; it is not a claim that the leader '
                             'started'))
    write_csv('replacement_depth_2026.csv',
              ['club', 'position_group', 'rank1_player', 'rank1_share', 'rank2_player',
               'rank2_share', 'depth_gap', 'field', 'source_class', 'source_url', 'note'], rep)
    return rows, rep


def build_availability_counts(official_week10):
    """Designation counts per club-week, 2023-2026, official captures overriding where they exist."""
    nick = {'Cardinals': 'AZ', 'Falcons': 'ATL', 'Ravens': 'BAL', 'Bills': 'BUF',
            'Panthers': 'CAR', 'Bears': 'CHI', 'Bengals': 'CIN', 'Browns': 'CLE',
            'Cowboys': 'DAL', 'Broncos': 'DEN', 'Lions': 'DET', 'Packers': 'GB',
            'Texans': 'HOU', 'Colts': 'IND', 'Jaguars': 'JAX', 'Chiefs': 'KC',
            'Raiders': 'LV', 'Chargers': 'LAC', 'Rams': 'LA', 'Dolphins': 'MIA',
            'Vikings': 'MIN', 'Patriots': 'NE', 'Saints': 'NO', 'Giants': 'NYG',
            'Jets': 'NYJ', 'Eagles': 'PHI', 'Steelers': 'PIT', '49ers': 'SF',
            'Seahawks': 'SEA', 'Buccaneers': 'TB', 'Titans': 'TEN',
            'Commanders': 'WAS'}
    counts = {}
    for season in sorted(PINNED_INJURY):
        with gzip.open(PINNED_INJURY[season], 'rt') as fh:
            for r in csv.DictReader(fh):
                wk = str(r.get('week') or '')
                if not wk.isdigit() or not (1 <= int(wk) <= 18):
                    continue
                key = (r['team'], int(season), int(wk))
                d = counts.setdefault(key, [0, 0, 0])
                st = (r.get('report_status') or '').strip()
                if st == 'Out':
                    d[0] += 1
                elif st == 'Doubtful':
                    d[1] += 1
                elif st == 'Questionable':
                    d[2] += 1
    with open(CAP_WK10_1112, newline='') as fh:
        d10 = {}
        for r in csv.DictReader(fh):
            d = d10.setdefault(nick[r['team_nickname']], [0, 0, 0])
            st = (r['game_status'] or '').strip()
            if st == 'Out':
                d[0] += 1
            elif st == 'Doubtful':
                d[1] += 1
            elif st == 'Questionable':
                d[2] += 1
    for code, d in d10.items():
        counts[(code, 2026, 10)] = d
    with open(os.path.join(INPUTS, 'injuries_week11_2026-11-19.txt')) as fh:
        d11 = {}
        for line in fh:
            if not line.strip() or line.startswith('#'):
                continue
            p = line.rstrip('\n').split('|')
            d = d11.setdefault(p[0], [0, 0, 0])
            st = (p[5] or '').strip()
            if st == 'Out':
                d[0] += 1
            elif st == 'Doubtful':
                d[1] += 1
            elif st == 'Questionable':
                d[2] += 1
    for code, d in d11.items():
        counts[(code, 2026, 11)] = d
    rows = []
    for (club, season, week), d in sorted(counts.items()):
        official = season == 2026 and week in (10, 11)
        rows.append(dict(club=club, season=season, week=week, out=d[0], doubtful=d[1],
                         questionable=d[2],
                         source_class='OFFICIAL' if official else 'PINNED-DATASET',
                         source_url=CAP_WK10_URL if (season == 2026 and week == 10) else
                         (INJURY_URL if (season == 2026 and week == 11) else
                          'https://github.com/nflverse/nflverse-data/releases/download/'
                          'injuries/injuries_%d.csv.gz' % season)))
    write_csv('availability_counts.csv',
              ['club', 'season', 'week', 'out', 'doubtful', 'questionable', 'source_class',
               'source_url'], rows)
    return {(r['club'], r['season'], r['week']): (r['out'], r['doubtful'], r['questionable'])
            for r in rows}, rows


def build_ablation(games, official_week10, avail):
    """Identical models with and without the verified availability features."""
    seasons = [2023, 2024, 2025, 2026]
    teams = sorted({g['away'] for g in games} | {g['home'] for g in games})
    pairs, coefs = [], {}
    for season in seasons:
        train = [g for g in games if g['season'] < season]
        if not train:
            continue
        base = E.fit_ratings(train, teams, seasons_used=6)
        withab = E.fit_with_availability(train, teams, avail, seasons_used=6)
        coefs[season] = withab.coef
        test = [g for g in games if g['season'] == season]
        if season == 2026 and not test:
            test = [dict(season=2026, week=10, away=r['away'], home=r['home'],
                         away_score=r['away_score'], home_score=r['home_score'])
                    for r in official_week10]
        for g in test:
            if g['home_score'] == g['away_score']:
                continue
            out = 1.0 if g['home_score'] > g['away_score'] else 0.0
            pairs.append(dict(season=season, week=g['week'], away=g['away'], home=g['home'],
                              p_without=round(base.p_home_win(g['home'], g['away']), 6),
                              p_with=round(E.p_home_win_with_availability(withab, g), 6),
                              outcome_home_win=int(out), home_score=g['home_score'],
                              away_score=g['away_score'],
                              home_out=avail.get((g['home'], season, g['week']),
                                                 (0, 0, 0))[0],
                              away_out=avail.get((g['away'], season, g['week']),
                                                 (0, 0, 0))[0],
                              cluster=f'{season}-W{int(g["week"]):02d}',
                              source_url=CORPUS_URL))
    per_season = []
    for season in seasons:
        sub = [r for r in pairs if r['season'] == season]
        if not sub:
            continue
        outs = [r['outcome_home_win'] for r in sub]
        b0 = E.brier([r['p_without'] for r in sub], outs)
        b1 = E.brier([r['p_with'] for r in sub], outs)
        per_season.append(dict(season=season, n_games=len(sub), brier_without=round(b0, 6),
                               brier_with=round(b1, 6), difference=round(b1 - b0, 6),
                               log_loss_without=round(E.logloss(
                                   [r['p_without'] for r in sub], outs), 6),
                               log_loss_with=round(E.logloss(
                                   [r['p_with'] for r in sub], outs), 6),
                               note='refitted on all earlier seasons only',
                               source_url=CORPUS_URL))
    write_csv('availability_ablation_by_season.csv',
              ['season', 'n_games', 'brier_without', 'brier_with', 'difference',
               'log_loss_without', 'log_loss_with', 'note', 'source_url'], per_season)
    if pairs:
        write_csv('availability_ablation_games.csv',
                  ['season', 'week', 'away', 'home', 'p_without', 'p_with', 'outcome_home_win',
                   'home_score', 'away_score', 'home_out', 'away_out', 'cluster',
                   'source_url'], pairs)
    prows = [(r['cluster'], r['p_with'], r['p_without'], float(r['outcome_home_win']))
             for r in pairs]
    diff = E.paired_diff_ci(prows, reps=2000) if prows else None
    rows = []
    if pairs:
        outs = [float(r['outcome_home_win']) for r in pairs]
        b0 = E.brier([r['p_without'] for r in pairs], outs)
        for label, key in (('WITHOUT availability features', 'p_without'),
                           ('WITH availability features', 'p_with')):
            ps = [r[key] for r in pairs]
            rows.append(dict(variant=label, n_games=len(ps), brier=round(E.brier(ps, outs), 6),
                             log_loss=round(E.logloss(ps, outs), 6),
                             difference_vs_without='' if key == 'p_without'
                             else round(E.brier(ps, outs) - b0, 6),
                             diff_lo95='', diff_hi95='',
                             note='pooled over the 2023-2026 chronological holdouts',
                             source_url=CORPUS_URL))
        rows.append(dict(variant='DIFFERENCE (with minus without)', n_games=diff['n_games'],
                         brier=round(diff['point'], 6), log_loss='',
                         difference_vs_without=round(diff['point'], 6),
                         diff_lo95=round(diff['lo'], 6), diff_hi95=round(diff['hi'], 6),
                         note='mean paired squared-error difference with a game-cluster '
                              'bootstrap 95% interval; negative means the availability term '
                              'helped. No fixed point penalty is applied anywhere in this desk.',
                         source_url=CORPUS_URL))
    write_csv('availability_ablation.csv',
              ['variant', 'n_games', 'brier', 'log_loss', 'difference_vs_without', 'diff_lo95',
               'diff_hi95', 'note', 'source_url'], rows)
    cro = []
    for season, c in sorted(coefs.items()):
        cro.append(dict(fit_window=f'all seasons before {season}', season=season,
                        coef_out=round(c['out'], 4), coef_doubtful=round(c['doubtful'], 4),
                        coef_questionable=round(c['questionable'], 4),
                        note='points per official designation, shrinkage ridge of 10 pseudo-'
                             'observations; the sign and size are estimated, never assumed',
                        source_url=CORPUS_URL))
    write_csv('availability_coefficients.csv',
              ['fit_window', 'season', 'coef_out', 'coef_doubtful', 'coef_questionable',
               'note', 'source_url'], cro)
    print(f'  ablation: n={len(pairs)} paired, difference '
          f'{round(diff["point"], 5) if diff else "n/a"} '
          f'[{round(diff["lo"], 5) if diff else ""}, {round(diff["hi"], 5) if diff else ""}]')
    return rows, avail


def build_registers(slate, injuries, fams, pref, avail_delta, standings_exact, n_clubs):
    """Requirements, questions, suggestions, leaderboard, team view and the flag register."""
    # ---- leaderboard: signal separate from staking, backtest never on this board
    lb = []
    divisions = [
        ('singles · side', 'backtest_families.csv', 'F4_OPPONENT_AWARE'),
        ('singles · total', 'backtest_totals.csv', 'F6_TOTAL_OPPONENT_AWARE'),
        ('singles · moneyline', 'backtest_families.csv', 'F5_MARKET_LINE_BENCHMARK'),
    ]
    f4 = next(f for f in fams if f['family'] == 'F4_OPPONENT_AWARE')
    fsp = next(f for f in fams if f['family'] == 'F5_MARKET_LINE_BENCHMARK')
    for division, src, fam in divisions:
        lb.append(dict(
            division=division, strategy=fam, status='PAPER',
            signal_metric='Brier skill vs de-vigged close',
            signal_value=(f4['brier_skill_vs_close'] if fam == 'F4_OPPONENT_AWARE'
                          else fsp['brier_skill_vs_close']),
            signal_lo95=(f4['skill_lo95'] if fam == 'F4_OPPONENT_AWARE'
                         else fsp['skill_lo95']),
            signal_hi95=(f4['skill_hi95'] if fam == 'F4_OPPONENT_AWARE'
                         else fsp['skill_hi95']),
            n_settled=0,
            staking_metric='flat 1u ROI at the de-vigged closing price',
            staking_roi=(f4['staking_roi'] if fam == 'F4_OPPONENT_AWARE' else ''),
            staking_n=(f4['n_bets'] if fam == 'F4_OPPONENT_AWARE' else ''),
            certified='no', tier='C', reward='none — no strategy certified',
            demotion_trigger='a 90% lower bound of signal_value below 0, or ROI <= -10% over '
                             '50 settled bets, or an input hash change without a new '
                             'registration',
            what_would_change_our_mind='a positive lower bound after Holm correction on a '
                                       'prospective sample, or (in the other direction) the '
                                       'same result on 300 settled bets',
            backtest_reference='NOT ON THIS BOARD — the backtest lives in '
                               'data/backtest_families.csv',
            source_url=BENCHMARK_URL))
    for division in ('game parlay', 'same-game parlay', 'prop combo'):
        lb.append(dict(
            division=division, strategy='none eligible', status='BLOCKED',
            signal_metric='joint probability validated directly',
            signal_value='', signal_lo95='', signal_hi95='', n_settled=0,
            staking_metric='', staking_roi='', staking_n='',
            certified='no', tier='—', reward='none',
            demotion_trigger='not applicable — nothing is live',
            what_would_change_our_mind='a fitted joint distribution that beats the independent '
                                       'product by more than 1 pp on held-out games, plus the '
                                       'operator\'s void and push rules quoted from its own '
                                       'rules page',
            backtest_reference='n/a',
            source_url=CORPUS_URL))
    write_csv('leaderboard.csv',
              ['division', 'strategy', 'status', 'signal_metric', 'signal_value',
               'signal_lo95', 'signal_hi95', 'n_settled', 'staking_metric', 'staking_roi',
               'staking_n', 'certified', 'tier', 'reward', 'demotion_trigger',
               'what_would_change_our_mind', 'backtest_reference', 'source_url'], lb)

    # ---- per-team view: starters out by designation, usage gap, net count
    summary = {}
    for r in injuries:
        if r['player'] == '__NO_INJURIES_REPORTED__':
            summary.setdefault(r['club'], {'out': 0, 'doubtful': 0, 'questionable': 0,
                                           'rows': 0, 'no_injuries': 'yes'})
            continue
        d = summary.setdefault(r['club'], {'out': 0, 'doubtful': 0, 'questionable': 0,
                                           'rows': 0, 'no_injuries': 'no'})
        d['rows'] += 1
        st = (r['status'] or '').strip()
        d['out'] += st == 'Out'
        d['doubtful'] += st == 'Doubtful'
        d['questionable'] += st == 'Questionable'
    rep = {}
    with open(os.path.join(DATA, 'replacement_depth_2026.csv'), newline='') as fh:
        for r in csv.DictReader(fh):
            rep.setdefault(r['club'], []).append(r)
    opp = {}
    for s in slate:
        opp[s['home']] = s['away']
        opp[s['away']] = s['home']
    trows = []
    for club in sorted(set(list(summary) + list(opp))):
        d = summary.get(club, {'out': 0, 'doubtful': 0, 'questionable': 0, 'rows': 0,
                               'no_injuries': 'not in report'})
        gaps = [float(x['depth_gap']) for x in rep.get(club, []) if x['depth_gap'] not in ('', None)]
        biggest = max(rep.get(club, []), key=lambda x: float(x['depth_gap'] or -9),
                      default=None)
        trows.append(dict(
            club=club, week11_opponent=opp.get(club, ''),
            out=d['out'], doubtful=d['doubtful'], questionable=d['questionable'],
            report_rows=d['rows'], printed_no_injuries=d['no_injuries'],
            largest_usage_gap_position=biggest['position_group'] if biggest else '',
            largest_usage_gap=(biggest['depth_gap'] if biggest else ''),
            usage_gap_n=len(gaps),
            replacement_named='NOT CONFIRMED — no official inactive list in the repository, so '
                              'a replacement is bounded by the usage gap, never named',
            net_availability_count=d['out'] + d['doubtful'] + d['questionable'],
            source_url=INJURY_URL))
    write_csv('team_view_week11.csv',
              ['club', 'week11_opponent', 'out', 'doubtful', 'questionable', 'report_rows',
               'printed_no_injuries', 'largest_usage_gap_position', 'largest_usage_gap',
               'usage_gap_n', 'replacement_named', 'net_availability_count', 'source_url'],
              trows)

    # ---- questions
    write_csv('questions.csv', ['id', 'question', 'known_now', 'missing', 'discovery_route',
                                'blocks', 'urgency', 'source_url'],
              [dict(id=i, question=q, known_now=k, missing=m, discovery_route=r, blocks=b,
                    urgency=u, source_url=s)
               for i, q, k, m, r, b, u, s in RD.QUESTIONS])
    # ---- suggestions
    write_csv('suggestions.csv', ['id', 'suggestion', 'options_considered', 'recommendation',
                                  'cost', 'review_status', 'condition_to_accept',
                                  'what_would_change_our_mind', 'evidence_path'],
              [dict(id=i, suggestion=s_, options_considered=o, recommendation=r, cost=c,
                    review_status=st, condition_to_accept=cond,
                    what_would_change_our_mind=ch, evidence_path=e)
               for i, s_, o, r, c, st, cond, ch, e in RD.SUGGESTIONS])

    # ---- requirements ledger
    f4 = next(f for f in fams if f['family'] == 'F4_OPPONENT_AWARE')
    tskill = None
    with open(os.path.join(DATA, 'backtest_totals.csv'), newline='') as fh:
        tskill = next(csv.DictReader(fh))
    ab = {}
    with open(os.path.join(DATA, 'availability_ablation.csv'), newline='') as fh:
        for r in csv.DictReader(fh):
            ab[r['variant']] = r
    diff = ab['DIFFERENCE (with minus without)']
    reqs = [
        ('R01', 'Price-snapshot store with opening and closing numbers for every originated '
                'market', 'PARTIALLY MET',
         'A stamped closing capture per fixture',
         '52 originated rows each carry a named-operator open price with a read stamp and the '
         'operator URL; 0 closing prices exist because the 13 fixtures kick off after this build',
         'market_snapshots.csv'),
        ('R02', 'Verified results feed that backtests can be computed from', 'MET',
         'A 32/32 reconciliation of the corpus aggregate to the official standings',
         f'{standings_exact}/{n_clubs} clubs reconcile exactly on W, L, T, PF and PA after the '
         '14 official Week 10 finals are appended; the pinned dataset alone reproduces 30/32 '
         'because it prints no Week 10 score', 'standings_reconciliation.csv'),
        ('R03', 'Originate the side first, then the total, then the moneyline', 'MET',
         'Three markets per fixture in that published order',
         '52 rows: 13 side, 13 total, 26 moneyline, in that market_order sequence',
         'origination_week11.csv'),
        ('R04', 'Fair line, market line and the difference as separate columns', 'MET',
         'No cell mixes two concepts',
         'fair_line, market_line and difference_fair_minus_market are separate on every one of '
         'the 52 rows; the market line is the median of two named operators',
         'origination_week11.csv'),
        ('R05', 'Separate signal from staking in the leaderboard', 'MET',
         'Two columns on two scales with no merged score',
         'signal_value is Brier skill; staking_roi is a flat-unit return; the 2026 tail already '
         'shows a strategy with ROI above zero and a skill interval below zero',
         'leaderboard.csv'),
        ('R06', 'Track the depth of the replacement, not the fact of a replacement',
         'PARTIALLY MET', 'An official inactive list to confirm a replacement',
         '246 club/position rows publish the measured usage gap from rank 1 to rank 2 '
         '(offensive snap share); no replacement is named because no official inactive list '
         'is in the repository', 'replacement_depth_2026.csv'),
        ('R07', 'Correlations only from officially sourced numbers, with n published', 'MET',
         'n beside every coefficient',
         '5 coefficients, every one carrying n (28 to 7,087) and its source class; the '
         'official-standings pair carries n=32', 'correlations.csv'),
        ('R08', 'A demotion gate that sends a live strategy back to paper', 'MET',
         'Three mechanical triggers frozen before results',
         'The gate is in the registration with its review level; every leaderboard row carries '
         'the trigger it would be demoted by', 'preregistration.json'),
        ('R09', 'Pre-register every strategy and keep backtest numbers off the leaderboard',
         'MET', 'A commit hash as the registration and no backtest column on the board',
         'preregistration.json was committed before the evaluation code ran; its sha256 is in '
         'build_manifest.json and recomputed by verify.py; the ranked board has n_settled=0 '
         'and a column that says where the backtest lives instead', 'preregistration.json'),
        ('R10', 'Availability graph as a first-class dataset (expected vs actual)',
         'PARTIALLY MET', 'An official participant record per game',
         '255 Week 11 rows carry the official designation set with its read clock; the actual '
         'side is playing time from a pinned dataset, not an official feed',
         'availability_week11.csv'),
        ('R11', 'Do not model depth from jersey order; use playing time', 'MET',
         'No jersey number anywhere in the pipeline',
         'Every usage rank is a mean offensive snap share; the transcribed official report has '
         'no jersey numbers in it at all', 'depth_usage_2026.csv'),
        ('R12', 'Make the injury signal a surprise, never a level', 'MET',
         'Two clocks on every delta row',
         f'{len(avail_delta)} delta rows, each with a prior read clock of 2026-11-18T03:55:13Z '
         'and today\'s clock; no level enters the model as a feature',
         'injury_delta.csv'),
        ('R13', '32-club roster/IR sweep before any team-level model is trusted',
         'NOT MET', 'An official reserve-list capture for all 32 clubs',
         'not attempted this session; the repository holds partial reserve-list captures from '
         'other desks, which this desk does not re-publish as verified', 'flagged.csv'),
        ('R14', 'Fixture-context features from published schedule facts only', 'MET',
         'Each fact links to the schedule page',
         'Kickoff as printed, network and the neutral-site flag for all 13 fixtures, each from '
         'the official week page', 'origination_week11.csv'),
        ('R15', 'Store every model output as a probability plus its inputs', 'MET',
         'A hash over the exact input object for every output',
         'inputs_sha256 on all 52 rows; the input object is rebuilt and re-hashed by verify.py',
         'origination_week11.csv'),
        ('R16', 'Publish a removal-of-luck panel', 'MET',
         'Base rate, sample-size requirement and a skill interval',
         '6 panels: the home-win base rate with a Wilson interval at n=6,591, the break-even '
         'probability, the bets needed to prove 55% (783) and 54% (1,224), the model skill '
         'interval and the signal/staking split', 'luck_panel.csv'),
        ('R17', 'Two-sided "what would change our mind" on every strategy entry', 'MET',
         'Both directions named on every row',
         'Every leaderboard row and every suggestion row carries the field in both directions',
         'leaderboard.csv'),
        ('R18', 'Price a line ourselves and publish the residual against the market, on a '
                'schedule, from day one', 'MET',
         'A residual column and a committed capture cadence',
         'difference_fair_minus_market on all 52 rows plus a committed capture workflow; the '
         'residuals are large and the backtest says why (the model loses to the close)',
         'origination_week11.csv'),
        ('R19', 'Turn the 136-game log into the pre-registered backtest corpus',
         'PARTIALLY MET', 'A scored row for all 136 games',
         'The pinned dataset prints 136 scored 2026 games for weeks 1-9 and none for weeks '
         '10-18; 14 official Week 10 finals are appended from today\'s read, so the log is 150 '
         'games and 13 remain unscored because they have not been played',
         'corpus_coverage.csv'),
        ('R20', 'Decide the price-data policy before any backtest is published', 'MET',
         'A written policy with a date, before the first figure',
         'Policy P-9E54D765-01 is in the frozen registration; every price carries its operator '
         'and read clock', 'preregistration.json'),
        ('R21', 'Store every injury-hub read with its clock time and publish the delta',
         'MET', 'Two clocks on every delta row',
         f'{len(avail_delta)} delta rows; a zero-row intra-day drift table is published too, '
         'which is itself the finding that the page did not move between 06:57Z and 11:10Z',
         'injury_delta.csv'),
        ('R22', 'Decision-readiness table on the landing page: gate and clearing number',
         'MET', 'One row per brief line on the landing page itself',
         'This table is rendered on the landing page with the observed number on every row',
         'requirements.csv'),
        ('R23', 'Transcribe the venue of every fixture from the official game centre',
         'PARTIALLY MET', 'Twelve further game-centre reads',
         '1 of 13 read this session (IND at HOU: HOUSTON, TX / RELIANT STADIUM); the other 12 '
         'are blank and flagged, not inferred', 'flagged.csv'),
        ('R24', 'Publish the league\'s dated schedule announcement beside the live schedule',
         'NOT MET', 'The announcement page with its publication date',
         'not read this session; the live Week 11 page is linked and dated, the announcement '
         'is not', 'flagged.csv'),
        ('R25', 'Publish the league\'s dated schedule announcement beside the live schedule '
                'page (duplicate line in the brief)', 'SEE R24', 'As above', 'As above',
         'flagged.csv'),
        ('R26', 'Use official Game Books for actual starters and game-day status', 'NOT MET',
         'One official Game Book per week',
         'not read this session; the desk does not infer starters from anything else',
         'flagged.csv'),
        ('R27', 'Ingest game-level results so the ratings are opponent-aware', 'MET',
         'Ratings fitted on opponent-adjusted margins, not raw points',
         '7,103 scored games fitted with an additive offence/defence model and a home-field '
         'term; the walk-forward uses only prior weeks', 'ratings_2026.csv'),
        ('R28', 'Injury and personnel ablations instead of fixed penalties', 'MET',
         'Identical models with and without the features, plus uncertainty',
         f'The difference is {diff["brier"]} higher squared error with the term on, '
         f'95% interval [{diff["diff_lo95"]}, {diff["diff_hi95"]}] over {diff["n_games"]} '
         'paired games; no fixed penalty anywhere', 'availability_ablation.csv'),
        ('R29', 'Automate immutable multi-day availability snapshots', 'NOT MET',
         'A scheduled capture with retained hashes',
         'the repository holds single captures; this desk adds one stamped read and a '
         'committed workflow stub, but no multi-day series exists yet', 'flagged.csv'),
        ('R30', 'Capture official inactive lists and snap counts', 'NOT MET',
         'An official inactive list',
         'snap counts are present in a pinned dataset (136 club-games); no official inactive '
         'list is in the repository', 'designation_reliability.csv'),
        ('R31', 'Fix the two depth-parsing failures before widening coverage', 'NOT APPLICABLE',
         'A decision on the Texans image source',
         'this desk does not parse club depth pages at all; depth comes from playing time, so '
         'the two failures cannot recur here', 'depth_usage_2026.csv'),
        ('R32', 'Model depth slots as groups, not a single starter', 'MET',
         'Clubs can name several players at rank 1',
         'the usage table is a ranked list inside a position group; it never asserts "the '
         'starter", so a three-receiver group is three rows with three measured shares',
         'depth_usage_2026.csv'),
        ('R33', 'Treat roster turnover as a first-class data event', 'NOT MET',
         'A dated roster-event register',
         'not built this session; the desk does not claim any depth row is durable',
         'flagged.csv'),
        ('R34', 'Start with a singles-only shadow baseline', 'MET',
         'A simple pre-registered model, frozen and recorded before kickoff',
         'REG-9E54D765-V1 is frozen; singles are the only divisions on the board and every row '
         'is PAPER', 'preregistration.json'),
        ('R35', 'Keep parlays and prop combos behind a joint-evidence gate', 'MET',
         'A directly validated joint probability and the operator void rules',
         'three combo divisions are published as BLOCKED with the reason and the clearing '
         'condition', 'leaderboard.csv'),
        ('R36', 'Proper-score leaderboard divisions', 'MET',
         'Separate divisions ranked by benchmark-relative skill with uncertainty',
         'six divisions; the three singles divisions carry a skill interval, the three combo '
         'divisions are blocked', 'leaderboard.csv'),
        ('R37', 'Rank with proper scores and uncertainty, not win rate', 'MET',
         'A game-cluster lower bound and a multiplicity adjustment',
         'the ranking metric is Brier skill with a 2,000-resample game-cluster interval and a '
         'Holm correction across the families tested', 'backtest_families.csv'),
        ('R38', 'Durable snapshot storage and alerts', 'NOT MET',
         'Storage outside the static site, plus a freshness alert',
         'not built; captures are committed files, which is not durable storage',
         'flagged.csv'),
        ('R39', 'Split the public analysis layer from the private data layer', 'MET',
         'No row-level official data on the public site',
         'the site publishes derived aggregates, originated probabilities and links to the '
         'official pages; no official row is re-published', 'preregistration.json'),
        ('R40', 'Per-team view: starters out, replacements named, net count',
         'PARTIALLY MET', 'An official inactive list to name a replacement',
         '26 clubs with out/doubtful/questionable counts, the largest measured usage gap at '
         'each club, and an explicit "not confirmed" replacement cell',
         'team_view_week11.csv'),
        ('R41', 'Announced-starter evidence field', 'NOT MET',
         'A dated official announced-starter source',
         'not read this session; the desk publishes no announced-starter claim',
         'flagged.csv'),
        ('R42', 'Official depth-chart register with date and source per row', 'NOT MET',
         'A per-club official depth page read with a date',
         'not read this session; the usage table is the measured substitute and says so',
         'depth_usage_2026.csv'),
        ('R43', 'Calibrate what "Questionable" means empirically', 'MET',
         'A play rate with an interval and n',
         'pooled 61.7% [60.3, 63.0] with n=4,970 rows; Doubtful 0.6% [0.2, 1.8] with n=499; '
         'Out 0.02% [0.0, 0.14] with n=4,087',
         'designation_reliability.csv'),
        ('R44', 'Interactive offence vs defence matchup deficiency matrix', 'PARTIALLY MET',
         'A published starter/backup map per club',
         'a static deficiency table built from the measured usage gaps and the availability '
         'counts is published; it is not interactive and claims no starter',
         'deficiency_matrix.csv'),
        ('R45', 'Flag stale depth rows against the official transactions log', 'NOT MET',
         'An official transactions log',
         'no depth page is parsed here, so nothing can be stale; the transactions log was not '
         'read', 'flagged.csv'),
        ('R46', 'Point-in-time snapshot ledger for injuries, depth and inactives',
         'PARTIALLY MET', 'Retained captures with hashes across days',
         'each read in this desk carries a UTC clock; no multi-day ledger exists yet',
         'injury_delta.csv'),
        ('R47', 'Populate missing game-status designations (three Lions players)', 'MET',
         'The official cells as printed',
         'the Week 11 official report prints Kerby Joseph, Cade Mays and D.J. Reed with an '
         'EMPTY game-status cell; the desk publishes them empty and flags it rather than '
         'copying the Week 10 article value', 'flagged.csv'),
        ('R48', 'Re-capture the Week 10 injury tables', 'PARTIALLY MET',
         'A fresh stamped Week 10 read',
         'this desk uses the 2026-11-12T16:52:39Z Week 10 capture as its point-in-time set and '
         'does not re-read Week 10 today; the Week 11 report is re-read in full',
         'availability_week11.csv'),
        ('R49', 'Reject: deriving depth from jersey number, experience or salary', 'MET',
         'No such derivation anywhere',
         'the rejection is recorded in the registration and enforced by the usage method',
         'preregistration.json'),
        ('R50', 'Represent shared and empty depth slots faithfully', 'NOT MET',
         'A structured per-club depth source',
         'not attempted; the measured usage rank is a different object and does not pretend to '
         'represent a club\'s slot layout', 'depth_usage_2026.csv'),
        ('R51', 'Resolve the depth-order source before building a backup-deficiency feature',
         'NOT MET', 'Route (a) or (b) verified for all 32 clubs',
         'neither route is verified for all 32 clubs: the club pages are not parsed and the '
         'playing-time route covers one season of club-games', 'depth_usage_2026.csv'),
        ('R52', 'Score injury-designation reliability before using it as a feature', 'MET',
         'A play rate with intervals over several seasons',
         'four seasons, 4,970 Questionable rows, published with intervals; the feature is used '
         'as an estimated coefficient, and its ablation result is negative',
         'designation_reliability.csv'),
        ('R53', 'Snapshot the injury report every Wed/Thu/Fri with a dated history',
         'NOT MET', 'A scheduled capture job with a store',
         'one read per session; no schedule exists in this desk', 'flagged.csv'),
        ('R54', 'Treat the injury report as a timestamped series', 'PARTIALLY MET',
         'Several reads across the practice week',
         'three clocks exist for Week 11 (11-18T03:55Z, 11-19T06:57Z, 11-19T11:10Z) and the '
         'delta between the first and the last is published',
         'injury_delta.csv'),
        ('R55', 'Use snap counts as the starter proxy when the depth chart is unavailable',
         'MET', 'A published snap-share threshold',
         'every usage rank is a snap-share ranking; no threshold is asserted because none is '
         'official', 'depth_usage_2026.csv'),
        ('R56', 'Add a control baseline (random; favourites only) to every leaderboard run',
         'MET', 'Control rows in every scored table',
         'F2_RANDOM and F3_FAVOURITE_ONLY are scored on the same games and published beside the '
         'model, with their own intervals', 'backtest_families.csv'),
        ('R57', 'Two-stage skill leaderboard (proper-score qualification then CLV/ROI escrow)',
         'PARTIALLY MET', 'A prospective CLV sample',
         'stage one is implemented; stage two has no sample and is published as waiting',
         'leaderboard.csv'),
        ('R58', 'Vig-free market consensus vs originated fair-line decomposition', 'MET',
         'De-vigged market probability beside the model probability',
         'the market probability is de-vigged proportionally from two named operators and '
         'carried on every originated row', 'origination_week11.csv'),
        ('R59', 'Weekly "what changed" diff instead of a static snapshot', 'PARTIALLY MET',
         'Two weekly snapshots to diff',
         'one delta exists (2026-11-18 to 2026-11-19, 560 rows); a second week is needed for a '
         'weekly diff', 'injury_delta.csv'),
        ('R60', 'Publish every model total twice until one wins', 'NOT MET',
         'A second total estimator and a frozen comparison plan',
         'one estimator is registered; adding a second after seeing this result would be a '
         'registered violation', 'backtest_totals.csv'),
        ('R61', 'Drift alarm on every scraper', 'MET',
         'Pinned row counts and required fields that fail loudly',
         'verify.py pins the row count of every table and the required fields of every '
         'register; a missing field fails the build', 'verify.py'),
        ('R62', 'Capture the reserve list so "not listed" never means "available"', 'NOT MET',
         'An official reserve-list capture',
         'not captured this session; no row in this desk treats absence from the report as '
         'availability', 'flagged.csv'),
        ('R63', 'Reject: ranking strategies by season-long ROI', 'MET',
         'The rejection recorded with its reason',
         'the board ranks skill; ROI is published as a separate column and never used to rank',
         'leaderboard.csv'),
        ('R64', 'Archive weekly injury reports for past seasons', 'PARTIALLY MET',
         'Official archived reports',
         'the repository holds pinned 2023-2026 designation rows, which is a dataset, not an '
         'official archive; the reliability study rests on it and says so',
         'designation_reliability.csv'),
        ('R65', 'Pre-register each strategy before results are seen', 'MET',
         'A frozen text with a commit',
         'REG-9E54D765-V1 in the first commit of this namespace; hash recorded and checked',
         'preregistration.json'),
        ('R66', '2026 kickoff and onside-kick regime priors filter', 'NOT MET',
         'The 2026 rule text and its effect on totals',
         'not modelled; the desk publishes no kickoff-regime adjustment', 'flagged.csv'),
        ('R67', 'Freeze a rule before it sees data', 'MET', 'A commit hash as the registration',
         'the registration commit precedes every evaluation file', 'preregistration.json'),
        ('R68', 'Split data into train, validation and final holdout seasons', 'MET',
         'A holdout that is never used for tuning',
         'the last two seasons (2025, 2026) are the holdout and are reported separately on '
         'every family row', 'backtest_by_season.csv'),
        ('R69', 'Suggestion section a reviewer can choose from', 'MET',
         'A page with options, a recommendation and a review status',
         '14 suggestions, each with options considered, a recommendation, a cost, a review '
         'status, a condition to accept and a two-sided falsifier', 'suggestions.csv'),
        ('R70', 'Clear list of questions, information and answers needed before a decision',
         'MET', 'A register with what is known, what is missing and the route',
         '14 questions, each with the known-now value, the missing piece, the discovery route '
         'and what it blocks', 'questions.csv'),
        ('R71', 'Executive summary', 'MET', 'A single page stating the headline honestly',
         'summary page published with the negative result in the headline',
         'summary.html'),
    ]
    write_csv('requirements.csv',
              ['id', 'requirement', 'status', 'blocking_gate', 'observed', 'evidence_path'],
              [dict(id=i, requirement=r, status=s, blocking_gate=g, observed=o,
                    evidence_path=e) for i, r, s, g, o, e in reqs])
    return reqs


def build_deficiency(slate, avail_rows, rep_rows):
    """Static matchup deficiency table from measured inputs only."""
    counts = {(r['club'], r['season'], r['week']): r for r in avail_rows}
    usage = {}
    for r in rep_rows:
        usage.setdefault(r['club'], {})[r['position_group']] = r
    rows = []
    for s in slate:
        for club, other in ((s['home'], s['away']), (s['away'], s['home'])):
            c = counts.get((club, 2026, 11))
            pos_rows = [r for r in rep_rows
                        if r['club'] == club and r['depth_gap'] not in ('', None)]
            big = max(pos_rows, key=lambda r: float(r['depth_gap']), default=None)
            rows.append(dict(
                club=club, week11_opponent=other,
                out=c['out'] if c else '', doubtful=c['doubtful'] if c else '',
                questionable=c['questionable'] if c else '',
                largest_usage_gap_position=big['position_group'] if big else '',
                largest_usage_gap=big['depth_gap'] if big else '',
                interpretation='a larger usage gap at a position means the drop from the club '
                               'usage leader to the next player is larger, so an absence there '
                               'is more likely to matter; this is a measured gap, not a claim '
                               'that anyone is out',
                source_url=INJURY_URL))
    write_csv('deficiency_matrix.csv',
              ['club', 'week11_opponent', 'out', 'doubtful', 'questionable',
               'largest_usage_gap_position', 'largest_usage_gap', 'interpretation',
               'source_url'], rows)
    return rows


def build_flags(slate, avail_delta, drift):
    """The Flagged-for-Review register. Each row is something this session actually saw."""
    import gzip as _gzip
    blank_2026 = 0
    with _gzip.open(CORPUS_PATH, 'rt') as fh:
        for r in csv.DictReader(fh):
            if r['season'] == '2026' and (not r['away_score'] or not r['home_score']):
                blank_2026 += 1
    prior_rows = 0
    with open(CAP_1118, newline='') as fh:
        for _ in csv.DictReader(fh):
            prior_rows += 1
    early_rows = 0
    with open(CAP_1119_06, newline='') as fh:
        for _ in csv.DictReader(fh):
            early_rows += 1
    rows = [
        dict(id='F01', severity='HIGH',
             item='The pinned dataset prints no score at all for 2026 weeks 10-18',
             detail=f'{blank_2026} of the 272 2026 rows in data/decision-desk/raw/games.csv.gz '
                    'carry an empty away_score and home_score, including every Week 11 and '
                    'later fixture. Only weeks 1-9 are scored (136 games).',
             impact='Any table that treats this file as a complete 2026 feed understates each '
                    'club by the games it omits; a 32/32 reconciliation is impossible from '
                    'this file alone.',
             resolution='This desk appends the 14 official Week 10 finals read today and '
                        'publishes the gap week by week in data/corpus_coverage.csv. The '
                        'remaining 121 fixtures are unplayed or unread, and are labelled so.',
             evidence='data/corpus_coverage.csv', source_url=CORPUS_URL),
        dict(id='F02', severity='HIGH',
             item='A published capture asked for the Week 11 injury page and served Week 10',
             detail=f'data/nfl-desk-6cbf25fa/injury_reads/capture_injuries_2026-11-18.csv '
                    f'({prior_rows} rows) records requested_url = '
                    'https://www.nfl.com/injuries/league/2026/reg11 and source_url = '
                    'https://www.nfl.com/injuries/league/2026/reg10. It is Week 10 content '
                    'filed under a Week 11 request.',
             impact='Any delta that calls this file the Week 11 prior read compares two '
                    'different weeks and describes page drift as time drift.',
             resolution='This desk publishes the delta but labels every row with that caveat, '
                        'and its own read asserts the printed heading "Injuries - WEEK 11".',
             evidence='data/injury_delta.csv', source_url=INJURY_URL),
        dict(id='F03', severity='MEDIUM',
             item='The pinned spread is stored home-favoured POSITIVE, the opposite of the '
                  'operator print',
             detail='The stored line correlates +0.431 with the realised home margin '
                    '(n=7,087). Fitting the model under the opposite assumption gives a mean '
                    'absolute error of 8.22 points against 3.41 for the stored convention.',
             impact='A pipeline that treats a negative stored spread as "home favoured" '
                    'silently inverts every side it originates.',
             resolution='The convention is measured at every build and published in '
                        'data/sign_convention.csv; the origination table prints the operator '
                        'convention and says so on each row.',
             evidence='data/sign_convention.csv', source_url=CORPUS_URL),
        dict(id='F04', severity='LOW',
             item='Two clubs are printed with different codes by the operator and the dataset',
             detail='nfl.com prints LA and AZ; the pinned dataset prints LAR and ARI. Without '
                    'an alias the 2026 reconciliation splits two clubs into four.',
             impact='A silent 30/32 reconciliation that looks like a data problem.',
             resolution='One alias table is applied at load time and published here; the '
                        'reconciliation is 32/32 with it.',
             evidence='data/standings_reconciliation.csv', source_url=STANDINGS_URL),
        dict(id='F05', severity='MEDIUM',
             item='Two clubs are printed as "No Injuries Reported" rather than as a table',
             detail='The official Week 11 page prints that phrase for CIN and WAS. A capture '
                    'that turns the phrase into a player row produces a phantom injury entry; '
                    'a capture that drops it produces an empty club.',
             impact='Club-level counts and any "injury-free" claim depend on which choice the '
                    'capture made.',
             resolution='This desk transcribes the phrase as its own marker row '
                        '(__NO_INJURIES_REPORTED__) and publishes the club as "printed no '
                        'injuries", never as "zero injuries".',
             evidence='data/availability_week11.csv', source_url=INJURY_URL),
        dict(id='F06', severity='MEDIUM',
             item='Three Lions players print a blank game-status cell on the official page',
             detail='Kerby Joseph, Cade Mays and D.J. Reed are printed on the Week 11 report '
                    'with an empty Game Status cell. An earlier desk recorded all three as '
                    'Out from a separate article. Both can be true; the cell is blank.',
             impact='Copying the article value into the table would publish a designation the '
                    'report does not carry.',
             resolution='The cell stays blank and the three rows are listed here for review.',
             evidence='data/availability_week11.csv', source_url=INJURY_URL),
        dict(id='F07', severity='HIGH',
             item='Only one of thirteen venues was read this session',
             detail='IND at HOU prints HOUSTON, TX / RELIANT STADIUM on the official game '
                    'centre (read today). The other twelve game centres were not read, so the '
                    'venue column does not exist in this desk.',
             impact='A venue-dependent total model would be built on one fixture.',
             resolution='Left unread and flagged. No venue is inferred from a club name.',
             evidence='data/flagged.csv', source_url=GAME_URL.format(
                 slug='colts-at-texans-2026-reg-11')),
        dict(id='F08', severity='MEDIUM',
             item='The intra-day drift table is empty because the earlier capture only covers '
                  'one game',
             detail=f'The 2026-11-19T06:57:28Z capture holds {early_rows} rows (the Thursday '
                    'game only). Comparing it with the full read at 11:10Z therefore cannot '
                    'show drift for the other twelve fixtures.',
             impact='An empty diff here is not evidence that the page was stable.',
             resolution='The table is published with zero rows and this note; the drift '
                        'question is recorded as Q01-adjacent work for a full-page capture.',
             evidence='data/injury_drift_intraday.csv', source_url=INJURY_URL),
        dict(id='F09', severity='LOW',
             item='One capture stores a page-level phrase in the practice-status field',
             detail='The 06:57Z capture carries rows whose practice_status reads "No Injuries '
                    'Reported", i.e. a page statement in a player-level field.',
             impact='A join on practice status silently treats a phrase as a status.',
             resolution='Not edited (another session owns the file); recorded here and in Q14.',
             evidence='data/nfl-desk-6e13b9ff/wk11_tnf_injury_2026-11-19.csv',
             source_url='https://github.com/sassnarep3-star/Own5/blob/main/data/'
                        'nfl-desk-6e13b9ff/wk11_tnf_injury_2026-11-19.csv'),
        dict(id='F10', severity='MEDIUM',
             item='"Played" is measured as "has a snap record", not "was active"',
             detail='No official inactive list exists in the repository, so the reliability '
                    'study in data/designation_reliability.csv cannot separate a player who '
                    'was inactive from one who dressed and never played.',
             impact='The Questionable play rate is a lower bound on availability.',
             resolution='Published as a caveat on every row; an official inactive list is the '
                        'clear condition.',
             evidence='data/designation_reliability.csv',
             source_url='https://github.com/nflverse/nflverse-data/releases/download/'
                        'snap_counts/snap_counts.csv.gz'),
        dict(id='F11', severity='LOW',
             item='"Note" appears as a designation value in the pinned injury data',
             detail='Six rows in the 2023-2026 pinned files carry report_status "Note", which is '
                    'not one of the four official designations.',
             impact='A model that treats the four designations as exhaustive miscodes these '
                    'six rows.',
             resolution='Published as its own category with n=6 rather than merged into a '
                        'designation.',
             evidence='data/designation_reliability.csv',
             source_url='https://github.com/nflverse/nflverse-data/releases/download/'
                        'injuries/injuries_2026.csv.gz'),
        dict(id='F12', severity='MEDIUM',
             item='Closing prices do not exist yet for any originated market',
             detail='All 13 Week 11 fixtures kick off after this build, so every closing cell '
                    'is empty by construction, not by omission.',
             impact='No CLV, no closing-line skill, and no staking escrow can be computed.',
             resolution='The closing policy file names the single capture that would fill it.',
             evidence='data/closing_policy.csv', source_url=SLATE_URL),
        dict(id='F13', severity='MEDIUM',
             item='The availability ablation rests on two official designation weeks',
             detail='Only 2026 week 10 (read 2026-11-12T16:52:39Z) and week 11 (read today) '
                    'are stamped official sets; every earlier season comes from the pinned '
                    'dataset.',
             impact='A negative result on this evidence is about these two weeks.',
             resolution='Published with the source class of every count in '
                        'data/availability_counts.csv.',
             evidence='data/availability_ablation.csv',
             source_url='https://github.com/nflverse/nflverse-data/releases/tag/injuries'),
        dict(id='F14', severity='LOW',
             item='Two of the desk\'s own first numeric passes were wrong and are recorded',
             detail='(a) the signed spread-to-probability benchmark was first built with an '
                    'unsigned formula, which made the market benchmark look far worse than the '
                    'close; (b) the sign convention was first reported as "flipped". Both were '
                    'caught by measurement and corrected before publication.',
             impact='Presentation only; the published numbers are the corrected ones.',
             resolution='The measured sign convention is now a published table and the '
                        'convention is asserted in verify.py.',
             evidence='data/sign_convention.csv', source_url=CORPUS_URL),
        dict(id='F15', severity='LOW',
             item='Twelve of thirteen fixtures have no second-source price cross-check',
             detail='Both named operators price all 13 fixtures, so the market column is a '
                    'genuine two-book median; but no independent third source was read to '
                    'confirm either operator\'s print.',
             impact='A mis-transcribed operator price would not be caught by a third party.',
             resolution='Prices are transcribed verbatim in inputs/ with the read stamp, so a '
                        'reviewer can diff them against the operator page.',
             evidence='inputs/markets_week11_2026-11-19.txt',
             source_url='https://sportsbook.fanduel.com/navigation/nfl'),
    ]
    write_csv('flagged.csv',
              ['id', 'severity', 'item', 'detail', 'impact', 'resolution', 'evidence',
               'source_url'], rows)
    return rows


def main():
    print('build_data.py')
    standings = load_standings()
    slate = load_slate()
    markets = load_markets()
    injuries = load_injuries()
    week10 = load_week10_results()
    games, blank = load_corpus()
    print(f'  corpus: {len(games)} scored REG games '
          f'{min(g["season"] for g in games)}-{max(g["season"] for g in games)}')

    build_sources()
    _, standings_exact, n_clubs = build_results(games, standings, week10, blank)
    consensus = build_slate_and_markets(slate, markets)
    build_sign_convention(games)

    # origination uses every game strictly before Week 11 of 2026
    train_now = [g for g in games if g['season'] < 2026 or (g['season'] == 2026 and g['week'] < 11)]
    teams = sorted({g['away'] for g in games} | {g['home'] for g in games})
    r_now = E.fit_ratings(train_now, teams, seasons_used=6)
    print(f'  week-11 fit: n={r_now.n_games} mu={r_now.mu:.2f} hfa={r_now.hfa:.2f} '
          f'sigma_m={r_now.sigma_margin:.2f} sigma_t={r_now.sigma_total:.2f}')
    build_ratings_table(r_now, CORPUS_URL)
    build_origination(slate, consensus, r_now)

    wf = walk_forward(games)
    write_csv('walkforward_games.csv', FIELDS_WF, wf)
    fams, holdout = build_backtest(wf)
    build_luck(wf, fams)
    build_correlations(games, r_now, standings)

    _, avail_delta, drift_rows = build_availability(injuries, CAP_1118, CAP_1119_06)
    build_designation_reliability()
    build_depth_usage(SNAP_PATH)
    avail, avail_rows = build_availability_counts(week10)
    build_ablation(games, week10, avail)

    build_registers(slate, injuries, fams, consensus, avail_delta, standings_exact, n_clubs)
    with open(os.path.join(DATA, 'replacement_depth_2026.csv'), newline='') as fh:
        rep_rows = list(csv.DictReader(fh))
    build_deficiency(slate, avail_rows, rep_rows)
    build_flags(slate, avail_delta, drift_rows)

    manifest = {
        'built_utc': READ_UTC,
        'registration_sha256': sha256_file(os.path.join(HERE, 'preregistration.json')),
        'input_hashes': {
            name: sha256_file(os.path.join(INPUTS, name))
            for name in sorted(os.listdir(INPUTS))
        },
        'repository_inputs': {
            'games.csv.gz': sha256_file(CORPUS_PATH),
            'snap_counts_2026.csv.gz': sha256_file(SNAP_PATH),
            'capture_1118.csv': sha256_file(CAP_1118),
            'capture_1119_0657.csv': sha256_file(CAP_1119_06),
            'capture_wk10_1112.csv': sha256_file(CAP_WK10_1112),
        },
        'engine_sha256': sha256_file(os.path.join(HERE, 'engine.py')),
        'builder_sha256': sha256_file(os.path.abspath(__file__)),
    }
    with open(os.path.join(DATA, 'build_manifest.json'), 'w') as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write('\n')
    print('  wrote build_manifest.json')


if __name__ == '__main__':
    main()


