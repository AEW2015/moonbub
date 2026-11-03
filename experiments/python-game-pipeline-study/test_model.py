from dataclasses import FrozenInstanceError
import unittest
import numpy as np
import model


class Clock:
    def __init__(self):self.value=0
    def __call__(self):return self.value
    def advance(self,ms):self.value+=int(ms*1e6)


def factories(clock,encode=7,decode=11,oracle=900):
    class Encoder(model.gc.Encoder):
        def expected_hash(self,*args,**kwargs):
            value=super().expected_hash(*args,**kwargs);clock.advance(oracle);return value
    class Controller(model.normal_controller.Controller):
        def __init__(self,config):super().__init__(Encoder(),config)
        def prepare(self,*args,**kwargs):
            decision=super().prepare(*args,**kwargs);clock.advance(encode);return decision
    class Receiver(model.gc.Receiver):
        def receive(self,*args,**kwargs):
            result=super().receive(*args,**kwargs);clock.advance(decode);return result
    return dict(controller_factory=Controller,receiver_factory=Receiver,clock_ns=clock)


class PipelineTests(unittest.TestCase):
    def frames(self,n=12):return [np.full((16,32,3),60+i,np.uint8) for i in range(n)]
    def config(self,**kwargs):return model.Config(rectangles=((0,0,16,16),),**kwargs)
    def drained(self,row):
        self.assertTrue(all(x is None for x in row['unresolved_sender_slots']))
        self.assertFalse(row['unresolved_ingress_frames']);self.assertFalse(row['unresolved_credits'])
        self.assertFalse(row['pending_ids']);self.assertIsNone(row['waiting_at_end'])
        self.assertLessEqual(row['peak_sender_slots'],2);self.assertLessEqual(row['peak_ingress_slots'],2)
        self.assertLessEqual(row['peak_credits'],2);self.assertLessEqual(row['peak_framebuffer_roles'],3)

    def test_actual_packets_exact_services_feedback_and_oracle_exclusion(self):
        clock=Clock();r=model.run(self.frames(),{},self.config(decoder_service='python_wall'),**factories(clock))
        self.assertEqual(r['presented_eventual'],12);self.drained(r)
        self.assertTrue(all(p['encode_service_ms']==7 and p['decode_service_ms']==11 for p in r['packets']))
        self.assertGreater(clock.value/1e6,12*900)
        self.assertLess(r['presented'][-1]['at_ms'],500)
        self.assertEqual(r['forward_header_bytes'],31);self.assertEqual(r['feedback_protocol_bytes'],24)
        self.assertEqual(r['feedback_ipv4_udp_bytes'],12*(24+28))
        for p in r['packets']:
            ack=next(a for a in r['feedback'] if a['kind']=='received' and a['id']==p['id'] and a['accepted'])
            self.assertGreaterEqual(ack['at_ms'],p['decode_done_ms']+10)
            self.assertAlmostEqual(p['decode_done_ms']-p['decode_started_ms'],11)

    def test_postprepare_deadline_pays_work_and_refund_waits_encode_completion(self):
        clock=Clock();r=model.run(self.frames(),{},self.config(frame_deadline_ms=5),**factories(clock))
        self.assertEqual(r['presented_eventual'],0);self.assertEqual(r['forward_ipv4_udp_bytes'],0)
        self.assertEqual(r['drops_by_reason']['deadline_after_encode'],12);self.drained(r)
        for p in r['packets']:
            self.assertEqual(p['encode_service_ms'],7)
            self.assertAlmostEqual(p['released_ms']-p['encode_started_ms'],7)

    def test_timeout_during_decode_waits_physical_reader_drain(self):
        clock=Clock();r=model.run(self.frames(18),{},self.config(decoder_service='python_wall',ack_timeout_ms=20,frame_deadline_ms=300),
                                **factories(clock,decode=65))
        self.assertTrue(any(not x['physical_drained'] for x in r['timeout_events']))
        for p in r['packets']:
            if p.get('expire_requested')=='ack_timeout' and 'decode_done_ms' in p:
                self.assertGreaterEqual(p['released_ms'],p['decode_done_ms'])
        self.drained(r)

    def test_loss_corruption_ack_loss_duplicates_wrongepoch_recover(self):
        clock=Clock();r=model.run(self.frames(36),{},self.config(data_loss_ids=(4,),corruption_ids=(10,),feedback_loss_ids=(7,),
                            duplicate_chunk_ids=(13,),duplicate_feedback_ids=(16,),wrong_epoch_feedback_ids=(19,),refresh_period=10),
                            **factories(clock))
        self.drained(r);self.assertEqual(r['presented'][-1]['id'],35)
        self.assertTrue(any(x['kind']=='lost' for x in r['feedback']))
        self.assertTrue(any(x.get('epoch')==2 and not x['accepted'] for x in r['feedback'] if x['kind']=='received'))
        self.assertTrue(r['timeout_events'])

    def test_paid_cap_rejection_and_overload_conservation(self):
        clock=Clock();r=model.run(self.frames(60),{},self.config(frame_cap=1),**factories(clock,encode=80))
        self.assertEqual(r['forward_ipv4_udp_bytes'],0);self.assertEqual(r['presented_eventual'],0)
        self.assertTrue(all(p['encode_service_ms']==80 and not p['admitted'] for p in r['packets']))
        self.assertGreater(r['drops_by_reason']['latest_replaced'],0);self.drained(r)
        self.assertEqual(r['prepared']+r['drops_by_reason']['latest_replaced'],60)

    def test_reorder_multichunk_and_assumed_receiver_service(self):
        rng=np.random.default_rng(908)
        frames=[rng.integers(0,256,(32,48,3),dtype=np.uint8) for _ in range(6)]
        clock=Clock();r=model.run(frames,{},self.config(reverse_chunks=True,decoder_service='assumed',decode_ms=3),**factories(clock,decode=50))
        self.assertTrue(any(p['datagram_count']>1 for p in r['packets']))
        self.assertTrue(all(p['decode_service_ms']==3 and p['decode_wall_ms']==50 for p in r['packets']))
        self.assertEqual(r['presented_eventual'],6);self.drained(r)

    def test_acquisition_delay_and_config_validation(self):
        cfg=self.config()
        with self.assertRaises(FrozenInstanceError):cfg.fps=50
        for bad in (self.config(controller='oracle'),self.config(frame_cap=50000),self.config(decoder_service='fpga'),self.config(acquisition_ms=-1)):
            with self.assertRaises(ValueError):model.run(self.frames(),{},bad)
        clock=Clock();r=model.run(self.frames(),{},self.config(acquisition_ms=12),**factories(clock))
        self.assertGreaterEqual(r['presented'][0]['age_ms'],12);self.drained(r)


if __name__=='__main__':unittest.main()
