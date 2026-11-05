import csv
import json
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.rows=[]; self.in_row=False; self.row_links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='tr': self.in_row=True; self.row_links=[]
        if tag=='a' and 'href' in attrs:
            self.links.append(attrs['href'])
            if self.in_row: self.row_links.append(attrs['href'])
        if tag=='link' and 'href' in attrs: self.links.append(attrs['href'])
    def handle_endtag(self,tag):
        if tag=='tr':
            self.rows.append(self.row_links); self.in_row=False

class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths=[HERE/x for x in ('index.html','results.html','correlations.html','strategy.html','flagged.html')]
        cls.before={p:p.read_bytes() for p in cls.paths}
        subprocess.run([sys.executable, str(HERE/'build.py')],check=True)

    def test_reproducible_build(self):
        self.assertEqual(self.before,{p:p.read_bytes() for p in self.paths})

    def test_local_links_and_each_data_row_has_official_source(self):
        count=0
        for p in self.paths:
            parser=Links(); parser.feed(p.read_text(encoding='utf-8'))
            for link in parser.links:
                parts=urlsplit(link)
                if not parts.scheme and parts.path:
                    self.assertTrue((p.parent/unquote(parts.path)).is_file(),f'{p.name}: {link}')
            for row in parser.rows:
                if not row: continue # header
                self.assertTrue(any(urlsplit(h).hostname in ('www.nba.com','www.itl.nist.gov') for h in row),f'{p.name}: {row}')
                count+=1
        self.assertEqual(count,47)

    def test_independently_transcribed_sample_matches_prior_dataset(self):
        with (HERE/'edwards-sample.csv').open(newline='',encoding='utf-8') as f: sample=list(csv.DictReader(f))
        with (ROOT/'nba-signal-lab/data/game_logs_2025_26.csv').open(newline='',encoding='utf-8') as f:
            original={r['game_id']:r for r in csv.DictReader(f) if r['player_id']=='1630162'}
        self.assertEqual(len(sample),11)
        self.assertEqual(len({r['game_id'] for r in sample}),11)
        for row in sample:
            for field, orig in [('points','pts'),('rebounds','reb'),('assists','ast')]:
                self.assertEqual(row[field],original[row['game_id']][orig])

    def test_scores_and_margin_sign(self):
        with (HERE/'results.csv').open(newline='',encoding='utf-8') as f: scores=list(csv.DictReader(f))
        m=json.loads((ROOT/'nba-signal-lab/data/outputs.json').read_text())['model_lines']
        lookup={(r['game_date'],r['away_team'],r['home_team']):r for r in m}
        self.assertEqual(len(scores),6)
        self.assertEqual(len({(r['date'],r['away'],r['home']) for r in scores}),6)
        self.assertTrue(all(urlsplit(r['source_url']).hostname=='www.nba.com' for r in scores))
        correct=0
        for r in scores:
            pred=lookup[(r['date'],r['away'],r['home'])]['model_home_spread']
            actual=int(r['home_score'])-int(r['away_score'])
            correct+=(pred>0)==(actual>0)
        self.assertEqual(correct,3)
        self.assertIn('10.48 point margin MAE',self.paths[0].read_text())
        self.assertIn('13.08 point total MAE',self.paths[0].read_text())

if __name__=='__main__': unittest.main(verbosity=2)
