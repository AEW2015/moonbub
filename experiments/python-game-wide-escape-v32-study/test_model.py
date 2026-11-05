import struct,unittest,zlib
import numpy as np
import model as m

def repair(p):
 p=bytearray(p);struct.pack_into('<I',p,12,zlib.crc32(p[:12]+p[16:])&0xffffffff);return bytes(p)
class EscapeTests(unittest.TestCase):
 def fixture(self):
  a=np.zeros((3,4,2),np.int8);a[0,1]=(-68,67);a[2,2]=(19,-18);return a
 def test_roundtrip_extremes_and_narrow(self):
  for a in [self.fixture(),np.full((15,23,2),18,np.int8),np.zeros((15,23,2),np.int8)]:np.testing.assert_array_equal(m.unpack(m.pack(a)),a)
 def test_crc_truncation_and_trailing(self):
  p=m.pack(self.fixture());bad=bytearray(p);bad[-1]^=1
  for a in [bytes(bad),p[:-1],p+b'\0',p[:15]]:
   with self.assertRaises(ValueError):m.unpack(a)
 def test_duplicate_reorder_index_and_vector_bounds(self):
  p=m.pack(self.fixture());nb=m.HEADER.unpack_from(p)[3];start=16+nb
  cases=[]
  q=bytearray(p);q[start+4:start+6]=q[start:start+2];cases.append(q)
  q=bytearray(p);q[start:start+4],q[start+4:start+8]=q[start+4:start+8],q[start:start+4];cases.append(q)
  q=bytearray(p);struct.pack_into('<H',q,start,12);cases.append(q)
  q=bytearray(p);struct.pack_into('<b',q,start+2,69);cases.append(q)
  q=bytearray(p);struct.pack_into('<bb',q,start+2,18,18);cases.append(q)
  for q in cases:
   with self.assertRaises(ValueError):m.unpack(repair(q))
 def test_escape_base_nonzero_and_encode_invalid(self):
  a=self.fixture();p=m.pack(a);head=list(m.HEADER.unpack_from(p));base=np.zeros_like(a);base[0,1]=(1,0);narrow=m.frozen.pack_vectors(base);entries=p[16+head[3]:];head[3]=len(narrow);q=m.HEADER.pack(*head)+narrow+entries
  with self.assertRaises(ValueError):m.unpack(repair(q))
  a[0,1]=(69,0)
  with self.assertRaises(ValueError):m.pack(a)
  with self.assertRaises(ValueError):m.pack(np.zeros((15,23,2),np.int16))
class CompletenessTests(unittest.TestCase):
 def fixture(self):
  import json
  from pathlib import Path
  import importlib.util,sys
  spec=importlib.util.spec_from_file_location('escape32_completeness_verifier',Path(__file__).resolve().parent/'verify.py')
  v=importlib.util.module_from_spec(spec);sys.modules[spec.name]=v;spec.loader.exec_module(v)
  return v,json.loads((v.HERE/'results.json').read_text()),json.loads((v.b.OLD/'results.json').read_text())
 def test_exact_scope_accepts(self):
  v,data,old=self.fixture();self.assertTrue(v.check_completeness(data,old))
 def test_rejects_missing_extra_reordered_cases_and_rows(self):
  import copy
  v,data,old=self.fixture()
  for target in ('current','original'):
   for change in ('missing_scene','extra_scene','scene_order','missing_row','extra_row','row_order','row_id'):
    d,o=copy.deepcopy(data),copy.deepcopy(old);doc=d if target=='current' else o
    if change=='missing_scene':doc['cases'].pop()
    elif change=='extra_scene':doc['cases'].append(copy.deepcopy(doc['cases'][0]))
    elif change=='scene_order':doc['cases'].reverse()
    elif change=='missing_row':doc['cases'][0]['rows'].pop()
    elif change=='extra_row':doc['cases'][0]['rows'].append(copy.deepcopy(doc['cases'][0]['rows'][0]))
    elif change=='row_order':doc['cases'][0]['rows'].reverse()
    else:doc['cases'][0]['rows'][0]['id']=99
    with self.subTest(target=target,change=change),self.assertRaises(ValueError):v.check_completeness(d,o)
 def test_rejects_alignment_and_summary(self):
  import copy
  v,data,old=self.fixture()
  for change in ('key','vectors','frames'):
   d=copy.deepcopy(data)
   if change=='key':d['cases'][0]['rows'][0]['key']=not d['cases'][0]['rows'][0]['key']
   elif change=='vectors':d['cases'][0]['rows'][0]['vectors']={}
   else:d['cases'][0]['summary']['frames']=11
   with self.subTest(change=change),self.assertRaises(ValueError):v.check_completeness(d,old)
 def test_rejects_missing_or_self_final_pins(self):
  v,_,_=self.fixture()
  with self.assertRaises(ValueError):v.validate_final_pins({})
  with self.assertRaises(ValueError):v.validate_final_pins({'sourcepins.json':'0'*64})
if __name__=='__main__':unittest.main()
