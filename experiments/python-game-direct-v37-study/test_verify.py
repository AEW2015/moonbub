"""Fail-closed independent evidence checks, without importing the direct sender."""
import unittest
import verify as v


class IndependentTests(unittest.TestCase):
    def test_exact_packet_parity_rejects_same_pixels_different_valid_wire(self):
        data=v.load(v.OLD/'results.json');row=data['cases'][0]['rows'][0]
        skip=v.raw(row['skip']['packet'],v.OLD);full=v.raw(row['full']['packet'],v.OLD)
        # Both valid frozen variants display exactly the same image.
        self.assertEqual(row['full']['display_sha256'],row['skip']['display_sha256'])
        v.frozen.parse(skip);v.frozen.parse(full)
        self.assertNotEqual(full,skip)
        with self.assertRaises(ValueError):v.exact_packet(full,skip)
        self.assertTrue(v.exact_packet(skip,skip)['skip'])

    def test_reject_missing_duplicate_reordered_frame_cohort(self):
        v.ordered([{'id':0},{'id':1}],2)
        for rows in ([{'id':0}], [{'id':0},{'id':0}], [{'id':1},{'id':0}], [{'id':0},{'id':True}]):
            with self.assertRaises(ValueError):v.ordered(rows,2)

    def test_finite_positive_equal_paired_samples_required(self):
        self.assertEqual(v.validate_samples({'proof':[2.,4.,3.],'direct':[1.,3.,2.]}),{'proof':3.,'direct':2.})
        for bad in ({'proof':[],'direct':[]},{'proof':[1.],'direct':[1.,2.]},
                    {'proof':[float('nan')],'direct':[1.]},{'proof':[1.],'direct':[float('inf')]},
                    {'proof':[1.],'direct':[0.]},{'proof':[True],'direct':[1.]},
                    {'proof':[1.],'direct':[1.],'other':[1.]}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):v.validate_samples(bad)

if __name__=='__main__':unittest.main()
