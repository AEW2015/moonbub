import unittest
import numpy as np
import fixtures
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location("golden_vector_verify",Path(__file__).with_name("verify.py"))
verify=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(verify)

class GoldenVectors(unittest.TestCase):
    def test_source_pins_and_full_manifest(self):
        d=verify.verify();self.assertEqual(d['positive_frames'],10)
    def test_negative_packet_atomicity(self):
        self.assertEqual(verify.check_negative(verify.load()),{'receiver':8,'feedback':2})
    def test_abort_retry_and_read_owned_key(self):
        self.assertTrue(verify.check_lifecycle(verify.load()))
    def test_ui_is_excluded_from_reference_tag_and_yuv(self):
        spec=next(s for s in fixtures.specs() if s['width']==720);row=spec['frames'][0]
        enc=fixtures.encoder(spec);rgb,ui=fixtures.prepare(enc,spec,row)
        plain=fixtures.codec.Encoder(epoch=16,mode=spec['mode']).prepare(rgb,0,force_key=True)
        a=fixtures.codec.identity(ui.packet,decode=True);b=fixtures.codec.identity(plain.packet,decode=True)
        self.assertEqual(a['inner'],b['inner']);self.assertEqual(a['stored_tag'],b['stored_tag'])
        self.assertEqual(a['patch_count'],1);self.assertEqual(b['patch_count'],0)
        aa=fixtures.codec.Receiver(epoch=16).begin(ui.packet);bb=fixtures.codec.Receiver(epoch=16).begin(plain.packet)
        for x,y in zip(aa.planes,bb.planes):np.testing.assert_array_equal(x,y)
    def test_fragmented_gf02_out_of_order_and_pinned_reader(self):
        row=next(c for c in verify.load()['cohorts'] if c['spec']['name']=='full720-ui')['rows'][0]
        chunks=[verify.read_blob(d) for d in row['gf02']];self.assertEqual(len(chunks),3)
        ingress=fixtures.transport.Reassembler(epoch=16);self.assertIsNone(ingress.feed(chunks[2],0))
        self.assertIsNone(ingress.feed(chunks[2],1));self.assertIsNone(ingress.feed(chunks[0],2))
        completed=ingress.feed(chunks[1],3);self.assertEqual(completed.data,verify.read_blob(row['ar02']))
        altered=chunks[0][:-1]+bytes([chunks[0][-1]^1])
        with self.assertRaises(ValueError):ingress.feed(altered,4)
        self.assertIs(ingress.pending[0]['complete'],completed)
        ingress.reject(completed);self.assertFalse(ingress.pending)
    def test_corrupt_gf02_never_delivers_or_publishes(self):
        row=next(c for c in verify.load()['cohorts'] if c['spec']['name']=='full720-ui')['rows'][0]
        chunks=[verify.read_blob(d) for d in row['gf02']]
        chunks[0]=chunks[0][:-1]+bytes([chunks[0][-1]^1])
        ingress=fixtures.transport.Reassembler(epoch=16)
        for i,chunk in enumerate(chunks[:-1]):self.assertIsNone(ingress.feed(chunk,i))
        with self.assertRaises(ValueError):ingress.feed(chunks[-1],3)
        self.assertFalse(ingress.pending);self.assertEqual(ingress.committed,-1)
    def test_fixture_paths_are_bounded(self):
        with self.assertRaises(ValueError):verify.read_blob(dict(path='../nope'))
        with self.assertRaises(ValueError):verify.read_blob(dict(path='/nope'))

if __name__=='__main__':unittest.main()
