import struct
import unittest
import zlib
import numpy as np
import skip_codec as s


def map_for(w,h):
    return s.gm.roi.declared_map(w,h,((0,0,16,16),),8,16)


class SkipTests(unittest.TestCase):
    def test_actual_dense_split_and_zero_planes_roundtrip(self):
        rng=np.random.default_rng(1401)
        for coeff in (np.zeros((12,8,8),np.int16),rng.integers(-12,13,(12,8,8),dtype=np.int16)):
            coeff[1]=0;coeff[1,0,0]=-7
            for structured in (False,True):
                packet,info=s.encode_plane(coeff,4,structured=structured)
                np.testing.assert_array_equal(s.decode_plane(packet,12,4),coeff)
                self.assertEqual(len(packet),info['selected_bytes'])
                if structured:self.assertEqual(len(packet),min(info['dense_bytes'],info['split_bytes']))

    def test_split_parser_rejects_invalid_mask_dc_padding_and_lengths(self):
        n=3
        def packet(mask,ndc=0,dc=b'',full=b''):
            return s.PLANE.pack(s.PLANE_MAGIC,1,n,1,ndc,len(full))+mask+dc+full
        for bad in (packet(b'\xc0'),packet(b'\x01'),packet(b'\x40',1,b'\x00\x00'),
                    packet(b'\x40',1,struct.pack('<h',2049)),packet(b'\x40',0)):
            with self.assertRaises(ValueError):s.decode_plane(bad,n,1)

    def test_pruning_is_measured_integer_bound_and_protects_scale8(self):
        rng=np.random.default_rng(1402);w,h=32,16;m=map_for(w,h)
        c=np.zeros((8,8,8),np.int16);c[:,0,0]=1
        for limit in (2,4):
            changed,info=s.prune(c,m,w,h,0,limit)
            tables=s.gm.roi.block_tables(m,w,h,0)
            before=s.gm.ft.inverse(c.astype(np.int64)*tables)
            after=s.gm.ft.inverse(changed.astype(np.int64)*tables)
            self.assertLessEqual(np.max(np.abs(before-after)),limit)
            protected=s.gm.roi.block_scales(m,w,h,0)==8
            np.testing.assert_array_equal(changed[protected],c[protected])
            self.assertEqual(info['protected'],int(protected.sum()))
            self.assertGreater(info['zeroed'],0)

    def test_keys_are_never_pruned_and_exact_profile_matches_gm(self):
        rng=np.random.default_rng(1403);m=map_for(32,16)
        normal=s.gm.Encoder();exact=s.Encoder();lossy=s.Encoder(profile='prune',limit=4)
        a=s.gm.Receiver();b=s.Receiver();c=s.Receiver()
        for i in range(6):
            rgb=rng.integers(80,130,(16,32,3),dtype=np.uint8)
            base=normal.prepare(rgb,i,scale_map=m,force_key=i==3)
            e=exact.prepare(rgb,i,scale_map=m,force_key=i==3)
            l=lossy.prepare(rgb,i,scale_map=m,force_key=i==3)
            expected,_=a.receive(base);actual,ei=b.receive(e.packet);out,li=c.receive(l.packet)
            np.testing.assert_array_equal(expected,actual)
            if i in (0,3):self.assertEqual(l.level,0);np.testing.assert_array_equal(out,actual)
            self.assertEqual(exact.expected_hash(i),s.hashlib.sha256(actual.tobytes()).hexdigest())
            normal.ack(i,epoch=1)
            self.assertTrue(exact.ack(i,epoch=1,content_crc=ei['content_crc']))
            self.assertTrue(lossy.ack(i,epoch=1,content_crc=li['content_crc']))

    def test_chroma_halo_preserves_priority_pixels_under_bilinear_color(self):
        w,h=48,48;m=map_for(w,h)
        coeff=[np.zeros((36,8,8),np.int16),np.zeros((9,8,8),np.int16),np.zeros((9,8,8),np.int16)]
        coeff[1][:,0,0]=2
        prediction=tuple(np.full(shape,128,np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))
        pruned=[s.prune(c,m,w,h,i,4)[0] for i,c in enumerate(coeff)]
        baseline=s.gm.ft.planes_to_rgb(s.fast_codec.reconstruct(coeff,prediction,m,w,h))
        actual=s.gm.ft.planes_to_rgb(s.fast_codec.reconstruct(pruned,prediction,m,w,h))
        np.testing.assert_array_equal(actual[:16,:16],baseline[:16,:16])
        self.assertTrue(np.any(pruned[1]!=coeff[1]))
        protected=m==8;halo=protected.copy();halo[:,1:]|=protected[:,:-1];halo[1:,:]|=protected[:-1,:];halo[1:,1:]|=protected[:-1,:-1]
        np.testing.assert_array_equal(pruned[1][halo.reshape(-1)],coeff[1][halo.reshape(-1)])

    def test_internal_candidate_rejects_nonzero_global_prediction(self):
        e=s.Encoder();rng=np.random.default_rng(1405);rgb=rng.integers(0,256,(64,96,3),dtype=np.uint8)
        m=map_for(96,64);key=e.prepare(rgb,0,scale_map=m)
        e.ack(0,epoch=1,content_crc=s.tag(key.packet))
        moved=np.roll(rgb,4,axis=1);p=e.analyze(moved,1,mode='global')
        self.assertTrue(p.dx or p.dy)
        with self.assertRaises(ValueError):e.encode_sr_candidate(p,m)

    def test_cap_reject_does_not_commit_and_work_is_paid(self):
        e=s.Encoder(frame_cap=60);rgb=np.full((16,32,3),80,np.uint8)
        before=e._generation;d=e.prepare(rgb,0,scale_map=map_for(32,16))
        self.assertFalse(d.accepted);self.assertGreater(d.service_ms,0);self.assertGreater(d.candidate_bytes,60)
        self.assertEqual(e.pending,{});self.assertEqual(e.last_issued,-1);self.assertEqual(e._generation,before)

    def test_wrong_ack_expiry_key_drain_and_p_reference(self):
        e=s.Encoder(window=2);rx=s.Receiver();m=map_for(32,16);rgb=np.full((16,32,3),90,np.uint8)
        d=e.prepare(rgb,0,scale_map=m)
        self.assertFalse(e.ack(0,epoch=2,content_crc=s.tag(d.packet)))
        self.assertFalse(e.ack(0,epoch=1,content_crc=s.tag(d.packet)^1))
        self.assertFalse(e.can_prepare())
        _,info=rx.receive(d.packet);self.assertTrue(e.ack(0,epoch=1,content_crc=info['content_crc']))
        p=e.prepare(rgb,1,scale_map=m);q=e.prepare(rgb,2,scale_map=m)
        self.assertFalse(e.can_prepare());self.assertFalse(e.can_prepare(True))
        self.assertTrue(e.expire(1));self.assertTrue(e.expire(2));self.assertEqual(e.anchor_id,0)
        key=e.prepare(rgb,3,scale_map=m,force_key=True);self.assertTrue(e.expire(3));self.assertIsNone(e.anchor_id)

    def test_atomic_bad_frame_session_geometry_crc_and_replay(self):
        m=map_for(32,16);e=s.Encoder();rx=s.Receiver();rgb=np.full((16,32,3),120,np.uint8)
        d=e.prepare(rgb,0,scale_map=m)
        def altered(index,value):
            fields=list(s.HEADER.unpack_from(d.packet));fields[index]=value
            return s.seal(s.HEADER.pack(*fields)+d.packet[s.HEADER.size:-4])
        bads=[d.packet[:-1]+bytes([d.packet[-1]^1]),altered(3,2),altered(2,3),altered(6,31)]
        for bad in bads:
            with self.assertRaises(ValueError):rx.receive(bad)
            self.assertIsNone(rx.anchor_id);self.assertEqual(rx.last_frame_id,-1)
        _,info=rx.receive(d.packet)
        with self.assertRaises(ValueError):rx.receive(d.packet)
        self.assertEqual(rx.anchor_id,0)


if __name__=='__main__':unittest.main()
