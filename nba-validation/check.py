from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parent
class Audit(HTMLParser):
    def __init__(self,path):
        super().__init__(); self.path=path; self.body=False; self.row=False; self.official=False; self.count=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='tbody': self.body=True
        if tag=='tr' and self.body: self.row=True; self.official=False
        for attr in ('href','src'):
            if attr not in a: continue
            u=urlsplit(a[attr])
            if u.scheme:
                assert u.scheme=='https',a[attr]
                if self.row and u.hostname in ('www.nba.com','official.nba.com'): self.official=True
            elif u.path: assert (self.path.parent/unquote(u.path)).exists(),a[attr]
            elif u.fragment: assert f'id="{u.fragment}"' in self.path.read_text()
    def handle_endtag(self,tag):
        if tag=='tr' and self.row:
            assert self.official, 'Missing official context link'; self.count+=1; self.row=False
        if tag=='tbody': self.body=False
count=0
for p in ROOT.glob('*.html'):
    a=Audit(p);a.feed(p.read_text());count+=a.count
assert len(list(ROOT.glob('*.html')))==8
print(f'PASS: 8 pages, {count} official-linked rows; all local targets exist. Not an external-link or factual-verification substitute.')
