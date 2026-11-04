import unittest
from unittest.mock import patch
import numpy as np
import model
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location("refresh_v16_verify",Path(__file__).with_name("verify.py"))
verify=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(verify)

class TickClock:
    def __init__(self):self.value=0
    def __call__(self):
        v=self.value;self.value+=1000000;return v

class RefreshTests(unittest.TestCase):
    def run_case(self,**kw):
        cfg=model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),refresh_period=8,**kw)
        out=model.run([np.full((16,32,3),40+i,np.uint8) for i in range(64)],config=cfg,clock_ns=TickClock())
        verify.check_case({'result':out},primary=False)
        return out
    def test_key_background_policy_does_not_change_p_maps_or_initial_key(self):
        observed=[];old=model.rc.Encoder.prepare
        def capture(enc,rgb,i,**kw):
            observed.append((i,kw['force_key'],set(np.unique(kw['scale_map']))))
            return old(enc,rgb,i,**kw)
        with patch.object(model.rc.Encoder,'prepare',capture):
            out=self.run_case(refresh_key_background_scale=32)
        packets={p['id']:p for p in out['packets']}
        for i,key,scales in observed:
            self.assertEqual(scales,{32} if packets[i]['refresh_key'] else {16})
        self.assertTrue(any(p['refresh_key'] for p in packets.values()))
        self.assertEqual(packets[0]['background_scale'],16)
    def test_lost_refresh_chunk_retries_independent_key(self):
        out=self.run_case(drop_first_refresh_chunk=True)
        lost=next(p for p in out['packets'] if p.get('fault_refresh_chunk_dropped'))
        later=[p for p in out['packets'] if p['id']>lost['id']]
        self.assertTrue(later[0]['key'])
        self.assertTrue(any(f['kind']=='ack_applied' and f['id']>lost['id'] for f in out['feedback']))
        self.assertFalse(out['unresolved_encoder_pending']);self.assertFalse(out['unresolved_ingress'])
    def test_lost_refresh_ack_never_exposes_unconfirmed_bank(self):
        out=self.run_case(drop_first_refresh_ack=True)
        lost=next(p for p in out['packets'] if p.get('fault_refresh_ack_lost'))
        self.assertFalse(any(f['kind']=='ack_applied' and f['id']==lost['id'] for f in out['feedback']))
        expired=next(f for f in out['feedback'] if f['kind']=='expired' and f['id']==lost['id'])
        self.assertTrue(all(v is None for v in expired['sender_banks'].values()))
        self.assertTrue(next(p for p in out['packets'] if p['id']>lost['id'])['key'])
    def test_invalid_policy_and_flags_rejected(self):
        for change in (dict(refresh_key_background_scale=8),dict(refresh_key_background_scale=True),dict(drop_first_refresh_ack=1),dict(drop_first_refresh_chunk=1)):
            with self.assertRaises(ValueError):self.run_case(**change)
    def test_full_canvas_refresh_priority_map_preserves_scale8(self):
        observed=[];old=model.rc.Encoder.prepare
        def capture(enc,rgb,i,**kw):
            observed.append((i,kw['force_key'],kw['scale_map'].copy()))
            return old(enc,rgb,i,**kw)
        cfg=model.Config(codec_mode='gm',refresh_period=4,refresh_key_background_scale=32)
        with patch.object(model.rc.Encoder,'prepare',capture):
            out=model.run([np.full((480,720,3),40+i,np.uint8) for i in range(12)],config=cfg,clock_ns=TickClock())
        expected=model.rc.gm.roi.declared_map(720,480,((16,48,192,80),(160,352,400,80)),8,32)
        packets={p['id']:p for p in out['packets']}
        refreshed=[a for i,key,a in observed if packets[i]['refresh_key']]
        self.assertTrue(refreshed)
        for a in refreshed:np.testing.assert_array_equal(a,expected)
        self.assertTrue(all(c['selected_exact_pixels']==21120 and c['selected_ui_mismatches']==0 for c in out['commits']))

if __name__=='__main__':unittest.main()
