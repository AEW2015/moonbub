"""Independent evidence must reject wrong wire, timing and cohort identity."""
import unittest
import verify as v

class IndependentTests(unittest.TestCase):
    def test_cohort_requires_exact_int_order(self):
        v.ordered([{'id':i} for i in range(48)])
        for rows in ([{'id':i} for i in range(47)],[{'id':0}]*48,[{'id':i} for i in reversed(range(48))],
                     [{'id':False}]+[{'id':i} for i in range(1,48)]):
            with self.assertRaises(ValueError):v.ordered(rows)

    def test_timing_shape_finite_domain_and_order(self):
        row=dict(id=0,paired_timing_ms={'direct':[4.,3.,5.],'faster':[2.,1.,3.]},
                 paired_median_ms={'direct':4.,'faster':2.},paired_order=[['direct','faster'],['faster','direct'],['direct','faster']])
        self.assertEqual(v.timings(row),{'direct':4.,'faster':2.})
        for bad in ({'direct':[1.],'faster':[1.]},{'direct':[1.,2.,3.],'faster':[1.,float('nan'),2.]},
                    {'direct':[1.,2.,3.],'faster':[1.,False,2.]},{'direct':[1.,2.,3.],'faster':[1.,0.,2.]}):
            with self.assertRaises(ValueError):v.timings(dict(row,paired_timing_ms=bad))
        with self.assertRaises(AssertionError):v.timings(dict(row,paired_order=[['faster','direct']]*3))

    def test_identical_display_is_weaker_than_wire_parity(self):
        data=v.load(v.HERE.parent/'python-game-canonical-v36-study/results.json');row=data['cases'][0]['rows'][0]
        folder=v.HERE.parent/'python-game-canonical-v36-study'
        full=v.raw(row['full']['packet'],folder);skip=v.raw(row['skip']['packet'],folder)
        self.assertEqual(row['full']['display_sha256'],row['skip']['display_sha256'])
        with self.assertRaises(ValueError):v.exact_wire(full,skip)
        self.assertTrue(v.exact_wire(skip,skip)['skip'])

if __name__=='__main__':unittest.main()
