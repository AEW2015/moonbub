import hashlib,json,struct,unittest
import numpy as np
import model

class InlineTests(unittest.TestCase):
    def planes(self,w=22,h=18):
        return [((np.arange(ph*pw).reshape(ph,pw)*13+pi*17)%256).astype(np.uint8) for pi,(ph,pw) in enumerate(((h,w),(h//2,w//2),(h//2,w//2)))]
    def feed(self,t,planes):
        for pi,p in enumerate(planes):
            for y in range(0,p.shape[0],8):
                for x in range(0,p.shape[1],8):t.push(pi,y,x,p[y:y+8,x:x+8])
    def expected(self,p):return model.trace.codec.reference_tag([x.astype(np.int16) for x in p])
    def test_partial_geometry_compact_expansion_and_publication_match(self):
        p=self.planes();t=model.StripeTagger(22,18);self.feed(t,p)
        self.assertEqual(t.finish(self.expected(p),packet_validated=True,allow_publication=True),self.expected(p))
        self.assertEqual(t.publication_tag,self.expected(p));self.assertEqual(t.canonical_bytes,4+2*sum(x.size for x in p))
        self.assertEqual(t.local_array_bytes,22*10)
    def test_no_tag_before_complete_explicit_finish(self):
        t=model.StripeTagger(22,18)
        with self.assertRaises(ValueError):t.tag
        with self.assertRaises(ValueError):t.publication_tag
        self.feed(t,self.planes())
        with self.assertRaises(ValueError):t.tag
    def test_ordinary_frame_has_private_tag_but_cannot_publish(self):
        p=self.planes();t=model.StripeTagger(22,18);self.feed(t,p);t.finish(self.expected(p),packet_validated=True,allow_publication=False)
        self.assertEqual(t.tag,self.expected(p))
        with self.assertRaises(ValueError):t.publication_tag
    def test_duplicate_reordered_and_wrong_plane_fail_closed(self):
        a=np.zeros((8,8),np.uint8)
        for args in ((0,0,0,a),(0,0,16,a),(1,0,8,a)):
            t=model.StripeTagger(32,16);t.push(0,0,0,a)
            with self.assertRaises(ValueError):t.push(*args)
            self.assertTrue(t.failed)
            with self.assertRaises(ValueError):t.tag
    def test_truncated_abort_and_wrong_tag_do_not_publish(self):
        p=self.planes()
        for action in ('truncated','abort','bad_tag','bad_crc'):
            t=model.StripeTagger(22,18)
            if action!='truncated':self.feed(t,p)
            if action=='abort':t.abort()
            expected=b'Z'*16 if action=='bad_tag' else self.expected(p)
            with self.assertRaises(ValueError):t.finish(expected,packet_validated=action!='bad_crc',allow_publication=True)
            with self.assertRaises(ValueError):t.publication_tag
    def test_dtype_and_cropped_shape_are_checked(self):
        for a in (np.zeros((8,8),np.int16),np.zeros((7,8),np.uint8)):
            t=model.StripeTagger(22,18)
            with self.assertRaises(ValueError):t.push(0,0,0,a)
    def test_stalled_input_does_not_hash_future_tiles(self):
        t=model.StripeTagger(22,18);p=self.planes();t.push(0,0,0,p[0][:8,:8]);before=(t.canonical_bytes,t.tiles,t.x)
        for _ in range(100):self.assertEqual((t.canonical_bytes,t.tiles,t.x),before)
        self.assertEqual(t.canonical_bytes,4)
    def test_extra_input_invalidates_private_candidate_not_a_new_publication(self):
        p=self.planes();t=model.StripeTagger(22,18);self.feed(t,p);t.finish(self.expected(p),packet_validated=True,allow_publication=True)
        with self.assertRaises(ValueError):t.push(0,0,0,p[0][:8,:8])
        with self.assertRaises(ValueError):t.publication_tag
    def test_corrupt_actual_ar03_rejected_before_tile_output(self):
        d=json.loads((model.HERE.parent/'python-game-ar03-trace-study/results.json').read_text());row=d['cohorts'][0]['rows'][0]
        b=model.fixture.raw(row['ar03']);calls=[]
        with self.assertRaises(ValueError):model.reconstruct(row,'bad',packet_override=b[:-1]+bytes([b[-1]^1]),hook=lambda *x:calls.append(x))
        self.assertFalse(calls)
    def test_abort_during_actual_generation_cannot_publish_partial_hash(self):
        d=json.loads((model.HERE.parent/'python-game-ar03-trace-study/results.json').read_text());cohort=d['cohorts'][-1];row=cohort['rows'][0]
        seen=[]
        def hook(t,*args):
            seen.append(t)
            if len(seen)==4:raise RuntimeError('injected downstream abort')
        with self.assertRaises(RuntimeError):model.reconstruct(row,cohort['name'],hook=hook)
        self.assertEqual(len(seen),4);self.assertTrue(seen[-1].failed)
        with self.assertRaises(ValueError):seen[-1].publication_tag
        with self.assertRaises(ValueError):seen[-1].tag
    def test_actual_partial_fixture_producer_and_export_roundtrip(self):
        d=json.loads((model.HERE.parent/'python-game-ar03-trace-study/results.json').read_text());cohort=d['cohorts'][-1];row=cohort['rows'][0]
        proof,data=model.reconstruct(row,cohort['name'])
        tag,t=model.replay_stream(data,bytes.fromhex(proof['private_tag_hex']),eligible=proof['published'])
        self.assertEqual(tag.hex(),proof['private_tag_hex']);self.assertEqual(t.tiles,proof['tiles'])
        for bad in (data[:-1],data+b'X'):
            with self.assertRaises(ValueError):model.replay_stream(bad,tag,eligible=proof['published'])
    def test_hash_backpressure_and_stripe_ownership_are_explicit(self):
        frame=json.loads((model.HERE.parent/'python-game-causal-stripe-study/results.json').read_text())['frames'][0];a=model.schedule(frame);b=model.schedule(frame,inline=model.InlineBudget(hash_MBps=.01))
        self.assertGreater(b['frame_done_ms'],a['frame_done_ms']);self.assertGreater(b['hash_backpressure_ms'],0)
        last={}
        for s in b['stripes']:
            if s['coefficient_slot'] in last:self.assertGreaterEqual(s['entropy_start_ms'],last[s['coefficient_slot']])
            last[s['coefficient_slot']]=s['done_ms']
        self.assertEqual(a['tag_bank_reread_bytes'],0)
        self.assertEqual(b['config']['tag_hash_MBps'],b['inline_config']['hash_MBps'])
    def test_inline_copy_can_lose_when_tag_bank_memory_is_fast(self):
        frame=json.loads((model.HERE.parent/'python-game-causal-stripe-study/results.json').read_text())['frames'][0]
        r=model.schedule(frame,model.v19.Budget(bytes_per_sample=1,effective_sdram_MBps=1000,memory_burst_overhead_ns=.01))
        self.assertGreater(r['frame_done_ms'],r['baseline_serial_frame_ms'])
    def test_sha_padding_service_delays_final_tag_permission(self):
        frame=json.loads((model.HERE.parent/'python-game-causal-stripe-study/results.json').read_text())['frames'][0]
        r=model.schedule(frame)
        self.assertEqual(r['sha256_compression_service_bytes']%64,0)
        self.assertGreaterEqual(r['sha256_compression_service_bytes'],r['canonical_bytes_hashed']+9)
        self.assertGreater(r['sha256_finalize_service_ms'],0)
        self.assertGreaterEqual(r['bank_publication_earliest_ms'],r['reference_tag_ready_ms'])
        self.assertEqual(r['reference_tag_ready_ms'],r['stripes'][-1]['hash_done_ms'])
    def test_service_configuration_rejects_invalid_budget(self):
        with self.assertRaises(ValueError):model.InlineBudget(hash_MBps=0).validate()
        with self.assertRaises(ValueError):model.InlineBudget(hash_state_planning_bytes=-1).validate()
if __name__=='__main__':unittest.main()
