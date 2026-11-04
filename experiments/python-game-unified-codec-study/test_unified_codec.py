import struct
import unittest
import numpy as np
import unified_codec as u
from ui_plugin import PatchSelector


class UnifiedTests(unittest.TestCase):
    def image(self,value=70,w=64,h=48):return np.full((h,w,3),value,np.uint8)
    def step(self,enc,rx,i,rgb=None,**kwargs):
        rgb=self.image(70+i) if rgb is None else rgb
        d=enc.prepare(rgb,i,**kwargs);self.assertTrue(d.accepted)
        actual,info,ack=rx.receive(d.packet)
        self.assertEqual(enc.expected_hash(i),u.hashlib.sha256(actual.tobytes()).hexdigest())
        self.assertEqual(enc.expected_base_hash(i),info['base_rgb_sha256'])
        self.assertTrue(enc.ack(ack))
        for slot in (0,1):
            a,b=enc.banks[slot],rx.banks[slot]
            self.assertEqual(a is None,b is None)
            if a is not None:
                self.assertEqual((a.frame_id,a.tag),(b.frame_id,b.tag))
                for aa,bb in zip(a.planes,b.planes):np.testing.assert_array_equal(aa,bb)
        return d,actual,info,ack

    def test_exact_selection_shares_analysis_and_matches_gm_references(self):
        rng=np.random.default_rng(1501)
        controls=[(u.Encoder(mode=mode),u.Receiver()) for mode in ('gm','exact')]
        for i in range(8):
            rgb=rng.integers(70,120,(48,64,3),dtype=np.uint8) if i%2 else self.image(75+i)
            out=[]
            for enc,rx in controls:
                d,actual,_,_=self.step(enc,rx,i,rgb,promote=i in (2,5),force_key=i==6)
                self.assertEqual(d.info['analyze_calls'],1)
                self.assertEqual(d.info['forward_calls'],3)
                chosen=[a for a in d.info['inner_attempts'] if a['selected']]
                self.assertEqual(len(chosen),1)
                self.assertEqual(chosen[0]['bytes'],min(a['bytes'] for a in d.info['inner_attempts']))
                out.append(actual)
            np.testing.assert_array_equal(out[0],out[1])
        self.assertEqual(controls[1][0].analysis_count,8)
        self.assertEqual(controls[1][0].forward_calls,24)

    def test_dense_packet_gm_fallback_and_actual_split_bytes(self):
        noise=np.random.default_rng(1502).integers(0,256,(48,64,3),dtype=np.uint8)
        noisy=u.Encoder(mode='exact').prepare(noise,0)
        flat=u.Encoder(mode='exact').prepare(self.image(128),0)
        self.assertEqual(noisy.info['inner_codec'],'GM01')
        self.assertEqual(flat.info['inner_codec'],'SR01')
        self.assertTrue(all(p['shared_gm_dense_payload'] for p in noisy.info['sr_planes']))
        self.assertEqual(noisy.info['inner_bytes'],noisy.info['minimum_complete_inner_bytes'])

    def test_partial_geometry_dispatch_and_never_pruned_key(self):
        rng=np.random.default_rng(1503)
        for w,h in ((2,2),(34,18),(64,48)):
            for mode in ('gm','exact','prune4'):
                enc,rx=u.Encoder(mode=mode),u.Receiver()
                for i in range(3):
                    rgb=rng.integers(70,130,(h,w,3),dtype=np.uint8)
                    d,_,_,_=self.step(enc,rx,i,rgb)
                    if i==0:self.assertEqual(d.info['level'],0)

    def test_pruned_integration_bound_and_priority_halo(self):
        w,h=48,48;m=u.gm.roi.declared_map(w,h,((0,0,16,16),),8,16)
        controls=[(u.Encoder(mode=mode),u.Receiver()) for mode in ('gm','prune4')]
        source=self.image(128,w,h)
        for enc,rx in controls:self.step(enc,rx,0,source,scale_map=m)
        source=source.copy();source[:,:,0]+=2;source[16:,:,1]+=1
        outputs=[];planes=[]
        for enc,rx in controls:
            d=enc.prepare(source,1,scale_map=m)
            task=rx.begin(d.packet);planes.append(task.planes)
            actual,_,ack=rx.complete(task);outputs.append(actual);enc.ack(ack)
            if enc.mode=='prune4':
                self.assertTrue(d.info['pruning'])
                self.assertTrue(all(x['max_reconstructed_yuv_delta']<=4 for x in d.info['pruning']))
        for a,b in zip(*planes):self.assertLessEqual(np.max(np.abs(a-b)),4)
        np.testing.assert_array_equal(outputs[0][:16,:16],outputs[1][:16,:16])

    def test_ui_is_exact_display_only_and_outer_feedback_bound(self):
        rect=((0,0,16,8),)
        controls=[(u.Encoder(mode='exact',patch_builder=PatchSelector(rectangles=rect) if ui else None),u.Receiver()) for ui in (False,True)]
        rgb=np.random.default_rng(1504).integers(40,180,(48,64,3),dtype=np.uint8)
        for i in range(3):
            decisions=[];tasks=[]
            for enc,rx in controls:
                decisions.append(enc.prepare(rgb,i,promote=i==1));tasks.append(rx.begin(decisions[-1].packet))
            for a,b in zip(tasks[0].planes,tasks[1].planes):np.testing.assert_array_equal(a,b)
            self.assertEqual(u.identity(decisions[0].packet)['inner'],u.identity(decisions[1].packet)['inner'])
            np.testing.assert_array_equal(u.corpus.rgb565(tasks[1].rgb[:8,:16]),u.corpus.rgb565(rgb[:8,:16]))
            acks=[]
            for (_,rx),task in zip(controls,tasks):acks.append(rx.complete(task)[2])
            with self.assertRaises(ValueError):controls[1][0].ack(acks[0])
            for (enc,_),ack in zip(controls,acks):self.assertTrue(enc.ack(ack))
            for slot in (0,1):
                a,b=controls[0][0].banks[slot],controls[1][0].banks[slot]
                if a is not None:self.assertEqual(a.tag,b.tag)

    def test_all_ui_is_validated_before_reference_or_replay_publication(self):
        enc=u.Encoder(patch_builder=PatchSelector(rectangles=((0,0,16,8),)));rx=u.Receiver()
        d=enc.prepare(self.image(),0);meta=u.identity(d.packet)
        first=meta['patch_packets'][0]
        fields=list(u.HEADER.unpack_from(d.packet));fields[-2]=2
        blob=struct.pack('<I',len(first))+first;blob*=2;fields[-1]=len(blob)
        duplicate=u.seal(u.HEADER.pack(*fields)+meta['inner']+blob)
        body=bytearray(d.packet[:-4]);body[-1]^=1;bad_crc=u.seal(bytes(body))
        for packet in (duplicate,bad_crc):
            with self.assertRaises(ValueError):rx.begin(packet)
            self.assertEqual(rx.banks,{0:None,1:None});self.assertEqual(rx.last_frame_id,-1)
            self.assertIsNone(rx.active);self.assertEqual(rx.readers,0)
        _,_,ack=rx.receive(d.packet);enc.ack(ack)
        with self.assertRaises(ValueError):rx.receive(d.packet)

    def test_cap_and_invalid_callback_never_reserve_or_publish(self):
        class IgnoringBudget:
            def select(self,rgb,budget):
                packet=u.fast_codec.hybrid.hp.encode_patch(rgb,(0,0,16,8))
                return type('Selection',(),dict(patches=(packet,),details={}))()
        enc=u.Encoder(frame_cap=230,patch_builder=IgnoringBudget())
        before=(enc.banks.copy(),enc.last_issued,enc._generation)
        d=enc.prepare(self.image(),0)
        self.assertFalse(d.accepted);self.assertGreater(d.info['bytes'],230)
        self.assertEqual(before,(enc.banks,enc.last_issued,enc._generation));self.assertFalse(enc.pending)
        self.assertGreater(d.info['reconstruction_ms'],0)
        class WrongWords:
            def select(self,rgb,budget):
                packet=u.fast_codec.hybrid.hp.encode_patch(np.zeros_like(rgb),(0,0,16,8))
                return type('Selection',(),dict(patches=(packet,),details={}))()
        e=u.Encoder(patch_builder=WrongWords())
        with self.assertRaises(ValueError):e.prepare(self.image(),0)
        self.assertFalse(e.pending);self.assertEqual(e.last_issued,-1)

    def test_version_dispatch_and_every_feedback_publication_binding(self):
        enc,rx=u.Encoder(),u.Receiver();d=enc.prepare(self.image(),0)
        _,_,ack=rx.receive(d.packet)
        values=list(u.FEEDBACK.unpack_from(ack))
        changes=((0,b'AF01'),(1,1),(3,2),(4,1),(5,u.body_crc(u.identity(d.packet)['inner'])),(6,1),(7,2),(8,b'1'*16))
        for index,value in changes:
            changed=values.copy();changed[index]=value
            try:accepted=enc.ack(u.seal(u.FEEDBACK.pack(*changed)))
            except ValueError:accepted=False
            self.assertFalse(accepted)
            self.assertIn(0,enc.pending);self.assertIsNone(enc.banks[0])
        self.assertTrue(enc.ack(ack))
        for magic in (b'AR01',b'NOPE'):
            body=magic+d.packet[4:-4]
            with self.assertRaises(ValueError):u.identity(u.seal(body))

    def test_overlap_leases_uncertain_promotion_and_key_fallback(self):
        enc,rx=u.Encoder(),u.Receiver();self.step(enc,rx,0);self.step(enc,rx,1,promote=True)
        zero=enc.prepare(self.image(75),2,reference_bank=0)
        lease=enc.acquire(0)
        self.assertTrue(enc.can_prepare(promote=True))
        promoted=enc.prepare(self.image(80),3,promote=True)
        self.assertIsNone(enc.banks[1]);self.assertTrue(enc.can_prepare())
        fallback=enc.prepare(self.image(81),4,reference_bank=0)
        self.assertEqual(fallback.reference_bank,0)
        self.assertFalse(enc.can_prepare(True))
        lost=None
        for d in (zero,promoted,fallback):
            _,_,ack=rx.receive(d.packet)
            if d.promoted:lost=ack
            else:enc.ack(ack)
        enc.release(lease);enc.expire(3)
        self.assertIsNone(enc.banks[1]);self.assertFalse(enc.ack(lost))
        self.step(enc,rx,5,promote=True)
        lease=rx.acquire(1);d=enc.prepare(self.image(85),6,promote=True)
        with self.assertRaises(ValueError):rx.begin(d.packet)
        rx.release(lease);task=rx.begin(d.packet)
        self.assertEqual(rx.readers,1);rx.abort(task)
        self.assertEqual(rx.readers,0);self.assertIsNone(rx.active)
        with self.assertRaises(ValueError):rx.complete(task)


if __name__=='__main__':unittest.main()
