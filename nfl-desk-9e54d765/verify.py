#!/usr/bin/env python3
"""verify.py — fail-closed verification for desk 9e54d765.

The build is only publishable if every check below passes. Checks fall into five groups:

  1. structure   — the expected tables exist and hold the expected number of rows
  2. provenance  — every row that makes a factual claim carries a source link
  3. integrity   — the registration hash and every input hash still match the manifest
  4. rules       — the pre-registered rules that a careless edit could quietly break
                   (no backtest number on the leaderboard, no settled bets, closing cells
                   empty by policy, the sign convention still measured the same way)
  5. site        — no broken internal link, no placeholder text, no unescaped page

Run from anywhere:  python3 nfl-desk-9e54d765/verify.py
Exit code 0 = every check passed. Non-zero = do not publish.
"""
import csv
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
REPO = os.path.dirname(HERE)
INPUTS = os.path.join(HERE, 'inputs')

PASS, FAIL = [], []


def check(ok, name, detail=''):
    (PASS if ok else FAIL).append((name, detail))
    print(f'{"PASS" if ok else "FAIL"}  {name}' + (f'  [{detail}]' if detail else ''))
    return ok


def read(name):
    with open(os.path.join(DATA, name), newline='') as fh:
        return list(csv.DictReader(fh))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------------ 1. structure
EXPECTED_ROWS = {
    'sources.csv': 13,
    'origination_week11.csv': 52,
    'market_snapshots.csv': 156,
    'standings_reconciliation.csv': 32,
    'results_2026.csv': 150,
    'availability_week11.csv': 255,
    'availability_summary.csv': 26,
    'team_view_week11.csv': 26,
    'deficiency_matrix.csv': 26,
    'designation_reliability.csv': 22,
    'correlations.csv': 5,
    'backtest_families.csv': 5,
    'backtest_totals.csv': 1,
    'leaderboard.csv': 6,
    'questions.csv': 14,
    'suggestions.csv': 14,
    'flagged.csv': 15,
    'requirements.csv': 71,
    'availability_ablation.csv': 3,
    'availability_coefficients.csv': 4,
    'closing_policy.csv': 1,
    'sign_convention.csv': 2,
}


def check_structure():
    for name, n in EXPECTED_ROWS.items():
        rows = read(name)
        check(len(rows) == n, f'row count {name}', f'{len(rows)} rows, expected {n}')
    # every table has a header and no ragged rows
    for name in os.listdir(DATA):
        if not name.endswith('.csv'):
            continue
        with open(os.path.join(DATA, name), newline='') as fh:
            r = csv.reader(fh)
            header = next(r)
            bad = 0
            for row in r:
                if len(row) != len(header):
                    bad += 1
        check(bad == 0, f'no ragged rows {name}', f'{bad} bad')
    check(len(read('requirements.csv')) >= 60, 'requirement ledger covers the brief',
          f'{len(read("requirements.csv"))} rows')


