import unittest
import numpy as np
import helpers as h
model=h.module('raster41_test_model',h.HERE/'model.py')

class RasterTests(unittest.TestCase):
    def test_global_neighbors_cross_old_tile_boundaries_and_signed_DC_clip(self):
        temporal=np.full((24,32),128,np.int16);target=np.full_like(temporal,96)
        predictions,positions=model.global_predictions(temporal,target)
        # bx2 and by2 have actual global neighbors although old parity is zero.
        self.assertTrue(np.all(predictions[2][2]==96));self.assertEqual(positions[2],1)
        self.assertTrue(np.all(predictions[1][8]==96));self.assertEqual(positions[8],2)
        for p in predictions:self.assertTrue(np.all(p[0]==128))
        target[7,8:16]=255;target[8:16,7]=0
        preds,_=model.global_predictions(temporal,target)
        self.assertTrue(np.all(preds[1][5]==255));self.assertFalse(np.any(preds[2][5]));self.assertTrue(np.all(preds[3][5]==128))
    def test_flat_oracle_eligibility_removes_forced_tile_temporal_islands(self):
        source=np.full((16,32),96,np.int16);base=np.full_like(source,128);tables=np.repeat(h.m.ft.qtable(16)[None],8,axis=0)
        raw=h.m.ft.forward(h.spatial.blocks(source).astype(np.int64)-h.spatial.blocks(base))
        coeff=h.m.ft.round_quantize(raw,tables).astype(np.int16);safe=np.zeros(8,bool)
        target=h.spatial.plane_from_blocks(np.clip(h.m.ft.inverse(coeff.astype(np.int64)*tables)+h.spatial.blocks(base),0,255).astype(np.int16),16,32)
        proposal=model.plane_proposals(source,base,target,coeff,tables,safe)
        self.assertGreater(np.count_nonzero(proposal['modes']),0)
        self.assertNotEqual(proposal['modes'][2],0) # tile parity would force mode0
        for block,mode in enumerate(proposal['modes']):self.assertEqual(proposal['eligibility'][block,int(mode)],1)
        self.assertTrue(np.all(proposal['costs'][:,0,4:] == 1))
    def test_hidden_oracle_is_canonical_and_source_not_mutated(self):
        source=tuple(np.full(s,96 if i==0 else 128,np.int16)for i,s in enumerate(((480,720),(240,360),(240,360))))
        saved=tuple(a.copy()for a in source);q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
        oracle=model.prepare_oracle(source,None,q,0,h.m.NO_REF)
        for plane,safe in zip(oracle['target'],h.canonical.HIDDEN):self.assertTrue(np.all(h.spatial.blocks(plane)[safe]==128))
        for a,b in zip(source,saved):np.testing.assert_array_equal(a,b)
        for fid,rid,ref in((True,h.m.NO_REF,None),(0,0,None),(1,1,source)):
            with self.assertRaises(ValueError):model.prepare_oracle(source,ref,q,fid,rid)
    def test_strict_packet_guard(self):
        self.assertEqual(model.choose_packet(b'abc',b'xyz'),'control');self.assertEqual(model.choose_packet(b'abc',b'xy'),'candidate')
        self.assertEqual(model.choose_packet(b'abc',bytes(49153)),'control')
        with self.assertRaises(ValueError):model.choose_packet(b'',b'x')

if __name__=='__main__':unittest.main()
