import gc
import hashlib
import importlib.util
import struct
from pathlib import Path
import sys
import unittest
import weakref
import numpy as np
import inline_tag

_spec=importlib.util.spec_from_file_location('inline_readonly_verify',Path(__file__).with_name('verify.py'))
verify=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=verify;_spec.loader.exec_module(verify)

def planes(width=34,height=18):
    rng=np.random.default_rng(1610)
    return tuple(rng.integers(0,256,s,dtype=np.int16) for s in ((height,width),(height//2,width//2),(height//2,width//2)))

def reference(ps):
    h,w=ps[0].shape
    return hashlib.sha256(struct.pack('<HH',w,h)+b''.join(np.asarray(p,dtype='<i2').tobytes() for p in ps)).digest()[:16]

class InlineTests(unittest.TestCase):
    def test_retained_twenty_exact_cases_and_counterfactual(self):
        self.assertEqual(verify.verify()['exact_cases'],20)
    def test_partial_edge_stripes_and_tiles(self):
        for w,h in ((2,2),(34,18),(66,50),(720,480)):
            ps=planes(w,h);tag,info=inline_tag.compute(ps)
            self.assertEqual(tag,reference(ps));self.assertEqual(info['stripe_storage_bytes'],min(h,8)*w*2)
    def test_explicit_finalize_hides_all_partial_tags(self):
        ps=planes();tagger=inline_tag.StripeTagger(34,18)
        for args in inline_tag.tiles(ps):
            with self.assertRaises(ValueError):_ =tagger.tag
            tagger.push(*args)
        with self.assertRaises(ValueError):_ =tagger.tag
        self.assertEqual(tagger.finalize(),reference(ps));self.assertEqual(tagger.tag,reference(ps))
        with self.assertRaises(ValueError):tagger.finalize()
    def test_bad_dtype_shape_and_range_fail_closed(self):
        for tile in (np.zeros((8,8),np.uint8),np.zeros((8,8),np.int32),np.zeros((7,8),np.int16),
                     np.full((8,8),-1,np.int16),np.full((8,8),256,np.int16)):
            tagger=inline_tag.StripeTagger(34,18)
            with self.assertRaises(ValueError):tagger.push(0,0,0,tile)
            with self.assertRaises(ValueError):tagger.push(0,0,0,np.zeros((8,8),np.int16))
            with self.assertRaises(ValueError):tagger.finalize()
            with self.assertRaises(ValueError):_=tagger.tag
    def test_order_duplicate_extra_and_truncation_fail_before_publication(self):
        ps=planes();args=list(inline_tag.tiles(ps))
        for sequence in ([args[1]],[args[0],args[0]],args+[(3,0,0,np.zeros((8,8),np.int16))]):
            t=inline_tag.StripeTagger(34,18)
            with self.assertRaises(ValueError):
                for a in sequence:t.push(*a)
            with self.assertRaises(ValueError):t.finalize()
            with self.assertRaises(ValueError):_=t.tag
        t=inline_tag.StripeTagger(34,18);t.push(*args[0])
        with self.assertRaises(ValueError):t.finalize()
        with self.assertRaises(ValueError):_=t.tag
    def test_one_owned_stripe_does_not_retain_producer_tile(self):
        ps=planes();t=inline_tag.StripeTagger(34,18)
        tile=ps[0][:8,:8];pointer=weakref.ref(tile);t.push(0,0,0,tile);del tile;gc.collect()
        self.assertIsNone(pointer());self.assertEqual(t._stripe.nbytes,8*34*2)
        for i,a in enumerate(inline_tag.tiles(ps)):
            if i:t.push(*a)
        self.assertEqual(t.finalize(),reference(ps))
    def test_big_endian_source_is_canonically_little_endian(self):
        ps=planes();tag,_=inline_tag.compute(tuple(p.astype('>i2') for p in ps))
        self.assertEqual(tag,reference(ps))
    def test_bad_dimensions(self):
        for w,h in ((0,2),(3,2),(2,3),(True,2),(5000,2)):
            with self.assertRaises(ValueError):inline_tag.StripeTagger(w,h)

if __name__=='__main__':unittest.main()
