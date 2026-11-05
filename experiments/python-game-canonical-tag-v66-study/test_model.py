"""Negotiated profiles, one actual hash, atomic state and visible-bank faults."""
import hashlib,struct,unittest
from unittest.mock import patch
import numpy as np
import helpers as h
r=h.bound('canonical66_owned_receiver_tests',h.HERE/'receiver.py',h)
w=h.bound('canonical66_owned_protocol_tests',h.HERE/'protocol.py',h)

def fixtures(profile):
    folder=h.HERE.parent/h.FOLDERS[0];rows=h.load(folder/'results.json')['cases'][0]['rows'][:3];old=h.oldrx.Receiver();packets=[];outputs=[];sources=[]
    for row in rows:
        source=h.raw(row['packet'],folder);reference=old.ref;out=old.receive(source)
        packet,evidence=w.convert(source,profile,reference=reference if not out[2]['key']else None,normalized=out[0]);packets.append(packet);outputs.append(out);sources.append(source)
    return sources,packets,outputs

def edit(packet,*,outer_edits=(),inner_edits=(),hud=None):
    outer=list(w.OUTER.unpack_from(packet));inside=packet[w.OUTER.size:w.OUTER.size+outer[11]];fields=list(w.INNER.unpack_from(inside))
    for index,value in inner_edits:fields[index]=value
    inner=w.seal(w.INNER.pack(*fields)+inside[w.INNER.size:-4]);overlay=packet[w.OUTER.size+outer[11]:-4]if hud is None else hud
    for index,value in outer_edits:outer[index]=value
    outer[11]=len(inner);outer[12]=len(overlay);return w.seal(w.OUTER.pack(*outer)+inner+overlay)

def snapshot(rx):
    return (rx.ref,rx.rid,rx.hud,rx.last,rx.cached_tag,tuple(a.copy()for a in rx.ref)if rx.ref is not None else None)
def unchanged(rx,before):
    assert rx.ref is before[0]and rx.rid==before[1]and rx.hud is before[2]and rx.last==before[3]and rx.cached_tag==before[4]
    if rx.ref is not None:
        for a,b in zip(rx.ref,before[5],strict=True):np.testing.assert_array_equal(a,b)

