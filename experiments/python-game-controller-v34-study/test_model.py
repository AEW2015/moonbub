import copy
import unittest
from unittest import mock
import numpy as np
import helpers as h
from controller import choose,complete,SCENES,POLICIES

class FrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        old=h.load(h.HERE.parent/'python-game-global-v33-study/results.json')
        hu=h.load(h.HERE.parent/'python-game-hud-runs-v33-study/results.json')
        case=next(c for c in old['cases'] if c['scene']==SCENES[0] and c['policy']=='band_control')
        hudcase=next(c for c in hu['cases'] if c['scene']==SCENES[0])
        cls.bases=[h.raw(r['base_packet'],h.HERE.parent/'python-game-global-v33-study') for r in case['rows'][:2]]
        cls.huds=[h.raw(r['packet'],h.HERE.parent/'python-game-hud-runs-v33-study') for r in hudcase['rows'][:2]]
        cls.key=h.p.encode_pair(cls.bases[0],cls.huds[0],epoch=25,frame_id=0)
        cls.pair=h.p.encode_pair(cls.bases[1],cls.huds[1],epoch=25,frame_id=1,key=False,source_slot=0,destination_slot=1)
        split=h.load(h.HERE.parent/'python-game-split-v33-study/results.json')
        row=next(r for r in split['rows'] if r['scene']==SCENES[0] and r['id']==1)
        folder=h.HERE.parent/'python-game-split-v33-study'
        parent=h.m.parse(h.raw(row['baseline']['base_packet'],folder))['vectors']
        cls.child=h.raw(row['trials'][1]['base_packet'],folder);meta=h.m.parse(cls.child)
        cls.motion,_=h.frame.prepare_motion(parent,meta['vectors'],720,480)
        cls.gm34=h.frame.wrap(cls.child,cls.motion)
        cls.hpair=h.p.encode_pair(cls.gm34,cls.huds[1],epoch=25,frame_id=1,key=False,source_slot=0,destination_slot=1)

    def ready(self):
        rx=h.p.Receiver();pixels,patches,ack=rx.receive(self.key);return rx,pixels

    def stable_reject(self,rx,pair,**kwargs):
        banks,hud,last,ack=rx.banks,rx.hud,rx.last_frame_id,rx.last_ack
        tags=[h.m.C.reference_tag(b.planes) if b else None for b in banks]
        with self.assertRaises(ValueError):rx.receive(pair,**kwargs)
        self.assertIs(rx.banks,banks);self.assertIs(rx.hud,hud)
        self.assertEqual((rx.last_frame_id,rx.last_ack),(last,ack))
        self.assertEqual(tags,[h.m.C.reference_tag(b.planes) if b else None for b in rx.banks])

    def pair_with(self,base=None,hud=None):
        p=h.p;b=self.gm34 if base is None else base;u=self.huds[1] if hud is None else hud
        return p.seal(p.PAIR.pack(b'CP34',1,p.PUBLISH,25,1,0,1,len(b),len(u),p.digest(b),p.digest(u))+b+u)

    def test_actual_CP34_HX33_commit_and_exact_ACK(self):
        rx,key=self.ready();pixels,patches,ack=rx.receive(self.pair);h.p.validate_ack(ack,self.pair)
        expected,_=h.m.decode(self.bases[1],key,expected_epoch=25,expected_reference_id=0)
        for a,b in zip(pixels,expected,strict=True):np.testing.assert_array_equal(a,b)
        self.assertEqual(sum(p['words'].size for p in patches),21120)
        self.assertEqual((rx.banks[0].frame_id,rx.banks[1].frame_id),(0,1))

    def test_GM34_literal_adapter_never_calls_encoder(self):
        rx,key=self.ready()
        with (mock.patch.object(h.frame.hierarchy,'pack',side_effect=AssertionError('encoder in receive')),
              mock.patch.object(h.frame.runtime.base,'pack_vectors',side_effect=AssertionError('motion encoder in receive'))):
            pixels,meta=h.frame.decode(self.gm34,key,expected_epoch=25,expected_reference_id=0)
        expected,_=h.m.decode(self.child,key,expected_epoch=25,expected_reference_id=0)
        for a,b in zip(pixels,expected,strict=True):np.testing.assert_array_equal(a,b)
        self.assertEqual(meta['wire_magic'],'GM34');self.assertEqual(meta['internal_raw_vector_bytes'],2701)
        h.p.validate_ack(rx.receive(self.hpair)[2],self.hpair)

    def test_GM34_bounds_CRC_lengths_and_child_binding(self):
        for bad in (self.gm34[:-1],self.gm34+b'\0',self.gm34[:90]+bytes([self.gm34[90]^1])+self.gm34[91:]):
            with self.assertRaises(ValueError):h.frame.parse_metadata(bad)
        fields=list(h.frame.HEADER.unpack_from(self.gm34));fields[13]+=1
        with self.assertRaises(ValueError):h.frame.parse_metadata(h.frame.seal(h.frame.HEADER.pack(*fields)+self.gm34[h.frame.HEADER.size:-4]))
        fields=list(h.frame.HEADER.unpack_from(self.gm34));fields[8]=32
        with self.assertRaises(ValueError):h.frame.parse_metadata(h.frame.seal(h.frame.HEADER.pack(*fields)+self.gm34[h.frame.HEADER.size:-4]))
        with self.assertRaises(ValueError):h.frame.wrap(self.bases[1],self.motion)

    def test_late_HUD_failure_does_not_publish_valid_base(self):
        rx,_=self.ready();fields=list(h.p.hud.p.HUD.unpack_from(self.huds[1]));fields[9]=bytes([fields[9][0]^1])+fields[9][1:]
        bad=h.p.seal(h.p.hud.p.HUD.pack(*fields)+self.huds[1][h.p.hud.p.HUD.size:-4])
        pair=self.pair_with(hud=bad);h.p.parse_pair(pair)
        self.stable_reject(rx,pair)
        h.p.validate_ack(rx.receive(self.hpair)[2],self.hpair)

    def test_wrong_reference_bank_and_output_tag_are_atomic(self):
        for index in (10,11):
            rx,_=self.ready();fields=list(h.frame.HEADER.unpack_from(self.gm34));fields[index]=bytes([fields[index][0]^1])+fields[index][1:]
            bad=h.frame.seal(h.frame.HEADER.pack(*fields)+self.gm34[h.frame.HEADER.size:-4])
            self.stable_reject(rx,self.pair_with(base=bad))

    def test_gates_replay_epoch_bank_and_ACK_binding(self):
        rx,_=self.ready()
        for flags in (dict(write_drained=False),dict(vblank=False),dict(write_drained=1)):
            self.stable_reject(rx,self.hpair,**flags)
        self.stable_reject(rx,self.key)
        bad=bytearray(self.hpair);bad[-1]^=1;self.stable_reject(rx,bytes(bad))
        fields=list(h.p.PAIR.unpack_from(self.hpair));fields[5]=1
        self.stable_reject(rx,h.p.seal(h.p.PAIR.pack(*fields)+self.hpair[h.p.PAIR.size:-4]))
        ack=rx.receive(self.hpair)[2];af=list(h.p.ACK.unpack_from(ack));af[4]=bytes(16)
        with self.assertRaises(ValueError):h.p.validate_ack(h.p.seal(h.p.ACK.pack(*af)),self.hpair)

    def test_fixed_HUD_and_inner_geometry_reject_before_pixel_decode(self):
        p=h.p;ui=p.hud.p.ui;payload=p.seal(ui.row.HEADER.pack(b'HP01',1,1,0,0,720,480,1,345600,43200)+b'\0\0'+bytes(43200))
        blank=tuple(np.full(shape,128,np.int16) for shape in ((480,720),(240,360),(240,360)))
        prep=h.adaptive.analyze_with(h.m.base,blank,None,epoch=25,frame_id=0,reference_id=h.m.NO_REF,block_size=32,motion_mode='zero')
        base=h.m.encode_prepared(prep,h.m.roi.declared_map(720,480,h.n.ROIS,8,16))[0]
        for rect in ((0,0,720,480),(0,0,1,1)):
            fields=list(p.hud.p.HUD.unpack_from(self.huds[0]));fields[0]=b'HU25';fields[2]=1
            fields[10:14]=[len(payload),0,0,0];fields[14:18]=[1,0,0,0];fields[18:]=list(rect)+[0]*12
            hud=p.seal(p.hud.p.HUD.pack(*fields)+payload)
            pair=p.seal(p.PAIR.pack(b'CP34',1,p.KEY|p.PUBLISH,25,0,255,0,len(base),len(hud),p.digest(base),p.digest(hud))+base+hud)
            self.assertLess(len(pair),49152)
            with mock.patch.object(p.hud,'decode_hud',side_effect=AssertionError('pixel decode before bound')):
                self.stable_reject(p.Receiver(),pair)

class SelectionTests(unittest.TestCase):
    def test_integer_size_error_guard_shadow_and_ties(self):
        def c(size,sse):return dict(complete_bytes=size,hybrid=dict(active_squared_error=sse))
        shadow=c(100,100);a,b,d=c(90,101),c(100,99),c(99,100)
        self.assertIs(choose(shadow,[a,b,d]),d);self.assertFalse(a['qualified']);self.assertFalse(b['qualified'])
        self.assertIsNone(choose(None,[d]))
        zero=c(100,0);self.assertIs(choose(zero,[c(90,1)]),zero)
        self.assertIs(choose(shadow,[c(49153,0)]),shadow)

    def test_complete_unique_cohort_matrix_and_frame_order(self):
        cases=[dict(scene=s,policy=p,rows=[dict(id=i) for i in range(48)]) for s in SCENES for p in POLICIES]
        complete(cases)
        for bad in (cases[:-1],cases+[cases[0]],cases[:-1]+[cases[0]]):
            with self.assertRaises(ValueError):complete(bad)
        bad=copy.deepcopy(cases);bad[0]['rows'][1]['id']=0
        with self.assertRaises(ValueError):complete(bad)
if __name__=='__main__':unittest.main()
