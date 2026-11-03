import dataclasses
import unittest

import numpy as np

from model import Config,run,AnchorEncoder,AnchorReceiver


class Clock:
    def __init__(self):self.value=0
    def __call__(self):return self.value
    def advance(self,ms):self.value+=int(ms*1e6)


class MeasuredTests(unittest.TestCase):
    def frames(self,n=12):return [np.full((16,32,3),70+i,np.uint8) for i in range(n)]

    def factories(self,clock,encode=7,decode=11,oracle=900):
        class Encoder(AnchorEncoder):
            def prepare(self,*args,**kwargs):
                packet=super().prepare(*args,**kwargs);clock.advance(encode);return packet
            def expected_hash(self,*args,**kwargs):
                value=super().expected_hash(*args,**kwargs);clock.advance(oracle);return value
        class Receiver(AnchorReceiver):
            def receive(self,*args,**kwargs):
                result=super().receive(*args,**kwargs);clock.advance(decode);return result
        return dict(encoder_factory=Encoder,receiver_factory=Receiver,clock_ns=clock)

    def test_exact_per_call_service_and_oracle_exclusion(self):
        clock=Clock()
        r=run(self.frames(),{},Config(decoder_service='python_wall'),**self.factories(clock))
        self.assertEqual(r['presented_eventual'],12)
        self.assertTrue(all(p['encode_service_ms']==p['encode_wall_ms']==7 for p in r['packets']))
        self.assertTrue(all(p['decode_service_ms']==p['decode_wall_ms']==11 for p in r['packets']))
        self.assertGreater(clock.value/1e6,12*900)
        self.assertLess(r['presented'][-1]['at_ms'],500)
        for packet in r['packets']:
            commit=next(c for c in r['commits'] if c['id']==packet['id'])
            self.assertAlmostEqual(commit['at_ms']-packet['decode_started_ms'],11)

    def test_assumed_receiver_service_records_unselected_measurement(self):
        clock=Clock()
        r=run(self.frames(),{},Config(decoder_service='assumed',decode_ms=3),**self.factories(clock,decode=50))
        self.assertTrue(all(p['decode_wall_ms']==50 and p['decode_service_ms']==3 for p in r['packets']))
        self.assertEqual(r['presented_eventual'],12)

    def test_slow_encoding_skips_real_captures_and_drains(self):
        clock=Clock()
        r=run(self.frames(60),{},Config(),**self.factories(clock,encode=80))
        self.assertLess(r['prepared'],60)
        self.assertLess(r['metrics']['steady_fps'],30)
        self.assertLess(r['presented_strict'],60)
        self.assertEqual(r['prepared']+r['drops_by_reason']['latest_replaced'],60)
        self.assertLessEqual(r['peak_compressed_slots'],2)
        self.assertLessEqual(r['peak_framebuffers'],3)
        self.assertTrue(all(x is None for x in r['unresolved_slots']))
        self.assertFalse(r['unresolved_pending'])
        self.assertFalse(r['pending_ids'])

    def test_loss_timeout_and_corruption_still_recover(self):
        clock=Clock()
        r=run(self.frames(24),{},Config(data_loss_ids=(4,),ack_loss_ids=(7,),corruption_ids=(10,),refresh_period=0,ack_timeout_ms=90),**self.factories(clock))
        self.assertEqual(r['presented'][-1]['id'],23)
        self.assertEqual(r['drops_by_reason']['data_loss'],1)
        self.assertEqual(r['drops_by_reason']['receiver_rejected'],1)
        self.assertTrue(all(x is None for x in r['unresolved_slots']))

    def test_cap_rejection_pays_measured_encode_service(self):
        clock=Clock()
        r=run(self.frames(),{},Config(frame_cap=1,cap_backoff_max=32),**self.factories(clock))
        self.assertEqual(r['transmitted'],0)
        self.assertTrue(all(p['encode_service_ms']==7 for p in r['packets']))
        self.assertEqual([p['quant_scale'] for p in r['packets'][:4]],[8,16,32,32])
        self.assertTrue(all(x is None for x in r['unresolved_slots']))

    def test_config_is_immutable_and_modes_validated(self):
        cfg=Config()
        with self.assertRaises(dataclasses.FrozenInstanceError):cfg.decode_ms=10
        for cfg in (Config(decoder_service='native'),Config(encoder_profile='x'),Config(motion_mode='x'),Config(decode_ms=-1)):
            with self.assertRaises(ValueError):run(self.frames(),{},cfg)


if __name__=='__main__':unittest.main()
