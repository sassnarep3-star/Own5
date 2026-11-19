#!/usr/bin/env python3
"""Fail-closed verifier for the 8ad92a0e desk. Exit 1 on any failure.
Checks: pinned counts, row provenance, blank-by-policy cells, arithmetic identities,
internal link integrity, and registration discipline."""
import csv, json, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, 'data', 'nfl-desk-8ad92a0e')

FAILURES = []
CHECKS = 0


def ck(cond, label):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILURES.append(label)


def rd(name):
    with open(os.path.join(DATA, name), newline='') as f:
        return list(csv.DictReader(f))


def main():
    stand = rd('standings_2026_reg_20261119.csv')
    sched = rd('schedule_2026_wk11.csv')
    results = rd('results_2026_through_wk10.csv')
    lines = rd('lines_wk11.csv')
    snaps = rd('price_snapshots.csv')
    corr = rd('correlations.csv')
    luck = rd('luck_panel.csv')
    reqs = rd('requirements.csv')
    qs = rd('questions.csv')
    sug = rd('suggestions.csv')
    flags = rd('flagged.csv')
    srcs = rd('sources.csv')
    gates = rd('gates.csv')
    strats = rd('strategies.csv')
    lb = rd('leaderboard.csv')
    clubs = rd('injury_wk11_clubs.csv')
    players = rd('injury_wk11_players.csv')
    spec = json.load(open(os.path.join(DATA, 'model_spec.json')))

    # ---- V1 pinned counts (drift alarm) ----
    pins = [('standings', len(stand), 32), ('schedule rows', len(sched), 19),
            ('results', len(results), 150), ('lines', len(lines), 39),
            ('snapshots', len(snaps), 39), ('correlations', len(corr), 9),
            ('luck', len(luck), 10), ('requirements', len(reqs), 65),
            ('questions', len(qs), 18), ('suggestions', len(sug), 14),
            ('flags', len(flags), 18), ('sources', len(srcs), 10),
            ('gates', len(gates), 12), ('strategies', len(strats), 6),
            ('leaderboard', len(lb), 6), ('injury clubs', len(clubs), 26),
            ('injury players', len(players), 253)]
    for name, got, want in pins:
        ck(got == want, f'V1 {name}: {got} != pinned {want}')

    # ---- V2 provenance: every row of every CSV has an https source ----
    for name, rows in [('standings', stand), ('schedule', sched), ('results', results),
                       ('lines', lines), ('snapshots', snaps), ('correlations', corr),
                       ('requirements', reqs), ('questions', qs), ('suggestions', sug),
                       ('flagged', flags), ('sources', srcs), ('gates', gates),
                       ('strategies', strats), ('leaderboard', lb),
                       ('injury clubs', clubs), ('injury players', players)]:
        for i, r in enumerate(rows, 2):
            u = r.get('source_url', '') or r.get('url', '')
            ck(u.startswith('https://'), f'V2 {name} row {i}: missing https source_url')
            if u:
                host = re.match(r'https://([^/]+)', u).group(1)
                ck(host in ('www.nfl.com', 'github.com', 'sassnarep3-star.github.io'),
                   f'V2 {name} row {i}: host {host} not allowlisted')
    for i, r in enumerate(luck, 2):
        ck(r['source_file'] == 'results_2026_through_wk10.csv', f'V2 luck row {i}: source_file')

    # ---- V3 reconciliation 32/32 ----
    wl = defaultdict(lambda: [0, 0, 0, 0, 0])
    for r in results:
        a, h, ap, hp = r['away'], r['home'], int(r['away_pts']), int(r['home_pts'])
        if ap > hp:
            wl[a][0] += 1; wl[h][1] += 1
        elif hp > ap:
            wl[h][0] += 1; wl[a][1] += 1
        else:
            wl[a][2] += 1; wl[h][2] += 1
        wl[a][3] += ap; wl[a][4] += hp
        wl[h][3] += hp; wl[h][4] += ap
    exact = 0
    for s in stand:
        if wl[s['club']] == [int(s['w']), int(s['l']), int(s['t']), int(s['pf']), int(s['pa'])]:
            exact += 1
    ck(exact == 32, f'V3 reconciliation: {exact}/32 clubs')
    ck(sum(int(r['w']) for r in stand) == sum(int(r['l']) for r in stand), 'V3 league W=L')
    ck(sum(int(r['pf']) for r in stand) == sum(int(r['pa']) for r in stand), 'V3 league PF=PA')

    # ---- V4 schedule integrity: 32 clubs exactly once; 13 games + 6 byes ----
    games = [r for r in sched if r['game_id']]
    byes = [r for r in sched if not r['game_id']]
    ck(len(games) == 13, f'V4 games {len(games)}')
    ck(len(byes) == 6, f'V4 byes {len(byes)}')
    seen = [r['away'] for r in games] + [r['home'] for r in games] + [r['bye_club'] for r in byes]
    ck(sorted(seen) == sorted(s['club'] for s in stand), 'V4 clubs exactly once')

    # ---- V5 lines: order side<total<ML; market cells blank; probability ranges ----
    order_rank = {'1-SIDE': 1, '2-TOTAL': 2, '3-MONEYLINE': 3}
    by_game = defaultdict(list)
    for r in lines:
        by_game[r['game_id']].append(r)
        ck(r['market'] in ('SIDE', 'TOTAL', 'MONEYLINE'), f'V5 market {r["game_id"]}')
        ck(r['market_line'] == '' and r['market_price'] == '' and r['difference'] == '',
           f'V5 market cells not blank: {r["game_id"]} {r["market"]}')
        ck(re.fullmatch(r'[0-9a-f]{16}', r['inputs_sha256']) is not None,
           f'V5 inputs hash {r["game_id"]}')
        p = float(r['model_prob_home_or_over'])
        ck(0.0 <= p <= 1.0, f'V5 prob range {r["game_id"]}')
    for g, rs in by_game.items():
        ck(len(rs) == 3, f'V5 {g}: {len(rs)} markets')
        ranks = [order_rank[r['order']] for r in sorted(rs, key=lambda x: x['order'])]
        ck(ranks == [1, 2, 3], f'V5 {g}: origination order {ranks} (side->total->ML)')

    # ---- V6 snapshots: open only, market cells blank ----
    for r in snaps:
        ck(r['status'] == 'OPEN', f'V6 status {r["snapshot_id"]}')
        ck(r['market_open'] == '' and r['market_close'] == '', f'V6 market cells {r["snapshot_id"]}')
        ck(r['opened_at'] == '2026-11-19T11:30:00Z', f'V6 opened_at {r["snapshot_id"]}')

    # ---- V7 leaderboard: no performance values, no backtest/ROI columns ----
    lb_cols = set(lb[0].keys()) if lb else set()
    for bad in ('roi', 'backtest', 'return_pct', 'profit'):
        ck(not any(bad in c.lower() for c in lb_cols), f'V7 forbidden column {bad}')
    for r in lb:
        ck(r['signal_score'] == '' and r['signal_n'] == '' and r['staking_return'] == '',
           f'V7 performance cell not blank: {r["strategy_id"]}')
        ck('backtest' not in r['grading_note'].lower().replace('backtest numbers forbidden', ''),
           f'V7 backtest number on board: {r["strategy_id"]}')

    # ---- V8 strategies: registration commit + two-sided change-mind field ----
    for r in strats:
        ck(re.fullmatch(r'[0-9a-f]{40}', r['pre_reg_commit']) is not None,
           f'V8 pre_reg_commit {r["strategy_id"]}')
        ck(r['what_would_change_our_mind'].strip() != '', f'V8 change-mind field {r["strategy_id"]}')
        ck(r['demotion_rule'].strip() != '', f'V8 demotion field {r["strategy_id"]}')

    # ---- V9 model identity recompute from standings ----
    L = spec['league_scoring_mean']; K = spec['shrinkage_k']
    hfa = spec['hfa_estimate_pts']; sigma = spec['sigma_margin']
    st = {r['club']: r for r in stand}
    def rates(c):
        gp = int(st[c]['w']) + int(st[c]['l']) + int(st[c]['t'])
        pf = (int(st[c]['pf']) + L * K) / (gp + K)
        pa = (int(st[c]['pa']) + L * K) / (gp + K)
        return pf, pa
    for g in games:
        rs = {r['market']: r for r in by_game[g['game_id']]}
        pf_a, pa_a = rates(g['away']); pf_h, pa_h = rates(g['home'])
        exp_h = (pf_h + pa_a) / 2.0; exp_a = (pf_a + pa_h) / 2.0
        margin = (exp_h - exp_a) + hfa; total = exp_h + exp_a
        ck(abs(float(rs['SIDE']['expected_home_margin_or_total']) - margin) < 0.051,
           f'V9 side margin {g["game_id"]}')
        ck(abs(float(rs['SIDE']['model_fair_line']) - (-margin)) < 0.051, f'V9 side line {g["game_id"]}')
        ck(abs(float(rs['TOTAL']['model_fair_line']) - total) < 0.051, f'V9 total {g["game_id"]}')

    # ---- V10 injuries: club sums match player rows; designations pinned ----
    pcount = Counter(p['club'] for p in players)
    out_n = sum(1 for p in players if p['game_status'] == 'Out')
    q_n = sum(1 for p in players if p['game_status'] == 'Questionable')
    ck(out_n == 9 and q_n == 7, f'V10 designations Out={out_n} Q={q_n}')
    for c in clubs:
        ck(int(c['rows']) == pcount[c['club']], f'V10 club row count {c["club"]}')
    ck(sum(int(c['rows']) for c in clubs) == 253, 'V10 total rows')

    # ---- V11 correlations: n published and correct ----
    for r in corr:
        n = int(r['n'])
        ck(n in (32, 150), f'V11 n value {r["corr_id"]}')
        ck(abs(float(r['r'])) <= 1.0, f'V11 r range {r["corr_id"]}')
        ck(r['ci95_low'] != '' and r['ci95_high'] != '', f'V11 CI missing {r["corr_id"]}')

    # ---- V12 requirements: gate + number on every row ----
    for r in reqs:
        ck(r['blocking_gate'].strip() != '', f'V12 gate {r["req_id"]}')
        ck(r['number_to_clear'].strip() != '', f'V12 number {r["req_id"]}')
        ck(r['status'] in ('MET', 'PARTIAL', 'BLOCKED', 'OPEN', 'RULE-ADOPTED'),
           f'V12 status {r["req_id"]}')

    # ---- V13 questions/suggestions discipline ----
    for r in qs:
        ck(r['discovery_route'].strip() != '', f'V13 route {r["q_id"]}')
        ck(r['answer'] == '', f'V13 answer must stay blank until sourced: {r["q_id"]}')
    for r in sug:
        ck(r['decision'] == '', f'V13 decision must stay blank (owner decides): {r["s_id"]}')
        ck(r['status'] == 'PROPOSED', f'V13 status {r["s_id"]}')

    # ---- V14 HTML pages exist; internal links resolve; no plain-http ----
    pages = [f for f in os.listdir(HERE) if f.endswith('.html')]
    ck(len(pages) == 12, f'V14 page count {len(pages)}')
    href_re = re.compile(r'href="([^"]+)"')
    for pg in pages:
        html = open(os.path.join(HERE, pg)).read()
        for h in href_re.findall(html):
            if h.startswith('https://'):
                ck(not h.startswith('http://'), f'V14 plain http in {pg}')
                continue
            if h.startswith('#') or h.startswith('mailto:'):
                continue
            target = h.split('#')[0]
            ck(os.path.exists(os.path.join(HERE, target)), f'V14 broken link {pg} -> {h}')

    # ---- V15 flagged register completeness ----
    sev = Counter(f['severity'] for f in flags)
    ck(len(flags) == 18, 'V15 flag count')
    ck(all(f['status'] == 'OPEN' for f in flags), 'V15 flag status')
    ck(sev['BLOCKING'] >= 1, 'V15 at least one blocking flag')

    print(f'verify: {CHECKS} checks, {len(FAILURES)} failures')
    for f in FAILURES[:40]:
        print('  FAIL:', f)
    if FAILURES:
        sys.exit(1)
    print('PASS all desk checks')


if __name__ == '__main__':
    main()
