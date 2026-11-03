import csv
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('nba_sensitivity', HERE / 'build.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class SensitivityTest(unittest.TestCase):
    def test_correlations_match_existing_lab(self):
        with m.INPUT.open(newline='') as f:
            rows = list(csv.DictReader(f))
        results = m.analyze(rows)
        self.assertEqual(len(results), 5)
        self.assertAlmostEqual(results[0][2], -0.0239, places=4)
        self.assertAlmostEqual(results[1][2], 0.5762, places=4)
        self.assertAlmostEqual(results[2][2], 0.7974, places=4)
        self.assertAlmostEqual(results[3][2], 0.2925, places=4)
        self.assertAlmostEqual(results[4][2], 0.2053, places=4)
        self.assertTrue(all(len(loo) == 10 for _,_,_,loo,_ in results))

    def test_generated_links_and_rows(self):
        m.build()
        text = m.OUTPUT.read_text()
        self.assertEqual(text.count('<tr><td><a href="https://www.nba.com/game/'), 50)
        self.assertIn('not figures published by the NBA', text)

if __name__ == '__main__':
    unittest.main()
