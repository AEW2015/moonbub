"""Resume the frozen candidate through full-cell simulation and routed reports.

No hardware APIs, BIT emission or firmware installation.
"""
from pathlib import Path
import json,subprocess,sys,time,runpy
p=Path(__file__).resolve().parent;b=Path('C:/mb70/dy71-v025-20261107-v003')
e=b/'offline-flow';e.mkdir(exist_ok=False);rows=[]
deadline=time.monotonic()+1800
print('WAITING_FOR_FROZEN_FULL_SYNTHESIS',flush=True)
while not(b/'synth-execution.json').exists():
 assert time.monotonic()<deadline,'Synthesis wait budget expired'
 time.sleep(5)
s=json.loads((b/'synth-execution.json').read_text())
assert s['returncode']==0 and s['completion_marker'] and not s['native_errors'] and s['inputs_unchanged'],s
steps=[('full-synth-cell-sim',[sys.executable,str(p/'run-xsim-full-synth.py')]),
 ('bulk-structure',[sys.executable,str(p/'verify-bulk-netlist.py'),'--netlist',str(b/'bulk-funcsim.v'),'--out',str(b/'bulk-port-gate.json')]),
 ('implementation',[sys.executable,str(b/'run-phase.py'),'implementation'])]
for label,cmd in steps:
 print('START',label,flush=True);start=time.monotonic()
 with(e/(label+'.log')).open('x') as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(label=label,cmd=cmd,returncode=q.returncode,seconds=time.monotonic()-start));(e/'execution.json').write_text(json.dumps(rows,indent=2)+'\n')
 print('END',label,q.returncode,flush=True);assert q.returncode==0,(label,str(e/(label+'.log')))
m=runpy.run_path(str(Path('C:/mb70/scripts/cu66-v71/image_dy71_candidate.py')))
t=m['timing_metrics']((b/'timing-summary.rpt').read_text());r=m['route_metrics']((b/'route-status.rpt').read_text())
(e/'result.json').write_text(json.dumps(dict(status='ROUTED_TIMING_REPORTS_PASS_PENDING_NATIVE_AUDIT',timing=t,routes=r,BIT=False,hardware=False),indent=2)+'\n')
print('ROUTED_REPORT_GATES_PASS_PENDING_NATIVE_AUDIT',json.dumps(t),flush=True)
