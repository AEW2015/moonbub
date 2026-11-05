"""Negotiation, one actual canonical hash, late-failure atomicity and fault scope."""
import json,unittest
import numpy as np
import verify as v

class CanonicalTagProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=v.HERE.parent/'python-game-binary-v38-study';rows=json.loads((folder/'results.json').read_text())['cases'][0]['rows'][:3]
        rx=v.helper.oldrx.Receiver();cls.old=[];cls.outputs=[];cls.meta=[];cls.wires={p:[]for p in v.PROFILES}
        for row in rows:
            packet=v.raw(row['packet'],folder);reference=rx.ref;out,hud,meta,count=rx.receive(packet);cls.old.append(packet);cls.outputs.append(out);cls.meta.append(meta)
            for profile in v.PROFILES:cls.wires[profile].append(v.expected_wire(packet,profile,reference,out)[0])
    def test_one_output_hash_each_key_P_and_readonly_cached_tag(self):
        for profile in v.PROFILES:
            rx=v.subject.Receiver(profile)
            for fid,packet in enumerate(self.wires[profile]):
                with v.counted()as(calls,legacy):out,hud,meta,count=rx.receive(packet)
                self.assertEqual(len(calls),1);self.assertIs(calls[0][0],out);self.assertEqual(calls[0][1],profile)
                self.assertEqual(len(legacy),int(profile=='CS66'));self.assertEqual(rx.cached_tag,v.tag(out,profile));self.assertEqual(rx.rid,fid)
                for plane in out:self.assertFalse(plane.flags.writeable)
                with self.assertRaises(ValueError):out[0][0,0]=0
                with self.assertRaises(AttributeError):rx.cached_tag=b'x'*16
                with self.assertRaises(AttributeError):rx.profile='CS38'
    def test_explicit_profile_rejects_old_and_cross_profile(self):
        for profile in v.PROFILES:
            v.reject(v.subject.Receiver(profile),self.old[0],calls=0)
            cross='CU66'if profile=='CS66'else'CS66';v.reject(v.subject.Receiver(profile),self.wires[cross][0],calls=0)
        with self.assertRaises(ValueError):v.subject.Receiver('CS38')
    def test_crc_reference_id_tag_replay_and_output_failure_are_atomic(self):
        for profile in v.PROFILES:
            rx=v.subject.Receiver(profile);rx.receive(self.wires[profile][0]);p=self.wires[profile][1]
            v.reject(rx,p[:-1]+bytes([p[-1]^1]),calls=0)
            v.reject(rx,self.wires[profile][2],calls=0) # missing frame1, actual committed rid is0
            v.reject(rx,v.rebuild(p,outer_changes={9:b'R'*16},inner_changes={10:b'R'*16}),calls=0)
            v.reject(rx,v.rebuild(p,outer_changes={10:b'O'*16}),calls=1)
            rx.receive(p);v.reject(rx,p,calls=0)
    def test_structurally_valid_late_HUD_tag_failure_cannot_publish_cache(self):
        for profile in v.PROFILES:
            rx=v.subject.Receiver(profile);rx.receive(self.wires[profile][0]);bad=v.corrupt_late_HUD(self.wires[profile][1])
            meta=v.subject.parse(bad,profile);self.assertEqual(meta['frame_id'],1)
            calls,legacy=v.reject(rx,bad,calls=1);self.assertEqual(legacy,int(profile=='CS66'))
            rx.receive(self.wires[profile][1]);self.assertEqual(rx.last,1)
    def test_visible_privileged_memory_fault_affecting_output_fails_canonical_hash(self):
        safe=np.repeat(np.repeat(v.f.f.safe_blocks()[0],8,0),8,1)
        locations=np.argwhere((self.outputs[1][0]>8)&(self.outputs[1][0]<247)&~safe);y,x=map(int,locations[len(locations)//2])
        self.assertFalse(np.any(self.meta[1]['vectors']))
        for profile in v.PROFILES:
            rx=v.subject.Receiver(profile);rx.receive(self.wires[profile][0]);fault=[p.copy()for p in rx.ref]
            fault[0][y,x]+=1 if fault[0][y,x]<255 else -1
            for p in fault:p.setflags(write=False)
            rx.ref=tuple(fault) # privileged test injection, not a supported update or ECC model
            prediction=v.m.predict(rx.ref,self.meta[1]['vectors'],self.meta[1]['block_size'])
            reconstructed=v.m.gm.reconstruct(self.meta[1]['coefficients'],prediction,self.meta[1]['qmap'],720,480);normalized=v.f.f.normalize(reconstructed)
            self.assertNotEqual(int(normalized[0][y,x]),int(self.outputs[1][0][y,x]))
            v.reject(rx,self.wires[profile][1],calls=1)
    def test_hidden_fault_may_be_normalized_away_so_this_is_not_ECC(self):
        y,x=map(int,np.argwhere(np.repeat(np.repeat(v.f.f.safe_blocks()[0],8,0),8,1))[0])
        for profile in v.PROFILES:
            rx=v.subject.Receiver(profile);rx.receive(self.wires[profile][0]);bad=[p.copy()for p in rx.ref];bad[0][y,x]=0
            for p in bad:p.setflags(write=False)
            rx.ref=tuple(bad)
            with v.counted()as(calls,legacy):out,*_=rx.receive(self.wires[profile][1])
            self.assertEqual(len(calls),1);v.oldproof.equal_planes(out,self.outputs[1])
    def test_uint8_domain_validation_precedes_narrowing(self):
        good=self.outputs[0];self.assertEqual(v.subject.wire.tag_u8(good),v.tag(good,'CU66'))
        for dtype,value in((np.int16,-1),(np.uint16,256),(np.uint64,2**64-1)):
            planes=[p.astype(dtype)for p in good];planes[0][0,0]=value
            with self.subTest(dtype=dtype),self.assertRaises(ValueError):v.subject.wire.tag_u8(tuple(planes))
        for planes in(tuple(p.astype(float)for p in good),tuple(p.astype(bool)for p in good),(good[0][:-1],good[1],good[2])):
            with self.assertRaises(ValueError):v.subject.wire.tag_u8(planes)
    def test_wire_size_and_hash_budget_scope(self):
        for profile in v.PROFILES:
            for old,new in zip(self.old,self.wires[profile],strict=True):self.assertEqual(len(old)-len(new),16)
        self.assertEqual(v.INNER.size,v.m.HEADER.size-16)
        self.assertEqual(v.demand(2,1)['padded_SHA256_blocks_per_tag'],16201);self.assertEqual(v.demand(1,1)['padded_SHA256_blocks_per_tag'],8101)
        self.assertEqual(v.demand(2,1)['total_round_cycles'],1036864)

if __name__=='__main__':unittest.main()
