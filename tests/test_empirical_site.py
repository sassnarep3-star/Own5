import json
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / 'empirical'
ALLOWED = {
    'github.com', 'www.nfl.com', 'vlab.ncep.noaa.gov',
    'www.itl.nist.gov', 'www.gamblingcommission.gov.uk', 'scikit-learn.org',
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.rows, self.row = [], [], [], None
        self.current_table = None
        self.in_body = False
        self.tables = {}
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'id' in d: self.ids.append(d['id'])
        for key in ('href', 'src'):
            if key in d: self.links.append(d[key])
        if tag == 'table':
            self.current_table = d.get('id')
            self.tables[self.current_table] = []
        if tag == 'tbody': self.in_body = True
        if tag == 'tr' and self.in_body: self.row = []
        if tag == 'a' and self.row is not None: self.row.append(d.get('href', ''))
    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.tables[self.current_table].append(self.row)
            self.row = None
        if tag == 'tbody': self.in_body = False
        if tag == 'table': self.current_table = None


class EmpiricalSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = sorted(DIR.glob('*.html'))
        cls.report = json.loads((ROOT/'data/derived/report.json').read_text())

    def test_deterministic_build(self):
        subprocess.run([sys.executable, 'scripts/build_empirical.py', '--check'], cwd=ROOT, check=True, capture_output=True, text=True)

    def test_every_page_and_local_link(self):
        self.assertEqual({p.name for p in self.pages}, {'index.html','lines.html','correlations.html','validation.html','games.html','players.html','review.html'})
        for page in self.pages:
            with self.subTest(page=page.name):
                parser = PageParser(); parser.feed(page.read_text(encoding='utf-8'))
                self.assertEqual(len(parser.ids),len(set(parser.ids)))
                self.assertTrue(parser.rows, 'each page contains a data table')
                for url in parser.links:
                    parts=urlsplit(url)
                    if parts.scheme or parts.netloc: continue
                    target=(page.parent/unquote(parts.path)).resolve() if parts.path else page
                    self.assertTrue(target.is_relative_to(ROOT), (page,url))
                    self.assertTrue(target.is_file(), (page,url))
                    if parts.fragment and target.suffix == '.html':
                        other=PageParser(); other.feed(target.read_text(encoding='utf-8'))
                        self.assertIn(parts.fragment,other.ids,(page,url))
                for row in parser.rows:
                    valid=[urlsplit(u) for u in row if urlsplit(u).scheme == 'https']
                    self.assertTrue(valid, 'every data row must cite an official source')
                    self.assertTrue(all(u.hostname in ALLOWED for u in valid), valid)
                    for u in valid:
                        if u.hostname == 'github.com':
                            self.assertTrue(u.path.startswith('/nfl-football-ops/Big-Data-Bowl'), u.geturl())
                self.assertNotIn('src="https:', page.read_text())
                self.assertNotIn('localhost', page.read_text())

    def test_row_counts_and_no_javascript_content(self):
        expected={
            'index.html': {'model-summary':3},
            'lines.html': {'historical-lines':44},
            'correlations.html': {'associations':6,'joint-events':3},
            'validation.html': {'gate-results':2,'gate-policy':7},
            'games.html': {'game-archive':91},
            'players.html': {'player-archive':34},
            'review.html': {'review-flags':10},
        }
        for page in self.pages:
            p=PageParser(); p.feed(page.read_text(encoding='utf-8'))
            self.assertEqual({k:len(v) for k,v in p.tables.items()}, expected[page.name])
        players=(DIR/'players.html').read_text(encoding='utf-8')
        self.assertEqual(players.count('class="missing" aria-label="Unverified; value intentionally blank"'),3)
        lines=(DIR/'lines.html').read_text(encoding='utf-8')
        self.assertEqual(lines.count('class="missing" aria-label="Unverified; value intentionally blank"'),44)
        self.assertIn('Not live quotes; not a recommendation.', lines)
        corr=(DIR/'correlations.html').read_text(encoding='utf-8')
        self.assertEqual(corr.count('class="missing" aria-label="Unverified; value intentionally blank"'),6)

    def test_research_report_has_no_qualified_or_rewarded_entries(self):
        self.assertEqual(self.report['counts']['qualified_strategies'],0)
        self.assertTrue(all(not r['eligible'] and r['reward_credits'] is None for r in self.report['scores']['candidates']))
        self.assertEqual(self.report['counts']['paired_player_rows'],31)


if __name__ == '__main__': unittest.main()
