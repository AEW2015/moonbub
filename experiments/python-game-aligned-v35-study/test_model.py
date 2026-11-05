import unittest
import numpy as np
import helpers as h


class MaskTests(unittest.TestCase):
    def test_scalar_support_complete_blocks_and_union(self):
        for length in (1,2,5,8,13):
            support=h.mask.axis_support(length)
            for sample,(low,high) in enumerate(support):
                reads=[]
                for pixel in range(2*length):
                    base=pixel//2
                    dependency={base}
                    if pixel%2:dependency.add(min(base+1,length-1))
                    if sample in dependency:reads.append(pixel)
                self.assertEqual(list(range(low,high)),reads)
        source=(np.full((50,66),74,np.int16),np.full((25,33),90,np.int16),np.full((25,33),152,np.int16))
        # Adjacent odd rectangle halves together cover a complete footprint.
        rectangles=((15,15,9,18),(24,15,9,18),(0,0,8,8),(58,42,8,8))
        saved=tuple(p.copy() for p in source)
        for policy in ('core8','luma8'):
            result=h.mask.mask_source(source,rectangles,policy)
            covered=h.mask.coverage(source[0].shape,rectangles)
            outside=~covered
            np.testing.assert_array_equal(h.m.ft.planes_to_rgb(source)[outside],h.m.ft.planes_to_rgb(result)[outside])
            for axis,(before,after) in enumerate(zip(source,result)):
                self.assertFalse(np.shares_memory(before,after))
                self.assertTrue(np.all(after[(after!=before)]==128))
                for by in range(0,before.shape[0],8):
                    for bx in range(0,before.shape[1],8):
                        tile=after[by:by+8,bx:bx+8]
                        changed=np.any(tile!=before[by:by+8,bx:bx+8])
                        footprint=[]
                        for py in range(50):
                            cy={py//2}
                            if py%2:cy.add(min(py//2+1,24))
                            for px in range(66):
                                cx={px//2}
                                if px%2:cx.add(min(px//2+1,32))
                                uses=(by<=py<by+8 and bx<=px<bx+8) if not axis else any(by<=iy<by+8 and bx<=ix<bx+8 for iy in cy for ix in cx)
                                if uses:footprint.append((py,px))
                        fully_covered=all(any(rx<=px<rx+rw and ry<=py<ry+rh for rx,ry,rw,rh in rectangles) for py,px in footprint)
                        expected=tile.shape==(8,8) and fully_covered and (not axis or policy=='core8')
                        self.assertEqual(bool(changed),expected)
                        if changed:self.assertEqual(tile.shape,(8,8));self.assertTrue(np.all(tile==128))
                np.testing.assert_array_equal(before,saved[axis])
            if policy=='luma8':
                np.testing.assert_array_equal(source[1],result[1]);np.testing.assert_array_equal(source[2],result[2])
        # This CH block's support is15..32 inclusive, not merely16..31.
        safe=h.mask.mask_source(source,rectangles)
        self.assertTrue(np.all(safe[1][8:16,8:16]==128))
        unsafe=h.mask.mask_source(source,((16,16,16,16),))
        np.testing.assert_array_equal(unsafe[1],source[1])
        # Edge clamp admits a complete first block with no negative halo.
        edge=h.mask.mask_source(source,((0,0,16,16),))
        self.assertTrue(np.all(edge[1][:8,:8]==128))

    def test_invalid_inputs_and_partial_union(self):
        source=(np.zeros((20,20),np.int16),np.zeros((10,10),np.int16),np.zeros((10,10),np.int16))
        for rect in (((-1,0,4,4),),((0,0,21,4),),((0,0,0,4),),((0.,0,4,4),),((True,0,4,4),),((0,0,4),),None):
            with self.assertRaises(ValueError):h.mask.mask_source(source,rect)
        for planes in (None,source[:2],(source[0],source[1].astype(float),source[2]),(source[0],source[1][:-1],source[2])):
            with self.assertRaises(ValueError):h.mask.mask_source(planes,())
        with self.assertRaises(ValueError):h.mask.mask_source(source,(),policy='other')
        unchanged=h.mask.mask_source(source,((0,0,7,20),(8,0,12,20)))
        np.testing.assert_array_equal(unchanged[0][:,:8],source[0][:,:8])
        self.assertTrue(np.all(unchanged[0][:16,8:16]==128))
        np.testing.assert_array_equal(unchanged[0][16:],source[0][16:])

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
