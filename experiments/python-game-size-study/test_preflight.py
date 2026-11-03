from dataclasses import replace
import hashlib
import unittest
import numpy as np
import preflight as s


class SizeTests(unittest.TestCase):
    def test_eighty_families_exact_raw_sparse_and_extreme(self):
        rng=np.random.default_rng(8801)
        for case in range(80):
            width=1+case%8;n=width*(1+case%4)
            a=rng.integers(-2048,2049,(n,8,8),dtype=np.int16)
            a[rng.random(a.shape)<case/80]=0
            if case%5==0:a[:]=0
            a.reshape(n,64)[:,0]=np.where(np.arange(n)%2,2048,-2048)
            self.assertEqual(s.coefficient_size(a,width),len(s.gc.token_coeff.encode_coefficients(a,width)))

    def test_all_zigzag_positions_and_existing_72_plane_shapes(self):
        for pos in range(64):
            a=np.zeros((3,8,8),np.int16)
            a.reshape(3,64)[1,s.gc.ft.ZIGZAG[pos]]=1
            self.assertEqual(s.coefficient_size(a,3),len(s.gc.token_coeff.encode_coefficients(a,3)))
        # GM01 packets on small actual key/P histories exercise current qmaps.
        enc=s.Encoder();rx=s.gc.Receiver();rng=np.random.default_rng(8802)
        for i in range(6):
            rgb=rng.integers(0,256,(34,66,3),dtype=np.uint8)
            p=enc.analyze(rgb,i);m=s.gc.roi.declared_map(66,34,((0,0,16,16),),8,32)
            sized=enc.estimate_candidate(p,m);candidate=enc.emit_sized(sized)
            expected=s.gc.Encoder();other=expected.analyze(rgb,i)
            if i==0:self.assertEqual(candidate.packet,expected.encode_candidate(other,m).packet)
            packet=enc.commit(candidate);actual,_=rx.receive(packet)
            self.assertEqual(hashlib.sha256(actual.tobytes()).hexdigest(),enc.expected_hash(i));enc.ack(i,epoch=1)

    def test_admission_exact_without_serializing_rejected_and_stale(self):
        rgb=np.full((32,48,3),60,np.uint8)
        config=s.rate.Config(frame_cap=1,rectangles=((0,0,16,16),))
        control=s.Controller(config=config);decision=control.prepare(rgb,0)
        self.assertFalse(decision.accepted);self.assertEqual(len(decision.attempts),2)
        self.assertTrue(all(not a['serialized'] for a in decision.attempts));self.assertFalse(control.encoder.pending)
        enc=s.Encoder();p=enc.analyze(rgb,0);m=s.gc.roi.declared_map(48,32,((0,0,16,16),),8,16)
        sized=enc.estimate_candidate(p,m)
        with self.assertRaises(ValueError):enc.emit_sized(replace(sized))
        enc.commit(enc.emit_sized(sized))
        with self.assertRaises(ValueError):enc.emit_sized(sized)


if __name__=='__main__':unittest.main()
