"""Supplemental post-timing AF02 overload regression; no timed sources edited."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import model

spec=importlib.util.spec_from_file_location('unified_overload_verifier',Path(__file__).with_name('verify.py'))
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)


class Clock:
    def __init__(self):self.value=0
    def __call__(self):
        value=self.value;self.value+=1000000;return value


class OverloadFeedbackTests(unittest.TestCase):
    def test_actual_two_ingress_busy_is_paid_and_af02_nack_drains(self):
        clock=Clock();original=model.rc.Receiver.begin
        def delayed_begin(rx,packet):
            result=original(rx,packet);clock.value+=90000000;return result
        images=[np.full((16,32,3),40+i,np.uint8) for i in range(36)]
        cfg=model.Config(width=32,height=16,ui_rectangles=((0,0,16,8),),
                         codec_mode='exact',promotion_period=0)
        with patch.object(model.rc.Receiver,'begin',delayed_begin):
            result=model.run(images,config=cfg,clock_ns=clock)
        verify.check_case({'result':result},primary=False)
        busy=[p for p in result['packets'] if 'GF02 busy' in p.get('feed_errors',[])]
        self.assertTrue(busy)
        for p in busy:
            self.assertTrue(any(w['stage']=='feed_batch' and w['id']==p['id'] and w['service_ms']>0 for w in result['work']))
            self.assertTrue(any(f['kind']=='parsed' and f['id']==p['id'] and f['status']==model.rc.NACK for f in result['feedback']))
            self.assertEqual(p['release_reason'],'receiver_nack')
        self.assertEqual(result['peak_ingress'],2)
        self.assertFalse(result['unresolved_encoder_pending'])
        self.assertFalse(result['unresolved_ingress'])
        self.assertEqual(result['unresolved_receiver_readers'],0)


if __name__=='__main__':unittest.main()
