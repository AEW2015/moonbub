import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).with_name('checkpoint.py')
class Checkpoint(unittest.TestCase):
 def setup_input(self,root):
  run=root/'run';checks=root/'checks';fx=root/'fx';run.mkdir();checks.mkdir();fx.mkdir();frames=[]
  log=['CONFIG frames=300 jitter_cycles=200000 pclk_half_ps=18470 capture_phase_cycles=833333']
  epoch=1000000
  for i in range(30):
   b=bytes([i]);(fx/f'{i:04}.jpg').write_bytes(b);frames.append({'jpeg_sha256':hashlib.sha256(b).hexdigest()});(checks/f'{i:04}.json').write_text(json.dumps({'pixels':345600,'exact_rgb565_pixels':345600})); j=200000 if i%3==1 else (-200000 if i%3==2 else 0);arrival=epoch+i*10000000//3+j;present=epoch+i*10000000//3+3800000
   log.extend((f'ARRIVAL id={i} cycle={arrival} target={arrival}', f'PRESENT_PASS id={i} cycle={present} writes=345600 bursts=43200 underruns=0',f'SCAN_PASS id={i} pixels=345600'))
  (fx/'manifest.json').write_text(json.dumps({'frames':frames}));(run/'run.log').write_text('\n'.join(log)+'\n');return run,checks,fx
 def evaluate(self,root,paths):
  return subprocess.run([sys.executable,str(SCRIPT),*map(str,paths),str(root/'result.json')],capture_output=True,text=True)
 def test_prefix_passes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=self.setup_input(root);r=self.evaluate(root,p);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads((root/'result.json').read_text())['exact_cmodel_pixels'],10368000)
 def test_missing_scan_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=self.setup_input(root);f=p[0]/'run.log';f.write_text(f.read_text().replace('SCAN_PASS id=7 pixels=345600',''));self.assertNotEqual(self.evaluate(root,p).returncode,0)
 def test_wrong_arrival_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=self.setup_input(root);f=p[0]/'run.log';f.write_text(f.read_text().replace('ARRIVAL id=0 cycle=1000000 target=1000000','ARRIVAL id=0 cycle=1000001 target=1000000'));self.assertNotEqual(self.evaluate(root,p).returncode,0)
if __name__=='__main__':unittest.main()
