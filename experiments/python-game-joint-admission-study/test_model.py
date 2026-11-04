import unittest,importlib.util,sys,struct
from pathlib import Path
from unittest.mock import patch
import numpy as np
import model,gateway,framing
s=importlib.util.spec_from_file_location('joint_check',Path(__file__).with_name('verify.py'));verify=importlib.util.module_from_spec(s);s.loader.exec_module(verify)
class Clock:
    def __init__(self):self.value=0
    def __call__(self):v=self.value;self.value+=1000000;return v
class JointTests(unittest.TestCase):
    def run_case(self,count=48,**kw):
        cfg=model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),refresh_period=8,promotion_period=4,feedback_latency_ms=2,decode_age_ms=200,**kw)
        images=[np.full((16,32,3),40+i,np.uint8) for i in range(count)]
        r=model.run(images,config=cfg,clock_ns=Clock());verify.check_case(dict(result=r),False);return r
    def test_actual_decodes_and_publications_with_candidate_commit(self):
        r=self.run_case();self.assertEqual(r['presented_eventual'],48)
        self.assertTrue(any(p['promoted'] for p in r['packets']));self.assertTrue(any(p['refresh_key'] for p in r['packets']))
        self.assertTrue(all(p['committed'] for p in r['packets']))
    def test_precommit_admission_rejection_never_burns_identity_or_publishes(self):
        r=self.run_case(admission_age_ms=1)
        self.assertFalse(r['commits']);self.assertFalse(r['gateway']['wire'])
        self.assertTrue(all(not p['committed'] and p['rejection_reason']=='admission_rejected' for p in r['packets']))
        self.assertFalse(r['sender_banks_final']['0'])
    def test_lost_credit_recovers_only_through_actual_query(self):
        r=self.run_case(lose_first_packet_credit=True,duplicate_packet_credit=True)
        self.assertGreater(r['gateway']['counters'].get('queries_consumed',0),0)
        self.assertGreater(r['gateway']['counters'].get('stale_credit',0),0)
        self.assertGreater(r['presented_eventual'],30)
    def test_lost_publication_ack_does_not_use_unconfirmed_key(self):
        r=self.run_case(drop_first_refresh_ack=True)
        lost=next(p for p in r['packets'] if p.get('fault_refresh_ack_lost'))
        self.assertFalse(any(f['kind']=='ack_applied' and f['id']==lost['id'] for f in r['feedback']))
        self.assertTrue(any(f['kind']=='expired' and f['id']==lost['id'] for f in r['feedback']))
        self.assertGreater(r['presented_eventual'],20)
    def test_forward_loss_and_corruption_have_no_invalid_decoded_references(self):
        for change in (dict(drop_packet_frame=8),dict(corrupt_packet_frame=8)):
            r=self.run_case(**change)
            self.assertGreater(r['presented_eventual'],20)
            self.assertTrue(any(p['id']>8 and p['committed'] for p in r['packets']))
    def test_slow_feedback_aggregation_and_low_link_drop_safely(self):
        r=self.run_case(aggregate_ms=8,link_mbps=.02)
        self.assertLess(r['presented_eventual'],48)
    def test_actual_credit_prefix_and_fragment_size(self):
        data=framing.datagrams(b'ABCD'*400,1,3)[0];wrapped=gateway.TOKEN.pack(1,2,0,7)+data
        self.assertLessEqual(len(wrapped),1064)
        self.assertEqual(gateway.unwrap(wrapped)['seq'],7)
        with self.assertRaises(ValueError):gateway.unwrap(gateway.TOKEN.pack(2,2,0,7)+data)
        with self.assertRaises(ValueError):gateway.unwrap(wrapped[:10])
    def test_wire_af_corruption_cannot_publish_sender_bank(self):
        r=self.run_case(count=24,corrupt_af_frame=0)
        self.assertFalse(any(f['kind']=='ack_applied' and f['id']==0 for f in r['feedback']))
        self.assertTrue(any(f['kind']=='expired' and f['id']==0 for f in r['feedback']))
    def test_gf_route_must_match_ar03_body_before_decode(self):
        e=model.rc.Encoder(mode='gm');c=e.build(np.full((16,32,3),70,np.uint8),0);d=e.commit(c)
        chunks=framing.datagrams(d.packet,1,99);rx=framing.Reassembler();complete=None
        for b in chunks:complete=rx.feed(b,0)
        with self.assertRaises(ValueError):model.validate_complete(complete)
    def test_reserved_query_and_reply_slots_are_rejected(self):
        bad=gateway.seal(gateway.QUERY.pack(b'QC18',1,0,1,1,123))
        with self.assertRaises(ValueError):gateway.parse(bad,gateway.QUERY,b'QC18')
        bad=gateway.seal(gateway.REPLY.pack(b'PC18',1,6,0,1,0,123))
        with self.assertRaises(ValueError):gateway.parse(bad,gateway.REPLY,b'PC18')
    def test_lost_credits_pay_construction_and_reverse_wire(self):
        r=self.run_case(count=12,lose_first_packet_credit=True)
        self.assertTrue(any(w['stage']=='credit_build' for w in r['work']))
        self.assertGreater(len([f for f in r['feedback'] if f['kind']=='wire' and f['channel']=='credit']),r['gateway']['counters']['credits_applied'])
    def test_paid_ack_overlap_cannot_clobber_new_candidate_commit(self):
        clock=Clock();old=model.rc.Encoder.ack
        def slow(e,b):out=old(e,b);clock.value+=45000000;return out
        images=[np.full((16,32,3),40+i,np.uint8) for i in range(48)]
        cfg=model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),refresh_period=8,promotion_period=4,feedback_latency_ms=2,decode_age_ms=250)
        with patch.object(model.rc.Encoder,'ack',slow):r=model.run(images,config=cfg,clock_ns=clock)
        verify.check_case(dict(result=r),False)
        self.assertTrue(any(p.get('build_done_ms',0)<f['at_ms'] for p in r['packets'] if p['committed'] for f in r['feedback'] if f['kind']=='ack_applied'))
        self.assertFalse(r['unresolved_encoder_pending'])
    def test_expiry_during_paid_ack_resumes_waiting_candidate(self):
        clock=Clock();old_ack=model.rc.Encoder.ack;old_build=model.rc.Encoder.build
        def slow_ack(e,b):
            fid=model.rc.parse_feedback(b)['frame_id'];out=old_ack(e,b)
            if fid>0:clock.value+=45000000
            return out
        def slow_build(e,rgb,fid,**kw):
            c=old_build(e,rgb,fid,**kw)
            if fid>0:clock.value+=25000000
            return c
        images=[np.full((16,32,3),40+i,np.uint8) for i in range(12)]
        cfg=model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),feedback_latency_ms=2,decode_age_ms=250,ack_timeout_ms=40)
        with patch.object(model.rc.Encoder,'ack',slow_ack),patch.object(model.rc.Encoder,'build',slow_build):r=model.run(images,config=cfg,clock_ns=clock)
        verify.check_case(dict(result=r),False)
        self.assertTrue(any(f['kind']=='ack_discarded_after_expiry' for f in r['feedback']))
        self.assertFalse(r['unresolved_candidate']);self.assertFalse(r['unresolved_candidate_readers'])
    def test_misrouted_datagram_rejected_through_actual_worker(self):
        r=self.run_case(count=24,misroute_frame=0)
        self.assertFalse(any(c['id']==0 for c in r['commits']))
        self.assertTrue(any('route is not bound' in p.get('decode_error','') for p in r['packets']))
    def test_worker_malformed_prefix_rejects_without_inventing_credit(self):
        events=[];cfg=model.Config();rx=framing.Reassembler()
        def event(at,kind,value):events.append((at,kind,value))
        def timed(stage,fid,fn):return fn(),dict(done_ms=0.,wall_ms=0.)
        e=gateway.Engine(cfg,rx,event,timed,[]);e.enqueue(0,[b'bad'])
        item=dict(frame=0,slot=0,seq=1,crc=123,data=b'bad',index=0,control=False)
        e.frames[0]['next']=1;e.tokens[0]=item;e.mailbox.append(item)
        e.pump(0)
        self.assertEqual(events[0][1],'gw_malformed_done')
        e.step(events[0][1],events[0][2],events[0][0])
        self.assertEqual(e.counter['malformed_rejected'],1);self.assertIs(e.tokens[0],item)
        self.assertFalse(rx.pending)
    def test_timeout_during_paid_completion_cannot_publish(self):
        clock=Clock();old=model.rc.Receiver.complete
        def slow(rx,task):out=old(rx,task);clock.value+=200000000;return out
        images=[np.full((16,32,3),70,np.uint8) for _ in range(6)]
        cfg=model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),decode_age_ms=80)
        with patch.object(model.rc.Receiver,'complete',slow):r=model.run(images,config=cfg,clock_ns=clock)
        verify.check_case(dict(result=r),False);self.assertFalse(r['commits']);self.assertFalse(r['sender_banks_final']['0'])
if __name__=='__main__':unittest.main()
