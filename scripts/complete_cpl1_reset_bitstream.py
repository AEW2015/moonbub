"""Bounded route repair and gated image completion for the running reset candidate."""
from pathlib import Path
import argparse,json,subprocess,sys,time
r=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--candidate',default='fpga/candidates/cp23-reset-tags-20261105-v001');args=a.parse_args();c=(r/args.candidate).resolve()
o=c/'evidence/bitstream-completion01';o.mkdir(parents=True,exist_ok=False)
steps=[];deadline=time.monotonic()+7200
def progress(status,**kw):
 (o/'progress.json').write_text(json.dumps(dict(status=status,hardware=False,**kw),indent=2)+'\n')
def waitfile(p):
 while not p.exists():
  if time.monotonic()>deadline:raise TimeoutError(str(p))
  time.sleep(15)
def run(label,cmd):
 cmd=[sys.executable,*map(str,cmd)]
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=r,stdout=f,stderr=subprocess.STDOUT)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode))
 (o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 return q.returncode
origin=c/'implementation02';selected=origin
progress('WAITING_FOR_RUNNING_ROUTE');waitfile(origin/'execution.json')
assert json.loads((origin/'execution.json').read_text())['returncode']==0
passed=run('route-gate',['scripts/check_cpl1_capture_build.py',origin])==0
for name,directive in [('postroute-reset-alternate01','AlternateReplication'),('postroute-reset-aggressive01','AggressiveExplore')]:
 if passed:break
 progress('BOUNDED_PHYSICAL_OPTIMIZATION',parent=str(selected),directive=directive)
 target=c/name
 assert run(name,['scripts/postroute_cpl1_capture.py','--parent',selected/'routed.dcp','--output',target,'--directive',directive])==0
 selected=target
 passed=run(name+'-gate',['scripts/check_cpl1_capture_build.py',origin,'--result',selected])==0
if not passed:
 progress('BLOCKED_BY_ROUTED_TIMING_NO_IMAGE',result=str(selected));raise SystemExit(2)
progress('TIMING_PASSED_WAITING_FOR_FULL_MODELS',result=str(selected))
for n in ['full-budget-fast01','full-budget-slow01','envelope-equivalence02']:
 waitfile(c/'evidence'/n/'result.json')
image=c/'image-reset01'
progress('GENERATING_GATED_BITSTREAM',result=str(selected))
rc=run('image',['scripts/image_cpl1_reset_candidate.py','--candidate',c,'--result',selected.name,'--output',image])
assert rc==0,'Image gate or native generation failed; inspect image.log'
progress('BITSTREAM_COMPLETE_NOT_PROGRAMMED',result=str(selected),image=str(image))
(o/'result.json').write_text(json.dumps(dict(status='BITSTREAM_COMPLETE_NOT_PROGRAMMED',candidate=str(c),selected_route=str(selected),image=str(image),hardware=False),indent=2)+'\n')
assert run('selected-reset-audit',['scripts/run_cpl1_reset_audit.py','--checkpoint',selected/'routed.dcp','--output',c/'evidence/reset-audit-selected01'])==0
assert run('completion-manifest',['scripts/manifest_cpl1_reset_completion.py','--candidate',c])==0
print('BITSTREAM_COMPLETE_NOT_PROGRAMMED',image)
