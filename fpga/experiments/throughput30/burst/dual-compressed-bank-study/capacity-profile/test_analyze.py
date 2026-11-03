#!/usr/bin/env python3
import hashlib,json,tempfile,unittest
from pathlib import Path
import analyze

class CapacityTests(unittest.TestCase):
 def test_nearest_rank(self):
  self.assertEqual(analyze.nearest_rank(list(range(1,101)),95),95)
  self.assertEqual(analyze.nearest_rank([5,3,4],99),5)
  with self.assertRaises(ValueError):analyze.nearest_rank([],95)
 def test_boundary_hash_and_bram(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);rows=[]
   for fid,n in enumerate((32767,32768,32769,49152,49153,65536,65537)):
    data=bytes([fid])*n;(p/f'{fid:04d}.jpg').write_bytes(data)
    rows.append({'id':fid,'jpeg_bytes':n,'jpeg_sha256':hashlib.sha256(data).hexdigest()})
   (p/'manifest.json').write_text(json.dumps({'frames':rows}))
   r=analyze.inspect(p/'manifest.json')
   self.assertEqual([r['caps'][str(c)]['oversize_count'] for c in analyze.CAPS],[5,3,1]);self.assertEqual(r['p95_nearest_rank_bytes'],65537)
   self.assertEqual([analyze.bram(c)['estimated_ramb36_pair'] for c in analyze.CAPS],[16,24,32])
   f=p/'0000.jpg';v=bytearray(f.read_bytes());v[0]^=1;f.write_bytes(v)
   with self.assertRaisesRegex(ValueError,'fixture hash or length mismatch'):analyze.inspect(p/'manifest.json')
 def test_duplicate_id_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);data=b'x';(p/'0000.jpg').write_bytes(data);row={'id':0,'jpeg_bytes':1,'jpeg_sha256':hashlib.sha256(data).hexdigest()};(p/'manifest.json').write_text(json.dumps({'frames':[row,row]}))
   with self.assertRaisesRegex(ValueError,'invalid frame metadata'):analyze.inspect(p/'manifest.json')
if __name__=='__main__':unittest.main()
