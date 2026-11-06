"""Bind exact-cycle/index proof to native leaf reports; no board qualification."""
from pathlib import Path
import hashlib,json,re
root=Path(__file__).resolve().parents[2];directory=root/'fpga/experiments/cu66-v71/inverse-index'
source=directory/'cu71_idct_indexed.sv';proof=directory/'evidence/regression01';ooc=directory/'evidence/ooc01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
test=json.loads((proof/'result.json').read_text());run=json.loads((ooc/'execution.json').read_text())
assert test['status']=='PASS_EXACT_CYCLE_PARENT_AND_3471_GOLDENS_TWO_SEEDS'
assert run['returncode']==0 and run['source_sha256']==sha(source)
for name,h in test['source_sha256'].items():assert sha(root/name)==h,name
lines=(ooc/'timing.rpt').read_text().splitlines();i=next(i for i,line in enumerate(lines)if line.strip().startswith('WNS(ns)'));v=lines[i+2].split();assert len(v)==12
timing=dict(setup_ns=float(v[0]),setup_failures=int(v[2]),hold_ns=float(v[4]),hold_failures=int(v[6]),pulse_ns=float(v[8]),pulse_failures=int(v[10]))
assert timing['setup_ns']>0 and timing['setup_failures']==0
names=['derivation.json','evidence/regression01/result.json','evidence/regression01/source-freeze.json','evidence/regression01/execution.json','evidence/regression01/tb_idct.sv','evidence/regression01/seed69004501.log','evidence/regression01/seed69004502.log','evidence/ooc01/execution.json','evidence/ooc01/executed.tcl','evidence/ooc01/timing.rpt','evidence/ooc01/setup-paths.rpt','evidence/ooc01/utilization.rpt']
(directory/'qualification.json').write_text(json.dumps(dict(status='PASS_EXACT_CYCLE_GOLDENS_AND_SYNTHESIZED_LEAF_ESTIMATE_NOT_BOARD_SIGNOFF',
 source_sha256=sha(source),timing=timing,resources=dict(LUT=7687,FF=5150,DSP=17,RAMB36=0,RAMB18=0),
 tiles_per_seed=3471,seeds=2,added_public_cycles=0,
 index_invariant='row/column indices are six-bit concatenations of group2,lane-row1,k3; everyword offset equals original bounded arithmetic',
 payload_startup='Unknown four-state values retained; only valid payload consumed, no INIT-zero assumption',
 proof_hashes={name:sha(directory/name)for name in names},hardware=False,routed_timing=False),indent=2)+'\n')
print(json.dumps(dict(status='INDEXED_IDCT_QUALIFIED_FOR_INTEGRATION_ONLY',timing=timing,source_sha256=sha(source))))
