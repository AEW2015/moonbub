import unittest
import numpy as np
import helpers as h
model=h.module('spatial38_test_model',h.HERE/'model.py')

class SpatialTests(unittest.TestCase):
    def test_edges_tile_boundary_DC_signed_rounding_and_clip(self):
        base=np.full((4,8,8),128,np.int16);decoded=base.copy()
        decoded[0,7,:]=np.arange(8)+100;decoded[1,7,:]=255;decoded[2,:,7]=0
        indices=np.array([3]);pred=model.predictor(base,decoded,indices,2,1,1,1)
        np.testing.assert_array_equal(pred[0],np.full((8,8),255))
        pred=model.predictor(base,decoded,indices,2,1,1,2);self.assertFalse(np.any(pred))
        dc=model.predictor(base,decoded,indices,2,1,1,3)
        self.assertTrue(np.all(dc==128)) # residual127 +(-128), mean-0.5 rounds0
        for mode in range(4):self.assertTrue(np.all(model.predictor(base,decoded,np.array([0]),2,0,0,mode)==128))
    def test_canonical_modes_actual_dense_RLE_and_zero(self):
        self.assertEqual(model.pack_modes(np.zeros(20,np.uint8)),b'\x02')
        dense=model.pack_modes(np.array([0,1,2,3,2],np.uint8));self.assertEqual(dense,b'\x00\x1b\x80')
        run=model.pack_modes(np.full(100,2,np.uint8));self.assertEqual(run,b'\x01\x02\x64\x00')
        for bad in(np.array([],np.uint8),np.array([4],np.uint8),np.array([0],np.int16)):
            with self.assertRaises(ValueError):model.pack_modes(bad)
    def test_isolated_proxy_matches_actual_CP02_and_hidden_immediate_reconstruction(self):
        rng=np.random.default_rng(38);coeff=rng.integers(-5,6,(9,8,8),dtype=np.int16)
        counts=h.m.counter.isolated_packet_bytes(coeff)
        for c,n in zip(coeff,counts):self.assertEqual(len(h.m.gm.token_coeff.encode_coefficients(c[None],1)),n)
        source=np.full((16,16),80,np.int16);base=np.full_like(source,128)
        tables=np.repeat(h.m.ft.qtable(16)[None],4,axis=0);safe=np.array([True,False,False,False])
        for policy in('mode0control','spatial'):
            c,decoded,modes,costs,_=model.encode_plane(source,base,tables,safe,policy)
            self.assertTrue(np.all(decoded[:8,:8]==128));self.assertFalse(np.any(c[0]));self.assertEqual(modes[0],0)
            self.assertTrue(np.all(costs[0]==0))
    def test_mode0_and_spatial_source_ownership(self):
        source=np.full((16,16),96,np.int16);base=np.full_like(source,128);safe=np.zeros(4,bool)
        tables=np.repeat(h.m.ft.qtable(16)[None],4,axis=0)
        original=source.copy();ref=base.copy()
        for policy in('mode0control','spatial'):model.encode_plane(source,base,tables,safe,policy)
        np.testing.assert_array_equal(source,original);np.testing.assert_array_equal(base,ref)

if __name__=='__main__':unittest.main()
