"""Independent malformed/atomic/no-reencode receiver checks from retained wire."""
import copy,json,struct,unittest
import numpy as np
import verify as v

SOURCE=v.OLD

def inputs():
    rows=json.loads((SOURCE/'results.json').read_text())['cases'][0]['rows']
    return tuple(v.raw(r['packet'],SOURCE) for r in rows[:2])

def parts(packet):
    outer=list(v.adapter.HEADER.unpack_from(packet));inner=packet[v.adapter.HEADER.size:v.adapter.HEADER.size+outer[11]]
    fields=list(v.m.HEADER.unpack_from(inner));p=v.m.HEADER.size+fields[12]+fields[13];payloads=[]
    maps=inner[v.m.HEADER.size:p]
    for n in fields[14:17]:payloads.append(inner[p:p+n]);p+=n
    return outer,fields,maps,payloads,packet[v.adapter.HEADER.size+outer[11]:-4]

def rebuild(packet,*,outer_index=None,outer_value=None,inner_index=None,inner_value=None,payload_index=None,payload=None,hud=None):
    outer,fields,maps,payloads,overlay=parts(packet)
    if inner_index is not None:fields[inner_index]=inner_value
    if payload_index is not None:payloads[payload_index]=payload
    if hud is not None:overlay=hud
    fields[14:17]=map(len,payloads);inner=v.seal(v.m.HEADER.pack(*fields)+maps+b''.join(payloads))
    outer[11]=len(inner);outer[12]=len(overlay)
    if outer_index is not None:outer[outer_index]=outer_value
    return v.seal(v.adapter.HEADER.pack(*outer)+inner+overlay)

class DirectReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.direct=v.direct_module();cls.key,cls.pframe=inputs()
    def parse_rejected(self,packet):
        with self.assertRaises(ValueError),v.no_reencode():self.direct.parse(packet)
    def test_direct_without_entropy_reencode_matches_independent_adapter(self):
        converted,count=v.adapter.convert(self.key);expected=v.f.parse(converted)
        with v.no_reencode():
            parsed=self.direct.parse(self.key);rx=self.direct.Receiver();result=rx.receive(self.key)
        v.equal_meta(parsed,expected);v.equal_meta(result[2],expected)
        self.assertGreater(count,0);v.assert_no_new_encoder()
    def test_six_fractional_motion_legacy_dispatch_frames(self):
        folder=v.HERE.parent/'python-game-implicit-v37-study'
        cases=json.loads((folder/'results.json').read_text())['cases'];case=next(c for c in cases if c['kind']=='fractional_motion')
        rx,expected=self.direct.Receiver(),v.f.Receiver()
        for row in case['rows']:
            original=v.raw(row['packet'],folder);outer=list(v.adapter.HEADER.unpack_from(original))
            inner=original[v.adapter.HEADER.size:v.adapter.HEADER.size+outer[11]];fields=list(v.m.HEADER.unpack_from(inner));fields[0]=b'GS38'
            newinner=v.seal(v.m.HEADER.pack(*fields)+inner[v.m.HEADER.size:-4]);outer[0]=b'CS38';outer[8]=self.direct.PROFILE
            packet=v.seal(v.adapter.HEADER.pack(*outer)+newinner+original[v.adapter.HEADER.size+outer[11]:-4])
            a,hud,meta=expected.receive(original)
            with v.no_reencode():b,parts,newmeta,count=rx.receive(packet)
            v.equal_planes(a,b);v.equal_hud(hud,parts);v.equal_meta(meta,newmeta);self.assertEqual(count,0)
            self.assertTrue(all(d in(0,1,2,3,4)for d in newmeta['dispatch']))
    def test_no_reencode_guard_detects_the_old_adapter(self):
        with self.assertRaisesRegex(AssertionError,'re-encode forbidden'),v.no_reencode():v.adapter.convert(self.key)
    def test_outer_bounds_identity_crc_and_immutable_type(self):
        for data in (bytearray(self.key),b'',self.key[:-1],self.key+b'\0',self.key[:-1]+bytes([self.key[-1]^1])):
            with self.subTest(kind=type(data).__name__,n=len(data)):self.parse_rejected(data)
        for index,value in ((0,b'BAD!'),(1,2),(2,0),(3,26),(4,v.m.NO_REF),(5,0),(6,719),(7,479),(8,bytes(16)),(9,b'X'*16),(10,bytes(16))):
            with self.subTest(index=index):self.parse_rejected(v.outer_edit(self.key,index,value))
    def test_inner_binding_and_dispatch_failure(self):
        for index,value in ((0,b'BAD!'),(3,26),(4,1),(5,0),(6,718),(8,31)):
            with self.subTest(index=index):self.parse_rejected(rebuild(self.key,inner_index=index,inner_value=value))
        self.parse_rejected(rebuild(self.key,payload_index=0,payload=b'\x07'))
        self.parse_rejected(rebuild(self.key,payload_index=0,payload=b''))
    def test_arithmetic_nested_crc_and_geometry(self):
        _,_,_,payloads,_=parts(self.key)
        for i,payload in enumerate(payloads):
            if payload[0] in (5,6):
                corrupted=payload[:-1]+bytes([payload[-1]^1])
                self.parse_rejected(rebuild(self.key,payload_index=i,payload=corrupted))
                fields=list(v.adapter.decoder.FRAME.unpack_from(payload,1));fields[3]+=1
                changed=v.seal(v.adapter.decoder.FRAME.pack(*fields)+payload[1+v.adapter.decoder.FRAME.size:-4])
                self.parse_rejected(rebuild(self.key,payload_index=i,payload=payload[:1]+changed));return
        self.fail('fixture has no arithmetic plane')
    def test_nonzero_hidden_coefficients_rejected_before_reconstruction(self):
        safe=v.f.f.safe_blocks()[0].reshape(-1);coeff=np.zeros((len(safe),8,8),np.int16)
        coeff[np.flatnonzero(safe)[0],0,0]=1
        entropy=v.f.f.frozen.shared.entropy
        plan=entropy._plane_plan(coeff,90,v.m);encoded,*_=entropy._construct(coeff,90,plan,v.m)
        self.parse_rejected(rebuild(self.key,payload_index=0,payload=encoded))
    def test_late_output_hud_and_replay_failures_leave_committed_reference(self):
        rx=self.direct.Receiver()
        with v.no_reencode():rx.receive(self.key)
        # Correctly sealed outer packet with late reconstruction identity mismatch.
        v.assert_rejected_atomically(rx,v.outer_edit(self.pframe,10,b'Q'*16))
        # Correct outer/inner identity, damaged separately CRC-protected HUD.
        *_,hud=parts(self.pframe)
        v.assert_rejected_atomically(rx,rebuild(self.pframe,hud=hud[:-1]+bytes([hud[-1]^1])))
        # Inner pre-normalization identity is checked separately.
        v.assert_rejected_atomically(rx,rebuild(self.pframe,inner_index=11,inner_value=b'R'*16))
        v.assert_rejected_atomically(rx,v.outer_edit(self.pframe,9,b'Z'*16))
        v.assert_rejected_atomically(rx,rebuild(self.pframe,outer_index=9,outer_value=b'Z'*16,inner_index=10,inner_value=b'Z'*16))
        with v.no_reencode():rx.receive(self.pframe)
        v.assert_rejected_atomically(rx,self.pframe)
        self.assertEqual(rx.rid,1);self.assertEqual(rx.last,1)
    def test_paired_whole_receive_timing_domain_and_order(self):
        row=dict(id=0,paired_timing_ms={'adapter':[3.,2.,4.],'direct':[2.,1.,3.]},paired_median_ms={'adapter':3.,'direct':2.},paired_order=[['adapter','direct'],['direct','adapter'],['adapter','direct']])
        v.paired_timings(row)
        v.check_timing_summary(dict(mean_paired_median_ms={'adapter':3.,'direct':2.},direct_to_adapter_ratio=2/3),[row])
        for field,value in [('samples',[0.,1.,2.]),('samples',[True,1.,2.]),('samples',[float('nan'),1.,2.]),('median',2.5),('order',[['adapter','direct']]*3)]:
            bad=copy.deepcopy(row)
            if field=='samples':bad['paired_timing_ms']['direct']=value
            elif field=='median':bad['paired_median_ms']['direct']=value
            else:bad['paired_order']=value
            with self.subTest(field=field),self.assertRaises(AssertionError):v.paired_timings(bad)
    def test_failed_first_key_does_not_publish_partial_state(self):
        rx=self.direct.Receiver()
        v.assert_rejected_atomically(rx,v.outer_edit(self.key,10,b'F'*16))
        self.assertIsNone(rx.ref);self.assertIsNone(rx.hud)
        with v.no_reencode():rx.receive(self.key)
        self.assertEqual(rx.rid,0)

if __name__=='__main__':unittest.main()
