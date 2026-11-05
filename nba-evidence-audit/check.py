from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
P=Path(__file__).resolve().parent
class Checker(HTMLParser):
 def __init__(self): super().__init__(); self.rows=[]; self.row=None; self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='tr': self.row=[]
  if tag=='a' and 'href' in a:
   self.links.append(a['href'])
   if self.row is not None: self.row.append(a['href'])
 def handle_endtag(self,tag):
  if tag=='tr': self.rows.append(self.row); self.row=None
for path in P.glob('*.html'):
 c=Checker(); c.feed(path.read_text()); assert len(c.rows)>1
 for row in c.rows[1:]: assert any(urlparse(x).hostname in ('www.nba.com','official.nba.com') for x in row), (path,row)
 for link in c.links:
  if not urlparse(link).scheme: assert (path.parent/link).exists(),(path,link)
 print(path.name, len(c.rows)-1, 'rows checked')
