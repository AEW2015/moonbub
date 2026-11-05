"""Producer ownership, actual no-encode behavior, and legacy receive checks."""
import contextlib,json,struct,sys,unittest,zlib
from unittest.mock import patch
import numpy as np
import helpers as h
import receiver as r

def inputs():
    folder=h.HERE.parent/h.FOLDERS[0];rows=h.load(folder/'results.json')['cases'][0]['rows']
    return tuple(h.raw(row['packet'],folder)for row in rows[:2])

@contextlib.contextmanager
def no_encode():
    targets={id(v):v for v in list(sys.modules.values())if hasattr(v,'_plane_plan')and hasattr(v,'_construct')}
    retained=h.f.f.frozen.shared.entropy;targets[id(retained)]=retained
    with contextlib.ExitStack()as stack:
        for value in targets.values():
            for name in('_plane_plan','_construct'):
                stack.enter_context(patch.object(value,name,side_effect=AssertionError('forbidden entropy encode')))
        yield

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def adapt_old(packet):
    outer=list(h.f.HEADER.unpack_from(packet));inner=packet[h.f.HEADER.size:h.f.HEADER.size+outer[11]]
    fields=list(h.m.HEADER.unpack_from(inner));fields[0]=b'GS38'
    inner=seal(h.m.HEADER.pack(*fields)+inner[h.m.HEADER.size:-4])
    outer[0]=b'CS38';outer[8]=r.PROFILE
    return seal(h.f.HEADER.pack(*outer)+inner+packet[h.f.HEADER.size+outer[11]:-4])

class DirectTests(unittest.TestCase):
    def test_key_and_P_receive_without_encode_and_guard_detects_old_adapter(self):
        packets=inputs();old=h.adapter.Receiver();new=r.Receiver()
        for packet in packets:
            expected=old.receive(packet)
            with no_encode():got=new.receive(packet)
            for a,b in zip(got[0],expected[0],strict=True):np.testing.assert_array_equal(a,b)
            for a,b in zip(got[1],expected[1],strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            for name in('qmap','vectors'):np.testing.assert_array_equal(got[2][name],expected[2][name])
            self.assertEqual(got[3],expected[3]);self.assertEqual(got[2]['decode_work']['entropy_construct_calls'],0)
        with self.assertRaisesRegex(AssertionError,'forbidden entropy encode'),no_encode():old.receive(packets[0])
    def test_owned_readonly_coefficients_and_committed_arrays_do_not_alias_history(self):
        key,pframe=inputs();rx=r.Receiver();first=rx.receive(key);before=tuple(a.copy()for a in rx.ref);oldref=rx.ref;oldhud=rx.hud
        for a in(*first[0],*first[2]['coefficients'],first[2]['qmap'],first[2]['vectors'],*(p['words']for p in first[1])):
            self.assertFalse(a.flags.writeable)
            with self.assertRaises(ValueError):a.flat[0]=0
        second=rx.receive(pframe)
        for a,b,saved in zip(oldref,rx.ref,before,strict=True):
            self.assertFalse(np.shares_memory(a,b));np.testing.assert_array_equal(a,saved)
        for a,b in zip(oldhud,rx.hud,strict=True):self.assertFalse(np.shares_memory(a['words'],b['words']))
        self.assertIs(second[0],rx.ref)
    def test_direct_legacy_dispatch_zero_dense_and_split_payloads(self):
        packet=inputs()[0];outer=list(r.HEADER.unpack_from(packet));inner=packet[r.HEADER.size:r.HEADER.size+outer[11]]
        fields=list(h.m.HEADER.unpack_from(inner));end=h.m.HEADER.size+fields[12]+fields[13];maps=inner[h.m.HEADER.size:end]
        overlay=packet[r.HEADER.size+outer[11]:-4];safe=h.f.f.safe_blocks()[0].reshape(-1)
        nonzero=np.zeros((len(safe),8,8),np.int16);nonzero[np.flatnonzero(~safe)[0],0,0]=2
        for mode in(0,1,2):
            coeff=np.zeros_like(nonzero)if mode==2 else nonzero
            plan=dict(kind={0:'dense',1:'split',2:'zero'}[mode]);payload=h.m.build_legacy(coeff,90,plan)[0]
            self.assertEqual(payload[0],mode)
            payloads=[payload,b'\x02',b'\x02'];fields[14:17]=map(len,payloads)
            inside=seal(h.m.HEADER.pack(*fields)+maps+b''.join(payloads));outer[11]=len(inside)
            candidate=seal(r.HEADER.pack(*outer)+inside+overlay)
            with no_encode():meta=r.parse(candidate)
            np.testing.assert_array_equal(meta['coefficients'][0],coeff)
            self.assertEqual(meta['dispatch'],[mode,2,2]);self.assertEqual(meta['binary_planes'],0)

    def test_CS37_legacy_payloads_and_fractional_motion_dispatch_unchanged(self):
        folder=h.HERE.parent/'python-game-implicit-v37-study';data=h.load(folder/'results.json');rows=data['cases'][2]['rows']
        old=h.f.Receiver();new=r.Receiver();dispatch=set();vectors=[]
        for row in rows:
            packet=h.raw(row['packet'],folder);expected=old.receive(packet)
            with no_encode():actual=new.receive(adapt_old(packet))
            self.assertEqual(actual[3],0);dispatch.update(actual[2]['dispatch']);vectors.append(actual[2]['vectors'])
            for a,b in zip(actual[0],expected[0],strict=True):np.testing.assert_array_equal(a,b)
        self.assertTrue(dispatch.issubset(set(range(5))));self.assertTrue(any(np.any(v%2)for v in vectors))

if __name__=='__main__':unittest.main()
