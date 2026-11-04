import unittest
from unittest.mock import patch
import numpy as np
import model


class TickClock:
    """Declared deterministic unit clock, absent from performance benchmark."""
    def __init__(self): self.value = 0
    def __call__(self):
        old = self.value; self.value += 1000000; return old


class OwnershipTests(unittest.TestCase):
    def run_case(self, **changes):
        count = changes.pop('count', 36)
        values = dict(width=32,height=16,promotion_period=4)
        values.update(changes)
        frames = [np.full((16,32,3),40+i,np.uint8) for i in range(count)]
        row = model.run(frames, config=model.Config(**values), clock_ns=TickClock())
        self.assertFalse(row['unresolved_ids'])
        self.assertTrue(all(x is None for x in row['unresolved_sender_slots']))
        self.assertFalse(row['unresolved_encoder_pending'])
        self.assertFalse(row['unresolved_ingress'])
        self.assertEqual(row['unresolved_receiver_readers'],0)
        self.assertFalse(row['unresolved_decode'])
        self.assertLessEqual(row['peak_sender'],values.get('window',3))
        self.assertLessEqual(row['peak_pending'],values.get('window',3))
        self.assertLessEqual(row['peak_ingress'],2)
        self.assertLessEqual(row['peak_framebuffers'],3)
        self.assertLessEqual(row['peak_feedback'],4)
        self.assertEqual(sorted([p['id'] for p in row['presented']]+[p['id'] for p in row['drops']]),list(range(count)))
        for work in row['work']:
            self.assertGreater(work['service_ms'],0)
            self.assertEqual(work['service_ms'],work['wall_ms'])
            self.assertAlmostEqual(work['done_ms']-work['start_ms'],work['service_ms'])
        for p in row['packets']:
            self.assertGreaterEqual(p['released_ms'],p['encode_done_ms'])
            if p['admitted'] and not p['key']:
                source=p['source_banks'][str(p['reference_bank'])]
                self.assertIsNotNone(source)
                self.assertEqual(source['id'],p['reference_id'])
                self.assertEqual(source['tag'],p['reference_tag'])
            if 'decode_done_ms' in p:
                self.assertTrue(p['read_pin_at_decode_start'])
                self.assertGreaterEqual(p['released_ms'],p['read_pin_release_ms'])
        for feedback in row['feedback']:
            if feedback['kind']=='ack_applied':
                packet=next(p for p in row['packets'] if p['id']==feedback['id'])
                self.assertGreaterEqual(feedback['at_ms'],packet['decode_done_ms'])
                self.assertNotIn('expiry_requested_ms',packet)
        return row

    def test_immutable_and_promoted_paths_have_bounded_valid_references(self):
        immutable=self.run_case(promotion_period=0)
        promoted=self.run_case()
        self.assertTrue(any(p['promoted'] for p in promoted['packets']))
        self.assertTrue(any(p['reference_bank']==1 for p in promoted['packets']))
        self.assertFalse(any(p['promoted'] for p in immutable['packets']))
        self.assertEqual(immutable['presented_eventual'],36)
        self.assertEqual(promoted['presented_eventual'],36)

    def test_lost_promotion_ack_does_not_promote_sender_and_falls_back(self):
        row=self.run_case(drop_first_promotion_ack=True,count=48)
        lost=next(p for p in row['packets'] if p.get('fault_promotion_ack_lost'))
        expired=next(f for f in row['feedback'] if f['kind']=='expired' and f['id']==lost['id'])
        self.assertIsNone(expired['sender_banks']['1'])
        self.assertFalse(any(f['kind']=='ack_applied' and f['id']==lost['id'] for f in row['feedback']))
        later=[p for p in row['packets'] if p['id']>lost['id']]
        self.assertTrue(later)
        self.assertEqual(later[0]['reference_bank'],0)
        self.assertGreater(row['presented_eventual'],5)

    def test_partial_lost_key_and_corruption_recover(self):
        for faults in (dict(drop_first_key_chunk=True),dict(corruption_ids=(0,))):
            row=self.run_case(**faults,count=48)
            self.assertTrue(any(p['id']>0 and p['key'] for p in row['packets']))
            self.assertGreater(row['presented_eventual'],0)

    def test_conflicting_feedback_expiry_wins_deferred_ack(self):
        row=self.run_case(conflict_first_promotion_feedback=True,count=48)
        nack=next(f for f in row['feedback'] if f['kind']=='parsed' and f['status']==model.rc.NACK)
        frame=nack['id']
        self.assertTrue(any(f['kind']=='parsed' and f['id']==frame and f['status']==model.rc.ACK for f in row['feedback']))
        self.assertFalse(any(f['kind']=='ack_applied' and f['id']==frame for f in row['feedback']))
        expired=next(f for f in row['feedback'] if f['kind']=='expired' and f['id']==frame)
        self.assertIsNone(expired['sender_banks']['1'])

    def test_rejected_work_has_no_wire_or_bank_publication(self):
        row=self.run_case(frame_cap=128,count=4)
        self.assertFalse(row['commits'])
        self.assertEqual(row['forward_ipv4_udp_bytes'],0)
        self.assertTrue(all(not p['admitted'] for p in row['packets']))
        self.assertTrue(all(p['encode_service_ms']>0 for p in row['packets']))

    def test_timeout_during_paid_ack_work_cannot_publish_future_reference(self):
        clock=TickClock(); original=model.rc.Encoder.ack
        def slow_ack(enc,data):
            result=original(enc,data);clock.value+=100000000;return result
        images=[np.full((16,32,3),40,np.uint8)]
        with patch.object(model.rc.Encoder,'ack',slow_ack):
            row=model.run(images,config=model.Config(width=32,height=16,promotion_period=0,ack_timeout_ms=50),clock_ns=clock)
        charge=next(w for w in row['work'] if w['stage']=='ack_apply')
        self.assertGreater(charge['service_ms'],100)
        self.assertTrue(any(f['kind']=='ack_discarded_after_expiry' for f in row['feedback']))
        self.assertFalse(any(f['kind']=='ack_applied' for f in row['feedback']))
        self.assertIsNone(row['sender_banks_final']['0'])
        self.assertEqual(row['packets'][0]['release_reason'],'ack_timeout')

    def test_deadline_during_paid_decoder_completion_aborts_publication(self):
        clock=TickClock();original=model.rc.Receiver.complete
        def slow_complete(rx,task):
            result=original(rx,task);clock.value+=100000000;return result
        images=[np.full((16,32,3),40,np.uint8)]
        with patch.object(model.rc.Receiver,'complete',slow_complete):
            row=model.run(images,config=model.Config(width=32,height=16,promotion_period=0,decode_age_ms=50),clock_ns=clock)
        self.assertTrue(any(w['stage']=='decode_complete' and w['service_ms']>100 for w in row['work']))
        self.assertTrue(any(w['stage']=='decode_abort' for w in row['work']))
        self.assertFalse(row['publications']);self.assertFalse(row['commits'])
        self.assertIsNone(row['receiver_banks_final']['0'])
        self.assertEqual(row['unresolved_receiver_readers'],0)
        self.assertFalse(row['unresolved_decode'])

    def test_invalid_resource_and_fault_configuration(self):
        frames=[np.zeros((16,32,3),np.uint8)]
        for changes in (dict(window=4),dict(promotion_period=-1),dict(fps=0),dict(drop_first_key_chunk=1)):
            with self.assertRaises(ValueError):model.run(frames,config=model.Config(**changes))


if __name__=='__main__':unittest.main()
