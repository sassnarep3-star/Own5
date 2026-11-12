"""Structural verification is not independent factual verification of external pages."""
import json, unittest, subprocess, sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parent
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.rows=[]; self.row=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='tr': self.row=[]
        if tag=='a':
            self.links.append(a['href'])
            if self.row is not None: self.row.append(a['href'])
        if tag=='link': self.links.append(a['href'])
        if tag=='script': self.links.append(a['src'])
    def handle_endtag(self,tag):
        if tag=='tr': self.rows.append(self.row); self.row=None
class Integrity(unittest.TestCase):
    def test_pages_and_rows(self):
        register=json.loads((ROOT/'register.json').read_text())
        for name, (_, rows) in register['pages'].items():
            page=Page(); page.feed((ROOT/f'{name}.html').read_text())
            self.assertEqual(len(page.rows)-1,len(rows))
            for row in page.rows[1:]: self.assertTrue(any(urlsplit(x).scheme=='https' for x in row))
            for link in page.links:
                if not urlsplit(link).scheme and not link.startswith('#'):
                    self.assertTrue((ROOT/unquote(link.split('#')[0])).exists(),link)
            for row in rows:
                self.assertTrue(row[-1])
                for source in row[-1]: self.assertIn(source,register['sources'])
    def test_missing_quantities_not_fabricated(self):
        register=json.loads((ROOT/'register.json').read_text())
        for row in register['pages']['correlations'][1][:4]: self.assertEqual(row[1],'')
        for row in register['pages']['leaderboard'][1][:3]: self.assertEqual(row[1],'')
    def test_no_gambling_execution(self):
        js=(ROOT/'app.js').read_text()
        self.assertNotIn('fetch(',js); self.assertNotIn('localStorage',js)
    def test_build_reproducible(self):
        paths=list(ROOT.glob('*.html'))+[ROOT/'register.json']
        before={p:p.read_bytes() for p in paths}
        subprocess.run([sys.executable,str(ROOT/'build.py')],check=True)
        for p in paths:self.assertEqual(before[p],p.read_bytes(),p.name)
if __name__=='__main__': unittest.main(verbosity=2)
