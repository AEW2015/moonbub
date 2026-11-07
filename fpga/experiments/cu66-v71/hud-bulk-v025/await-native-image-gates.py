"""Wait for report completion, then qualify/emit a bounded lab BIT. Never hardware."""
from pathlib import Path
import hashlib,json,runpy,subprocess,sys,time
p=Path(__file__).resolve().parent;b=Path('C:/mb70/dy71-v025-20261107-v003')
if '--incremental' in sys.argv:b=b/'incremental01'
if '--postroute' in sys.argv:b=b/'postroute01'
if '--postroute02' in sys.argv:b=b/'postroute02'
e=b/'image-flow';e.mkdir();rows=[]
deadline=time.monotonic()+7200
print('WAITING_FOR_ROUTED_REPORTS_NO_HARDWARE',flush=True)
while not(b/'implementation-execution.json').exists():
 assert time.monotonic()<deadline,'Implementation wait expired'
 time.sleep(5)
v=json.loads((b/'implementation-execution.json').read_text());assert v['returncode']==0 and v['completion_marker'] and v['inputs_unchanged'] and not v['native_errors'],v
m=runpy.run_path('C:/mb70/scripts/cu66-v71/image_dy71_candidate.py')
timing=m['timing_metrics']((b/'timing-summary.rpt').read_text());routes=m['route_metrics']((b/'route-status.rpt').read_text())
assert json.loads((p/'xsim-full-synth02/result.json').read_text())['netlist_sha256']==hashlib.sha256((b/'bulk-funcsim.v').read_bytes()).hexdigest()
for mode in ['audit','emit']:
 out=b/('audit01' if mode=='audit' else 'image01');cmd=[sys.executable,str(p/'image-gates.py'),'--mode',mode,'--build',str(b),'--out',str(out)]
 if mode=='emit':cmd+=['--audit',str(b/'audit01')]
 print('START_NATIVE_IMAGE_GATE',mode,flush=True)
 with(e/(mode+'.log')).open('x') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(mode=mode,cmd=cmd,returncode=r.returncode));(e/'execution.json').write_text(json.dumps(rows,indent=2));assert r.returncode==0,(mode,str(e/(mode+'.log')))
bit=b/'image01/moonbub-v025-lab.bit'
(e/'result.json').write_text(json.dumps(dict(status='LAB_BIT_EMITTED_PENDING_PHYSICAL_TEST',bit=str(bit),sha256=hashlib.sha256(bit.read_bytes()).hexdigest(),timing=timing,routes=routes,hardware=False,overall='INCOMPLETE'),indent=2)+'\n')
print('LAB_BIT_READY_PENDING_PHYSICAL_TEST',str(bit),flush=True)
