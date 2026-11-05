"""Independent streaming ownership, pause/configuration and border semantics."""
import unittest
import numpy as np
import verify as v

def inputs():
    rng=np.random.default_rng(640001)
    planes=(rng.integers(95,114,(480,720),np.uint8),rng.integers(0,256,(240,360),np.uint8),rng.integers(0,256,(240,360),np.uint8))
    for p in planes:p.setflags(write=False)
    patches=[]
    for rect in v.n.RECTS:
        x,y,w,h=rect;words=rng.integers(0,65536,(h,w),np.uint16);words.setflags(write=False);patches.append(dict(rect=rect,words=words))
    return planes,patches,v.guard()

def golden(planes,patches,mask,preset):
    Y,work=v.full.filtered_luma(planes[0],mask,preset)
    rgb=v.n.overlay(v.m.C.corpus.rgb565(v.m.ft.planes_to_rgb((Y,planes[1],planes[2]))),tuple(p['words']for p in patches))
    return Y,rgb,work

class StreamingProofTests(unittest.TestCase):
    def test_all_presets_exact_luma_edges_and_owned_lines(self):
        planes,patches,mask=inputs()
        for preset in v.full.PRESETS:
            expected,work=v.full.filtered_luma(planes[0],mask,preset);reader=v.subject.FilteredRows(planes[0],mask,preset);held=[]
            for y,row in enumerate(reader):
                np.testing.assert_array_equal(row,expected[y]);self.assertFalse(row.flags.writeable)
                for cached in reader.cache.values():self.assertFalse(np.shares_memory(row,cached))
                if y in(6,7,8,471,472,479):held.append((row,row.copy()))
                for previous,copy in held:np.testing.assert_array_equal(previous,copy)
                self.assertLessEqual(len(reader.cache),4);self.assertLessEqual(len(reader.pending),1)
            self.assertEqual(reader.loads,480);self.assertLessEqual(reader.lookahead,2)
            for key in('vertical_changed_edges','horizontal_changed_edges','changed_luma_samples'):self.assertEqual(reader.work()[key],work[key])
    def test_complete_filter_color_HUD_and_pause_audit(self):
        planes,patches,mask=inputs();Y,rgb,work=golden(planes,patches,mask,v.STRONG)
        yh,rh,actual,pauses=v.verify_frame(planes,patches,mask,v.STRONG,Y,rgb,work)
        self.assertEqual(yh,v.digest(Y.tobytes()));self.assertEqual(rh,v.digest(rgb.astype('<u2').tobytes()));self.assertEqual(pauses,len(v.PAUSE_ROWS))
        self.assertEqual(actual['luma']['Y_rows_loaded'],480);self.assertEqual(actual['luma']['peak_cached_vertical_rows'],4)
    def test_pull_stalls_have_no_prefetch_and_pending_pair_is_bounded(self):
        planes,patches,mask=inputs();scan=v.subject.Scanout(planes,patches,v.n.RECTS,mask,v.STRONG)
        self.assertEqual(scan.luma.loads,0);self.assertEqual(scan.cb.loads,0);v.paused(scan)
        for _ in range(8):next(scan)
        self.assertEqual(scan.y,8);self.assertEqual(scan.luma.loads,10);self.assertEqual(tuple(scan.luma.pending),(8,));v.paused(scan)
        next(scan);self.assertEqual(scan.luma.loads,10);self.assertEqual(len(scan.luma.pending),0);v.paused(scan)
    def test_profile_and_HUD_metadata_are_owned_during_pause(self):
        planes,patches,mask=inputs();preset=dict(v.STRONG);saved=[dict(p)for p in patches];Y,rgb,work=golden(planes,saved,mask,v.STRONG)
        scan=v.subject.Scanout(planes,patches,v.n.RECTS,mask,preset);firstY,firstRGB=next(scan)
        preset['strength']=0;patches[0]['words']=np.zeros_like(patches[0]['words']);patches[0]['rect']=(0,0,1,1)
        with self.assertRaises(TypeError):scan.luma.preset['strength']=1
        with self.assertRaises(TypeError):scan.patches[0]['rect']=(0,0,1,1)
        np.testing.assert_array_equal(firstY,Y[0]);np.testing.assert_array_equal(firstRGB,rgb[0]);v.paused(scan)
        for y,(actualY,actualRGB)in enumerate(scan,start=1):np.testing.assert_array_equal(actualY,Y[y]);np.testing.assert_array_equal(actualRGB,rgb[y])
    def test_writable_or_invalid_static_inputs_are_rejected(self):
        planes,patches,mask=inputs()
        with self.assertRaises(ValueError):v.subject.FilteredRows(planes[0],mask.copy(),v.STRONG)
        with self.assertRaises(ValueError):v.subject.FilteredRows(planes[0].copy(),mask,v.STRONG)
        with self.assertRaises(ValueError):v.subject.FilteredRows(planes[0],mask,dict(v.STRONG,strength=4))
        changed=list(patches);changed[0]=dict(changed[0],words=changed[0]['words'].copy())
        with self.assertRaises(ValueError):v.subject.Scanout(planes,changed,v.n.RECTS,mask,v.STRONG)

if __name__=='__main__':unittest.main()
