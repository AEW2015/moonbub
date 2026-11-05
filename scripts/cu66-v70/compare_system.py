#!/usr/bin/env python3
"""Compare declared command-model schedules; never infer physical FPS."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v70/system'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 paths=[AREA/'full-direct/results.json',AREA/'full-strip/results.json']
 d,s=[json.loads(p.read_text())for p in paths]
 assert d['source_sha256']==s['source_sha256'],'different source/fixture set'
 assert d['clocks']==s['clocks'] and not d['strip'] and s['strip']
 assert d['status']==s['status']=='PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS'
 assert d['cadence_status']==s['cadence_status']=='FAIL_UNDERRUNS'
 rows=[]
 for a,b in zip(d['frames'],s['frames'],strict=True):
  assert (a['fid'],a['key'],a['generation'])==(b['fid'],b['key'],b['generation'])
  assert a['actual_writes']==b['actual_writes']==664320
  rows.append(dict(fid=a['fid'],key=a['key'],direct=a,strip=b,
   clock_reduction_percent=100*(a['cycles']-b['cycles'])/a['cycles'],
   ACT_reduction_percent=100*(a['ACT']-b['ACT'])/a['ACT'],
   direct_modeled_ms=a['cycles']*d['clocks']['memory_period_ps']/1e9,
   strip_modeled_ms=b['cycles']*d['clocks']['memory_period_ps']/1e9))
 result=dict(status='PASS_COMPARISON_WITH_FAILED_CADENCE',frames=rows,
  input_results_sha256={str(p.relative_to(ROOT)):sha(p)for p in paths},
  script_sha256=sha(Path(__file__).resolve()),
  note='same chronological packets/source/modelclocks; different transaction durations and phases create different concurrent scanout work; not a fixedarrivalwindow or physicalFPScomparison',
  cadence=dict(direct=d['cadence_status'],strip=s['cadence_status']),
  next_bottlenecks=['scalarwrite/responsecost','sharedauxreadercachethrashing','LCDline-service deadline','decode/paintserialization'])
 (AREA/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
 for r in rows:print(f'FRAME{r["fid"]} clocks_reduced={r["clock_reduction_percent"]:.4f}% ACT_reduced={r["ACT_reduction_percent"]:.4f}%')
 print('COMPARISON_PASS functional_outputs_exact=true cadence_failed=true physicalFPS_proven=false')
if __name__=='__main__':main()
