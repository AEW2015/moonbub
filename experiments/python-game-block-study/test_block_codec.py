import hashlib
import struct
import unittest
import zlib
import numpy as np
import block_codec as bc


def remint(packet,field=None,value=None,body_edit=None):
    fields=list(bc.HEADER.unpack_from(packet));payload=bytearray(packet[bc.HEADER.size:-4])
    if field is not None:fields[field]=value
    if body_edit:body_edit(payload)
    body=bc.HEADER.pack(*fields)+bytes(payload)
    return body+struct.pack('<I',zlib.crc32(body))


def mapping(w,h,scale=16):
    mw,mh=bc.roi.geometry(w,h);return np.full((mh,mw),scale,np.uint8)


def ack(enc,packet):
    return enc.ack(bc.HEADER.unpack_from(packet)[4],epoch=enc.epoch,frame_crc=zlib.crc32(packet[:-4]))


class CodecTests(unittest.TestCase):
    def test_key_matches_frozen_gm01_pixels_and_independent_receiver(self):
        rng=np.random.default_rng(11)
        for h,w in ((16,16),(18,34),(32,48)):
            rgb=rng.integers(0,256,(h,w,3),dtype=np.uint8);m=mapping(w,h)
            enc,rx=bc.Encoder(),bc.Receiver();packet=enc.prepare(rgb,0,scale_map=m)
            actual,info=rx.receive(packet)
            gm=bc.gc.Encoder();old=gm.prepare(rgb,0,scale_map=m);expected,_=bc.gc.Receiver().receive(old)
            np.testing.assert_array_equal(actual,expected)
            self.assertEqual(hashlib.sha256(actual.tobytes()).hexdigest(),enc.expected_hash(0))
            self.assertIsNone(enc.anchor_id);self.assertTrue(ack(enc,packet));self.assertEqual(enc.anchor_id,0)
            self.assertTrue(all(not p.flags.writeable for p in enc._anchor))

    def test_deterministic_sad_search_tie_order_and_even_edge_vectors(self):
        rng=np.random.default_rng(111);ref=rng.integers(0,256,(18,34),dtype=np.int16)
        current=ref[np.clip(np.arange(18)+2,0,17)[:,None],np.clip(np.arange(34)-2,0,33)]
        vectors,info=bc.estimate_vectors(current,ref,4)
        self.assertEqual(info['candidate_count'],25)
        np.testing.assert_array_equal(vectors,np.broadcast_to((-2,2),vectors.shape))
        zeros,_=bc.estimate_vectors(np.full_like(ref,80),np.full_like(ref,80),8)
        self.assertFalse(np.any(zeros))
        # Independent scalar SAD/min tuple for every partial macroblock.
        for by in range(vectors.shape[0]):
            for bx in range(vectors.shape[1]):
                costs=[]
                for dy in range(-4,5,2):
                    for dx in range(-4,5,2):
                        total=0
                        for y in range(by*16,min(by*16+16,18)):
                            for x in range(bx*16,min(bx*16+16,34)):
                                total+=abs(int(current[y,x])-int(ref[min(max(y+dy,0),17),min(max(x+dx,0),33)]))
                        costs.append((total,abs(dx)+abs(dy),dy,dx))
                _,_,dy,dx=min(costs)
                self.assertEqual(tuple(vectors[by,bx]),(dx,dy))

    def test_predict_luma_chroma_half_vector_and_clamped_partial_blocks(self):
        y=np.arange(18*34,dtype=np.int16).reshape(18,34)%256
        c=np.arange(9*17,dtype=np.int16).reshape(9,17)
        vectors=np.zeros((2,3,2),np.int8);vectors[:]=(-4,2);vectors[1,2]=(4,-4)
        predicted=bc.predict((y,c,c),vectors)
        for plane,p in enumerate((y,c,c)):
            size=16 if plane==0 else 8;factor=1 if plane==0 else 2
            for yy,xx in ((0,0),(p.shape[0]-1,p.shape[1]-1),(5,7)):
                dx,dy=vectors[yy//size,xx//size].astype(int)//factor
                self.assertEqual(predicted[plane][yy,xx],p[min(max(yy+dy,0),p.shape[0]-1),min(max(xx+dx,0),p.shape[1]-1)])

    def test_dense_sparse_actual_side_bytes_and_negative_vector_domains(self):
        zeros=np.zeros((2,3,2),np.int8)
        mode,data=bc.pack_vectors(zeros);self.assertEqual((mode,len(data)),(1,1))
        np.testing.assert_array_equal(bc.unpack_vectors(data,3,2,mode,False,4),zeros)
        dense=zeros.copy();dense[:]=(2,-4);mode,data=bc.pack_vectors(dense)
        self.assertEqual((mode,len(data)),(0,12))
        np.testing.assert_array_equal(bc.unpack_vectors(data,3,2,mode,False,4),dense)
        for args in ((b'\x01',3,2,1,False,4),(b'\x80\x00\x00',3,2,1,False,4),
                     (bytes([1,0])*6,3,2,0,False,4),(bytes([8,0])*6,3,2,0,False,4),
                     (b'',3,2,9,False,4),(b'\x00',3,2,0,True,4)):
            with self.assertRaises(ValueError):bc.unpack_vectors(*args)

    def test_whole_p_zero_residual_is_normative_yuv_prediction(self):
        rgb=np.full((16,32,3),128,np.uint8);m=mapping(32,16)
        enc,rx=bc.Encoder(),bc.Receiver();key=enc.prepare(rgb,0,scale_map=m);rx.receive(key);ack(enc,key)
        packet=enc.prepare(rgb,1,scale_map=m);p=bc.parse(packet,1)
        self.assertTrue(p['zero_residual']);self.assertEqual(p['coefficients'],(None,None,None))
        self.assertEqual(len(packet),bc.HEADER.size+4+p['map_bytes']+p['vector_bytes'])
        actual,info=rx.receive(packet)
        np.testing.assert_array_equal(actual,bc.ft.planes_to_rgb(bc.predict(enc._anchor,p['vectors'])))
        self.assertEqual(hashlib.sha256(actual.tobytes()).hexdigest(),enc.expected_hash(1));ack(enc,packet)
        # No source pixels or side image are carried by the zero-residual frame.
        self.assertLess(len(packet),80)

    def test_scene_cuts_noise_drop_and_independent_key_recovery(self):
        rng=np.random.default_rng(19);enc,rx=bc.Encoder(),bc.Receiver();m=mapping(32,32)
        frames=[np.full((32,32,3),128,np.uint8),rng.integers(0,256,(32,32,3),dtype=np.uint8),
                np.full((32,32,3),220,np.uint8),rng.integers(0,256,(32,32,3),dtype=np.uint8)]
        for i,rgb in enumerate(frames):
            packet=enc.prepare(rgb,i,scale_map=m,force_key=i==3)
            if i==1:enc.expire(i);continue
            actual,_=rx.receive(packet)
            self.assertEqual(hashlib.sha256(actual.tobytes()).hexdigest(),enc.expected_hash(i));ack(enc,packet)
        self.assertEqual(enc.anchor_id,3)

    def test_ack_loss_expiry_session_crc_and_two_credit_ownership(self):
        enc,rx=bc.Encoder(),bc.Receiver();rgb=np.full((16,32,3),128,np.uint8);m=mapping(32,16)
        key=enc.prepare(rgb,0,scale_map=m);rx.receive(key)
        with self.assertRaises(ValueError):enc.prepare(rgb,1,scale_map=m)
        for epoch,crc in ((2,zlib.crc32(key[:-4])),(1,0)):
            with self.assertRaises(ValueError):enc.ack(0,epoch=epoch,frame_crc=crc)
        self.assertIsNone(enc.anchor_id);enc.expire(0);self.assertFalse(ack(enc,key))
        recovery=enc.prepare(rgb,1,scale_map=m);self.assertTrue(bc.parse(recovery,1)['key'])
        rx.receive(recovery);ack(enc,recovery)
        one=enc.prepare(rgb,2,scale_map=m);two=enc.prepare(rgb,3,scale_map=m)
        with self.assertRaises(ValueError):enc.prepare(rgb,4,scale_map=m)
        with self.assertRaises(ValueError):enc.prepare(rgb,4,scale_map=m,force_key=True)
        self.assertEqual(enc.anchor_id,1);enc.expire(2);enc.expire(3);self.assertEqual(enc.anchor_id,1)
        with self.assertRaises(ValueError):bc.Receiver(2).receive(recovery)
        self.assertFalse(enc.pending)

    def test_acknowledged_reference_is_reconstruction_not_original_pixels(self):
        rng=np.random.default_rng(121);rgb=rng.integers(0,256,(32,32,3),dtype=np.uint8)
        enc,rx=bc.Encoder(),bc.Receiver();packet=enc.prepare(rgb,0,scale_map=mapping(32,32))
        rx.receive(packet);self.assertIsNone(enc._anchor);ack(enc,packet)
        for a,b in zip(enc._anchor,rx._anchor):np.testing.assert_array_equal(a,b)
        before=hashlib.sha256(enc._anchor[0].tobytes()).hexdigest();rgb[:]=0
        self.assertEqual(before,hashlib.sha256(enc._anchor[0].tobytes()).hexdigest())
        # P ACK loss does not invent a new P reference: the immutable key remains.
        p=enc.prepare(rgb,1,scale_map=mapping(32,32));rx.receive(p);enc.expire(1)
        self.assertEqual(enc.anchor_id,0);self.assertEqual(rx.anchor_id,0)
        nextp=enc.prepare(rgb,2,scale_map=mapping(32,32));actual,_=rx.receive(nextp)
        self.assertEqual(hashlib.sha256(actual.tobytes()).hexdigest(),enc.expected_hash(2));ack(enc,nextp)

    def test_parser_mutations_do_not_change_receiver_state(self):
        enc=bc.Encoder();rgb=np.full((16,32,3),128,np.uint8);m=mapping(32,16)
        packet=enc.prepare(rgb,0,scale_map=m)
        malformed=[packet[:-1],packet+b'\0',packet[:-1]+bytes([packet[-1]^1])]
        for field,value in ((0,b'GM01'),(1,2),(2,8),(3,2),(4,bc.NO_REF),(5,0),(6,3),(7,0),
                            (8,6),(9,2),(10,999),(12,999),(13,999),(14,0)):
            malformed.append(remint(packet,field,value))
        malformed.append(remint(packet,body_edit=lambda body:body.__setitem__(0,255)))
        for invalid in malformed:
            rx=bc.Receiver()
            with self.assertRaises(ValueError):rx.receive(invalid)
            self.assertIsNone(rx.anchor_id);self.assertEqual(rx.last_frame_id,-1)
        rx=bc.Receiver();rx.receive(packet)
        with self.assertRaises(ValueError):rx.receive(packet)

    def test_missing_reference_or_forged_zero_contract_never_commits(self):
        enc=bc.Encoder();rgb=np.full((16,32,3),128,np.uint8);m=mapping(32,16)
        key=enc.prepare(rgb,0,scale_map=m);ack(enc,key)
        packet=enc.prepare(rgb,1,scale_map=m)
        with self.assertRaises(ValueError):bc.Receiver().receive(packet)
        for invalid in (remint(packet,5,1),remint(key,2,3),remint(packet,14,1)):
            with self.assertRaises(ValueError):bc.parse(invalid,1)


if __name__=='__main__':unittest.main()
