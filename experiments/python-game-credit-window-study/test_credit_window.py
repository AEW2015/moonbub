import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
import adapter
import model

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'python-game-refresh-study'))
from replay import ServiceTape


class TickClock:
    def __init__(self):self.value = 0
    def __call__(self):
        previous = self.value; self.value += 1000000
        return previous


def tape(**changes):
    costs = {'resize': 1.0}
    for kind in ('key', 'p'):
        for stage, value in dict(encode=1., decode=5., packetize=.2, feed=.1,
                                 feedback_build=.2, feedback_parse=.2, encode_rejected=120.).items():
            costs[stage+'_'+kind] = value
    costs.update(changes)
    return ServiceTape(tuple(sorted(costs.items())), 'declared_unit_test_costs')


def timeline(result):
    return dict(presented=result['presented'], feedback=result['feedback'], allocations=result['allocations'],
                drops=result['drops'], packets=[{k:p.get(k) for k in ('id','packet_sha256','key',
                    'reference_id','encode_started_ms','encode_service_ms','decode_started_ms',
                    'decode_done_ms','released_ms','release_reason')} for p in result['packets']])


class CreditTests(unittest.TestCase):
    def run_case(self, credits=3, count=40, service=None, ui_cache_enabled=True, ops=None, **changes):
        frames = [np.full((16,32,3), 40+i//4, np.uint8) for i in range(count)]
        values = dict(width=32, height=16, rectangles=((0,0,16,16),), fps=30,
                      decoder_service='python_wall', refresh_period=0,
                      sender_slots=credits, credit_window=credits)
        values.update(changes)
        config = model.Config(**values)
        result = model.run(frames, {}, config,
                           controller_factory=adapter.make_controller(credit_window=credits,
                                                                      rectangles=((0,0,16,8),),
                                                                      ui_cache_enabled=ui_cache_enabled),
                           receiver_factory=lambda:adapter.DecoderState(fast=True),
                           clock_ns=TickClock(), service_tape=service or tape(),transport_ops=ops)
        self.assertFalse(result['pending_ids']);self.assertFalse(result['unresolved_credits'])
        self.assertTrue(all(x is None for x in result['unresolved_sender_slots']))
        self.assertFalse(result['unresolved_ingress_frames'])
        self.assertTrue(all(x==0 for x in result['unresolved_cpu'].values()))
        self.assertEqual(result['encoder_credit_window'],credits)
        self.assertLessEqual(result['peak_sender_slots'],credits)
        self.assertLessEqual(result['peak_credits'],credits)
        self.assertLessEqual(result['peak_ingress_slots'],2)
        self.assertLessEqual(result['peak_framebuffer_roles'],3)
        for p in result['packets']:
            if 'decode_done_ms' in p:self.assertGreaterEqual(p['released_ms'],p['decode_done_ms'])
        self.assertTrue(all(c['selected_rgb565_mismatches']==0 for c in result['commits']))
        return result, frames, config

    def test_two_credit_trace_matches_frozen_execution_copy(self):
        actual, frames, config = self.run_case(credits=2)
        spec = importlib.util.spec_from_file_location('frozen_execution_for_credit_test', HERE.parent/'python-game-execution-study/model.py')
        frozen = importlib.util.module_from_spec(spec);sys.modules[spec.name]=frozen;spec.loader.exec_module(frozen)
        expected = frozen.run(frames,{},config,
            controller_factory=adapter.make_controller(credit_window=2,rectangles=((0,0,16,8),)),
            receiver_factory=lambda:adapter.DecoderState(fast=True),
            clock_ns=TickClock(),service_tape=tape())
        self.assertEqual(timeline(actual),timeline(expected))

    def test_invalid_pool_bounds_and_factory_disagreement_fail_before_packets(self):
        frames = [np.zeros((16,32,3),np.uint8)]
        for changes in (dict(sender_slots=4,credit_window=4),dict(sender_slots=3,credit_window=2),
                        dict(sender_slots=True),dict(credit_window=0),dict(controller='gate')):
            with self.assertRaises(ValueError):model.run(frames,{},model.Config(**changes))
        with self.assertRaises(ValueError):
            model.run(frames,{},model.Config(sender_slots=3,credit_window=3),
                      controller_factory=adapter.make_controller(credit_window=2))
        with self.assertRaises(ValueError):adapter.make_controller(credit_window=4)

    def test_ui_cache_keeps_complete_packets_and_fixed_clock_schedule(self):
        cached,_,_=self.run_case(credits=2)
        baseline,_,_=self.run_case(credits=2,ui_cache_enabled=False)
        self.assertEqual(timeline(cached),timeline(baseline))
        attempts=[a for p in cached['packets'] for a in p.get('hybrid',{}).get('attempts',[])]
        self.assertTrue(any(a.get('candidate_details',{}).get('cache_hit') for a in attempts))

    def test_third_sender_hits_finite_two_ingress_and_recovery_is_paid(self):
        row,_,_ = self.run_case(count=80,fps=120,service=tape(decode_p=55.))
        self.assertEqual(row['peak_sender_slots'],3)
        self.assertEqual(row['peak_credits'],3)
        self.assertEqual(row['peak_ingress_slots'],2)
        failures = [p for p in row['packets'] if p.get('ingress_error')=='GF02 busy']
        self.assertTrue(failures)
        for p in failures:
            calls=[c for c in row['cpu_services'] if c['id']==p['id'] and c['stage']=='feed']
            self.assertTrue(calls);self.assertTrue(all(c['service_ms']>0 for c in calls))
        self.assertGreater(row['presented_eventual'],0)

    def test_loss_corruption_duplicate_and_wrong_feedback_drain(self):
        for faults in (dict(data_loss_ids=(0,)),dict(feedback_loss_ids=(0,)),
                       dict(corruption_ids=(14,),duplicate_chunk_ids=(22,),duplicate_feedback_ids=(28,),
                            wrong_epoch_feedback_ids=(32,),reverse_chunks=True)):
            row,_,_=self.run_case(count=60,**faults)
            self.assertGreater(row['presented_eventual'],0)
            self.assertTrue(all(c['service_ms']>0 for c in row['cpu_services']))

    def test_late_ack_during_parse_keeps_reader_and_cannot_install_reference(self):
        row,_,_=self.run_case(count=1,ack_timeout_ms=35,service=tape(feedback_parse_key=90.))
        parse=next(c for c in row['cpu_services'] if c['stage']=='feedback_parse')
        self.assertTrue(row['timeout_events'])
        self.assertFalse(row['timeout_events'][0]['physical_drained'])
        self.assertGreaterEqual(row['packets'][0]['released_ms'],parse['done_ms'])
        received=next(f for f in row['feedback'] if f['kind']=='received')
        self.assertFalse(received['accepted']);self.assertIsNone(received['sender_anchor_after'])

    def test_expiry_wins_after_deferred_valid_ack_while_duplicate_reader_drains(self):
        class ConflictingReceiverFeedback:
            # Fault injection emits real serialized GA01 ACK then NACK for the
            # same successfully decoded outer body. A duplicate feed reader
            # remains active so ACK promotion and NACK expiry both defer.
            def __init__(self):self.calls=0
            datagrams=staticmethod(model.transport.datagrams)
            parse_feedback=staticmethod(model.transport.parse_feedback)
            def feedback_datagram(self,*args,**kwargs):
                self.calls+=1
                if self.calls==2:kwargs['status']=model.transport.NACK;kwargs['reason']=4
                return model.transport.feedback_datagram(*args,**kwargs)
        calls=[];original=model.gc.Encoder.ack
        def record_ack(enc,*args,**kwargs):
            result=original(enc,*args,**kwargs);calls.append((enc.anchor_id,result));return result
        with patch.object(model.gc.Encoder,'ack',record_ack):
            row,_,_=self.run_case(count=1,ops=ConflictingReceiverFeedback(),
                duplicate_chunk_ids=(0,),duplicate_feedback_ids=(0,),feedback_latency_ms=0,
                service=tape(feed_key=100.),ack_timeout_ms=500)
        received=[f for f in row['feedback'] if f['kind']=='received']
        self.assertEqual([f['status'] for f in received],[model.transport.ACK,model.transport.NACK])
        self.assertTrue(all(f['accepted'] for f in received))
        self.assertFalse(any(f['kind']=='deferred_ack_accepted' for f in row['feedback']))
        self.assertEqual(calls,[])
        self.assertEqual(row['packets'][0]['release_reason'],'receiver_nack')
        feeds=[c for c in row['cpu_services'] if c['stage']=='feed']
        self.assertEqual(len(feeds),2)
        self.assertGreaterEqual(row['packets'][0]['released_ms'],max(c['done_ms'] for c in feeds))

        # Positive control: identical duplicate-reader ownership with no NACK
        # still promotes the valid deferred ACK once the final reader drains.
        control,_,_=self.run_case(count=1,duplicate_chunk_ids=(0,),duplicate_feedback_ids=(0,),
            feedback_latency_ms=0,service=tape(feed_key=100.),ack_timeout_ms=500)
        self.assertTrue(any(f['kind']=='deferred_ack_accepted' for f in control['feedback']))
        self.assertEqual(control['packets'][0]['release_reason'],'decoded_ack_after_drain')

    def test_full_cap_reject_still_pays_without_extra_sender_commit(self):
        row,_,_=self.run_case(count=4,frame_cap=60)
        self.assertFalse(row['commits']);self.assertEqual(row['forward_ipv4_udp_bytes'],0)
        self.assertTrue(all(not p['admitted'] and p['encode_service_ms']>0 for p in row['packets']))


if __name__=='__main__':unittest.main()
