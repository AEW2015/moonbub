"""Global frontier, hidden commit and availability-context regressions."""
import unittest
import numpy as np
import verify as v

class RasterTests(unittest.TestCase):
    def test_global_left_and_top_cross_old_tile_boundaries(self):
        base=np.full((24,24),100,np.int16);current=np.full((24,24),250,np.int16)
        current[:8,15]=130;current[15,:8]=70
        np.testing.assert_array_equal(v.predict_block(base,current,0,2,2),130)
        np.testing.assert_array_equal(v.predict_block(base,current,2,0,1),70)
        # Old tile-local rules would ignore these available global edges.
        np.testing.assert_array_equal(v.spatial.predict_block(base,current,0,2,2),100)
        np.testing.assert_array_equal(v.spatial.predict_block(base,current,2,0,1),100)

    def test_future_pixels_are_not_predictor_context(self):
        base=np.full((24,24),100,np.int16);a=np.full((24,24),-777,np.int16)
        a[:8,:]=120;a[8:16,:8]=90;b=a.copy()
        # For block(1,1), only row7 columns8..15 and column7 rows8..15 matter.
        b[8:,8:]=300;b[16:,:]=300
        for mode in range(4):np.testing.assert_array_equal(v.predict_block(base,a,1,1,mode),v.predict_block(base,b,1,1,mode))
        for mode in range(4):np.testing.assert_array_equal(v.predict_block(base,a,0,0,mode),100)

    def test_global_hidden_commit_is_visible_to_next_block(self):
        base=np.full((8,24),40,np.int16);coeff=np.zeros((3,8,8),np.int16)
        # First blockhidden, second usesleftedge, third mode0. Directional
        # andDCleft corrections coincide; stablemode2 is the representative.
        modes=np.array([0,2,0],np.uint8)
        hidden=np.array([[True,False,False]])
        component=v.spatial.canonical_modes(modes[~hidden.reshape(-1)])
        out,decoded,_,_=v.reconstruct_plane(base,coeff,component,np.ones((3,8,8),np.int64),hidden)
        np.testing.assert_array_equal(out[:,:16],128);np.testing.assert_array_equal(out[:,16:],40)
        np.testing.assert_array_equal(decoded,modes)

    def test_rank_context_uses_availability_not_parity(self):
        # A reader with no events can still demonstrate mandatoryN1 implicitrank.
        payload=b'\x03'+(18).to_bytes(4,'little')+bytes([0x40,0,0])
        reader=v.RankReader(payload)
        self.assertEqual(reader.rank(1,2,2),0);self.assertEqual(reader.finish()['binary_decisions'],0)
        for count in (0,5,True):
            with self.assertRaises(ValueError):v.RankReader(payload).rank(count,2,2)
        class RecordingBits:
            def __init__(self):self.pos=0;self.contexts=[]
            def decode(self,context):self.contexts.append(context);return 0
        for count,by,bx,context in ((4,2,2,42),(3,0,2,15),(2,2,0,24)):
            reader=v.RankReader(payload);bits=RecordingBits();reader.reader=bits
            self.assertEqual(reader.rank(count,by,bx),0)
            self.assertEqual(bits.contexts,[context])

    def packets(self):
        path=v.HERE/'results.json'
        if not path.exists():self.skipTest('actual RR41 archives required')
        rows=v.load(path)['cases'][0]['rows']
        return v.raw(rows[0]['control']['packet']),v.raw(rows[1]['control']['packet'])

    def rewrite(self,packet,change):
        outer=list(v.OUTER.unpack_from(packet));inner=packet[v.OUTER.size:v.OUTER.size+outer[11]]
        fields=list(v.INNER.unpack_from(inner));tail=bytearray(inner[v.INNER.size:-4])
        change(outer,fields,tail)
        inner=v.seal(v.INNER.pack(*fields)+tail)
        return v.seal(v.OUTER.pack(*outer)+inner+packet[v.OUTER.size+outer[11]:-4])

    def test_original_envelope_and_inner_CRC_are_checked_before_adapter(self):
        key,_=self.packets()
        outer=list(v.OUTER.unpack_from(key));end=v.OUTER.size+outer[11]
        body=bytearray(key[:-4]);body[end-1]^=1
        inner_bad=v.seal(bytes(body))
        outer_bad=key[:-1]+bytes([key[-1]^1])
        for packet in (inner_bad,outer_bad):
            rx=v.Receiver()
            with self.assertRaises(ValueError):rx.receive(packet)
            self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_resealed_profile_or_dispatch_cannot_publish(self):
        key,_=self.packets()
        def profile(outer,fields,tail):outer[8]=v.rank.PROFILE
        def dispatch(outer,fields,tail):tail[fields[10]]=255
        for change in (profile,dispatch):
            rx=v.Receiver()
            with self.assertRaises(ValueError):rx.receive(self.rewrite(key,change))
            self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_wrong_committed_output_cannot_publish(self):
        key,_=self.packets()
        def change(outer,fields,tail):outer[10]=fields[9]=bytes([1])*16
        rx=v.Receiver()
        with self.assertRaises(ValueError):rx.receive(self.rewrite(key,change))
        self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_wrong_prior_reference_preserves_accepted_state(self):
        key,predicted=self.packets()
        def change(outer,fields,tail):outer[9]=fields[8]=bytes([1])*16
        rx=v.Receiver();rx.receive(key);saved=(rx.ref,rx.hud,rx.rid,rx.last)
        with self.assertRaises(ValueError):rx.receive(self.rewrite(predicted,change))
        self.assertIs(rx.ref,saved[0]);self.assertIs(rx.hud,saved[1]);self.assertEqual((rx.rid,rx.last),saved[2:])

if __name__=='__main__':unittest.main()
