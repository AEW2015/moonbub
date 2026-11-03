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
    def config(self,**kwargs):return model.Config(rectangles=((0,0,16,16),),width=32,height=16,**kwargs)
    def drained(self,row):
        self.assertTrue(all(x is None for x in row['unresolved_sender_slots']))
        self.assertFalse(row['unresolved_ingress_frames']);self.assertFalse(row['unresolved_credits'])
        self.assertFalse(row['pending_ids']);self.assertIsNone(row['waiting_at_end'])
        self.assertTrue(all(v==0 for v in row['unresolved_cpu'].values()))
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
        clock=Clock();r=model.run(frames,{},model.Config(rectangles=((0,0,16,16),),width=48,height=32,reverse_chunks=True,decoder_service='assumed',decode_ms=3),**factories(clock,decode=50))
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





def services(clock,packetize=2,feed=3,build=4,parse=5,resize=6):
    class Ops:
        @staticmethod
        def datagrams(*args):
            out=model.transport.datagrams(*args);clock.advance(packetize);return out
        @staticmethod
        def feed(ingress,*args):
            try:return ingress.feed(*args)
            finally:clock.advance(feed)
        @staticmethod
        def feedback_datagram(*args,**kwargs):
            out=model.transport.feedback_datagram(*args,**kwargs);clock.advance(build);return out
        @staticmethod
        def parse_feedback(*args):
            try:return model.transport.parse_feedback(*args)
            finally:clock.advance(parse)
    def resize_op(*args):
        result=model.corpus._letterbox(*args);clock.advance(resize);return result
    return dict(transport_ops=Ops,resize_frame=resize_op)


