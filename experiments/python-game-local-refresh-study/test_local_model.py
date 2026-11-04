import importlib.util
from pathlib import Path
import unittest
import numpy as np
import model
s=importlib.util.spec_from_file_location('local_refresh_check',Path(__file__).with_name('verify.py'));verify=importlib.util.module_from_spec(s);s.loader.exec_module(verify)
class Clock:
    def __init__(self):self.value=0
    def __call__(self):v=self.value;self.value+=1000000;return v
class ModelTests(unittest.TestCase):
    def run_case(self,**kw):
        cfg=model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),refresh_period=8,promotion_period=4,**kw)
        images=[np.full((16,32,3),40+i,np.uint8) for i in range(64)]
        out=model.run(images,config=cfg,clock_ns=Clock());verify.check_case({'result':out},primary=False)
        return out
    def test_local_refresh_continues_bank1_while_key_writer_pending(self):
        out=self.run_case(feedback_latency_ms=60);keys=[p for p in out['packets'] if p['refresh_key'] and p['admitted']]
        self.assertTrue(keys)
        overlapping=[]
        for p in keys:
            self.assertTrue(p['source_banks']['1'])
            later=[q for q in out['packets'] if q['id']>p['id'] and q['encode_started_ms']<p['released_ms']]
            overlapping.extend(later)
            self.assertTrue(all(not q['key'] and q['reference_bank']==1 and q['refresh_deferred'] for q in later))
        self.assertTrue(overlapping)
    def test_lost_refresh_publication_keeps_bank1_and_retries_key0(self):
        out=self.run_case(drop_first_refresh_ack=True)
        lost=next(p for p in out['packets'] if p.get('fault_refresh_ack_lost'))
        expired=next(f for f in out['feedback'] if f['kind']=='expired' and f['id']==lost['id'])
        self.assertIsNone(expired['sender_banks']['0']);self.assertIsNotNone(expired['sender_banks']['1'])
        self.assertTrue(any(p['key'] and p['id']>lost['id'] for p in out['packets']))
        self.assertFalse(any(f['kind']=='ack_applied' and f['id']==lost['id'] for f in out['feedback']))
    def test_partial_refresh_chunk_loss_safe_continuity_and_global_control(self):
        local=self.run_case(drop_first_refresh_chunk=True)
        self.assertTrue(any(p.get('fault_refresh_chunk_dropped') for p in local['packets']))
        global_=self.run_case(refresh_policy='global')
        self.assertTrue(any(p['refresh_key'] for p in global_['packets']))
        self.assertFalse(any(p['refresh_deferred'] for p in global_['packets']))
    def test_invalid_policy_rejected(self):
        with self.assertRaises(ValueError):self.run_case(refresh_policy='unbounded')
if __name__=='__main__':unittest.main()
