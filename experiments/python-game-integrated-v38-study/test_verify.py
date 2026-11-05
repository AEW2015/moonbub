"""Independent checks distinguish exact wire parity from equal visible output."""
import unittest
import verify as v

class IndependentTests(unittest.TestCase):
    def test_exact_wire_rejects_valid_CN36_same_picture(self):
        data=v.load(v.OLD/'results.json');row=data['cases'][0]['rows'][0]
        cs=v.raw(row['packet'],v.OLD)
        cnfolder=v.HERE.parent/'python-game-canonical-v36-study'
        cnrow=v.load(cnfolder/'results.json')['cases'][0]['rows'][0]['skip']
        cn=v.raw(cnrow['packet'],cnfolder)
        self.assertEqual(row['display_sha256'],cnrow['display_sha256'])
        with self.assertRaises(ValueError):v.exact_wire(cn,cs)
        self.assertTrue(v.exact_wire(cs,cs)['key'])

    def test_ordered_cohort_rejects_missing_duplicate_bool(self):
        v.ordered([{'id':0},{'id':1}],2)
        for bad in ([{'id':0}],[{'id':0},{'id':0}],[{'id':1},{'id':0}],[{'id':False},{'id':1}]):
            with self.assertRaises(ValueError):v.ordered(bad,2)

    def test_paired_clock_domain_medians_and_order(self):
        row=dict(id=0,paired_timing_ms={'baseline':[3.,5.,4.],'integrated':[2.,4.,3.]},
                 paired_median_ms={'baseline':4.,'integrated':3.},
                 paired_order=[['baseline','integrated'],['integrated','baseline'],['baseline','integrated']])
        self.assertEqual(v.timings(row),{'baseline':4.,'integrated':3.})
        for samples in ({'baseline':[1.],'integrated':[1.]},{'baseline':[1.,2.,3.],'integrated':[1.,True,3.]},
                        {'baseline':[1.,2.,3.],'integrated':[1.,float('nan'),3.]},{'baseline':[1.,2.,3.],'integrated':[0.,2.,3.]}):
            with self.assertRaises(ValueError):v.timings(dict(row,paired_timing_ms=samples))
        with self.assertRaises(AssertionError):v.timings(dict(row,paired_median_ms={'baseline':5.,'integrated':3.}))
        with self.assertRaises(AssertionError):v.timings(dict(row,paired_order=[['integrated','baseline']]*3))

if __name__=='__main__':unittest.main()
