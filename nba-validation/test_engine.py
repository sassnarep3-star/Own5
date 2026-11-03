import unittest
from engine import *
class EngineTests(unittest.TestCase):
    def test_prices(self):
        self.assertEqual(fair_decimal(.5),2)
        self.assertAlmostEqual(expected_return(.5,.1,1.8),0)
    def test_invalid(self):
        for p in (None,True,-.1,1.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): fair_decimal(p)
        with self.assertRaises(ValueError): fair_decimal(0)
        with self.assertRaises(ValueError): expected_return(.8,.3,2)
        with self.assertRaises(ValueError): expected_return(.5,0,1)
    def test_dependence(self):
        self.assertEqual(joint_bounds(.6,.7),(.2999999999999998,.6))
        self.assertAlmostEqual(joint_from_phi(.5,.5,0),.25)
        self.assertAlmostEqual(joint_from_phi(.5,.5,1),.5)
        self.assertAlmostEqual(joint_from_phi(.5,.5,-1),0)
        with self.assertRaises(ValueError): joint_from_phi(.1,.9,1)
        with self.assertRaises(ValueError): joint_from_phi(0,.5,0)
    def test_holm(self):
        self.assertEqual(holm([.01,.04,.03]),[True,False,False])
        self.assertEqual(holm([.001,.01,.02]),[True]*3)
        self.assertEqual(holm([]),[])
    def test_gates(self):
        self.assertFalse(eligible({}))
        all_pass={g:True for g in GATES}
        self.assertTrue(eligible(all_pass))
        for g in GATES:
            for invalid in (False,None,1,'pass'):
                self.assertFalse(eligible(dict(all_pass,**{g:invalid})))
    def test_median(self):
        self.assertEqual(empirical_line([1,2,3]),2)
        self.assertEqual(empirical_line([1,2]),1.5)
        for draws in ([],[float('nan')]):
            with self.assertRaises(ValueError): empirical_line(draws)
if __name__ == '__main__': unittest.main()
