import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).with_name('analyze.py')
class Accounting(unittest.TestCase):
 def fixture(self,root):
  run=root/'run';fx=root/'fx';run.mkdir();fx.mkdir();(run/'dumps').mkdir();frames=[]
  for i in range(2):
   b=bytes([i]);(fx/f'{i:04}.jpg').write_bytes(b);frames.append({'id':i,'jpeg_sha256':hashlib.sha256(b).hexdigest()})
  (fx/'manifest.json').write_text(json.dumps({'frames':frames}))
  (run/'dumps'/'0000.txt').touch();(run/'comparison0000.json').write_text(json.dumps({'pixels':345600,'exact_rgb565_pixels':345600}))
  text=('CONFIG frames=2 jitter_cycles=200000 pclk_half_ps=17029\n'
        'ARRIVAL id=0 cycle=100 target=100\nADMITTED id=0 cycle=500\n'
        'ARRIVAL id=1 cycle=3533433 target=3533433\nDROP_BUSY id=1 cycle=3533500\n'
        'PRESENT_PASS id=0 cycle=4000000 writes=345600 bursts=43200 underruns=0\n'
        'SCAN_PASS id=0 pixels=345600\n'
        'CADENCE_RESULT arrivals=2 admitted=1 busy_drops=1 presented=1 complete_scans=1\nTEST_PASS_BANK_QSPI_CADENCE10\n')
  (run/'run.log').write_text(text);return run,fx
 def evaluate(self,run,fx):
  p=subprocess.run([sys.executable,str(SCRIPT),str(run),str(fx),'--output',str(run/'result.json')],capture_output=True,text=True)
  return p,json.loads((run/'result.json').read_text()) if (run/'result.json').exists() else None
 def test_busy_drop_accounted(self):
  with tempfile.TemporaryDirectory() as d:
   run,fx=self.fixture(Path(d));p,out=self.evaluate(run,fx);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(out['dropped_ids'],[1]);self.assertEqual(out['exact_pixels'],345600)
 def test_wrong_jitter_fails(self):
  with tempfile.TemporaryDirectory() as d:
   run,fx=self.fixture(Path(d));f=run/'run.log';f.write_text(f.read_text().replace('cycle=3533433 target=3533433','cycle=3533434 target=3533434'));p,_=self.evaluate(run,fx);self.assertNotEqual(p.returncode,0)
 def test_lost_terminal_fails(self):
  with tempfile.TemporaryDirectory() as d:
   run,fx=self.fixture(Path(d));f=run/'run.log';f.write_text(f.read_text().replace('TEST_PASS_BANK_QSPI_CADENCE10',''));p,_=self.evaluate(run,fx);self.assertNotEqual(p.returncode,0)
 def test_hash_tampering_fails(self):
  with tempfile.TemporaryDirectory() as d:
   run,fx=self.fixture(Path(d));(fx/'0001.jpg').write_bytes(b'tampered');p,_=self.evaluate(run,fx);self.assertNotEqual(p.returncode,0)
if __name__=='__main__':unittest.main()
