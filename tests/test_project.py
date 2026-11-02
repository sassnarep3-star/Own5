import json
import math
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import analytics as a


class MathTests(unittest.TestCase):
    """Synthetic numbers below are mathematical fixtures, not NFL observations."""
    def test_american(self):
        self.assertAlmostEqual(a.decimal_from_american(-110), 1+100/110)
        self.assertEqual(a.decimal_from_american(150), 2.5)
    def test_invalid_american(self):
        for x in (0,99,-99,True,None,float('nan'),float('inf')):
            with self.assertRaises(ValueError): a.decimal_from_american(x)
    def test_fair_no_push(self): self.assertEqual(a.fair_decimal(.5),2)
    def test_fair_push(self): self.assertAlmostEqual(a.fair_decimal(.45,.1),2)
    def test_invalid_distribution(self):
        for args in ((0,0),(.8,.3),(-.1,0),(1.1,0),(True,0)):
            with self.assertRaises(ValueError): a.fair_decimal(*args)
    def test_ev(self):
        self.assertAlmostEqual(a.expected_return(.45,2,.1),0)
        self.assertAlmostEqual(a.expected_return(.6,2),.2)
    def test_invalid_odds(self):
        for d in (0,1,float('inf')):
            with self.assertRaises(ValueError): a.expected_return(.5,d)
    def test_devig(self): self.assertEqual(a.proportional_devig([1.9,1.9]),[.5,.5])
    def test_devig_invalid(self):
        for values in ([],[2],[1,2],[float('nan'),2]):
            with self.assertRaises(ValueError): a.proportional_devig(values)
    def test_pearson(self):
        self.assertAlmostEqual(a.pearson([1,2,3],[2,4,6]),1)
        self.assertAlmostEqual(a.pearson([1,2,3],[6,4,2]),-1)
    def test_undefined_not_zero(self): self.assertIsNone(a.pearson([1,1,1],[2,3,4]))
    def test_pearson_invalid(self):
        for x,y in (([],[]),([1],[1]),([1,2],[2]),([1,math.nan],[1,2])):
            with self.assertRaises(ValueError): a.pearson(x,y)
    def test_joint_bounds(self): self.assertEqual(a.joint_bounds(.8,.5),(.30000000000000004,.5))
    def test_settlement_ev(self): self.assertAlmostEqual(a.settlement_ev([(.4,2),(.5,-1),(.1,0)]),.3)
    def test_incomplete_settlement(self):
        for states in ([],[(.4,2)],[(1,-2)]):
            with self.assertRaises(ValueError): a.settlement_ev(states)
    def test_brier(self):
        self.assertEqual(a.brier([0,1],[0,1]),0)
        self.assertEqual(a.brier([.5,.5],[0,1]),.25)
    def test_invalid_brier(self):
        for p,y in (([],[]),([.5],[2]),([.5],[True]),([.5,.3],[0])):
            with self.assertRaises(ValueError): a.brier(p,y)
    def test_holm(self):
        self.assertEqual(a.holm([.01,.04,.03]),[.03,.06,.06])
        self.assertEqual(a.holm([]),[])
        self.assertEqual(a.holm([.9,.8]),[1,1])
    def test_gate_fail_closed(self):
        result = a.gate_decision({})
        self.assertFalse(result['eligible']); self.assertEqual(result['action'],'ABSTAIN')
        self.assertEqual(len(result['blocked_gates']),7)
    def test_truthy_not_evidence(self): self.assertFalse(a.gate_decision({f'G{i:02}':'passed' for i in range(1,8)})['eligible'])
    def test_paper_only(self): self.assertEqual(a.gate_decision({f'G{i:02}':True for i in range(1,8)})['action'],'PAPER_RESEARCH_ONLY')


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.ids=[]; self.rows=[]; self.row=None; self.in_body=False
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d: self.ids.append(d['id'])
        for field in ('href','src'):
            if field in d: self.links.append(d[field])
        if tag=='tbody': self.in_body=True
        if tag=='tr' and self.in_body: self.row=[]
        if tag=='a' and self.row is not None: self.row.append(d.get('href',''))
    def handle_endtag(self,tag):
        if tag=='tr' and self.row is not None: self.rows.append(self.row); self.row=None
        if tag=='tbody': self.in_body=False


class IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.d=json.loads((ROOT/'data/research.json').read_text())
    def test_all_data_rows_have_official_references(self):
        official={s['id'] for s in self.d['sources']}
        for key in ('facts','strategies','gates','correlations','markets','flags','competition'):
            for row in self.d[key]:
                with self.subTest(key=key,id=row['id']):
                    self.assertTrue(row['sources']); self.assertTrue(set(row['sources']) <= official)
    def test_sources_are_primary_publishers(self):
        allowed={'api.github.com','operations.nfl.com','nextgenstats.nfl.com','www.nfl.com','sportsbook.draftkings.com','scikit-learn.org','docs.scipy.org','www.statsmodels.org'}
        for s in self.d['sources']:
            self.assertEqual(urlsplit(s['url']).scheme,'https')
            self.assertIn(urlsplit(s['url']).hostname,allowed)
            self.assertTrue(s['finding']); self.assertTrue(s['limitation']); self.assertEqual(s['checked'],'2026-11-02')
    def test_unknowns_stay_null(self):
        for s in self.d['strategies']:
            for k in ('sample','roi','brier','edge','rank','reward'): self.assertIsNone(s[k])
            self.assertEqual(s['gates_passed'],0)
        for c in self.d['correlations']:
            for k in ('pearson','ci','n','joint_win'): self.assertIsNone(c[k])
        for m in self.d['markets']:
            self.assertIsNone(m['probability']); self.assertIsNone(m['fair_odds'])
        self.assertEqual(self.d['predictions'],[])
    def test_unique_ids(self):
        ids=[r['id'] for v in self.d.values() if isinstance(v,list) for r in v]
        self.assertEqual(len(ids),len(set(ids)))
    def test_all_pages_and_links(self):
        pages=[ROOT/'index.html',*sorted((ROOT/'pages').glob('*.html'))]
        self.assertEqual(len(pages),8)
        for page in pages:
            p=DocumentParser(); p.feed(page.read_text())
            self.assertEqual(len(p.ids),len(set(p.ids)),page)
            self.assertGreater(len(p.rows),0)
            for row in p.rows:
                self.assertTrue(any(urlsplit(u).scheme=='https' for u in row),f'Unlinked row in {page}')
            for u in p.links:
                parsed=urlsplit(u)
                if parsed.scheme or parsed.netloc: continue
                target=(page.parent/unquote(parsed.path)).resolve() if parsed.path else page
                self.assertTrue(target.is_file(),f'{page}: broken link {u}')
                self.assertTrue(target.is_relative_to(ROOT))
                if parsed.fragment and target.suffix=='.html':
                    dest=DocumentParser(); dest.feed(target.read_text())
                    self.assertIn(parsed.fragment,dest.ids)
    def test_no_external_runtime_dependencies(self):
        for page in [ROOT/'index.html',*(ROOT/'pages').glob('*.html')]:
            text=page.read_text()
            self.assertNotIn('src="https:',text)
            self.assertNotIn('localhost',text)
            self.assertNotIn('127.0.0.1',text)
        self.assertNotIn('@import', (ROOT/'assets/style.css').read_text())

if __name__=='__main__': unittest.main()
