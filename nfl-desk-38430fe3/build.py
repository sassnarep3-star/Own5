"""Build the 38430fe3 desk from the hand transcript of the official Week 10 injury report.

Reads only files inside this desk plus the two named repo artifacts (2026-11-12 capture and the
2026-11-17 partial read). Writes CSV/JSON data and static HTML. No timestamps are generated at
build time, so two builds produce identical bytes (verify.py checks this).
"""
import csv, collections, hashlib, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import content as C

TRANSCRIPT = os.path.join(HERE, "raw", "injury_report_wk10_transcript.psv")
OLD_CAPTURE = os.path.join(REPO_ROOT, "data", "decision-desk", "official", "official_injuries_wk10.csv")
PARTIAL_1117 = os.path.join(REPO_ROOT, "nfl-desk-35a1feb2", "raw", "official_reads_2026-11-17.txt")
READ_DATE = "2026-11-18"
READ_WINDOW = "2026-11-18 (fetch tool returns no clock time; the date is the only time recorded)"

NICK = {'WAS':'Commanders','NYG':'Giants','NE':'Patriots','DET':'Lions','KC':'Chiefs','ATL':'Falcons',
 'MIN':'Vikings','GB':'Packers','JAX':'Jaguars','TEN':'Titans','BUF':'Bills','NYJ':'Jets','MIA':'Dolphins',
 'IND':'Colts','CAR':'Panthers','NO':'Saints','HOU':'Texans','CLE':'Browns','LAR':'Rams','AZ':'Cardinals',
 'SEA':'Seahawks','LV':'Raiders','SF':'49ers','DAL':'Cowboys','PIT':'Steelers','CIN':'Bengals','LAC':'Chargers','BAL':'Ravens'}
ABBR = {'FP':'Full Participation in Practice','LP':'Limited Participation in Practice','DNP':'Did Not Participate In Practice'}

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f: h.update(f.read())
    return h.hexdigest()

def read_transcript():
    rows = []
    for line in open(TRANSCRIPT, encoding='utf-8'):
        if line.startswith('#') or not line.strip(): continue
        g, date, kick, net, tm, pl, pos, inj, prac, gs = line.rstrip('\n').split('|')
        rows.append(dict(game=g, date=date, kickoff=kick, network=net, team_code=tm, team=NICK[tm],
                         player=pl, position=pos, injury=inj, practice=prac, game_status=gs))
    for i, r in enumerate(rows, 1): r['row_id'] = f"WK10-{i:04d}"
    return rows

def read_old():
    out = {}
    for o in csv.DictReader(open(OLD_CAPTURE, encoding='utf-8')):
        out[(o['team_nickname'], o['player'])] = o
    return out

def read_partial_1117():
    """Parse the 2026-11-17 partial read (sibling desk transcription, section R8)."""
    with open(PARTIAL_1117, encoding='utf-8') as fh:
        txt = fh.read()
    block = txt.split('[R8]', 1)[1].split('[R9]', 1)[0]
    found = {}
    team = None
    for raw in re.split(r'\n|·', block):
        tok = raw.strip()
        m = re.match(r'^([A-Z]{2,3}):\s*(.*)$', tok)
        if m:
            team = m.group(1); tok = m.group(2)
        if tok.count('|') != 4 or team is None: continue
        parts = [p.strip() for p in tok.split('|')]
        name = parts[0]
        if 'cut off' in parts[4] or 'not read' in parts[4].lower(): continue
        def clean(v): return '' if v == '(blank)' else v.strip('()')
        prac = clean(parts[3]); prac = ABBR.get(prac, prac)
        gs = clean(parts[4])
        found[(team, name)] = (clean(parts[2]), prac, gs)
    return found

