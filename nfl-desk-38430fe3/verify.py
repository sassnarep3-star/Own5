"""Verification for desk 38430fe3. Exits non-zero on any failure.

Checks: recomputed counts equal the published numbers; every row has an official link or an
explicit 'internal evidence only' / UNVERIFIED marker; every evidence path exists in the repo;
every internal HTML link resolves; the build is deterministic (two builds, identical bytes).
"""
import csv, hashlib, html.parser, json, os, re, subprocess, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import content as C

fails = []
def check(cond, msg):
    if not cond: fails.append(msg)
    return cond

def read_csv(name):
    with open(os.path.join(HERE, 'data', name), encoding='utf-8') as f:
        return list(csv.DictReader(f))

def digest_tree(paths):
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(p.encode()); h.update(open(p, 'rb').read())
    return h.hexdigest()

def main():
    subprocess.run([sys.executable, os.path.join(HERE, 'build.py')], check=True, stdout=subprocess.DEVNULL)
    S = json.load(open(os.path.join(HERE, 'data', 'summary.json')))
    rows = read_csv('injury_report_wk10_2026-11-18.csv')
    teams = read_csv('injury_report_team_summary.csv')

    # --- transcript integrity: count, hash, and the transcription's own consistency
    trans = [l for l in open(os.path.join(HERE, 'raw', 'injury_report_wk10_transcript.psv'), encoding='utf-8') if not l.startswith('#') and l.strip()]
    check(len(trans) == len(rows) == 347, f'row count: transcript {len(trans)}, csv {len(rows)}, expected 347')
    check(hashlib.sha256(open(os.path.join(HERE,'raw','injury_report_wk10_transcript.psv'),'rb').read()).hexdigest() == S['transcript_sha256'], 'transcript hash drifted')
    check(all(r['source_url'] == C.INJ for r in rows), 'every injury row must link to the official Week 10 page')
    check(len({r['row_id'] for r in rows}) == len(rows), 'row ids must be unique')
    check(sum(int(t['rows']) for t in teams) == 347, 'team rows must sum to 347')
    check(len(teams) == 28, 'expected 28 clubs')
    check(len({r['game_no'] for r in rows}) == 14, 'expected 14 games')
    check(len({r['team_code'] for r in rows}) == 28, 'team codes must be 28')

    # --- recomputed numbers equal the published numbers
    with_gs = [r for r in rows if r['game_status']]
    check(len(with_gs) == 171 == S['with_game_status'], 'game-status count must be 171')
    check(sum(1 for r in rows if r['injury']) == 171, 'injury-entry count must be 171')
    check(sum(1 for r in rows if not r['injury'] and r['practice_status'].startswith('Did Not')) == 16, 'DNP-no-injury must be 16')
    check(sum(1 for t in teams if int(t['with_injury']) == 0) == 0, 'no club may have zero injury entries (claim C-01)')
    check(sum(1 for r in rows if r['game_status']=='Out') == S['out'] == 70, 'Out count')
    check(sum(1 for r in rows if r['game_status']=='Doubtful') == S['doubtful'] == 11, 'Doubtful count')
    check(sum(1 for r in rows if r['game_status']=='Questionable') == S['questionable'] == 90, 'Questionable count')
    lions = {r['player']: r['game_status'] for r in rows if r['team_name']=='Lions' and r['player'] in ('Kerby Joseph','Cade Mays','D.J. Reed')}
    check(lions == {'Kerby Joseph':'Out','Cade Mays':'Out','D.J. Reed':'Out'}, 'Lions designations (claim C-06)')
    sea = [r for r in rows if r['team_code']=='SEA']
    cin = [r for r in rows if r['team_code']=='CIN']
    check(len(sea)==15 and sum(1 for r in sea if r['injury'])==4, 'Seattle 15 rows / 4 injury entries (C-04)')
    check(len(cin)==9 and sum(1 for r in cin if r['injury'])==4, 'Cincinnati 9 rows / 4 injury entries (C-05)')
    check(not any(r['team_code']=='BAL' and r['player']=='Lamar Jackson' for r in rows), 'Lamar Jackson must be absent from the Ravens table (C-08)')
    check(not any(r['team_code']=='MIA' and r['player']=='Malik Willis' for r in rows), 'Willis absent from Dolphins table (C-07)')

    # --- deltas arithmetic
    d = S['delta']
    check(d['common'] == d['changed'] + d['unchanged'], 'delta: common = changed + unchanged')
    check(d['live_rows'] == d['common'] + d['added'], 'delta: live rows = common + added')
    check(d['old_rows'] == d['common'] + d['removed'], 'delta: old rows = common + removed')
    check(d['old_with_game_status'] == 6 and d['old_rows'] == 276 and d['old_clubs'] == 26, 'baseline figures (C-02, C-03)')
    p = S['partial_1117']
    check(p['compared'] == p['identical'] + p['different'] and p['different'] == 0, '2026-11-17 partial read: all overlapping rows agree')
    check(p['compared'] == 49, 'partial read overlap count is 49')

    # --- every requirement / claim / flag / source row: link or explicit marker, and evidence exists
    for r in C.REQS:
        ok_src = r[8].startswith('https://') or r[8] == 'internal evidence only'
        check(ok_src, f'{r[0]}: source must be an official URL or internal evidence only')
        if r[7]:
            check(os.path.exists(os.path.join(ROOT, r[7])), f'{r[0]}: evidence path missing: {r[7]}')
        check(r[3] in ('MET','PARTIAL','BLOCKED','NOT STARTED','REJECTED'), f'{r[0]}: bad status {r[3]}')
        check(bool(r[4]) and bool(r[5]), f'{r[0]}: blocking gate and clearing number required')
    check(len(C.REQS) == len({r[0] for r in C.REQS}), 'requirement ids unique')
    for c in C.CLAIMS:
        s = c['source']
        if s.startswith('https://www.nfl.com/'):
            pass
        elif s.startswith('https://github.com/sassnarep3-star/Own5/blob/main/'):
            check(os.path.exists(os.path.join(ROOT, s.replace('https://github.com/sassnarep3-star/Own5/blob/main/',''))), f"{c['id']}: repo evidence missing")
    for f_ in C.FLAGS:
        check(f_[5].startswith('https://') or f_[5]=='internal evidence only', f'{f_[0]}: flag must have a source link or be marked internal')
    for s_ in C.SOURCES:
        check(s_[2].startswith('https://'), f'{s_[0]}: source needs a URL')
    for s_ in C.SUGGESTIONS:
        check(s_[5].startswith('https://') or s_[5]=='internal evidence only', f'{s_[0]}: suggestion source')
    for q in C.QUESTIONS:
        check(q[4].startswith('https://') or q[4]=='internal evidence only', f'{q[0]}: question source')

    # --- HTML: internal links resolve, and rows carry a link or marker
    class P(html.parser.HTMLParser):
        def __init__(s):
            super().__init__(); s.links=[]; s.rows=[]; s.cur=None; s.in_row=False; s.row_has=False; s.table_cls=None
        def handle_starttag(s, tag, attrs):
            a = dict(attrs)
            if tag=='a' and 'href' in a: s.links.append(a['href'])
            if tag=='tr': s.in_row=True; s.row_has=False; s.row_text=''; s.row_links=0
            if tag=='a' and s.in_row: s.row_links+=1
        def handle_endtag(s, tag):
            if tag=='tr' and s.in_row:
                s.in_row=False
                s.rows.append((s.row_links, s.row_text))
        def handle_data(s, data):
            if s.in_row: s.row_text = getattr(s,'row_text','') + data
    pages = [f for f in os.listdir(HERE) if f.endswith('.html')]
    check(len(pages) >= 11, 'expected at least 11 pages')
    for pg in pages:
        text = open(os.path.join(HERE, pg), encoding='utf-8').read()
        parser = P(); parser.feed(text)
        for href in parser.links:
            if href.startswith(('http://','https://','#','mailto:')) or href.startswith('javascript'): continue
            target = href.split('#')[0]
            check(os.path.exists(os.path.join(HERE, target)), f'{pg}: broken internal link {href}')
        if pg == 'injuries.html':
            trs = [r for r in parser.rows if r[1].strip() and 'WK10-' in r[1]]
            check(len(trs) == 347, f'injuries.html must render 347 data rows, found {len(trs)}')
            check(all(n >= 1 for n,_ in trs), 'every injuries row must carry a link')
        if pg in ('claims.html','requirements.html','questions.html','suggestions.html','flagged.html','sources.html'):
            body_rows = [r for r in parser.rows if r[0] >= 0]
            for n, txt in body_rows:
                if txt.strip() and 'ID' not in txt[:4] and 'Source' not in txt[:10]:
                    check(n >= 1 or 'internal evidence only' in txt or 'UNVERIFIED' in txt, f'{pg}: a row has no source link or marker')

    # --- determinism: a second build changes no bytes
    before = {}
    targets = [os.path.join(HERE,'data',f) for f in os.listdir(os.path.join(HERE,'data'))] + [os.path.join(HERE,f) for f in os.listdir(HERE) if f.endswith('.html')]
    for t in targets: before[t] = hashlib.sha256(open(t,'rb').read()).hexdigest()
    subprocess.run([sys.executable, os.path.join(HERE,'build.py')], check=True, stdout=subprocess.DEVNULL)
    for t in targets:
        check(hashlib.sha256(open(t,'rb').read()).hexdigest() == before[t], f'non-deterministic output: {os.path.basename(t)}')

    if fails:
        print('FAIL', len(fails)); [print(' -', f) for f in fails]; sys.exit(1)
    print(f"verify: {S['rows']} injury rows · {S['clubs']} clubs · {S['games']} games · {len(C.REQS)} requirements · "
          f"{len(C.CLAIMS)} claims · {len(C.FLAGS)} flags · {len(pages)} pages · PASS (counts, provenance, evidence paths, links, determinism)")

if __name__ == '__main__':
    main()
