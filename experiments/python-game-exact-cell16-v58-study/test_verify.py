"""Exact all-plane MB equality, partial edges, fixed post-RDO semantics and gate."""
from dataclasses import replace
import json,unittest
from unittest.mock import patch
import numpy as np
import verify as v

def planes():return tuple(np.full(s,128,np.int16)for s in((480,720),(240,360),(240,360)))
def coefficients():return tuple(np.zeros((n,8,8),np.int16)for n in(5400,1350,1350))

class ExactMotionProofTests(unittest.TestCase):
    def test_entire_chroma_right_edge_difference_disqualifies_MB(self):
        zero=planes();grid=tuple(p.copy()for p in zero);grid[2][-1,-1]=129
        vectors=np.full((30,45,2),4,np.int8);vectors[0,0]=0
        choice,eligible,difference,cost=v.exact_selection(zero,grid,coefficients(),coefficients(),vectors)
        self.assertEqual(difference[29,44,2],1);self.assertEqual(int(difference.sum()),1)
        self.assertFalse(eligible[29,44]);self.assertFalse(eligible[0,0]);self.assertEqual(int(eligible.sum()),1348)
        self.assertFalse(choice.any());self.assertEqual(cost[29,44,0,0],6*35)
    def test_equal_source_YUV_error_does_not_qualify_different_pixels(self):
        zero=planes();zero[0][0,0]=127;zero[0][0,1]=129
        grid=tuple(p.copy()for p in zero);grid[0][0,0]=129;grid[0][0,1]=127
        self.assertEqual(int(np.square(zero[0].astype(np.int64)-128).sum()),int(np.square(grid[0].astype(np.int64)-128).sum()))
        vectors=np.full((30,45,2),4,np.int8)
        _,eligible,difference,_=v.exact_selection(zero,grid,coefficients(),coefficients(),vectors)
        self.assertEqual(difference[0,0,0],2);self.assertFalse(eligible[0,0])
    def test_post_RDO_bit_savings_must_strictly_pay_MV_charge(self):
        zero=planes();vectors=np.full((30,45,2),4,np.int8);zc=list(coefficients());gc=coefficients()
        # Last16cell contains four Y8blocks; DC4 costs four extra bits each.
        for by in(58,59):
            for bx in(88,89):zc[0][by*90+bx,0,0]=4
        chosen,eligible,_,cost=v.exact_selection(zero,zero,tuple(zc),gc,vectors)
        self.assertTrue(eligible[29,44]);self.assertEqual(int(cost[29,44,0].sum()),int(cost[29,44,1].sum()));self.assertFalse(chosen[29,44])
        zc[1][29*45+44,0,0]=1
        chosen,_,_,_=v.exact_selection(zero,zero,tuple(zc),gc,vectors);self.assertTrue(chosen[29,44])
    def test_hidden_bits_are_not_charged(self):
        c=coefficients();vectors=np.zeros((30,45,2),np.int8);cost=v.post_bits(c,vectors)
        visible=sum(int((~safe).sum())for safe in v.f.f.safe_blocks())
        self.assertEqual(int(cost[...,0].sum()),visible*35);self.assertEqual(cost[29,44,0],210)
        bad=list(coefficients());safe=v.f.f.safe_blocks()[0].reshape(-1);bad[0][np.flatnonzero(safe)[0],0,0]=1
        with self.assertRaises(AssertionError):v.post_bits(tuple(bad),vectors)
    def test_mixed_post_coefficients_serialize_without_quantization_or_RDO(self):
        source=planes();ref=planes();zero=v.proof.preparation(source,ref,1,0,'zero')
        vectors=np.full((15,23,2),4,np.int8);grid=replace(zero,vector_bytes=v.m.base.pack_vectors(vectors),prediction=v.m.predict(ref,vectors,32))
        y,x=np.indices((30,45));selected=((y+x)%2).astype(np.uint8)
        mixed,c,mv=v.mix(zero,grid,coefficients(),coefficients(),selected,ref)
        np.testing.assert_array_equal(mv,np.where(selected[...,None]!=0,v.expanded_vectors(grid),0))
        q=v.m.roi.declared_map(720,480,v.n.ROIS,8,16)
        with patch.object(v.m.base,'_quantize',side_effect=AssertionError('no requantization')),patch.object(v.m.counter,'rdo_skip',side_effect=AssertionError('no rerun RDO')):
            rebuilt=v.m.gm.reconstruct(c,mixed.prediction,q,720,480);canonical=v.f.f.normalize(rebuilt)
            v.proof.rxproof.equal_planes(canonical,source)
            hudcase=json.loads((v.proof.CONTROL/'results.json').read_text())['cases'][0]['rows'][1]
            hud=v.raw(hudcase['hud_packets']['HX33_selected'],v.proof.CONTROL)
            packet,out,_,_=v.mixed_intermediate(mixed,q,c,hud)
        self.assertTrue(packet);v.proof.rxproof.equal_planes(out,source)
        self.assertEqual(v.proof.rxproof.original_parts(packet)[1][8],16)
    def test_repeated_global32_vector_map_crops_column45(self):
        source=planes();p=v.proof.preparation(source,source,1,0,'zero')
        base=np.zeros((15,23,2),np.int8);base[...,0]=(np.arange(23)%9-4)*4
        p=replace(p,vector_bytes=v.m.base.pack_vectors(base));expanded=v.expanded_vectors(p)
        self.assertEqual(expanded.shape,(30,45,2));np.testing.assert_array_equal(expanded[29,44],base[14,22]);np.testing.assert_array_equal(expanded[29,43],base[14,21])
    def test_zero16_has_same_length_but_not_zero32_wire(self):
        source=planes();pz=v.proof.preparation(source,source,1,0,'zero');q=v.m.roi.declared_map(720,480,v.n.ROIS,8,16)
        p16,c,mv=v.mix(pz,pz,coefficients(),coefficients(),np.zeros((30,45),np.uint8),source)
        hudrow=json.loads((v.proof.CONTROL/'results.json').read_text())['cases'][0]['rows'][1];hud=v.raw(hudrow['hud_packets']['HX33_selected'],v.proof.CONTROL)
        a,_,pa,_=v.proof.expected_intermediate(pz,q,c,hud);b,_,pb,_=v.mixed_intermediate(p16,q,c,hud)
        wire32=v.proof.final_from_options(a,pa);wire16=v.proof.final_from_options(b,pb)
        self.assertEqual(len(wire32),len(wire16));self.assertNotEqual(wire32,wire16)
        self.assertEqual(v.proof.rxproof.original_parts(wire16)[1][8],16)
    def test_strict_complete_byte_gate_and_cap(self):
        self.assertEqual(v.choose(b'aa',b'bb'),'zero');self.assertEqual(v.choose(b'aaa',b'bb'),'mixed')
        self.assertEqual(v.choose(b'z'*49152,b'c'*49153),'zero')
        self.assertEqual(v.choose(b'z'*49152,b'c'*49151),'mixed')
        with self.assertRaises(ValueError):v.choose(b'z'*49153,b'c')

if __name__=='__main__':unittest.main()
