from dataclasses import replace
import unittest
import numpy as np
import cheap_gate as gate


class CheapGateTests(unittest.TestCase):
    def test_eighty_families_lower_never_exceeds_exact(self):
        rng=np.random.default_rng(8804)
        for case in range(80):
            width=1+case%8;n=width*(1+case%4)
            a=rng.integers(-2048,2049,(n,8,8),dtype=np.int16)
            a[rng.random(a.shape)<case/80]=0
            if case%5==0:a[:]=0
            self.assertLessEqual(gate.coefficient_lower_bound(a,width),gate.exact.coefficient_size(a,width))
        for pos in range(64):
            a=np.zeros((2,8,8),np.int16);a.reshape(2,64)[1,gate.gc.ft.ZIGZAG[pos]]=1
            self.assertLessEqual(gate.coefficient_lower_bound(a,2),len(gate.gc.token_coeff.encode_coefficients(a,2)))

    def test_skip_exact_serialize_after_lower_bound_and_stale_reject(self):
        rgb=np.full((32,48,3),70,np.uint8);config=gate.rate.Config(frame_cap=1,rectangles=((0,0,16,16),))
        c=gate.Controller(config=config);decision=c.prepare(rgb,0)
        self.assertFalse(decision.accepted);self.assertTrue(all(r['provably_rejected'] for r in decision.attempts))
        self.assertFalse(c.encoder.pending)
        enc=gate.Encoder();p=enc.analyze(rgb,0);m=gate.gc.roi.declared_map(48,32,((0,0,16,16),),8,16)
        plan=enc.gate(p,m)
        with self.assertRaises(ValueError):enc.emit_gate(replace(plan))
        candidate=enc.emit_gate(plan)
        self.assertEqual(candidate.packet,enc.encode_candidate(p,m).packet)
        enc.commit(candidate)
        with self.assertRaises(ValueError):enc.emit_gate(plan)


if __name__=='__main__':unittest.main()