def main():
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    rows = read_transcript()
    digest = sha256(TRANSCRIPT)
    old = read_old()
    partial = read_partial_1117()

    # ---- row-level CSV
    fields = ['row_id','game_no','game_date','kickoff_et_as_printed','networks','team_code','team_name',
              'player','position','injury','practice_status','game_status','source_url','read_date','read_window','transcript_sha256']
    with open(os.path.join(HERE,'data','injury_report_wk10_2026-11-18.csv'),'w',newline='',encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(fields)
        for r in rows:
            w.writerow([r['row_id'], r['game'], r['date'], r['kickoff'], r['network'], r['team_code'], r['team'],
                        r['player'], r['position'], r['injury'], r['practice'], r['game_status'], C.INJ,
                        READ_DATE, READ_WINDOW, digest])

    # ---- team summary
    teams = collections.OrderedDict()
    for r in rows:
        d = teams.setdefault(r['team_code'], collections.Counter(team=r['team'], game=r['game']))
        d['rows'] += 1
        if r['injury']: d['with_injury'] += 1
        if r['game_status'] == 'Out': d['out'] += 1
        if r['game_status'] == 'Doubtful': d['doubtful'] += 1
        if r['game_status'] == 'Questionable': d['questionable'] += 1
        if r['game_status']: d['with_game_status'] += 1
        if not r['injury'] and r['practice'].startswith('Did Not'): d['dnp_no_injury'] += 1
    team_rows = []
    for code, d in teams.items():
        team_rows.append(dict(team_code=code, team=d['team'], game_no=d['game'], rows=d['rows'],
            with_injury=d['with_injury'], out=d['out'], doubtful=d['doubtful'], questionable=d['questionable'],
            out_or_doubtful=d['out']+d['doubtful'], with_game_status=d['with_game_status'],
            dnp_no_injury=d['dnp_no_injury'], starters_out='', replacements_named='', source_url=C.INJ))
    tf = list(team_rows[0].keys())
    with open(os.path.join(HERE,'data','injury_report_team_summary.csv'),'w',newline='',encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=tf); w.writeheader(); w.writerows(team_rows)

    # ---- delta: 2026-11-12 repo capture -> 2026-11-18 read
    live = {(r['team'], r['player']): r for r in rows}
    drows = []
    changed = added = removed = unchanged = 0
    for k, r in live.items():
        if k in old:
            o = old[k]
            before = (o['injury'], o['practice_status'], o['game_status'])
            after = (r['injury'], r['practice'], r['game_status'])
            kind = 'unchanged' if before == after else 'changed'
            if kind == 'changed': changed += 1
            else: unchanged += 1
            drows.append([kind, r['team'], r['player'], *before, *after, 'nfl.com 2026-11-12 (repo capture)', C.INJ])
        else:
            added += 1
            drows.append(['added', r['team'], r['player'], '', '', '', r['injury'], r['practice'], r['game_status'], '', C.INJ])
    for k, o in old.items():
        if k not in live:
            removed += 1
            drows.append(['removed', k[0], k[1], o['injury'], o['practice_status'], o['game_status'], '', '', '', '', C.INJ])
    with open(os.path.join(HERE,'data','delta_2026-11-12_to_2026-11-18.csv'),'w',newline='',encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['change','team','player','injury_2026_11_12','practice_2026_11_12','game_status_2026_11_12',
                    'injury_2026_11_18','practice_2026_11_18','game_status_2026_11_18','note','source_url'])
        w.writerows(drows)
    old_inj = sum(1 for o in old.values() if o['injury'])
    old_gs = sum(1 for o in old.values() if o['game_status'])
    old_teams = len(set(o['team_nickname'] for o in old.values()))
    delta_summary = dict(old_rows=len(old), old_clubs=old_teams, old_with_injury=old_inj, old_with_game_status=old_gs,
        live_rows=len(rows), live_clubs=len(teams), live_with_injury=sum(1 for r in rows if r['injury']),
        live_with_game_status=sum(1 for r in rows if r['game_status']),
        common=unchanged+changed, changed=changed, unchanged=unchanged, added=added, removed=removed)

    # ---- delta: 2026-11-17 partial read -> 2026-11-18 read (overlap only)
    cmp_rows = []
    same = diff = 0
    for (tm, name), (inj, prac, gs) in partial.items():
        team = NICK.get(tm)
        key = (team, name)
        if key not in live:
            cmp_rows.append(['not in 2026-11-18 read', tm, name, inj, prac, gs, '', '', ''])
            diff += 1; continue
        r = live[key]
        a = (inj, prac, gs); b = (r['injury'], r['practice'], r['game_status'])
        if a == b: same += 1
        else:
            diff += 1
            cmp_rows.append(['changed', tm, name, inj, prac, gs, r['injury'], r['practice'], r['game_status']])
    with open(os.path.join(HERE,'data','delta_2026-11-17_to_2026-11-18.csv'),'w',newline='',encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['change','team_code','player','injury_2026_11_17','practice_2026_11_17','game_status_2026_11_17',
                    'injury_2026_11_18','practice_2026_11_18','game_status_2026_11_18'])
        w.writerows(cmp_rows)
    partial_summary = dict(compared=len(partial), identical=same, different=diff)

    # ---- register CSVs
    def write_register(name, header, data):
        with open(os.path.join(HERE,'data',name),'w',newline='',encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(header); w.writerows(data)
    write_register('claim_checks.csv', ['id','claim','how_checked','result','verdict','source_url','basis'],
        [[c['id'],c['claim'],c['checked'],c['result'],c['verdict'],c['source'],c['basis']] for c in C.CLAIMS])
    write_register('requirements_readiness.csv',['id','category','requirement','status','blocking_gate','number_that_clears','observed_now','evidence_link','source_kind','source_url'],
        [[r[0],r[1],r[2],r[3],r[4],r[5],r[6],(C.REPO+r[7] if r[7] else ''),
          ('official' if r[8].startswith('http') else 'internal evidence only'),
          (r[8] if r[8].startswith('http') else '')] for r in C.REQS])
    write_register('questions.csv',['id','question','answer_as_of_2026_11_18','next_step','source_url'],[list(q) for q in C.QUESTIONS])
    write_register('suggestions.csv',['id','topic','options','recommendation','what_would_change_our_mind','source_url'],
        [[s[0],s[1],s[2],s[3],s[4],s[5]] for s in C.SUGGESTIONS])
    write_register('flagged.csv',['id','severity','title','detail','related','source_url'],[list(f) for f in C.FLAGS])
    write_register('sources.csv',['id','source','url','how_read','used_for'],[list(s) for s in C.SOURCES])

    # ---- summary used by pages and verify.py
    status_counts = collections.Counter(r[3] for r in C.REQS)
    summary = dict(read_date=READ_DATE, read_window=READ_WINDOW, transcript_sha256=digest,
        rows=len(rows), clubs=len(teams), games=len(set(r['game'] for r in rows)),
        with_injury=sum(1 for r in rows if r['injury']),
        with_game_status=sum(1 for r in rows if r['game_status']),
        out=sum(1 for r in rows if r['game_status']=='Out'),
        doubtful=sum(1 for r in rows if r['game_status']=='Doubtful'),
        questionable=sum(1 for r in rows if r['game_status']=='Questionable'),
        dnp_no_injury=sum(1 for r in rows if not r['injury'] and r['practice'].startswith('Did Not')),
        clubs_zero_injury=sum(1 for t in team_rows if t['with_injury']==0),
        lions=[(r['player'], r['game_status']) for r in rows if r['team']=='Lions' and r['player'] in ('Kerby Joseph','Cade Mays','D.J. Reed')],
        delta=delta_summary, partial_1117=partial_summary, req_status=dict(status_counts),
        n_requirements=len(C.REQS), n_claims=len(C.CLAIMS), n_questions=len(C.QUESTIONS),
        n_suggestions=len(C.SUGGESTIONS), n_flags=len(C.FLAGS), n_sources=len(C.SOURCES))
    json.dump(summary, open(os.path.join(HERE,'data','summary.json'),'w'), indent=2, sort_keys=True)
    import render
    render.render_all(summary, rows, team_rows, drows, cmp_rows)
    print('built', summary['rows'], 'rows', summary['clubs'], 'clubs', summary['games'], 'games')

if __name__ == '__main__':
    main()
