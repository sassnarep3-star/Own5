import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('nba_compute',Path(__file__).parent/'compute.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class TestNBA(unittest.TestCase):
    def test_identity(self):
        self.assertAlmostEqual(m.pearson([1,2,3],[2,4,6]),1)
        self.assertAlmostEqual(m.pearson([1,2,3],[6,4,2]),-1)
        with self.assertRaises(ValueError): m.pearson([1,1,1],[1,2,3])
    def test_data(self):
        rows=m.load()
        self.assertEqual(len(rows),10)
        self.assertEqual(sum(r['win'] for r in rows),5)
        self.assertEqual(sum(r['points'] for r in rows),255)
        self.assertEqual(len(m.correlations(rows)),5)
if __name__=='__main__': unittest.main()