# ----------------------------------------------------------------------- 2. provenance
def check_provenance():
    # every originated row carries its schedule URL, its market URL and a hash
    rows = read('origination_week11.csv')
    bad = [r for r in rows if not r['source_url'].startswith('https://www.nfl.com/')
           or not r['market_url'].startswith('https://sportsbook.')
           or len(r['inputs_sha256']) != 64]
    check(not bad, 'every originated row has both source links and a sha256',
          f'{len(bad)} bad of {len(rows)}')
    # market order is strictly 1..52 and cycles side,total,moneyline,moneyline
    orders = [int(r['market_order']) for r in rows]
    check(orders == list(range(1, len(rows) + 1)), 'market_order is a clean running sequence')
    seq = [r['market'] for r in rows]
    expected = []
    for _ in range(len(rows) // 4):
        expected += ['side', 'total', 'moneyline', 'moneyline']
    check(seq == expected, 'side, then total, then moneyline for every fixture')
    # the fair/market/difference columns are separate and consistent on every row
    bad = [r for r in rows
           if abs(float(r['fair_line']) - float(r['market_line'])
                  - float(r['difference_fair_minus_market'])) > 0.011]
    check(not bad, 'difference equals fair minus market on every row', f'{len(bad)} bad')
    # probabilities are in (0,1)
    bad = [r for r in rows if not (0.0 < float(r['probability']) < 1.0)]
    check(not bad, 'every probability is strictly inside (0,1)', f'{len(bad)} bad')
    # each of the 13 fixtures has four rows
    gid = {}
    for r in rows:
        gid[r['game_id']] = gid.get(r['game_id'], 0) + 1
    check(len(gid) == 13 and set(gid.values()) == {4}, '13 fixtures x 4 market rows',
          f'{len(gid)} fixtures, counts {sorted(set(gid.values()))}')

    # every availability row carries the official URL and a read clock
    avail = read('availability_week11.csv')
    bad = [r for r in avail if not r['source_url'].endswith('/2026/reg11')
           or not r['read_utc'].endswith('Z')]
    check(not bad, 'every availability row has the official URL and a UTC clock',
          f'{len(bad)} bad')
    # delta rows carry two clocks
    delta = read('injury_delta.csv')
    bad = [r for r in delta if not r['prior_read_utc'].endswith('Z')
           or not r['this_read_utc'].endswith('Z')]
    check(not bad, 'every delta row carries two read clocks', f'{len(bad)} bad of {len(delta)}')
    check(all(r['prior_read_utc'] != r['this_read_utc'] for r in delta),
          'the two clocks on a delta row are genuinely different reads')
    # correlations all have n and a source
    corr = read('correlations.csv')
    bad = [r for r in corr if not r['n'] or int(r['n']) < 3 or not r['source_url']]
    check(not bad, 'every correlation carries n and a source', f'{len(bad)} bad')
    # every flagged row carries evidence and a source link
    fl = read('flagged.csv')
    bad = [r for r in fl if not r['evidence'] or not r['source_url'].startswith('http')]
    check(not bad, 'every flag carries evidence and an https source', f'{len(bad)} bad')
    # every question and suggestion has a route / a falsifier
    qs = read('questions.csv')
    bad = [r for r in qs if not r['discovery_route'] or not r['source_url']]
    check(not bad, 'every question names a discovery route and a source', f'{len(bad)} bad')
    sg = read('suggestions.csv')
    bad = [r for r in sg if not r['what_would_change_our_mind'] or not r['review_status']]
    check(not bad, 'every suggestion has a two-sided falsifier and a review status',
          f'{len(bad)} bad')
    # every requirement has a status, a gate, an observed value and an evidence path
    rq = read('requirements.csv')
    bad = [r for r in rq if not r['status'] or not r['blocking_gate'] or not r['observed']
           or not r['evidence_path']]
    check(not bad, 'every requirement row is fully populated', f'{len(bad)} bad')
    allowed = {'MET', 'PARTIALLY MET', 'NOT MET', 'NOT APPLICABLE', 'SEE R24'}
    bad = [r for r in rq if r['status'] not in allowed]
    check(not bad, 'every requirement status is from the published vocabulary',
          f'{len(bad)} bad')
    # every source row carries a URL and a class
    src = read('sources.csv')
    bad = [r for r in src if not r['url'].startswith('http') or not r['source_class']]
    check(not bad, 'every source row has a URL and a class', f'{len(bad)} bad')


# ------------------------------------------------------------------------ 3. integrity
def check_integrity():
    with open(os.path.join(DATA, 'build_manifest.json')) as fh:
        man = json.load(fh)
    reg = sha256_file(os.path.join(HERE, 'preregistration.json'))
    check(man['registration_sha256'] == reg,
          'the pre-registration hash still matches the file it was taken from',
          f'{reg[:16]}…')
    for name, want in man['input_hashes'].items():
        got = sha256_file(os.path.join(INPUTS, name))
        check(got == want, f'input unchanged: {name}', f'{got[:12]}…')
    for name, want in man['repository_inputs'].items():
        # the manifest stores logical names; map them back
        path = {
            'games.csv.gz': os.path.join(REPO, 'data/decision-desk/raw/games.csv.gz'),
            'snap_counts_2026.csv.gz':
                os.path.join(REPO, 'data/decision-desk/raw/snap_counts_2026.csv.gz'),
            'capture_1118.csv':
                os.path.join(REPO, 'data/nfl-desk-6cbf25fa/injury_reads/'
                                    'capture_injuries_2026-11-18.csv'),
            'capture_1119_0657.csv':
                os.path.join(REPO, 'data/nfl-desk-6e13b9ff/'
                                    'wk11_tnf_injury_2026-06.csv'),
            'capture_wk10_1112.csv':
                os.path.join(REPO, 'data/decision-desk/official/'
                                    'official_injuries_wk10.csv'),
        }.get(name)
        if path is None or not os.path.exists(path):
            # the 06:57 capture lives under a slightly different name; resolve by prefix
            cand = None
            base = os.path.join(REPO, 'data/nfl-desk-6e13b9ff')
            if os.path.isdir(base):
                for f in os.listdir(base):
                    if f.startswith('wk11_tnf_injury'):
                        cand = os.path.join(base, f)
            path = cand
        check(path is not None and os.path.exists(path),
              f'repository input present: {name}')
        if path and os.path.exists(path):
            check(sha256_file(path) == want, f'repository input unchanged: {name}',
                  f'{want[:12]}…')
    check(sha256_file(os.path.join(HERE, 'engine.py')) == man['engine_sha256'],
          'engine.py unchanged since the build')
    check(sha256_file(os.path.join(HERE, 'build_data.py')) == man['builder_sha256'],
          'build_data.py unchanged since the build')


# ---------------------------------------------------------------------------- 4. rules
def check_rules():
    lb = read('leaderboard.csv')
    # no backtest number on the ranked board
    forbidden = ('brier_skill_vs_close', 'brier_skill', 'backtest_skill', 'brier')
    bad = [r for r in lb for k in r if k.lower() in forbidden]
    check(not bad, 'no backtest column exists on the leaderboard')
    bad = [r for r in lb if r['status'] == 'PAPER' and r['n_settled'] not in ('0', '')]
    check(not bad, 'no settled bets exist on the ranked board', f'{len(bad)} bad')
    check(all(r['certified'] == 'no' for r in lb), 'nothing is certified')
    check(all(r['backtest_reference'] for r in lb),
          'every board row says where the backtest lives instead')
    check(all(r['demotion_trigger'] and r['what_would_change_our_mind'] for r in lb),
          'every board row carries a demotion trigger and a two-sided falsifier')
    # signal and staking are separate columns and are not equal
    check(any(r['signal_value'] and r['staking_roi'] and r['signal_value'] != r['staking_roi']
              for r in lb), 'signal and staking are separate, distinct values')
    # combo divisions are blocked, never ranked
    combos = [r for r in lb if 'parlay' in r['division'] or 'combo' in r['division']]
    check(len(combos) == 3 and all(r['status'] == 'BLOCKED' for r in combos),
          'the three combo divisions are published as BLOCKED')
    # closing cells are empty and explained
    snaps = read('market_snapshots.csv')
    check(all(r['closing_line'] == '' and r['closing_price'] == '' for r in snaps),
          'no closing value is invented')
    cp = read('closing_policy.csv')[0]
    check(cp['status'] == 'NOT READ' and cp['clear_by'],
          'the closing gap is explained and has a clearing condition')
    # the registration file states the demotion gate and the combo gate
    with open(os.path.join(HERE, 'preregistration.json')) as fh:
        reg = json.load(fh)
    check(bool(reg['demotion_gate']['triggers']), 'the demotion gate is frozen in the '
                                                  'registration')
    check('joint' in reg['combo_gate']['rule'].lower(), 'the combo gate is frozen in the '
                                                        'registration')
    check(reg['leaderboard_rules']['no_staking_in_signal_score'] is True,
          'the registration forbids mixing staking into the signal score')
    # sign convention is measured, not assumed
    sc = read('sign_convention.csv')
    chosen = [r for r in sc if r['chosen'] == 'yes']
    check(len(chosen) == 1, 'exactly one sign convention is chosen')
    check(float(chosen[0]['corr_stored_line_realised_home_margin']) > 0.2,
          'the chosen convention is supported by a positive correlation with the realised '
          'margin', chosen[0]['corr_stored_line_realised_home_margin'])
    check(float(chosen[0]['mean_abs_error']) < min(
        float(r['mean_abs_error']) for r in sc if r['chosen'] == 'no'),
        'the chosen convention has the lower mean absolute error')
    # reconciliation is complete
    rec = read('standings_reconciliation.csv')
    check(all(r['match'] == 'yes' for r in rec), '32/32 clubs reconcile to the official '
                                                 'standings', f'{sum(1 for r in rec if r["match"] == "yes")} exact')
    # no fixed penalty anywhere: the ablation must estimate coefficients
    co = read('availability_coefficients.csv')
    check(len(co) >= 3 and all('estimated' in r['note'].lower() for r in co),
          'availability effects are estimated coefficients, not fixed penalties')
    ab = read('availability_ablation.csv')
    check(any('DIFFERENCE' in r['variant'] for r in ab),
          'the ablation publishes the with-minus-without difference')
    check(any('no fixed point penalty' in r['note'].lower() for r in ab),
          'the ablation states that no fixed penalty is applied')
    # the headline negative result is present and not soft-pedalled
    fams = read('backtest_families.csv')
    model = next(r for r in fams if r['family'] == 'F4_OPPONENT_AWARE')
    check(float(model['skill_hi95']) < 0,
          'the model skill interval is wholly below zero and is published that way',
          f'[{model["skill_lo95"]}, {model["skill_hi95"]}]')
    check(any(r['family'] == 'F2_RANDOM' for r in fams),
          'a random control is scored beside the model')
    check(any(r['family'] == 'F3_FAVOURITE_ONLY' for r in fams),
          'a favourites-only control is scored beside the model')
    # a corpus-coverage table exists and shows the holes
    cov = read('corpus_coverage.csv')
    check(any(int(r['no_score_at_all']) > 0 for r in cov),
          'the weeks with no score in the pinned dataset are published')
    # the reliability study publishes a denominator and a numerator
    rel = read('designation_reliability.csv')
    check(all(int(r['designated_rows']) >= int(r['played_rows']) for r in rel),
          'no reliability row has more played rows than designated rows')
    # no availability row pretends a replacement is known
    tv = read('team_view_week11.csv')
    check(all('NOT CONFIRMED' in r['replacement_named'] for r in tv),
          'no team row claims a confirmed replacement')


# ----------------------------------------------------------------------------- 5. site
def check_site():
    pages = [f for f in os.listdir(HERE) if f.endswith('.html')]
    check(len(pages) == 12, 'site page count', f'{len(pages)} pages')
    allhtml = {}
    for p in pages:
        with open(os.path.join(HERE, p), encoding='utf-8') as fh:
            allhtml[p] = fh.read()
    # no placeholder text survives
    for token in ('TODO', 'FIXME', 'lorem', 'None', ' nan ', 'NaN'):
        bad = [p for p, t in allhtml.items() if token in t]
        if token in ('{', '}}'):
            continue
        check(not bad, f'no {token!r} on any page', ', '.join(bad))
    # internal links resolve
    missing = []
    for p, t in allhtml.items():
        for href in re.findall(r'href="([^"]+)"', t):
            if href.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            target = os.path.join(HERE, href.split('#')[0])
            if not os.path.exists(target):
                missing.append(f'{p} -> {href}')
    check(not missing, 'no broken internal link', '; '.join(missing[:5]))
    # every page carries the nav and a source discipline line
    for p in pages:
        check('nav' in allhtml[p] and 'Flagged for review' in allhtml[p],
              f'{p} carries the shared navigation')
    # the landing page states the negative result
    check('negative result' in allhtml['index.html'],
          'the landing page states the negative result in the headline')
    # no page prints an empty table cell without a marker
    for p in pages:
        empties = re.findall(r'<td></td>', allhtml[p])
        check(not empties, f'{p} has no silently empty cell', f'{len(empties)} found')
    # every page that shows a table also shows a source link
    for p in pages:
        if '<table' in allhtml[p]:
            check('href="https://' in allhtml[p], f'{p} links out to a source')
    # the flagged page lists every flag id
    fl = read('flagged.csv')
    check(all(r['id'] in allhtml['flagged.html'] for r in fl),
          'every flag is rendered on the flagged page')


def main():
    print('verify.py — desk 9e54d765\n')
    for fn in (check_structure, check_provenance, check_integrity, check_rules, check_site):
        print(f'--- {fn.__name__} ---')
        fn()
    print(f'\n{len(PASS)} checks, {len(FAIL)} failures')
    if FAIL:
        print('\nFAILURES')
        for name, detail in FAIL:
            print(f'  FAIL {name}  {detail}')
        print('\nDO NOT PUBLISH')
        return 1
    print('ALL CHECKS PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
