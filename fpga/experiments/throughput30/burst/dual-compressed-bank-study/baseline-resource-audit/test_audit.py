#!/usr/bin/env python3
"""Negative controls in temporary copies, never alter real evidence."""
import json,shutil,subprocess,tempfile,unittest
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[5]

class AuditTests(unittest.TestCase):
 def test_tampered_bound_source_is_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   dst=Path(t);script=dst/here.relative_to(root)/'audit.py';script.parent.mkdir(parents=True);shutil.copy(here/'audit.py',script)
   paths=[x['path'] for x in json.loads((root/'fpga/build-final/source-bindings.json').read_text())]
   for name in ('source-bindings.json','utilization.rpt','timing_summary.rpt','route_status.rpt','gate.txt','moonshine-rev4.1.bit','moonshine_routed.dcp','synthesized.dcp'):paths.append('fpga/build-final/'+name)
   paths += ['fpga/attempts/v3-routed/source-bindings.json','fpga/experiments/throughput30/burst/idct-dsp-study/narrow-x/jpeg_idct_x_narrow.v','fpga/experiments/throughput30/burst/idct-dsp-study/narrow-y-coeff/jpeg_idct_y_coeff.v']
   for name in paths:
    target=dst/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy(root/name,target)
   run=lambda:subprocess.run(['python3',str(script),str(dst/'audit.json')],capture_output=True,text=True)
   ok=run();self.assertEqual(ok.returncode,0,ok.stderr)
   p=dst/'fpga/rtl/moonshine_core.sv';p.write_bytes(p.read_bytes()+b'\n')
   bad=run();self.assertNotEqual(bad.returncode,0);self.assertIn('bindings fail',bad.stderr)
if __name__=='__main__':unittest.main()
