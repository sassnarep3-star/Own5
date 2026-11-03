"""Local consistency, source-link and blank-field checks (not remote source validation)."""
import importlib.util
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('nba_origin_builder',HERE/'build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Parser(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.in_row=False;self.cells=[];self.cell=None;self.links=[];self.local=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='tr': self.in_row=True;self.cells=[];self.links=[]
        if tag=='td' and self.in_row: self.cell=''
        if tag=='a':
            href=a.get('href','')
            if self.in_row:self.links.append(href)
            if not urlsplit(href).scheme and not href.startswith('#'):self.local.append(urlsplit(href).path)
    def handle_data(self,data):
        if self.cell is not None:self.cell+=data
    def handle_endtag(self,tag):
        if tag=='td' and self.cell is not None:self.cells.append(self.cell.strip());self.cell=None
        if tag=='tr' and self.in_row and self.cells:self.rows.append((self.cells,self.links));self.in_row=False
class SiteTest(unittest.TestCase):
    def test_build_is_deterministic(self):
        b.main();before={name:(HERE/name).read_bytes() for name,_ in b.NAV}
        b.main();self.assertEqual(before,{name:(HERE/name).read_bytes() for name,_ in b.NAV})
    def test_rows_and_links(self):
        total=0
        for name,_ in b.NAV:
            doc=Parser();doc.feed((HERE/name).read_text())
            self.assertTrue(doc.rows,name)
            for cells,links in doc.rows:
                self.assertEqual(len(links),1,(name,cells))
                self.assertTrue(links[0].startswith(('https://www.nba.com/','https://official.nba.com/')),(name,links))
            for path in doc.local:self.assertTrue((HERE/path).exists(),(name,path))
            total+=len(doc.rows)
        self.assertGreaterEqual(total,40)
    def test_blank_unverified_metrics(self):
        from html import unescape
        for name,keywords in {'lines.html':['Current fair line / over probability','Quoted book odds / spread'], 'correlations.html':['Threshold-specific prop-hit phi','Same-game joint probability'], 'leaderboard.html':['No qualified entries']}.items():
            p=Parser();p.feed((HERE/name).read_text())
            for key in keywords:
                cells=next(c for c,_ in p.rows if key in c[0]);self.assertIn('',cells[1:-1],(name,key,cells))
    def test_sample_calculation(self):
        import csv,statistics
        with b.SAMPLE.open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),10)
        self.assertEqual(statistics.median(int(r['points']) for r in rows),22)
        self.assertEqual(sum(abs(int(r['points'])-22) for r in rows)/10,9.5)
if __name__=='__main__':unittest.main()
