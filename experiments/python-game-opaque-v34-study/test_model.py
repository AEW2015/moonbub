import unittest
import numpy as np
import helpers as h


class MaskTests(unittest.TestCase):
    def test_visible_support_chroma_border_and_input_ownership(self):
        source=(np.full((48,48),74,np.int16),np.full((24,24),90,np.int16),np.full((24,24),152,np.int16))
        before=tuple(v.copy() for v in source);rect=((16,16,16,16),)
        safe=h.mask.mask_source(source,rect);full=h.mask.mask_source(source,rect,preserve_chroma_border=False)
        original=h.m.ft.planes_to_rgb(source);safe_rgb=h.m.ft.planes_to_rgb(safe);full_rgb=h.m.ft.planes_to_rgb(full)
        outside=np.ones((48,48),bool);outside[16:32,16:32]=False
        np.testing.assert_array_equal(original[outside],safe_rgb[outside])
        self.assertGreater(int(np.count_nonzero(original[outside]!=full_rgb[outside])),0)
        for a,b in zip(source,before):np.testing.assert_array_equal(a,b)
        self.assertTrue(np.all(safe[0][16:32,16:32]==128))
        self.assertTrue(np.all(safe[1][9:16,9:16]==128))
        np.testing.assert_array_equal(safe[1][8,:],source[1][8,:])
        for bad in (((1,2,4,4),),((0,0,50,4),),((0,0,0,4),)):
            with self.assertRaises(ValueError):h.mask.mask_source(source,bad)

    def test_invalid_hud_never_publishes_masked_base(self):
        if not (h.HERE/'results.json').exists():self.skipTest('benchmark archives needed')
        row=h.load(h.HERE/'results.json')['cases'][0]['rows'][0]
        pair=h.raw(row['packet'],h.HERE);rx=h.p.Receiver();snapshot=(rx.banks,rx.hud,rx.last_frame_id,rx.last_ack)
        # Outer CRC and SHA remain valid while the staged HX33 CRC is invalid.
        parsed=h.p.parse_pair(pair);bad_hud=bytearray(parsed['hud']);bad_hud[-1]^=1;bad_hud=bytes(bad_hud)
        fields=list(h.p.PAIR.unpack_from(pair));fields[-1]=h.p.digest(bad_hud)
        bad=h.p.seal(h.p.PAIR.pack(*fields)+parsed['base']+bad_hud)
        for malformed in (bad,pair[:-len(parsed['hud'])-4]+b'\0\0\0\0'):
            with self.assertRaises(ValueError):rx.receive(malformed)
            self.assertEqual((rx.banks,rx.hud,rx.last_frame_id,rx.last_ack),snapshot)
        rx.receive(pair);self.assertEqual(rx.last_frame_id,0)


if __name__=='__main__':unittest.main()
