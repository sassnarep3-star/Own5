import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import audit_repo as a

class AuditTests(unittest.TestCase):
    def test_target_resolution_normalizes_parent_segments(self):
        names={'index.html','docs/index.html','pages/review.html','assets/style.css'}
        self.assertEqual(a.internal_target('docs/index.html','../index.html',names),'index.html')
        self.assertEqual(a.internal_target('pages/review.html','../assets/style.css',names),'assets/style.css')
        self.assertEqual(a.internal_target('nba-desk/index.html','../docs/',names),'docs/index.html')
        self.assertIsNone(a.internal_target('index.html','https://www.nba.com/',names))
        self.assertIsNone(a.internal_target('index.html','#main',names))

    def test_inventory_covers_every_baseline_line(self):
        with (ROOT/'audit'/'scan_summary.json').open() as f: summary=json.load(f)
        rows=list(csv.DictReader((ROOT/'audit'/'file_inventory.csv').open()))
        manifest=[json.loads(l) for l in (ROOT/'audit'/'line_manifest.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows),summary['files'])
        self.assertEqual(len(manifest),summary['files'])
        self.assertEqual(sum(int(r['lines']) for r in rows),summary['lines'])
        self.assertEqual(sum(r['lines_scanned'] for r in manifest),summary['lines'])
        self.assertEqual(sum(int(r['bytes']) for r in rows),summary['bytes'])
        self.assertEqual(summary['python_syntax_errors'],0)
        self.assertEqual(summary['json_errors'],0)
        self.assertEqual(summary['js_syntax_errors'],0)
        self.assertTrue(all(r['review_url'].startswith(a.REPO+'/blob/'+a.BASELINE+'/') for r in rows))

    def test_findings_have_review_and_context_links(self):
        rows=list(csv.DictReader((ROOT/'audit'/'findings.csv').open()))
        self.assertGreaterEqual(len(rows),15)
        for r in rows:
            self.assertTrue(r['review_url'].startswith('https://github.com/'))
            self.assertTrue(r['source_url'].startswith('https://'))
            self.assertIn(r['severity'],('Low','Medium','High'))

if __name__=='__main__':
    unittest.main()