class ServiceTests(unittest.TestCase):
    frames=PipelineTests.frames
    config=PipelineTests.config
    drained=PipelineTests.drained
    def test_injected_costs_causal_stages_and_unchanged_packet_bytes(self):
        results=[]
        for charged in (False,True):
            clock=Clock()
            row=model.run(self.frames(12),{},self.config(transport_cpu=charged,resize_cpu=charged,decoder_service='python_wall'),
                          **factories(clock),**services(clock))
            self.drained(row);results.append(row)
            for cpu in row['cpu_services']:
                self.assertEqual(cpu['wall_ms'],dict(packetize=2,feed=3,feedback_build=4,feedback_parse=5)[cpu['stage']])
                self.assertEqual(cpu['service_ms'],cpu['wall_ms'] if charged else 0)
                self.assertAlmostEqual(cpu['done_ms']-cpu['start_ms'],cpu['service_ms'])
            self.assertTrue(all(r['wall_ms']==6 and r['service_ms']==(6 if charged else 0) for r in row['resize_services']))
            for packet in row['packets']:
                pub=next(s for s in row['encoder_states'] if s['kind']=='published' and s['id']==packet['id'])
                stage=next(s for s in row['encoder_states'] if s['kind']=='staged' and s['id']==packet['id'])
                self.assertNotIn(packet['id'],stage['pending']);self.assertIn(packet['id'],pub['pending'])
                self.assertEqual(pub['at_ms'],packet['encode_started_ms']+7)
                packetize=next(c for c in row['cpu_services'] if c['stage']=='packetize' and c['id']==packet['id'])
                feed_done=max(c['done_ms'] for c in row['cpu_services'] if c['stage']=='feed' and c['id']==packet['id'])
                build=next(c for c in row['cpu_services'] if c['stage']=='feedback_build' and c['id']==packet['id'])
                parse=next(c for c in row['cpu_services'] if c['stage']=='feedback_parse' and c['id']==packet['id'])
                self.assertGreaterEqual(packetize['start_ms'],pub['at_ms'])
                self.assertGreaterEqual(packet['decode_started_ms'],feed_done)
                self.assertGreaterEqual(build['start_ms'],packet['decode_done_ms'])
                self.assertGreaterEqual(packet['released_ms'],parse['done_ms'])
        self.assertEqual([(p['id'],p['packet_sha256']) for p in results[0]['packets']],
                         [(p['id'],p['packet_sha256']) for p in results[1]['packets']])
        self.assertEqual(sorted((c['stage'],c['id'],c.get('index',-1),c.get('output_sha256'),c.get('input_sha256')) for c in results[0]['cpu_services']),
                         sorted((c['stage'],c['id'],c.get('index',-1),c.get('output_sha256'),c.get('input_sha256')) for c in results[1]['cpu_services']))
        self.assertEqual([r['output_sha256'] for r in results[0]['resize_services']],
                         [r['output_sha256'] for r in results[1]['resize_services']])
        self.assertGreater(results[1]['packets'][0]['decode_done_ms'],results[0]['packets'][0]['decode_done_ms'])

    def test_timeout_waits_active_feed_and_decode_and_parse(self):
        clock=Clock()
        row=model.run(self.frames(18),{},self.config(ack_timeout_ms=15,decoder_service='python_wall',frame_deadline_ms=300),
                      **factories(clock,decode=30),**services(clock,feed=35,parse=25))
        self.drained(row)
        self.assertTrue(any(not t['physical_drained'] for t in row['timeout_events']))
        for cpu in row['cpu_services']:
            if cpu['stage'] in ('feed','feedback_build'):
                p=next(p for p in row['packets'] if p['id']==cpu['id'])
                self.assertGreaterEqual(p['released_ms'],cpu['done_ms'])

    def test_timeout_during_feedback_parse_cannot_release_active_owner(self):
        clock=Clock()
        row=model.run(self.frames(1),{},self.config(ack_timeout_ms=35,decoder_service='python_wall'),
                      **factories(clock),**services(clock,parse=25))
        self.drained(row)
        parse=next(c for c in row['cpu_services'] if c['stage']=='feedback_parse')
        timeout=row['timeout_events'][0]
        self.assertLess(parse['start_ms'],timeout['at_ms']);self.assertLess(timeout['at_ms'],parse['done_ms'])
        self.assertFalse(timeout['physical_drained'])
        self.assertGreaterEqual(row['packets'][0]['released_ms'],parse['done_ms'])

    def test_transport_rejection_still_pays_feed_and_nack_cpu(self):
        clock=Clock()
        row=model.run(self.frames(12),{},self.config(corruption_ids=(0,)),**factories(clock),**services(clock))
        self.drained(row)
        feed=next(c for c in row['cpu_services'] if c['stage']=='feed' and c['id']==0)
        self.assertEqual(feed['service_ms'],3)
        self.assertTrue(any(c['stage']=='feedback_build' and c['id']==0 for c in row['cpu_services']))
        self.assertTrue(any(f['kind']=='received' and f['status']==1 for f in row['feedback']))

    def test_feedback_descriptor_capacity_and_duplicate_serialization(self):
        clock=Clock()
        row=model.run(self.frames(1),{},self.config(feedback_slots=1,duplicate_feedback_ids=(0,)),
                      **factories(clock),**services(clock))
        self.drained(row)
        self.assertEqual(row['peak_cpu_queues']['feedback_inflight'],1)
        self.assertTrue(any(f['kind']=='queue_full' for f in row['feedback']))
        self.assertEqual(row['feedback_ipv4_udp_bytes'],52)

    def test_invalid_feedback_parse_work_is_paid_before_timeout(self):
        clock=Clock();kwargs=services(clock);original=kwargs['transport_ops']
        class Invalid(original):
            @staticmethod
            def feedback_datagram(*args,**kw):
                data=original.feedback_datagram(*args,**kw)
                return data[:-1]+bytes([data[-1]^1])
        kwargs['transport_ops']=Invalid
        row=model.run(self.frames(1),{},self.config(),**factories(clock),**kwargs)
        self.drained(row)
        self.assertTrue(any(f['kind']=='parse_rejected' for f in row['feedback']))
        self.assertEqual(next(c for c in row['cpu_services'] if c['stage']=='feedback_parse')['service_ms'],5)
        self.assertEqual(row['packets'][0]['release_reason'],'ack_timeout')

    def test_box_latest_capture_is_finite_and_rejection_costs_remain_paid(self):
        clock=Clock()
        row=model.run(self.frames(60),{},self.config(frame_cap=1),**factories(clock,encode=80),**services(clock,resize=60))
        self.drained(row)
        self.assertGreater(row['drops_by_reason'].get('resize_latest_replaced',0),0)
        self.assertTrue(all(p['encode_service_ms']==80 for p in row['packets']))
        self.assertTrue(all(r['service_ms']==60 for r in row['resize_services']))
        self.assertFalse(row['cpu_services'])


if __name__=='__main__':unittest.main()
