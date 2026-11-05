"""Independent mode syntax and tile-local prediction arithmetic regressions."""
import struct,unittest
import numpy as np
import verify as v

class IndependentTests(unittest.TestCase):
    def test_mode_syntax_dense_rle_zero_padding_and_nonminimal(self):
        for modes in (np.zeros(9,np.uint8),np.arange(13,dtype=np.uint8)%4,np.repeat(np.arange(4,dtype=np.uint8),20)):
            data=v.canonical_modes(modes);np.testing.assert_array_equal(v.unpack_modes(data,len(modes)),modes)
        # Five modes have six pad bits. Resealed packets must not hide a mode.
        data=v.canonical_modes(np.array([0,1,2,3,1],np.uint8));self.assertEqual(data[0],0)
        with self.assertRaises(ValueError):v.unpack_modes(data[:-1]+bytes([data[-1]|1]),5)
        for data,count in ((b'\x01\x00\x00\x00',4),(b'\x01\x04\x01\x00',1),(b'\x00\x00',4),(b'\x02\x00',4)):
            with self.assertRaises(ValueError):v.unpack_modes(data,count)

    def test_tile_edges_vertical_horizontal_dc_and_negative_rounding(self):
        base=np.full((16,16),100,np.int16);current=np.full((16,16),250,np.int16)
        # Unavailable edges must not read the unrelated 250 samples.
        for mode in range(4):np.testing.assert_array_equal(v.predict_block(base,current,0,0,mode),100)
        current[7,8:16]=np.arange(8)+90;current[8:16,7]=np.arange(8)+110
        np.testing.assert_array_equal(v.predict_block(base,current,1,1,1),np.broadcast_to(np.arange(8)+90,(8,8)))
        np.testing.assert_array_equal(v.predict_block(base,current,1,1,2),np.broadcast_to((np.arange(8)+110)[:,None],(8,8)))
        np.testing.assert_array_equal(v.predict_block(base,current,1,1,3),104)
        current[7,:8]=99;current[7,0]=103 # residual sum=-4 over8 ->halfup0
        np.testing.assert_array_equal(v.predict_block(base,current,1,0,3),100)
        current[7,0]=102 # residual sum=-5 ->-1
        np.testing.assert_array_equal(v.predict_block(base,current,1,0,3),99)

    def test_prediction_clips_and_immediate_hidden_commit_feeds_neighbors(self):
        base=np.full((16,16),40,np.int16);coeff=np.zeros((4,8,8),np.int16)
        modes=np.array([0,0,1,0],np.uint8);tables=np.ones((4,8,8),np.int64)
        hidden=np.array([[True,False],[False,False]])
        output=v.reconstruct_plane(base,coeff,modes,tables,hidden)
        np.testing.assert_array_equal(output[:8,:8],128)
        np.testing.assert_array_equal(output[8:,:8],128)
        np.testing.assert_array_equal(output[:8,8:],40)
        current=np.full((16,16),255,np.int16);base[8:,8:]=250
        np.testing.assert_array_equal(v.predict_block(base,current,1,1,1),255)
        modes[0]=1
        with self.assertRaises(ValueError):v.reconstruct_plane(base,coeff,modes,tables,hidden)

    def packets(self):
        path=v.HERE/'results.json'
        if not path.exists():self.skipTest('actual pilot archives required')
        rows=v.load(path)['cases'][0]['rows']
        return v.raw(rows[0]['packet']),v.raw(rows[1]['packet'])

    def rewrite(self,packet,change):
        outer=list(v.OUTER.unpack_from(packet));inner=packet[v.OUTER.size:v.OUTER.size+outer[11]]
        fields=list(v.INNER.unpack_from(inner));tail=bytearray(inner[v.INNER.size:-4])
        change(outer,fields,tail)
        inner=v.seal(v.INNER.pack(*fields)+tail)
        return v.seal(v.OUTER.pack(*outer)+inner+packet[v.OUTER.size+outer[11]:-4])

    def test_actual_mode_dispatch_and_profile_corruption_cannot_publish(self):
        key,_=self.packets()
        def mode(outer,fields,tail):tail[fields[10]]=255
        def profile(outer,fields,tail):outer[8]=bytes(16)
        for change in (mode,profile):
            rx=v.Receiver()
            with self.assertRaises(ValueError):rx.receive(self.rewrite(key,change))
            self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_actual_wrong_committed_output_cannot_publish(self):
        key,_=self.packets()
        def change(outer,fields,tail):outer[10]=fields[9]=bytes([1])*16
        rx=v.Receiver()
        with self.assertRaises(ValueError):rx.receive(self.rewrite(key,change))
        self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_actual_wrong_prior_reference_preserves_accepted_state(self):
        key,predicted=self.packets()
        def change(outer,fields,tail):outer[9]=fields[8]=bytes([1])*16
        rx=v.Receiver();rx.receive(key);saved=(rx.ref,rx.hud,rx.rid,rx.last)
        with self.assertRaises(ValueError):rx.receive(self.rewrite(predicted,change))
        self.assertIs(rx.ref,saved[0]);self.assertIs(rx.hud,saved[1]);self.assertEqual((rx.rid,rx.last),saved[2:])

if __name__=='__main__':unittest.main()
