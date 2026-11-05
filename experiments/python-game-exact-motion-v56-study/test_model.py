"""Exact post-RDO serialization, forbidden stages, sample equality and caps."""
import contextlib,unittest
from unittest.mock import patch
import numpy as np
import helpers as h
model=h.bound('exactmotion56_owned_tests',h.HERE/'model.py',h)

def fixture():
    f=h.load(h.SOURCE/'manifest.json')['cases'][0]['frames'][0];c=h.load(h.CONTROL/'results.json')['cases'][0]['rows'][0]
    canvas=np.frombuffer(h.raw(f['canvas_rgb24'],h.SOURCE),np.uint8).reshape(480,720,3).copy();source=tuple(v.astype(np.int16)for v in h.m.ft.rgb_to_planes(canvas))
    p=h.analysis.analyze_planes(source,None);q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16);hud=h.raw(c['hud_packets']['HX33_selected'],h.CONTROL)
    return p,q,hud,model.source_proposal(p,q,hud)

@contextlib.contextmanager
def forbid_RDO():
    with patch.object(h.m.base,'_quantize',side_effect=AssertionError('quantize forbidden')),patch.object(h.m.counter,'rdo_skip',side_effect=AssertionError('RDO forbidden')):yield

class ExactMotionTests(unittest.TestCase):
    def test_exact_zero_serializer_has_no_quantize_RDO_and_matches_golden(self):
        p,q,hud,z=fixture();choice=np.zeros((15,23),bool);vectors=np.zeros((15,23,2),np.int8)
        coeff,pred,mv,work=model.mix(z,z,choice,vectors)
        with forbid_RDO():result=model.serialize(p,coeff,pred,mv,q,hud,z['normalized'])
        self.assertEqual(result['packet'],z['packet']);got=h.rx.Receiver().receive(result['packet'])
        for a,b in zip(got[0],z['normalized'],strict=True):np.testing.assert_array_equal(a,b)
        with self.assertRaisesRegex(AssertionError,'quantize forbidden'),forbid_RDO():model.source_proposal(p,q,hud)
        changed=list(coeff);changed[0]=coeff[0].copy();changed[0][np.flatnonzero(h.base.canonical.HIDDEN[0])[0],0,0]=1
        with self.assertRaises(ValueError),forbid_RDO():model.serialize(p,tuple(changed),pred,mv,q,hud,z['normalized'])
    def test_nonzero_exact_post_RDO_mixture_roundtrips_without_requantization(self):
        reference=[np.full(shape,128,np.int16)for shape in((480,720),(240,360),(240,360))]
        reference[0][:,156:198]=128+np.arange(156,198,dtype=np.int16)[None,:]-160
        for plane in reference[1:]:plane[:,78:99]=128+2*(np.arange(78,99,dtype=np.int16)[None,:]-80)
        reference=h.base.maskplan.apply_plan(tuple(reference),h.base.PLAN)
        pz=h.analysis.analyze_planes(reference,reference,frame_id=1,reference_id=0)
        q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16);vectors=np.zeros((15,23,2),np.int8);vectors[5,5]=[4,0]
        pred=h.m.predict(reference,vectors,32);raw=h.m.base.old._forward(reference,pred)
        corrected=h.m.base._quantize(raw,q,720,480)
        for c,safe in zip(corrected,h.base.canonical.HIDDEN,strict=True):c[safe]=0
        norm=h.base.maskplan.apply_plan(h.m.gm.reconstruct(corrected,pred,q,720,480),h.base.PLAN)
        for a,b in zip(norm,reference,strict=True):np.testing.assert_array_equal(a,b)
        pg=h.m.Prepared(h.m._PREPARED_OWNER,25,1,0,720,480,False,32,'block',pz.reference_tag,
            h.m.base.pack_vectors(vectors),pred,raw,pz.source,{})
        zero=dict(normalized=reference,coefficients=tuple(np.zeros_like(c)for c in corrected),prepared=pz)
        grid=dict(normalized=norm,coefficients=corrected,prepared=pg)
        choice=np.zeros((15,23),bool);choice[5,5]=True
        _,eligible,_,_,_=model.selection(zero,grid,vectors);self.assertTrue(eligible[5,5])
        coeff,prediction,mv,work=model.mix(zero,grid,choice,vectors)
        control=h.load(h.CONTROL/'results.json')['cases'][0]['rows'];gold=h.load(h.GOLDEN/'results.json')['cases'][0]['rows'][0]
        hud=h.raw(control[1]['hud_packets']['HX33_selected'],h.CONTROL)
        with forbid_RDO():wire=model.serialize(pz,coeff,prediction,mv,q,hud,reference)
        receiver=h.rx.Receiver();receiver.receive(h.raw(gold['packet'],h.GOLDEN));receiver.ref=reference
        decoded,patches,meta,count=receiver.receive(wire['packet'])
        self.assertTrue(np.any(meta['vectors']));self.assertTrue(any(np.any(c)for c in meta['coefficients']))
        for a,b in zip(decoded,reference,strict=True):np.testing.assert_array_equal(a,b)

    def test_one_different_sample_disqualifies_partial_MB_and_nonzero_required(self):
        shapes=((480,720),(240,360),(240,360));planes=tuple(np.full(shape,128,np.int16)for shape in shapes)
        coeff=tuple(np.zeros((5400 if a==0 else 1350,8,8),np.int16)for a in range(3))
        z=dict(normalized=planes,coefficients=coeff);g=dict(normalized=tuple(p.copy()for p in planes),coefficients=coeff)
        vectors=np.zeros((15,23,2),np.int8);vectors[5,22]=[4,0]
        chosen,eligible,diffs,cost,work=model.selection(z,g,vectors)
        self.assertTrue(eligible[5,22]);self.assertEqual(int(eligible.sum()),1);self.assertFalse(chosen.any())
        g['normalized'][0][5*32,719]=129
        chosen,eligible,diffs,cost,work=model.selection(z,g,vectors)
        self.assertFalse(eligible[5,22]);self.assertEqual(diffs[5,22,0],1)
    def test_strict_actual_whole_byte_guard_and_cap(self):
        self.assertEqual(model.choose(100,99),'mixed');self.assertEqual(model.choose(100,100),'zero')
        self.assertEqual(model.choose(49153,49152),'mixed');self.assertEqual(model.choose(49154,49153),'zero')
        with self.assertRaises(ValueError):model.choose(100.,99)

if __name__=='__main__':unittest.main()
