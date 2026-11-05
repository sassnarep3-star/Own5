import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
import check

class SiteTests(unittest.TestCase):
    def test_relative_links(self):
        self.assertEqual(build.link('index.html','pages/lines.html'),'pages/lines.html')
        self.assertEqual(build.link('pages/lines.html','index.html'),'../index.html')
        self.assertEqual(build.link('pages/lines.html','assets/style.css'),'../assets/style.css')
        self.assertEqual(build.link('pages/audit.html','../index.html'),'../../index.html')

    def test_table_requires_provenance(self):
        html=build.table([{'x':'1','source_url':'https://www.nba.com/'}],'Test')
        self.assertIn('https://www.nba.com/',html)
        with self.assertRaises(ValueError):
            build.table([{'x':'1'}],'Missing source')

    def test_blank_cells_are_labeled(self):
        html=build.table([{'x':'','source_url':'https://www.nba.com/'}],'Blank')
        self.assertIn('blank — unverified',html)

    def test_static_checks_pass(self):
        self.assertEqual(check.main(),0)
        with (ROOT/'audit'/'verification.json').open() as f:
            result=json.load(f)
        self.assertEqual(result['failed'],0)
        self.assertEqual(result['pages'],11)
        self.assertGreater(result['table_rows'],900)

if __name__=='__main__':
    unittest.main()
