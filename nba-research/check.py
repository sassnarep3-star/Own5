#!/usr/bin/env python3
"""Static integrity/link/manifest checks for the generated research dashboard."""
from __future__ import annotations
import csv, hashlib, html.parser, json, posixpath, re
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
OUT=ROOT/'audit'

class Parser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.links=[]; self.ids=[]; self.tables=0; self.rows=0; self.h1=0; self.lang=None; self.title=False; self.viewport=False; self._in_title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html': self.lang=a.get('lang')
        if tag=='meta' and a.get('name')=='viewport': self.viewport=True
        if tag=='title': self._in_title=True
        if tag=='h1': self.h1+=1
        if tag=='table': self.tables+=1
        if tag=='tr': self.rows+=1
        if 'id' in a: self.ids.append(a['id'])
        for k in ('href','src'):
            if a.get(k): self.links.append(a[k])
    def handle_endtag(self,tag):
        if tag=='title': self._in_title=False
    def handle_data(self,data):
        if self._in_title and data.strip(): self.title=True

def resolve(page:Path,u:str):
    if u.startswith(('#','http://','https://','mailto:','tel:','data:','javascript:')): return None
    path=unquote(u.split('#',1)[0].split('?',1)[0])
    if not path: return None
    target=posixpath.normpath(posixpath.join(page.parent.relative_to(REPO).as_posix(),path))
    return REPO/target

def main():
    checks=[]
    def add(name,ok,detail=''):
        checks.append({'check':name,'status':'PASS' if ok else 'FAIL','detail':detail})
    pages=sorted(ROOT.rglob('*.html'))
    add('Expected page count',len(pages)==11,f'{len(pages)} HTML pages')
    broken=[]; total_links=0; table_rows=0; source_missing=[]
    for p in pages:
        text=p.read_text(encoding='utf-8'); parser=Parser(); parser.feed(text); parser.close()
        rel=p.relative_to(ROOT).as_posix()
        if parser.lang!='en' or not parser.title or not parser.viewport or parser.h1!=1:
            source_missing.append(f'{rel}: document metadata/h1')
        if '{{TABLE:' in text or '<!-- TABLE:' in text or 'TODO' in text:
            source_missing.append(f'{rel}: unresolved placeholder')
        dup={i for i in parser.ids if parser.ids.count(i)>1}
        if dup: source_missing.append(f'{rel}: duplicate ids {dup}')
        for u in parser.links:
            t=resolve(p,u)
            if t is None: continue
            total_links+=1
            if not t.exists(): broken.append(f'{rel}: {u} -> {t.relative_to(REPO)}')
        # Every generated data table row must contain a source/review anchor.
        for tbl in re.findall(r'<table\b.*?</table>',text,flags=re.S):
            for tr in re.findall(r'<tr\b.*?</tr>',tbl,flags=re.S)[1:]:
                table_rows+=1
                if '<a ' not in tr: source_missing.append(f'{rel}: table row without link')
    add('Internal links resolve',not broken,'; '.join(broken[:20]) or f'{total_links} internal links checked')
    add('Document structure and row provenance',not source_missing,'; '.join(source_missing[:20]) or f'{table_rows} generated table rows checked')
    # Manifest integrity.
    with (ROOT/'data/site_manifest.json').open() as f: manifest=json.load(f)
    bad=[]
    for rel,digest in manifest.items():
        p=ROOT/rel
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest: bad.append(rel)
    add('Build manifest matches files',not bad,'; '.join(bad[:20]) or f'{len(manifest)} files hashed')
    # Research document links.
    md_broken=[]
    for p in (ROOT/'research').glob('*.md'):
        text=p.read_text(encoding='utf-8')
        for u in re.findall(r'\]\(([^)]+)\)',text):
            if u.startswith(('http://','https://','#','mailto:')): continue
            t=(p.parent/unquote(u.split('#',1)[0])).resolve()
            if not t.exists(): md_broken.append(f'{p.name}: {u}')
    add('Research document links resolve',not md_broken,'; '.join(md_broken) or 'Markdown relative links checked')
    # Fail-closed invariants.
    with (ROOT/'data/summary.json').open() as f: summary=json.load(f)
    with (ROOT/'data/leaderboard.csv').open(newline='') as f: board=list(csv.DictReader(f))
    with (ROOT/'data/bets.csv').open(newline='') as f: bets=list(csv.DictReader(f))
    with (ROOT/'data/strategies.csv').open(newline='') as f: strategies=list(csv.DictReader(f))
    add('No fabricated performance',summary['settled_bets']==0 and not bets and not board and summary['certified_strategies']==0 and all(s['status']=='BLOCKED' and s['rank']=='' and s['reward']=='' for s in strategies),'Empty ledger and leaderboard; all strategies blocked')
    add('Integrity checks passed',summary['integrity_passed']==summary['integrity_checks'],f"{summary['integrity_passed']}/{summary['integrity_checks']}")
    result={'pages':len(pages),'internal_links':total_links,'table_rows':table_rows,'manifest_files':len(manifest),'checks':checks,'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks)}
    OUT.mkdir(exist_ok=True)
    with (OUT/'verification.json').open('w') as f: json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
    return 1 if result['failed'] else 0

if __name__=='__main__': raise SystemExit(main())
