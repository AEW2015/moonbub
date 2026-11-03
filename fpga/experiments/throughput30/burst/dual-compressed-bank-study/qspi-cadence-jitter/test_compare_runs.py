import hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path
SCRIPT=Path(__file__).with_name('compare-runs.py')
class CompareRuns(unittest.TestCase):
 def make(self,root,n=2):
  r={'input_frames':n,'distinct_input_hashes':n,'presented':n,'admitted':n,'busy_drops':0,'presented_within_capture_window':n,
     'config':{'frames':n},'capture_age_ms':{},'gap_ms':{},'last_window_offset_ms':-1,'exact_pixels':n*345600,
     'per_frame':[{'id':i,'capture_age_cycles':3333334} for i in range(n)]}
  path=root/f'{n}.json';path.write_text(json.dumps(r));return path
 def test_matching_inputs(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=root/'manifest.json';manifest.write_text(json.dumps({'frames':[{},{}]}));(root/'fixture-manifest.sha256').write_text(hashlib.sha256(manifest.read_bytes()).hexdigest());f=self.make(root)
   r=subprocess.run([sys.executable,str(SCRIPT),str(manifest),str(f),str(f)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['runs'][0]['presented_older_than_1_over_30s'],2)
 def test_different_lengths_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=root/'manifest.json';manifest.write_text(json.dumps({'frames':[{},{}]}));(root/'fixture-manifest.sha256').write_text(hashlib.sha256(manifest.read_bytes()).hexdigest());one=self.make(root,1);two=self.make(root,2)
   r=subprocess.run([sys.executable,str(SCRIPT),str(manifest),str(one),str(two)],capture_output=True,text=True);self.assertNotEqual(r.returncode,0)
if __name__=='__main__':unittest.main()
