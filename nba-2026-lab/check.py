"""Fail-closed structural audit of generated HTML tables and same-folder navigation."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import importlib.util
BASE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('builder', BASE/'build.py')
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
class Audit(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_row=False; self.in_body=False; self.row=''; self.hrefs=[]; self.rows=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='tbody': self.in_body=True
        if tag=='tr' and self.in_body: self.in_row=True; self.row=''; self.hrefs=[]
        if tag=='a':
            url=attrs.get('href','')
            if self.in_row: self.hrefs.append(url)
            elif not urlsplit(url).scheme and not url.startswith('#'):
                if not (BASE/urlsplit(url).path).exists():
                    # adjacent legacy site links are checked separately
                    if not (BASE/urlsplit(url).path).exists(): raise ValueError('broken link '+url)
    def handle_data(self,data):
        if self.in_row: self.row+=data
    def handle_endtag(self,tag):
        if tag=='tr' and self.in_row:
            if not self.hrefs or not all(x.startswith(('https://www.nba.com/','https://official.nba.com/')) for x in self.hrefs): raise ValueError('unofficial or absent row source '+self.row)
            self.rows.append(self.row); self.in_row=False
        if tag=='tbody': self.in_body=False
for name,_ in b.NAV:
    a=Audit(); a.feed((BASE/name).read_text()); print(name,len(a.rows),'official-linked rows')
for name in ('style.css','compute.py','data/edwards_2025_26_recent10.csv'):
    assert (BASE/name).exists()
