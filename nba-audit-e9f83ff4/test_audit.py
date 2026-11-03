import csv
from html.parser import HTMLParser
from pathlib import Path
import subprocess, unittest
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
class Scanner(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_body=False; self.in_row=False; self.row_links=[]; self.rows=[]; self.links=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='tbody': self.in_body=True
        if tag=='tr' and self.in_body: self.in_row=True; self.row_links=[]
        if tag=='a':
            href=attrs.get('href',''); self.links.append(href)
            if self.in_row: self.row_links.append(href)
    def handle_endtag(self, tag):
        if tag=='tr' and self.in_row: self.rows.append(self.row_links); self.in_row=False
        if tag=='tbody': self.in_body=False
class AuditTests(unittest.TestCase):
    def test_build_and_navigation(self):
        subprocess.run(['python3',str(HERE/'build.py')],check=True)
        for name in ('index.html','sample.html','review.html'):
            scan=Scanner(); scan.feed((HERE/name).read_text())
            self.assertTrue(scan.rows)
            for row in scan.rows:
                self.assertTrue(any(urlsplit(h).hostname in ('www.nba.com','official.nba.com') for h in row), row)
            for href in scan.links:
                if not urlsplit(href).scheme and href and not href.startswith('#'):
                    self.assertTrue((HERE/urlsplit(href).path).exists(),href)
    def test_sample_length(self):
        with (HERE.parent/'nba-2026-lab/data/edwards_2025_26_recent10.csv').open() as f:
            self.assertEqual(len(list(csv.DictReader(f))),10)
if __name__=='__main__': unittest.main()
