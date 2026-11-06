from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import subprocess

root=Path(__file__).parent
class Parser(HTMLParser):
 def __init__(self): super().__init__(); self.hrefs=[]; self.rows=[]; self.row=None
 def handle_starttag(self, tag, attrs):
  attrs=dict(attrs)
  if tag=='tr': self.row=[]
  if tag=='a':
   self.hrefs.append(attrs.get('href',''))
   if self.row is not None: self.row.append(attrs.get('href',''))
 def handle_endtag(self, tag):
  if tag=='tr': self.rows.append(self.row); self.row=None
subprocess.run(['python3',str(root/'build.py')],check=True)
for page in root.glob('*.html'):
 parser=Parser(); parser.feed(page.read_text())
 for href in parser.hrefs:
  if not urlparse(href).scheme and not href.startswith('#'): assert (root/href).exists(), (page,href)
 for row in parser.rows[1:]: assert any(urlparse(h).hostname in ('www.sf.gov','sf.gov','media.api.sf.gov','sfbos.archive.sf.gov','calcivilrights.ca.gov','www.hud.gov') for h in row), (page,row)
print('Six pages: local links and official-source-per-row checks passed.')
