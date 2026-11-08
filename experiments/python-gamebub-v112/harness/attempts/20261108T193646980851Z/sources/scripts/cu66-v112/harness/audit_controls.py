#!/usr/bin/env python3
"""Exercise causal-trace rejection, preserving each mutated input and failure."""
import copy, hashlib, importlib.util, json, sys, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v112_run',HERE/'run.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def strict_audit(path,offered):
 result=runner.audit(path,offered)
 records=[json.loads(x) for x in Path(path).read_text().splitlines()]
 for accept,done in zip(records[::2],records[1::2]):
  assert done['source_backpressure_ps']==accept['time_ps']-accept['offered_ps']
 return result

def main():
 summary=json.loads((runner.AREA/'results.json').read_text());attempt=runner.ROOT/summary['selected_receipt'];assert sha(attempt)==summary['selected_sha256']
 source=attempt.parent/'ten-repeated-frames-trace.jsonl';offered_path=attempt.parent/'ten-repeated-frames-schedule.json'
 offered=json.loads(offered_path.read_text());records=[json.loads(x) for x in source.read_text().splitlines()]
 assert strict_audit(source,offered)['events']==280
 out=runner.AREA/'trace-controls';out.mkdir(exist_ok=True)
 mutations={
  'backwards-completion':lambda r:r[1].update(time_ps=r[0]['time_ps']-1),
  'wrong-sequence':lambda r:r[2].update(sequence=999),
  'hidden-buffer-over-capacity':lambda r:r[2].update(resident_bytes=1040),
  'changed-offered-time':lambda r:r[2].update(offered_ps=r[2]['offered_ps']+1),
  'wrong-clock':lambda r:r[2].update(clock='host_monotonic_ns'),
  'masked-backpressure':lambda r:r[5].update(source_backpressure_ps=0),
 }
 results={}
 for name,mutate in mutations.items():
  changed=copy.deepcopy(records);mutate(changed);path=out/(name+'.jsonl');path.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in changed))
  try:strict_audit(path,offered)
  except AssertionError:results[name]={'status':'PASS_REJECTED','input_sha256':sha(path)}
  else:raise AssertionError('undetected '+name)
 receipt=dict(schema='v112-causal-trace-negative-controls-v1',status='PASS',source_trace_sha256=sha(source),source_schedule_sha256=sha(offered_path),selected_receipt_sha256=sha(attempt),script_sha256=sha(Path(__file__)),auditor_sha256=sha(HERE/'run.py'),controls=results,scope='trace-validator negative controls; actual RTL negative runs are in harness receipt')
 (out/'results.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
