import importlib.util
from pathlib import Path
import sys
import unittest
import numpy as np
import cadence_codec as c
import model
from test_model import TickClock


class GateTests(unittest.TestCase):
    def test_static_dc_and_noisy_samples_have_fixed_bounded_decision(self):
        zeros=tuple(np.zeros((512,8,8),np.int16) for _ in range(3))
        for a in zeros:a[:,0,0]=3
        d=c.screen(zeros)
        self.assertTrue(d['allow_sr']);self.assertEqual(d['total_sampled_blocks'],192)
        self.assertTrue(all(p['sampled_blocks']==64 for p in d['planes']))
        noisy=tuple(np.ones((512,8,8),np.int16) for _ in range(3))
        self.assertFalse(c.screen(noisy)['allow_sr'])
        mixed=(zeros[0],noisy[1],zeros[2])
        self.assertFalse(c.screen(mixed)['allow_sr'])
        for kwargs in (dict(threshold=float('nan')),dict(threshold=1.1),dict(sample_blocks_per_plane=65)):
            with self.assertRaises(ValueError):c.GateConfig(**kwargs)

    def test_screen_reads_only_declared_current_coefficient_samples(self):
        coeff=tuple(np.zeros((512,8,8),np.int16) for _ in range(3))
        before=tuple(a.copy() for a in coeff)
        first=c.screen(coeff)
        for a,b in zip(coeff,before):np.testing.assert_array_equal(a,b)
        selected=set(first['planes'][0]['sample_indices'])
        other=next(i for i in range(512) if i not in selected)
        changed=list(coeff);changed[0]=coeff[0].copy();changed[0][other,2,2]=100
        after=c.screen(tuple(changed))
        self.assertEqual(first['planes'],after['planes'])
        self.assertEqual(first['allow_sr'],after['allow_sr'])
        self.assertEqual(first['total_sampled_blocks'],after['total_sampled_blocks'])

    def test_exact_rgb_yuv_tags_ui_feedback_and_cap_are_unchanged(self):
        import ui_plugin
        rng=np.random.default_rng(1531)
        pairs=[(c.Encoder(mode=m,patch_builder=ui_plugin.PatchSelector(rectangles=((0,0,16,8),))),c.Receiver()) for m in ('gm','exact','gated')]
        for i in range(9):
            rgb=(np.full((48,64,3),70+i,np.uint8) if i%2==0 else rng.integers(0,256,(48,64,3),dtype=np.uint8))
            output=[];planes=[]
            for enc,rx in pairs:
                d=enc.prepare(rgb,i,promote=i in (2,5),force_key=i==7)
                self.assertEqual(d.info['analyze_calls'],1);self.assertEqual(d.info['forward_calls'],3)
                if enc.mode=='gated':
                    self.assertEqual(len(d.info['inner_attempts']),2 if d.info['gate']['allow_sr'] else 1)
                    self.assertGreater(d.info['gate_ms'],0)
                task=rx.begin(d.packet);planes.append(task.planes);actual,_,ack=rx.complete(task);output.append(actual)
                self.assertTrue(enc.ack(ack))
                np.testing.assert_array_equal(c.corpus.rgb565(actual[:8,:16]),c.corpus.rgb565(rgb[:8,:16]))
            for actual in output[1:]:np.testing.assert_array_equal(output[0],actual)
            for other in planes[1:]:
                for a,b in zip(planes[0],other):np.testing.assert_array_equal(a,b)
            for slot in (0,1):
                tags=[None if enc.banks[slot] is None else (enc.banks[slot].frame_id,enc.banks[slot].tag) for enc,_ in pairs]
                self.assertEqual(tags,[tags[0]]*3)
        e=c.Encoder(mode='gated',frame_cap=128)
        d=e.prepare(np.full((16,32,3),70,np.uint8),0)
        self.assertFalse(d.accepted);self.assertFalse(e.pending);self.assertEqual(e.last_issued,-1)
        self.assertGreater(d.info['gate_ms'],0)

    def test_copied_gm_and_exact_model_paths_match_frozen_parent_fixed_clock(self):
        path=Path(__file__).resolve().parent.parent/'python-game-unified-stream-study/model.py'
        spec=importlib.util.spec_from_file_location('frozen_unified_model_parity',path)
        parent=importlib.util.module_from_spec(spec);sys.modules[spec.name]=parent;spec.loader.exec_module(parent)
        images=[np.full((16,32,3),40+i,np.uint8) for i in range(18)]
        for mode in ('gm','exact'):
            params=dict(width=32,height=16,codec_mode=mode,ui_rectangles=((0,0,16,8),),promotion_period=4)
            a=parent.run(images,config=parent.Config(**params),clock_ns=TickClock())
            b=model.run(images,config=model.Config(**params),clock_ns=TickClock())
            for field in ('presented','drops','feedback','publications','wire'):
                self.assertEqual(a[field],b[field])
            for left,right in zip(a['packets'],b['packets']):
                for field in ('id','packet_sha256','reference_bank','reference_id','reference_tag','key','promoted'):
                    self.assertEqual(left[field],right[field])


if __name__=='__main__':unittest.main()
