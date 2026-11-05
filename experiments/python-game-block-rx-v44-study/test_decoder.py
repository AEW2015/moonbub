import importlib.util,sys,unittest,zlib,struct
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
import decoder as new
spec=importlib.util.spec_from_file_location('blockrx44_test_encoder',HERE.parent/'python-game-binary-v38-study/model.py');enc=importlib.util.module_from_spec(spec);sys.modules[spec.name]=enc;spec.loader.exec_module(enc)
class TestTiles(unittest.TestCase):
 def same(self,a,bw):
  packet,_=enc.encode(a,bw);reader=new.TileReader(packet,len(a),bw);tiles=list(reader);self.assertTrue(reader.finished);np.testing.assert_array_equal(np.stack(tiles),a);np.testing.assert_array_equal(np.stack(tiles),new.frozen.decode(packet,len(a),bw));self.assertFalse(reader.logical_workspace()['full_coefficient_frame_staged'])
 def test_zero_and_sparse_boundary_runs(self):
  for n,bw in((1,1),(12,4),(99,3)):
   a=np.zeros((n,8,8),np.int16);self.same(a,bw);a[-1,7,7]=-2048;a[0,0,0]=2048;a[-1,0,0]=-2048;self.same(a,bw)
 def test_dense_raw_and_owned_tiles(self):
  rng=np.random.default_rng(44);a=rng.integers(-2048,2049,(20,8,8),dtype=np.int16);packet,_=enc.encode(a,5);r=new.TileReader(packet,20,5);first=next(r);snapshot=first.copy();rest=list(r);np.testing.assert_array_equal(first,snapshot);np.testing.assert_array_equal(np.stack([first,*rest]),a)
 def test_row_reset_and_all_bands(self):
  a=np.zeros((24,8,8),np.int16)
  for i in range(24):a[i,0,0]=1000 if i%6==0 else -1000;a[i,(i//8)%8,i%8]=i-12
  self.same(a,6)
 def test_malformed_fails_no_success_state(self):
  a=np.zeros((4,8,8),np.int16);packet,_=enc.encode(a,2)
  for bad in(packet[:-1],packet+b'\0',packet[:7]+bytes([packet[7]^1])+packet[8:]):
   with self.assertRaises(ValueError):new.TileReader(bad,4,2)
 def test_raw_late_error_poisoned(self):
  H=new.frozen.FRAME;a=np.zeros((2,8,8),'<i2');a[1,7,7]=3000;body=H.pack(b'AB38',1,1,2,2,0,256,0,0,0,0,0,0)+a.tobytes();packet=body+struct.pack('<I',zlib.crc32(body));r=new.TileReader(packet,2,2);next(r)
  with self.assertRaises(ValueError):next(r)
  self.assertFalse(r.finished)
  with self.assertRaises(ValueError):next(r)
 def test_geometry_domains(self):
  for n,bw in((0,1),(4,3),(True,1),(2,257)):
   with self.assertRaises(ValueError):new.TileReader(b'',n,bw)
if __name__=='__main__':unittest.main()
