import struct
import unittest
from unittest.mock import patch

import numpy as np
import ui_plugin as ui


class TickClock:
    def __init__(self, increment=1000000): self.value = 0; self.increment = increment
    def __call__(self):
        old = self.value; self.value += self.increment; return old


class UnifiedUITests(unittest.TestCase):
    def setUp(self):
        self.rgb = np.full((48,64,3), [40,60,80], np.uint8)
        self.rects = ((4,4,16,16),(32,4,16,16))

    def test_selection_framing_roundtrip_and_exact_original_words(self):
        selector = ui.PatchSelector(rectangles=self.rects)
        d = selector.select(self.rgb, 49152)
        self.assertEqual(len(d.patches), 2)
        self.assertEqual(d.used_bytes, sum(4+len(p) for p in d.patches))
        validated = ui.parse_patches(ui.pack_patches(d.patches), len(d.patches),64,48)
        base = np.full_like(self.rgb, 150); before = base.copy()
        actual = ui.apply_patches(base, validated)
        np.testing.assert_array_equal(base,before)
        sourcewords = ui.hp.corpus.rgb565(self.rgb)
        words = ui.hp.corpus.rgb565(actual)
        outside = np.ones((48,64),bool)
        for x,y,w,h in self.rects:
            np.testing.assert_array_equal(words[y:y+h,x:x+w],sourcewords[y:y+h,x:x+w])
            outside[y:y+h,x:x+w] = False
        np.testing.assert_array_equal(words[outside],ui.hp.corpus.rgb565(base)[outside])
        self.assertTrue(all(not p['words'].flags.writeable for p in validated))
        none=ui.apply_patches(base,())
        np.testing.assert_array_equal(none,base)
        self.assertFalse(np.shares_memory(none,base))

    def test_current_word_cache_hits_even_when_rgb888_or_background_changes(self):
        selector=ui.PatchSelector(rectangles=self.rects)
        first=selector.select(self.rgb,49152)
        changed=self.rgb.copy();changed[30:40] = 255
        changed[4:20,4:20]+=np.array([1,1,1],np.uint8)
        with patch.object(ui.hybrid,'_encode_patch',side_effect=AssertionError('cache hit encoded again')):
            second=selector.select(changed,49152)
        self.assertEqual(first.patches,second.patches)
        self.assertTrue(all(r['candidate_details']['cache_hit'] for r in second.details['attempts']))
        self.assertTrue(all(r['candidate_details']['current_candidate_count']==0 for r in second.details['attempts']))
        self.assertTrue(all(r['validate_ms']>=0 for r in second.details['attempts']))
        self.rgb[4,4]=255
        third=selector.select(self.rgb,49152)
        self.assertFalse(third.details['attempts'][0]['candidate_details']['cache_hit'])

    def test_byte_budget_counts_prefix_and_retains_paid_losing_work(self):
        yy,xx=np.indices((48,64))
        image=np.stack((xx*3%256,yy*5%256,(xx*7+yy*11)%256),axis=-1).astype(np.uint8)
        image[4:20,32:48]=[40,60,80]
        selector=ui.PatchSelector(rectangles=self.rects)
        full=selector.select(image,49152)
        small_required=4+len(full.patches[1])
        d=selector.select(image,small_required)
        self.assertEqual(d.patches,(full.patches[1],))
        self.assertFalse(d.details['attempts'][0]['fits'])
        self.assertTrue(d.details['attempts'][1]['fits'])
        self.assertGreater(d.details['attempts'][0]['encode_ms'],0)
        self.assertEqual(d.used_bytes,small_required)
        too_small=selector.select(image,small_required-1)
        self.assertEqual(too_small.patches,())
        self.assertLessEqual(too_small.used_bytes,small_required-1)
        self.assertFalse(selector.select(image,0).details['attempts'])

    def test_all_geometry_crc_and_overlap_preflight_before_pixel_decode(self):
        good=ui.hp.encode_patch(self.rgb,self.rects[0])
        overlap=ui.hp.encode_patch(self.rgb,(8,8,16,16))
        invalid_crc=good[:-1]+bytes([good[-1]^1])
        header=list(ui.row.HEADER.unpack_from(good));header[3]=60
        bad_geometry=ui.hp._crc(ui.row.HEADER.pack(*header)+good[ui.row.HEADER.size:-4])
        for packets in ((good,overlap),(good,invalid_crc),(good,bad_geometry)):
            with patch.object(ui.row,'decode_any',side_effect=AssertionError('decoded before all preflights')):
                with self.assertRaises(ValueError):ui.validate_patches(packets,64,48)

    def test_payload_failure_cannot_publish_or_apply_partial_output(self):
        good=ui.hp.encode_patch(self.rgb,self.rects[0])
        raw=ui.hp.encode_patch(self.rgb,self.rects[1])
        header=list(ui.row.HEADER.unpack_from(raw))
        # A palette index references a nonexistent color; CRC/header/geometry
        # remain valid so full payload validation must reject it.
        payload=bytearray(raw[ui.row.HEADER.size:-4]);payload[-1]=255
        invalid=ui.hp._crc(ui.row.HEADER.pack(*header)+payload)
        original=np.full_like(self.rgb,170);before=original.copy()
        with self.assertRaises(ValueError):
            validated=ui.validate_patches((good,invalid),64,48)
            ui.apply_patches(original,validated)
        np.testing.assert_array_equal(original,before)

    def test_count_length_padding_and_type_canonicality(self):
        p=ui.hp.encode_patch(self.rgb,self.rects[0]);section=ui.pack_patches((p,))
        for data,count in ((section,0),(section+b'\0',1),(section[:-1],1),(b'',1),(section,True),(section,5)):
            with self.assertRaises(ValueError):ui.parse_patches(data,count,64,48)
        for packets in ((p,)*5,(bytearray(p),),b'bad'):
            with self.assertRaises(ValueError):ui.validate_patches(packets,64,48)
        with self.assertRaises(ValueError):ui.apply_patches(self.rgb,({'rect':self.rects[0],'words':np.zeros((1,1),np.uint16)},))

    def test_attempt_and_work_budget_never_refund_completed_work(self):
        selector=ui.PatchSelector(rectangles=self.rects)
        d=selector.select(self.rgb,49152,max_attempts=1)
        self.assertEqual(len(d.patches),1)
        late=selector.select(self.rgb,49152,work_budget_ms=3,clock_ns=TickClock())
        self.assertTrue(late.deadline_hit)
        self.assertEqual(late.patches,())
        self.assertEqual(late.used_bytes,0)
        self.assertTrue(late.details['attempts'])
        self.assertFalse(any(a['selected_in_output'] for a in late.details['attempts']))
        self.assertGreaterEqual(late.service_ms,3)
        immediate=selector.select(self.rgb,49152,work_budget_ms=0)
        self.assertTrue(immediate.deadline_hit)
        self.assertFalse(immediate.details['attempts'])
        with self.assertRaises(ValueError):selector.select(self.rgb,49152,clock_ns=lambda:float('nan'))

    def test_four_entry_bound_and_invalid_priority_configuration(self):
        selector=ui.PatchSelector(rectangles=self.rects)
        for x in (0,8,16,24,32):selector.cache(self.rgb,(x,0,8,8),'adaptive_row')
        self.assertEqual(len(selector.cache._entries),4)
        self.assertEqual(selector.cache.evictions,1)
        for kwargs in (dict(max_entries=5),dict(rectangles=(self.rects[0],)*5),dict(patch_policy='wrong')):
            with self.assertRaises(ValueError):ui.PatchSelector(**kwargs)
        for kwargs in (dict(byte_budget=-1),dict(byte_budget=True),dict(byte_budget=3,max_attempts=5),dict(byte_budget=3,work_budget_ms=-1)):
            with self.assertRaises(ValueError):selector.select(self.rgb,**kwargs)


if __name__=='__main__':unittest.main()
