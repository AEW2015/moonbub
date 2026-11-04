import unittest
import numpy as np
import model as m


class CounterTests(unittest.TestCase):
    def assert_sizes(self, a):
        got = m.isolated_packet_bytes(a)
        want = [len(m.oracle.encode_coefficients(x[None], 1)) for x in a]
        np.testing.assert_array_equal(got, want)

    def test_all_rice_k_escape_boundaries_and_signed_domain(self):
        # Every legal mapped DC value and AC value, every k including escapes.
        f = m.oracle.frozen
        for escape, maximum, count in ((14, 13, 8193), (12, 11, 4096)):
            values = np.arange(count)
            for k in range(maximum + 1):
                actual = np.array([len(f._rice(int(v), k, escape)) for v in values])
                np.testing.assert_array_equal(m._rice_lengths(values, k, escape), actual)
        for pos in (0, 1, 6, 21, 63):
            values = np.arange(-2048, 2049, dtype=np.int16)
            a = np.zeros((len(values), 8, 8), np.int16)
            a.reshape(-1, 64)[:, m.ZIGZAG[pos]] = values
            self.assert_sizes(a)

    def test_sparse_dense_zero_runs_padding_raw_and_negative_controls(self):
        rng = np.random.default_rng(2601)
        blocks = [np.zeros((8, 8), np.int16)]
        for pos in range(64):
            for value in (-2048, -1, 1, 2048):
                x = np.zeros(64, np.int16); x[m.ZIGZAG[pos]] = value
                blocks.append(x.reshape(8, 8))
        for density in (0, .01, .1, .5, 1):
            a = rng.integers(-2048, 2049, (128, 8, 8), dtype=np.int16)
            a[rng.random(a.shape) > density] = 0
            blocks.extend(a)
        a = np.asarray(blocks)
        self.assert_sizes(a)
        # Same syntax count cannot replace entropy magnitudes; same marginal
        # bits cannot replace separately padded DC/AC streams.
        low = np.ones((1, 8, 8), np.int16)
        high = np.full_like(low, 2048)
        self.assertNotEqual(int(m.isolated_packet_bytes(low)[0]), int(m.isolated_packet_bytes(high)[0]))
        self.assertEqual(int(m.isolated_packet_bytes(high)[0]), 128 + m.OVERHEAD)

    def test_general_packets_row_resets_and_noncontiguous(self):
        rng = np.random.default_rng(26)
        for n, w in ((1, 1), (12, 1), (12, 3), (12, 12), (256, 256), (513, 3)):
            for density in (0, .03, .5, 1):
                a = rng.integers(-2048, 2049, (n, 8, 8), dtype=np.int16)
                a[rng.random(a.shape) > density] = 0
                a[::2, 0, 0] = -2048
                a[1::2, 0, 0] = 2048
                self.assertEqual(m.count_packets(a, w), len(m.oracle.encode_coefficients(a, w)))
        a = np.zeros((65536, 8, 8), np.int16)
        self.assertEqual(m.count_packets(a, 256), len(m.oracle.encode_coefficients(a, 256)))
        self.assert_sizes(a[:8, :, ::-1])

    def test_raw_tie_is_raw_in_frozen_oracle(self):
        # Deterministic search for exactly 128 candidate payload bytes.
        rng = np.random.default_rng(2602)
        found = False
        for _ in range(10000):
            a = rng.integers(-700, 701, (1, 8, 8), dtype=np.int16)
            a.reshape(-1)[rng.choice(64, 1)] = 0
            z = a.reshape(1,64)[:,m.ZIGZAG].astype(np.int32)
            dc_bits = int(m._DC_MIN_LENGTH[m._mapped(z[:,0])][0])
            b,p = np.nonzero(z[:,1:]);p=p+1
            vals=m._mapped(z[b,p])-1
            prev=np.r_[0,p[:-1]]
            ac=5*len(p)+2*int(((p-prev-1)//16).sum())+2*int(not len(p) or p[-1]!=63)
            for lo,hi in ((1,5),(6,20),(21,63)):
                v=vals[(p>=lo)&(p<=hi)]
                ac+=min(int(m._rice_lengths(v,k,12).sum()) for k in range(12))
            if 4+(dc_bits+7)//8+(ac+7)//8==128:
                packet=m.oracle.encode_coefficients(a,1)
                self.assertEqual(packet[5],0)
                self.assertEqual(m.count_packets(a,1),len(packet))
                self.assert_sizes(a);found=True;break
        self.assertTrue(found)

    def test_invalid_inputs(self):
        good=np.zeros((1,8,8),np.int16)
        for a in (np.zeros((0,8,8),np.int16),np.zeros((65537,8,8),np.int16),
                  np.zeros((1,8,8),np.int32),np.zeros((1,64),np.int16),
                  np.full((1,8,8),-32768,np.int16),np.full((1,8,8),2049,np.int16)):
            for fn in (m.isolated_packet_bytes,lambda a:m.count_packets(a,1)):
                with self.assertRaises(ValueError):fn(a)
        for w in (None,True,False,np.int64(1),0,-1,257,2,1.0):
            with self.assertRaises(ValueError):m.count_packets(good,w)

    def test_rdo_choices_stats_and_final_plane_packet_parity(self):
        b=m.base;rng=np.random.default_rng(2603)
        rgb=rng.integers(0,256,(64,64,3),dtype=np.uint8)
        src=tuple(b.ft.rgb_to_planes(rgb));mapped=b.roi.declared_map(64,64,((0,0,16,16),),8,16)
        _,reference,_=b.encode_planes(src,None,mapped)
        changed=tuple(np.clip(x.astype(np.int32)+rng.integers(-10,11,x.shape),0,255).astype(np.int16) for x in src)
        p=b.analyze_planes(changed,reference,frame_id=1,reference_id=0,motion_mode='zero')
        coefficients=b._quantize(p.raw_coefficients,mapped,64,64)
        for lam in (0,.1,1,5,1000000):
            expected,old=b._rdo_skip(p,coefficients,mapped,lam)
            got,new=m.rdo_skip(p,coefficients,mapped,lam)
            for x,y in zip(expected,got):np.testing.assert_array_equal(x,y)
            for name,value in old.items():
                if name not in ('cp02_probe_calls','cp02_probe_bytes'):self.assertEqual(new[name],value,name)
            self.assertEqual(new['cp02_logical_probe_calls'],old['cp02_probe_calls'])
            self.assertEqual(new['cp02_logical_probe_bytes'],old['cp02_probe_bytes'])
            self.assertEqual(new['cp02_probe_calls'],0)
            for plane,(x,y) in enumerate(zip(expected,got)):
                self.assertEqual(b._encode_plane(x,8 if plane==0 else 4)[0],b._encode_plane(y,8 if plane==0 else 4)[0])
        key=b.analyze_planes(src,None)
        got,stats=m.rdo_skip(key,coefficients,mapped,1)
        self.assertIs(got,coefficients);self.assertEqual(stats['cp02_size_counter_calls'],0)


if __name__=='__main__':unittest.main(verbosity=2)
