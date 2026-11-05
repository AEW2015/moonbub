from pathlib import Path
from contextlib import ExitStack
import importlib.util,sys,struct,unittest,zlib
from unittest import mock
import numpy as np
import receiver as subject
h=subject.h;HERE=Path(__file__).resolve().parent
class Independent(unittest.TestCase):
 def test_explicit_legacy_capability_rejection(self):
  folder=HERE.parent/'python-game-implicit-v37-study';d=h.load(folder/'results.json');c=next(c for c in d['cases'] if c['kind']=='main');packet=h.raw(c['rows'][0]['packet'],folder);O=subject.envelope.HEADER;fields=list(O.unpack_from(packet));inner=packet[O.size:O.size+fields[11]];base=list(h.m.HEADER.unpack_from(inner));base[0]=b'GS38';body=h.m.HEADER.pack(*base)+inner[h.m.HEADER.size:-4];newinner=body+struct.pack('<I',zlib.crc32(body));fields[0]=b'CS38';fields[8]=subject.envelope.PROFILE;fields[11]=len(newinner);body=O.pack(*fields)+newinner+packet[O.size+len(inner):-4];wire=body+struct.pack('<I',zlib.crc32(body))
  previous=sys.modules.get('helpers')
  try:sys.modules['helpers']=h.old;old=h.module('stream48_test_full43_capability',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
  finally:
   if previous is None:sys.modules.pop('helpers',None)
   else:sys.modules['helpers']=previous
  old.Receiver().receive(wire)
  with self.assertRaisesRegex(ValueError,'arithmetic-only'):subject.Receiver().receive(wire)
 def test_no_plane_reconstruction_or_full_prediction_call(self):
  d=h.load(HERE.parent/'python-game-binary-qual-v40-study/results.json');rows=d['cases'][0]['rows'];rx=subject.Receiver()
  with ExitStack() as stack:
   stack.enter_context(mock.patch.object(h.m.gm,'reconstruct',side_effect=AssertionError('full-plane inverse')))
   stack.enter_context(mock.patch.object(h.m,'predict',side_effect=AssertionError('full-plane prediction')))
   for row in rows[:2]:rx.receive(h.raw(row['packet'],HERE.parent/'python-game-binary-qual-v40-study'))
 def test_table_lookup_matches_all_legal_maps(self):
  for scale in(8,16,32):
   q=np.full((30,45),scale,np.uint8)
   for axis in(0,1,2):
    all_tables=h.m.roi.block_tables(q,720,480,axis)
    for index in(0,len(all_tables)//2,len(all_tables)-1):np.testing.assert_array_equal(subject.TABLES[(0 if axis==0 else 1,scale)],all_tables[index])
if __name__=='__main__':unittest.main()
