"""Whole-packet integer/SSE guards preserve strict ties and cap rejection."""
import unittest
import helpers as h
model=h.bound('guard50_owned_model_tests',h.HERE/'model.py',h)
class GuardTests(unittest.TestCase):
    def test_strict_pareto_actual_integer_decisions(self):
        self.assertEqual(model.choose(100,50,99,50),'global_grid')
        self.assertEqual(model.choose(100,50,100,49),'global_grid')
        self.assertEqual(model.choose(100,50,100,50),'zero')
        self.assertEqual(model.choose(100,50,99,51),'zero')
        self.assertEqual(model.choose(100,50,101,49),'zero')
    def test_final_cap_and_failed_zero_do_not_create_unguarded_fallback(self):
        self.assertEqual(model.choose(49153,50,49152,50),'global_grid')
        self.assertIsNone(model.choose(49153,50,49152,51))
        self.assertIsNone(model.choose(49153,50,49153,49))
        self.assertEqual(model.choose(49152,50,49153,49),'zero')
    def test_no_float_rounding_or_sse_proxy_inputs(self):
        for args in((100.,50,99,50),(100,50,99,49.5),(True,50,0,0),(100,-1,99,0)):
            with self.assertRaises(ValueError):model.choose(*args)
if __name__=='__main__':unittest.main()
