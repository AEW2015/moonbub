from pathlib import Path
import json,subprocess,sys,tempfile,unittest

SCRIPT=Path(__file__).with_name('analyze.py')
class Analyze(unittest.TestCase):
 def run_case(self,line):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'log';p.write_text(line+'\n')
   return subprocess.run([sys.executable,str(SCRIPT),str(p)],capture_output=True,text=True)
 def test_valid(self):
  r=self.run_case('STAGE_TIMING begin=1 byte_first=2 byte_last=4 write_first=3 write_last=5 drained=6 reader_start=7 read_first=8 read_last=9 reader_done=10 pixel_first=8 pixel_last=11 present=12')
  self.assertEqual(r.returncode,0);j=json.loads(r.stdout);self.assertEqual(j['durations']['writer_begin_to_present']['cycles'],11)
 def test_missing_and_invalid_order_rejected(self):
  self.assertNotEqual(self.run_case('STAGE_TIMING begin=1').returncode,0)
  r=self.run_case('STAGE_TIMING begin=1 byte_first=2 byte_last=4 write_first=3 write_last=5 drained=5 reader_start=7 read_first=8 read_last=9 reader_done=10 pixel_first=8 pixel_last=11 present=12')
  self.assertNotEqual(r.returncode,0)
if __name__=='__main__':unittest.main()
