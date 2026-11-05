from pathlib import Path
from contextlib import ExitStack
import hashlib,struct,unittest,zlib
from unittest import mock
import numpy as np
import receiver as r
h=r.h;HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def source():
 rows=h.load(SOURCE/'results.json')['cases'][0]['rows'];return[h.raw(x['packet'],SOURCE) for x in rows[:2]]
def outer_tag(packet):
 fields=list(r.envelope.HEADER.unpack_from(packet));fields[10]=bytes([fields[10][0]^1])+fields[10][1:];body=r.envelope.HEADER.pack(*fields)+packet[r.envelope.HEADER.size:-4];return body+struct.pack('<I',zlib.crc32(body))
def state(rx):return(rx.rid,rx.last,None if rx.ref is None else tuple(hashlib.sha256(x.tobytes()).hexdigest() for x in rx.ref),None if rx.hud is None else tuple(hashlib.sha256(p['words'].tobytes()).hexdigest() for p in rx.hud))
class Streaming(unittest.TestCase):
 def test_key_P_exact_and_no_array_decoder_or_reencode(self):
  rx=r.Receiver();packets=source()
  with ExitStack() as stack:
   stack.enter_context(mock.patch.object(h.block.frozen,'decode',side_effect=AssertionError('whole coeff decode')))
   stack.enter_context(mock.patch.object(h.m.base,'_decode_plane',side_effect=AssertionError('legacy coeff decode')))
   for packet in packets:
    out,patches,meta,_=rx.receive(packet);self.assertEqual(meta['decode_work']['full_coefficient_array_bytes'],0);self.assertEqual(meta['decode_work']['full_prediction_array_bytes'],0)
    for p in out:self.assertFalse(p.flags.writeable)
    for p in patches:self.assertFalse(p['words'].flags.writeable)
 def test_late_failure_atomic_and_retry_same_id(self):
  key,p=source();rx=r.Receiver();rx.receive(key);before=state(rx)
  with self.assertRaises(ValueError):rx.receive(outer_tag(p))
  self.assertEqual(before,state(rx));rx.receive(p);self.assertEqual(rx.last,1)
  before=state(rx)
  with self.assertRaises(ValueError):rx.receive(p)
  self.assertEqual(before,state(rx))
 def test_prediction_tile_halfpel_edges(self):
  rng=np.random.default_rng(48);ref=tuple(rng.integers(0,256,shape,dtype=np.int16) for shape in((480,720),(240,360),(240,360)))
  for bs in(16,32):
   for value in((-18,-17),(-3,1),(0,0),(4,8),(17,18)):
    vectors=np.empty(((480+bs-1)//bs,(720+bs-1)//bs,2),np.int8);vectors[:]=value;gold=h.m.predict(ref,vectors,bs)
    for axis,plane in enumerate(gold):
     bh,bw=plane.shape[0]//8,plane.shape[1]//8
     for by,bx in((0,0),(0,bw-1),(bh-1,0),(bh-1,bw-1),(2,3)):
      actual,fetches=r.prediction_tile(ref,vectors,bs,axis,by,bx);np.testing.assert_array_equal(actual,plane[by*8:by*8+8,bx*8:bx*8+8]);den=2 if axis==0 else 4;self.assertEqual(fetches,64*(1+bool(value[0]%den))*(1+bool(value[1]%den)))
 def test_crc_and_geometry_rejections(self):
  packet=source()[0]
  for malformed in(packet[:-1],packet+b'\0',packet[:90]+bytes([packet[90]^1])+packet[91:]):
   rx=r.Receiver();before=state(rx)
   with self.assertRaises(ValueError):rx.receive(malformed)
   self.assertEqual(before,state(rx))
 def test_inverse_shortcuts_and_complex(self):
  rng=np.random.default_rng(480)
  for kind in('zero','DC','complex'):
   a=np.zeros((8,8),np.int64)
   if kind=='DC':a[0,0]=-1234
   elif kind=='complex':a=rng.integers(-522240,522241,(8,8),dtype=np.int64)
   actual,got=r.inverse_tile(a);self.assertEqual(got,kind);np.testing.assert_array_equal(actual,h.m.ft.inverse(a))
if __name__=='__main__':unittest.main()
