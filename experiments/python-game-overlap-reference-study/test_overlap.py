import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest
import numpy as np
import overlap_codec as overlap
import model

rc=overlap.frozen


class Clock:
    def __init__(self):self.value=0
    def __call__(self):
        old=self.value;self.value+=1000000;return old


class OverlapTests(unittest.TestCase):
    def image(self,i=60):return np.full((16,32,3),i,np.uint8)
    def key(self,enc,rx):
        d=enc.prepare(self.image(),0);self.finish(enc,rx,d);return d
    def finish(self,enc,rx,d):
        rgb,info,ack=rx.receive(d.packet)
        self.assertEqual(enc.expected_hash(d.frame_id),hashlib.sha256(rgb.tobytes()).hexdigest())
        self.assertTrue(enc.ack(ack));return rgb,info,ack

    def test_promotion_overlaps_key0_pending_and_key0_continues_before_ack(self):
        enc=overlap.Encoder();rx=rc.Receiver();self.key(enc,rx)
        normal=enc.prepare(self.image(61),1)
        self.assertTrue(enc.can_prepare(promote=True))
        promoted=enc.prepare(self.image(62),2,promote=True)
        self.assertEqual(promoted.info['pending_bank0_consumers'],1)
        self.assertIsNone(enc.banks[1]);self.assertTrue(enc.can_prepare())
        fallback=enc.prepare(self.image(63),3,reference_bank=0)
        self.assertEqual(fallback.reference_bank,0)
        self.assertFalse(enc.can_prepare(force_key=True))
        for d in (normal,promoted,fallback):self.finish(enc,rx,d)
        self.assertEqual(enc.banks[0].frame_id,0);self.assertEqual(enc.banks[1].frame_id,2)

    def test_bank1_consumers_drain_while_bank0_work_and_promotion_progress(self):
        enc=overlap.Encoder();rx=rc.Receiver();self.key(enc,rx)
        self.finish(enc,rx,enc.prepare(self.image(61),1,promote=True))
        old_user=enc.prepare(self.image(62),2)
        self.assertEqual(old_user.reference_bank,1);self.assertFalse(enc.can_prepare(promote=True))
        fallback=enc.prepare(self.image(63),3,reference_bank=0)
        self.finish(enc,rx,old_user)
        self.assertTrue(enc.can_prepare(promote=True))
        writer=enc.prepare(self.image(64),4,promote=True)
        self.assertEqual(writer.reference_bank,1)
        self.assertEqual(writer.info['pending_bank1_consumers'],0)
        self.assertEqual(writer.info['pending_bank0_consumers'],1)
        later=enc.prepare(self.image(65),5,reference_bank=0)
        for d in (fallback,writer,later):self.finish(enc,rx,d)
        chosen=enc.prepare(self.image(66),6)
        self.assertEqual(chosen.reference_bank,1);self.assertEqual(chosen.reference_id,4)

    def test_bank0_leases_do_not_block_bank1_writer_but_bank1_leases_do(self):
        enc=overlap.Encoder();rx=rc.Receiver();self.key(enc,rx)
        lease0=enc.acquire(0)
        self.assertTrue(enc.can_prepare(promote=True))
        writer=enc.prepare(self.image(61),1,promote=True)
        other0=enc.acquire(0)
        with self.assertRaises(ValueError):enc.acquire(1)
        self.assertFalse(enc.can_prepare(force_key=True))
        enc.release(lease0);enc.release(other0);self.finish(enc,rx,writer)
        lease1=enc.acquire(1)
        self.assertFalse(enc.can_prepare(promote=True))
        normal=enc.prepare(self.image(62),2,reference_bank=0)
        enc.release(lease1)
        self.assertTrue(enc.can_prepare(promote=True));self.finish(enc,rx,normal)

    def test_lost_promotion_ack_keeps_key0_continuity_and_content_guard(self):
        enc=overlap.Encoder();rx=rc.Receiver();self.key(enc,rx)
        writer=enc.prepare(self.image(61),1,promote=True)
        normal=enc.prepare(self.image(62),2)
        _,_,lost=rx.receive(writer.packet)
        self.finish(enc,rx,normal)
        self.assertTrue(enc.can_prepare());self.assertIsNone(enc.banks[1])
        self.assertTrue(enc.expire(1));self.assertFalse(enc.ack(lost))
        normal=enc.prepare(self.image(63),3);self.assertEqual(normal.reference_bank,0)
        self.finish(enc,rx,normal)
        writer=enc.prepare(self.image(64),4,promote=True)
        _,_,ack=rx.receive(writer.packet)
        fields=list(rc.FEEDBACK.unpack_from(ack));fields[8]=b'x'*16
        with self.assertRaises(ValueError):enc.ack(rc.seal(rc.FEEDBACK.pack(*fields)))
        self.assertIn(4,enc.pending);self.assertIsNone(enc.banks[1]);self.assertTrue(enc.ack(ack))

    def test_arithmetic_packets_match_serial_when_reference_choices_match(self):
        serial=rc.Encoder();other=overlap.Encoder();sr=rc.Receiver();orr=rc.Receiver()
        for i in range(12):
            kwargs=dict(force_key=i==8,promote=i%3==0)
            a=serial.prepare(self.image(60+i),i,**kwargs);b=other.prepare(self.image(60+i),i,**kwargs)
            self.assertEqual(a.packet,b.packet)
            self.finish(serial,sr,a);self.finish(other,orr,b)

    def test_rejected_promotion_preserves_existing_bank_and_pending_consumers(self):
        enc=overlap.Encoder(frame_cap=230);rx=rc.Receiver(frame_cap=230);self.key(enc,rx)
        self.finish(enc,rx,enc.prepare(self.image(61),1,promote=True))
        enc.prepare(self.image(62),2,reference_bank=0)
        old=(dict(enc.banks),dict(enc.pending),enc.last_issued,enc._generation)
        source=np.random.default_rng(1414).integers(0,256,(16,32,3),dtype=np.uint8)
        d=enc.prepare(source,3,promote=True)
        self.assertFalse(d.accepted);self.assertGreater(d.info['reconstruction_ms'],0)
        self.assertEqual(old,(enc.banks,enc.pending,enc.last_issued,enc._generation))

    def test_invalid_reference_choices_and_receiver_atomicity(self):
        enc=overlap.Encoder();rx=rc.Receiver();self.key(enc,rx)
        for bank in (1,2,False):
            with self.assertRaises(ValueError):enc.prepare(self.image(),1,reference_bank=bank)
        with self.assertRaises(ValueError):enc.prepare(self.image(),1,force_key=True,reference_bank=0)
        writer=enc.prepare(self.image(61),1,promote=True)
        with self.assertRaises(ValueError):enc.prepare(self.image(),2,reference_bank=1)
        fields=list(rc.HEADER.unpack_from(writer.packet));fields[8]=b'x'*16
        corrupt=rc.seal(rc.HEADER.pack(*fields)+writer.packet[rc.HEADER.size:-4])
        with self.assertRaises(ValueError):rx.receive(corrupt)
        self.assertEqual(rx.last_frame_id,0);self.assertIsNone(rx.banks[1])

    def bounded(self,row,count):
        self.assertFalse(row['unresolved_ids']);self.assertTrue(all(x is None for x in row['unresolved_sender_slots']))
        self.assertFalse(row['unresolved_encoder_pending']);self.assertFalse(row['unresolved_ingress'])
        self.assertEqual(row['unresolved_receiver_readers'],0);self.assertFalse(row['unresolved_decode'])
        self.assertLessEqual(row['peak_sender'],3);self.assertLessEqual(row['peak_pending'],3)
        self.assertLessEqual(row['peak_ingress'],2);self.assertLessEqual(row['peak_framebuffers'],3)
        self.assertLessEqual(row['peak_feedback'],4)
        self.assertEqual(sorted([p['id'] for p in row['presented']]+[p['id'] for p in row['drops']]),list(range(count)))
        for w in row['work']:
            self.assertEqual(w['wall_ms'],w['service_ms']);self.assertGreater(w['service_ms'],0)
        for p in row['packets']:
            if p['admitted'] and not p['key']:
                ref=p['source_banks'][str(p['reference_bank'])]
                self.assertEqual(ref['id'],p['reference_id']);self.assertEqual(ref['tag'],p['reference_tag'])
            if p['bank0_fallback']:
                self.assertFalse(p['promoted']);self.assertEqual(p['reference_bank'],0)

    def test_model_serial_fixed_clock_matches_frozen_parent_trace(self):
        path=Path(__file__).resolve().parents[1]/'python-game-reference-ownership-study/model.py'
        spec=importlib.util.spec_from_file_location('overlap_frozen_ownership',path)
        frozen=importlib.util.module_from_spec(spec);sys.modules[spec.name]=frozen;spec.loader.exec_module(frozen)
        frames=[self.image(40+i) for i in range(30)]
        changes=dict(width=32,height=16,promotion_period=4)
        a=frozen.run(frames,config=frozen.Config(**changes),clock_ns=Clock())
        b=model.run(frames,config=model.Config(reference_policy='serial',**changes),clock_ns=Clock())
        self.bounded(b,len(frames))
        for field in ('presented','drops','feedback','publications','wire','admission_wait_ms'):
            self.assertEqual(a[field],b[field],field)
        self.assertEqual([(p['id'],p.get('packet_sha256')) for p in a['packets']],
                         [(p['id'],p.get('packet_sha256')) for p in b['packets']])

    def test_model_fallback_drain_makes_progress_and_faults_recover(self):
        frames=[self.image(40+i) for i in range(60)]
        for faults in ({},dict(drop_first_promotion_ack=True),dict(drop_first_key_chunk=True),
                       dict(conflict_first_promotion_feedback=True)):
            cfg=model.Config(width=32,height=16,promotion_period=4,feedback_latency_ms=45,fps=60,**faults)
            row=model.run(frames,config=cfg,clock_ns=Clock());self.bounded(row,len(frames))
            self.assertGreater(row['presented_eventual'],0)
            self.assertTrue(any(p['bank0_fallback'] for p in row['packets']))
            self.assertTrue(any(p['promoted'] and p['info']['pending_bank0_consumers']>0 for p in row['packets']))
        with self.assertRaises(ValueError):model.run(frames,config=model.Config(reference_policy='unknown'))


if __name__=='__main__':unittest.main()
