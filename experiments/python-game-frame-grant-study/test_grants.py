import unittest,heapq
from unittest.mock import patch
import numpy as np
import model,frame_credit as fc,framing,gateway
from test_model import Clock,verify
class GrantTests(unittest.TestCase):
    def images(self,n=24,w=32,h=16):return [np.full((h,w,3),40+i,np.uint8) for i in range(n)]
    def cfg(self,**kw):return model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),feedback_latency_ms=2,decode_age_ms=250,**kw)
    def test_fixed_slow_decode_busy_reproduced_without_grants_eliminated_with_grants(self):
        outputs=[]
        for enabled in (False,True):
            clock=Clock();old=model.rc.Receiver.begin
            def slow(rx,b):
                out=old(rx,b);clock.value+=40000000;return out
            with patch.object(model.rc.Receiver,'begin',slow):r=model.run(self.images(48),config=self.cfg(frame_grants_enabled=enabled),clock_ns=clock)
            verify.check_case(dict(result=r),False);outputs.append(r)
        self.assertGreater(sum(p['feed_errors'].count('GF03 busy') for p in outputs[0]['packets']),0)
        self.assertEqual(sum(p['feed_errors'].count('GF03 busy') for p in outputs[1]['packets']),0)
        self.assertGreater(outputs[1]['presented_eventual'],0)
    def test_committed_but_never_packetized_deadline_cancels_grant(self):
        clock=Clock();old=model.rc.Encoder.commit
        def slow(enc,c):out=old(enc,c);clock.value+=120000000;return out
        cfg=self.cfg();cfg=model.Config(**{**cfg.__dict__,'decode_age_ms':50})
        with patch.object(model.rc.Encoder,'commit',slow):r=model.run(self.images(8),config=cfg,clock_ns=clock)
        verify.check_case(dict(result=r),False)
        self.assertTrue(any(p['committed'] for p in r['packets']))
        self.assertFalse(any(not w['control'] for w in r['gateway']['wire']))
        self.assertGreater(r['frame_grants']['counters']['cancel_confirmed'],0)
        self.assertFalse(r['publications'])
    def test_lost_grant_and_release_stop_without_inventing_capacity(self):
        for fault,reason in [('lose_first_frame_grant','frame_control_reply_timeout'),('lose_first_frame_release','frame_release_reply_timeout')]:
            r=model.run(self.images(24),config=self.cfg(**{fault:True}),clock_ns=Clock());f=r['frame_grants']
            self.assertTrue(f['safe_stop']);self.assertEqual(f['safe_stop_reason'],reason)
            self.assertLessEqual(f['peak_receiver'],2);self.assertLessEqual(f['peak_host'],2)
            self.assertTrue(f['pending'] or f['host_owned'] or f['receiver_owned'])
            if fault=='lose_first_frame_grant':self.assertFalse(r['commits']);self.assertFalse(any(p['committed'] for p in r['packets']))
    def test_stale_release_does_not_release_new_slot_owner(self):
        r=model.run(self.images(32),config=self.cfg(duplicate_frame_release=True),clock_ns=Clock())
        verify.check_case(dict(result=r),False)
        self.assertGreater(r['frame_grants']['counters'].get('stale_release',0),0)
    def protocol(self):
        events=[]
        def timed(stage,fid,fn):return fn(),dict(done_ms=0.,wall_ms=0.,service_ms=0.)
        p=fc.Protocol(model.Config(),lambda *x:events.append(x),timed)
        class Engine:
            reverse_free=0
            def reverse(self,*a,**kw):pass
        p.engine=Engine();return p
    def req(self,fid,seq,total=1200,crc=123):return dict(kind=fc.REQUEST,slot=0,epoch=1,frame=fid,seq=seq,total=total,crc=crc)
    def test_cancel_delayed_old_data_and_cancel_cannot_touch_reused_slot(self):
        p=self.protocol();a=self.req(0,1);p.receive(a,0);old=dict(p.receiver[0]);p.receive(dict(a,kind=fc.CANCEL,slot=0),1)
        b=self.req(1,2);p.receive(b,2);new=p.receiver[0];self.assertIsNotNone(new)
        old_fields=(b'GF03',3,1,0,1200,0,2,1008,55,123)
        self.assertIsNone(p.allowed(old_fields));p.consumed(old_fields);self.assertEqual(new['seen'],set())
        p.receive(dict(a,kind=fc.CANCEL,slot=0),3);self.assertIs(p.receiver[0],new)
        self.assertEqual(p.counter['cancel_rejected'],1)
    def test_duplicate_and_invalid_indices_do_not_satisfy_unique_fragment_inventory(self):
        p=self.protocol();p.receive(self.req(0,1),0)
        fields=(b'GF03',3,1,0,1200,0,2,1008,55,123)
        p.consumed(fields);p.consumed(fields)
        bad=list(fields);bad[5]=3;p.consumed(tuple(bad))
        self.assertEqual(p.receiver[0]['seen'],{0});self.assertEqual(p.receiver[0]['expected'],2)
        p.release_ready(1,lambda fid:True);self.assertIsNotNone(p.receiver[0])
    def test_combined_aggregated_control_and_data_bounds(self):
        rng=np.random.default_rng(4);images=[rng.integers(0,256,(64,128,3),dtype=np.uint8) for _ in range(20)]
        cfg=model.Config(width=128,height=64,codec_mode='gm',ui_rectangles=((0,0,16,8),),feedback_latency_ms=10,decode_age_ms=250,aggregate_ms=8,lose_first_packet_credit=True,duplicate_frame_release=True,admission_age_ms=250)
        r=model.run(images,config=cfg,clock_ns=Clock());verify.check_case(dict(result=r),False)
        self.assertLessEqual(r['gateway']['peak_mailbox'],6);self.assertEqual(r['gateway']['peak_tokens'],5)
        self.assertGreater(r['gateway']['counters'].get('queries_consumed',0),0)
        self.assertGreater(sum(w.get('frame_control',False) for w in r['gateway']['wire']),0)
    def test_packet_credit_blackhole_is_explicit_bounded_safe_stop(self):
        r=model.run(self.images(24),config=self.cfg(lose_all_packet_credits=True),clock_ns=Clock())
        self.assertTrue(r['frame_grants']['safe_stop'])
        self.assertEqual(r['frame_grants']['safe_stop_reason'],'packet_credit_query_timeout')
        self.assertLessEqual(r['gateway']['peak_mailbox'],6);self.assertLessEqual(r['gateway']['peak_tokens'],5)
        self.assertTrue(r['gateway']['outstanding_tokens'])
    def test_delayed_grant_cannot_clear_finish_and_wrong_slot_cancel_cannot_clear_owner(self):
        p=self.protocol();x=dict(self.req(3,7),kind=fc.GRANT,slot=0);p.host[3]=x
        p.pending=dict(kind=fc.FINISH,identity=fc.identity(x),slot=0);old=p.pending;p.feedback_owned=1
        p.apply_reply((x,None,x),1);self.assertIs(p.pending,old);self.assertIs(p.host[3],x)
        p.pending=dict(kind=fc.CANCEL,identity=fc.identity(x),slot=0);old=p.pending;p.feedback_owned=1
        wrong=dict(x,kind=fc.CANCELED,slot=1)
        p.apply_reply((wrong,None,wrong),2);self.assertIs(p.pending,old);self.assertIs(p.host[3],x)
        p.feedback_owned=1;release=dict(x,kind=fc.RELEASE);p.apply_reply((release,None,release),3)
        self.assertIs(p.pending,old);self.assertIs(p.host[3],x)
        p.pending=dict(kind=fc.FINISH,identity=fc.identity(x),slot=0);p.feedback_owned=1
        finished=dict(x,kind=fc.FINISHED);p.apply_reply((finished,None,finished),4);self.assertIn(3,p.host);self.assertIsNone(p.pending)
        p.feedback_owned=1;p.apply_reply((release,None,release),5);self.assertNotIn(3,p.host)
    def test_finished_frees_only_control_and_release_preserves_other_pending_request(self):
        p=self.protocol();x=dict(self.req(0,7),kind=fc.GRANT,slot=0);p.host[0]=x;p.seq=7
        p.pending=dict(kind=fc.FINISH,identity=fc.identity(x),slot=0);p.feedback_owned=1
        finished=dict(x,kind=fc.FINISHED);p.apply_reply((finished,None,finished),1)
        self.assertIn(0,p.host);self.assertIsNone(p.pending)
        self.assertTrue(p.request(1,1200,456,2));request=p.pending
        self.assertEqual(request['slot'],1)
        release=dict(x,kind=fc.RELEASE);p.feedback_owned=1;p.apply_reply((release,None,release),3)
        self.assertNotIn(0,p.host);self.assertIs(p.pending,request)
        wrong=dict(kind=fc.GRANT,slot=0,epoch=1,frame=1,seq=8,total=1200,crc=456)
        p.feedback_owned=1;p.apply_reply((wrong,None,wrong),4);self.assertIs(p.pending,request);self.assertNotIn(1,p.host)
    def test_receiver_never_substitutes_another_slot_and_cancel_rejects_queued_data(self):
        p=self.protocol();a=self.req(0,1);p.receive(a,0)
        p.receive(self.req(1,2),1);self.assertIsNone(p.receiver[1])
        p.receive(dict(self.req(1,3),slot=1),2);self.assertIsNotNone(p.receiver[1])
        p.host[0]=dict(a,kind=fc.GRANT);p.engine.frames={0:{'data':'queued'}}
        self.assertFalse(p.cancel(0,3));self.assertIn(0,p.host);self.assertIsNone(p.pending)
    def test_control_crc_reserved_slot_and_direction_rejected(self):
        b=fc.seal(fc.REQUEST,0,0,1,1000,123)
        with self.assertRaises(ValueError):fc.parse(b[:-1]+bytes([b[-1]^1]))
        with self.assertRaises(ValueError):fc.parse(fc.seal(fc.GRANT,fc.NO_SLOT,0,1,1000,123))
        p=self.protocol()
        with self.assertRaises(ValueError):p.receive(fc.parse(fc.seal(fc.RELEASE,0,0,1,1000,123)),0)
if __name__=='__main__':unittest.main()