class CanonicalTagTests(unittest.TestCase):
    def test_wire_removes_only16B_and_profiles_require_explicit_choice(self):
        self.assertEqual(w.INNER.size,60);self.assertEqual(h.m.HEADER.size,76)
        for profile in w.PROFILES:
            sources,packets,out=fixtures(profile)
            for source,packet in zip(sources,packets,strict=True):
                self.assertEqual(len(packet),len(source)-16);meta=r.parse(packet,profile);self.assertNotIn('base_tag',meta);self.assertEqual(meta['profile'],profile)
                a=w.OUTER.unpack_from(source);b=w.OUTER.unpack_from(packet)
                self.assertEqual(source[w.OUTER.size+h.m.HEADER.size:w.OUTER.size+a[11]-4],packet[w.OUTER.size+w.INNER.size:w.OUTER.size+b[11]-4])
                self.assertEqual(source[w.OUTER.size+a[11]:-4],packet[w.OUTER.size+b[11]:-4])
                with self.assertRaises(ValueError):r.parse(source,profile)
                with self.assertRaises(ValueError):h.oldrx.parse(packet)
                with self.assertRaises(ValueError):r.parse(packet,'CU66'if profile=='CS66'else'CS66')
    def test_key_and_P_have_one_actual_canonical_hash_and_cached_reference(self):
        for profile in w.PROFILES:
            sources,packets,expected=fixtures(profile);rx=r.Receiver(profile)
            for packet,want in zip(packets,expected,strict=True):
                original=h.m.C.reference_tag
                with patch.object(r,'canonical_tag',wraps=r.canonical_tag)as boundary,patch.object(h.m.C,'reference_tag',wraps=original)as low:
                    got=rx.receive(packet);self.assertEqual(boundary.call_count,1);self.assertEqual(low.call_count,1 if profile=='CS66'else 0)
                for a,b in zip(got[0],want[0],strict=True):np.testing.assert_array_equal(a,b)
                self.assertEqual(rx.cached_tag,got[2]['output_tag']);self.assertIsInstance(rx.cached_tag,bytes)
            old=h.oldrx.Receiver()
            for i,packet in enumerate(sources[:2]):
                with patch.object(h.m.C,'reference_tag',wraps=h.m.C.reference_tag)as spy:old.receive(packet);self.assertEqual(spy.call_count,2 if i==0 else 3)
    def test_packed_domain_validates_without_truncation(self):
        planes=tuple(np.zeros(s,np.int16)for s in((480,720),(240,360),(240,360)))
        self.assertEqual(w.tag_u8(planes),hashlib.sha256(struct.pack('<HH',720,480)+bytes(518400)).digest()[:16])
        for dtype,value in((np.int16,-1),(np.int16,256),(np.uint64,2**64-1),(np.float64,1.0)):
            bad=list(planes);bad[0]=np.zeros((480,720),dtype);bad[0][0,0]=value
            with self.assertRaises(ValueError):w.tag_u8(tuple(bad))
        with self.assertRaises(ValueError):w.tag_u8((np.zeros((479,720),np.uint8),*planes[1:]))
    def test_wrong_references_output_CRC_lateHUD_and_replay_are_atomic(self):
        for profile in w.PROFILES:
            _,packets,_=fixtures(profile);rx=r.Receiver(profile);rx.receive(packets[0]);before=snapshot(rx)
            with self.assertRaises(ValueError),patch.object(r,'canonical_tag',wraps=r.canonical_tag)as missing:rx.receive(packets[2])
            self.assertEqual(missing.call_count,0);unchanged(rx,before)
            badref=edit(packets[1],outer_edits=((9,b'R'*16),),inner_edits=((10,b'R'*16),))
            with self.assertRaises(ValueError),patch.object(r,'canonical_tag',wraps=r.canonical_tag)as spy:rx.receive(badref)
            self.assertEqual(spy.call_count,0);unchanged(rx,before)
            badoutput=edit(packets[1],outer_edits=((10,b'Q'*16),))
            with self.assertRaises(ValueError):rx.receive(badoutput)
            unchanged(rx,before)
            outer=w.OUTER.unpack_from(packets[1]);hud=packets[1][w.OUTER.size+outer[11]:-4];p=h.f.f.hud.p;fields=list(p.HUD.unpack_from(hud));fields[9]=b'Z'*16
            badhud=p.seal(p.HUD.pack(*fields)+hud[p.HUD.size:-4])
            with self.assertRaises(ValueError),patch.object(r,'canonical_tag',wraps=r.canonical_tag)as spy:rx.receive(edit(packets[1],hud=badhud))
            self.assertEqual(spy.call_count,1);unchanged(rx,before)
            corrupted=packets[1][:-1]+bytes([packets[1][-1]^1])
            with self.assertRaises(ValueError):rx.receive(corrupted)
            unchanged(rx,before);rx.receive(packets[1]);before=snapshot(rx)
            with self.assertRaises(ValueError):rx.receive(edit(packets[2],outer_edits=((5,0),),inner_edits=((5,0),)))
            unchanged(rx,before)
            with self.assertRaises(ValueError):rx.receive(packets[1])
            unchanged(rx,before)
    def test_owned_readonly_outputs_and_cached_tag_have_no_mutable_alias(self):
        for profile in w.PROFILES:
            _,packets,_=fixtures(profile);rx=r.Receiver(profile);out=rx.receive(packets[0]);tag=rx.cached_tag
            for a in(*out[0],*out[2]['coefficients'],out[2]['qmap'],out[2]['vectors'],*(p['words']for p in out[1])):self.assertFalse(a.flags.writeable)
            copied=bytearray(tag);copied[0]^=1;out[2]['output_tag']=b'X'*16;self.assertEqual(rx.cached_tag,tag)
            with self.assertRaises(AttributeError):rx.cached_tag=b'Z'*16
            with self.assertRaises(AttributeError):rx.profile='CS66'
            oldref=rx.ref;rx.receive(packets[1])
            for a,b in zip(oldref,rx.ref,strict=True):self.assertFalse(np.shares_memory(a,b))
    def test_privileged_visible_DDR_fault_detected_when_output_changes_and_key_recovers(self):
        for profile in w.PROFILES:
            _,packets,expected=fixtures(profile);rx=r.Receiver(profile);rx.receive(packets[0]);mask=h.f.f.safe_blocks()[0].repeat(8,0).repeat(8,1)
            visible=np.zeros((480,720),bool);visible[37:442]=True
            for xx,yy,ww,hh in h.f.f.n.RECTS:visible[yy:yy+hh,xx:xx+ww]=False
            valid=visible&(~mask)&(expected[1][0][0]>1)&(expected[1][0][0]<254)&(rx.ref[0]<255)
            y,x=np.argwhere(valid)[0];rx.ref[0].setflags(write=True);rx.ref[0][y,x]+=1;rx.ref[0].setflags(write=False);before=snapshot(rx)
            with self.assertRaisesRegex(ValueError,'canonical normalized'):rx.receive(packets[1])
            unchanged(rx,before)
            folder=h.HERE.parent/h.FOLDERS[1];row=h.load(folder/'results.json')['cases'][0]['rows'][24];oldpacket=h.raw(row['packet'],folder);old=h.oldrx.Receiver();out=old.receive(oldpacket)
            key,evidence=w.convert(oldpacket,profile,reference=None,normalized=out[0]);rx.receive(key);self.assertEqual(rx.rid,24)
            for a,b in zip(rx.ref,out[0],strict=True):np.testing.assert_array_equal(a,b)
    def test_hash_round_budget_is_explicit_assumption(self):
        a=w.hash_demand(2,3);b=w.hash_demand(2,1);c=w.hash_demand(1,1)
        self.assertEqual((a['preimage_bytes_per_tag'],a['padded_SHA256_blocks_per_tag']),(1036804,16201))
        self.assertEqual((c['preimage_bytes_per_tag'],c['padded_SHA256_blocks_per_tag']),(518404,8101))
        self.assertEqual(a['total_round_cycles'],3110592);self.assertEqual(b['total_round_cycles'],1036864);self.assertEqual(c['total_round_cycles'],518464)
        self.assertFalse(c['physical_timing_or_RTL_fit_proven'])

if __name__=='__main__':unittest.main()
