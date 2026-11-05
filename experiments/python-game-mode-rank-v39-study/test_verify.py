"""Stable distinct-predictor menu and arithmetic rank-domain regressions."""
import struct,unittest
import numpy as np
import verify as v

class RankTests(unittest.TestCase):
    def test_tile_top_left_has_one_menu_and_no_rank_events(self):
        base=np.full((16,16),100,np.int16);current=np.full((16,16),250,np.int16)
        modes,predictions=v.unique_predictors(base,current,0,0)
        self.assertEqual(modes,[0]);self.assertEqual(len(predictions),1)
        np.testing.assert_array_equal(predictions[0],100)

    def test_stable_duplicates_and_clipping_reduce_menu(self):
        base=np.full((16,16),100,np.int16);current=np.full((16,16),140,np.int16)
        modes,_=v.unique_predictors(base,current,1,1);self.assertEqual(modes,[0,1])
        current[8:16,7]=60
        modes,_=v.unique_predictors(base,current,1,1);self.assertEqual(modes,[0,1,2])
        base[8:,8:]=255;current[:]=255
        modes,predictions=v.unique_predictors(base,current,1,1);self.assertEqual(modes,[0])
        np.testing.assert_array_equal(predictions[0],255)

    def test_rank_and_derived_cardinality_are_bounded(self):
        self.assertEqual(v.canonical_mode([0,2,3],2),3)
        for rank in (-1,3,True,1.0):
            with self.assertRaises(ValueError):v.canonical_mode([0,2,3],rank)
        # AB38 encoding of zero decisions: finish bits01 plus16 guard zeros.
        empty=b'\x03'+(18).to_bytes(4,'little')+bytes([0x40,0,0])
        reader=v.RankReader(empty);self.assertEqual(reader.rank(1,0,0),0)
        work=reader.finish();self.assertEqual(work['binary_decisions'],0)
        for count in (0,5,True):
            with self.assertRaises(ValueError):v.RankReader(empty).rank(count,0,0)
        for payload in (empty[:-1],empty+b'\0',empty[:-1]+b'\x01'):
            with self.assertRaises(ValueError):v.RankReader(payload)

    def test_fallback_nonfirst_duplicate_mode_is_rejected(self):
        base=np.full((16,16),100,np.int16);coeff=np.zeros((4,8,8),np.int16)
        modes=np.array([2,0,0,0],np.uint8)
        component=v.spatial.canonical_modes(modes)
        with self.assertRaises(ValueError):v.reconstruct_plane(base,coeff,component,np.ones((4,8,8),np.int64),np.zeros((2,2),bool))

    def packets(self):
        path=v.HERE/'results.json'
        if not path.exists():self.skipTest('actual RP39 archives required')
        data=v.load(path);rows=data['cases'][0]['rows']
        ranked=next(v.raw(r['packet']) for c in data['cases'] for r in c['rows'] if v.parse(v.raw(r['packet']))['mode_payloads'][0][0]==3)
        return v.raw(rows[0]['packet']),v.raw(rows[1]['packet']),ranked

    def rewrite(self,packet,change):
        outer=list(v.OUTER.unpack_from(packet));inner=packet[v.OUTER.size:v.OUTER.size+outer[11]]
        fields=list(v.INNER.unpack_from(inner));tail=bytearray(inner[v.INNER.size:-4])
        change(outer,fields,tail)
        inner=v.seal(v.INNER.pack(*fields)+tail)
        return v.seal(v.OUTER.pack(*outer)+inner+packet[v.OUTER.size+outer[11]:-4])

    def test_resealed_unknown_mode_or_profile_cannot_publish(self):
        key,_,_=self.packets()
        def dispatch(outer,fields,tail):tail[fields[10]]=4
        def profile(outer,fields,tail):outer[8]=bytes(16)
        for change in (dispatch,profile):
            rx=v.Receiver()
            with self.assertRaises(ValueError):rx.receive(self.rewrite(key,change))
            self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_resealed_arithmetic_guard_truncation_cannot_publish(self):
        _,_,ranked=self.packets()
        # Use a key frame that actually carries a rank stream on plane0.
        self.assertTrue(v.parse(ranked)['key'])
        def change(outer,fields,tail):
            start=fields[10];bits=struct.unpack_from('<I',tail,start+1)[0]
            struct.pack_into('<I',tail,start+1,bits-1)
        rx=v.Receiver()
        with self.assertRaises(ValueError):rx.receive(self.rewrite(ranked,change))
        self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_resealed_wrong_output_tag_cannot_publish(self):
        key,_,_=self.packets()
        def change(outer,fields,tail):outer[10]=fields[9]=bytes([1])*16
        rx=v.Receiver()
        with self.assertRaises(ValueError):rx.receive(self.rewrite(key,change))
        self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_wrong_prior_reference_preserves_accepted_state(self):
        key,predicted,_=self.packets()
        def change(outer,fields,tail):outer[9]=fields[8]=bytes([1])*16
        rx=v.Receiver();rx.receive(key);saved=(rx.ref,rx.hud,rx.rid,rx.last)
        with self.assertRaises(ValueError):rx.receive(self.rewrite(predicted,change))
        self.assertIs(rx.ref,saved[0]);self.assertIs(rx.hud,saved[1]);self.assertEqual((rx.rid,rx.last),saved[2:])

if __name__=='__main__':unittest.main()
