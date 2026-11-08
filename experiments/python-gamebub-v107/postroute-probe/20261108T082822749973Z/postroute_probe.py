#!/usr/bin/env python3
"""One bounded diagnostic post-route phys_opt, preserving qualified runtime9 parent."""
import datetime,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v107/postroute-probe';BASE=Path('/home/lori/gamebub-build/cu66-v69');PARENT=ROOT/'experiments/python-gamebub-v107/native/20261108T081254078678Z/receipt.json';FLOW=ROOT/'fpga/experiments/cu66-v107-postroute-probe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def normalized_xdc(p):return [s.strip() for s in p.read_text().splitlines() if s.strip() and not s.lstrip().startswith('#')]
def legal_route(p):
 s=p.read_text();r=lambda label:int(re.search(label+r'\.+\s*:\s*(\d+)',s).group(1));assert r('# of nets with routing errors')==0;assert r('# of routable nets')==r('# of fully routed nets')>0
 return dict(routable=r('# of routable nets'),fully_routed=r('# of fully routed nets'),routing_errors=0)
def main():
 assert not (AREA/'results.json').exists(),'one probe already dispatched; no automatic retry/strategy sweep'
 parent=json.loads(PARENT.read_text());assert parent['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and parent['observed_exit_code']==0 and parent['routing_checkpoint_written'] and parent['source_snapshot_unchanged']
 dispatch=ROOT/'experiments/python-gamebub-v107/coordination/threshold-runtime-dispatch.json';dis=json.loads(dispatch.read_text());assert dis['status']=='RUNNER_RETURNED' and dis['runner_exit_code']==0 and dis['native_attempt_ordinal']==9 and dis['source_set_ordinal']==8
 parent_build=Path(parent['build_external']);assert str(parent_build)==dis['prepared_build'];inp=parent_build/'inputs.json';assert sha(inp)==parent['source_manifest_sha256'];inputs=json.loads(inp.read_text());assert inputs['native_attempt_ordinal']==9 and inputs['production_source_set_ordinal']==8
 canonical=ROOT/inputs['behavioral_qualification']['path'];assert sha(canonical)==inputs['behavioral_qualification']['sha256'];q=json.loads(canonical.read_text());assert q['status']=='PASS_EXACT_THRESHOLD_CANONICAL' and q['actual_RTL_run'] and all(x['exact_stdout_events_cycles_and_canonical'] for x in q['runs'])
 expected={n:h for n,h in q['source_sha256'].items() if Path(n).suffix in ('.sv','.svh')};assert len(expected)==18 and expected=={v['path']:v['sha256'] for v in inputs['source_origins'].values()}
 checkpoint=Path(parent['artifacts']['route.dcp']['external_path']);digest=parent['artifacts']['route.dcp']['sha256'];assert sha(checkpoint)==digest
 for n,a in parent['artifacts'].items():
  if n in ('route-status.rpt','route-setup-paths.rpt','route-timing-summary.rpt','effective-timing.xdc'):assert sha(Path(a['external_path']))==a['sha256'],n
 parent_legal=legal_route(parent_build/'results/route-status.rpt');paths=(parent_build/'results/route-setup-paths.rpt').read_text();assert 'Slack (VIOLATED) :        -2.333ns' in paths and 'coefficients/child/scratch/read_segment_reg[1]/C' in paths.split('Slack (VIOLATED)')[1] and 'route 9.325ns (75.931%)' in paths
 assert sha(parent_build/'report.tcl')==parent['recipe_snapshots_sha256']['report.tcl'];assert sha(parent_build/'component.xdc')==parent['recipe_snapshots_sha256']['component.xdc']
 launch=memory();assert launch['available_bytes']>=8*1024**3 and launch['psi_full_avg10']<1,launch
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir(parents=True);build=BASE/('v107-postroute-probe-'+stamp);build.mkdir();mapped='/build/'+build.name
 for src,name in [(PARENT,'parent-receipt.json'),(inp,'parent-inputs.json'),(canonical,'canonical-qualification.json'),(dispatch,'parent-dispatch.json'),(Path(__file__),'postroute_probe.py'),(FLOW/'run.tcl','run.tcl'),(parent_build/'report.tcl','report.tcl'),(parent_build/'component.xdc','component.xdc')]:shutil.copyfile(src,out/name)
 for n,h in parent['retained_source_snapshot_sha256'].items():
  p=parent_build/'snapshot'/n;assert sha(p)==h;dest=out/'sources'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 for n in ['run.tcl','report.tcl','component.xdc']:shutil.copyfile(out/n,build/n)
 for n,a in parent['artifacts'].items():
  p=Path(a['external_path'])
  if p.suffix in ('.rpt','.tsv','.txt','.xdc') and p.stat().st_size<16*1024**2:
   assert sha(p)==a['sha256'];dest=out/'parent-reports'/n;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
 name='gamebub-v107-postroute-'+stamp.lower();cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/cache/vivado.lic,dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={checkpoint},dst=/parent/route.dcp,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',mapped,'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','600s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source','run.tcl','-tclargs',mapped]
 r=dict(schema='v107-runtime9-single-postroute-physical-diagnostic-v1',status='RUNNING',command=cmd,parent_receipt=str(PARENT.relative_to(ROOT)),parent_receipt_sha256=sha(PARENT),checkpoint_external=str(checkpoint),checkpoint_sha256_before=digest,parent_checkpoint_readonly=True,parent_runner_terminal_exit0=True,parent_route_status=parent_legal,parent_setup_wns_ns=-2.333,parent_critical_route_fraction=.75931,canonical_sha256=sha(canonical),source_sha256=expected,source_snapshot_sha256=parent['retained_source_snapshot_sha256'],report_tcl_sha256=sha(build/'report.tcl'),constraint_file_sha256=sha(build/'component.xdc'),parent_manifest_sha256=sha(inp),part='xc7a100tcsg324-1',clock_period_ns=10,max_threads=2,cpus=2,memory_limit_bytes=8*1024**3,timeout_seconds=600,build_external=str(build),no_RTL_or_constraint_edits=True,no_new_source_or_synthesis=True,physical_commands=['phys_opt_design -directive AggressiveExplore'],launch_memory=launch,memory_samples=[],scope='One diagnostic on legal routed runtime9 state; not a clean fresh synthesis or reproducible winner, no policy source/native cap change or hardware claim.')
 write(out/'receipt.json',r);write(AREA/'results.json',dict(status='RUNNING',selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));start=time.monotonic();last=-5;stop=None;code=None
 print('POSTROUTE_PROBE_STARTED',out.relative_to(ROOT),flush=True)
 try:
  with (out/'tool.log').open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-start
    if elapsed-last>=5:
     m=dict(elapsed_seconds=elapsed,**memory());r['memory_samples'].append(m);last=elapsed
     if m['available_bytes']<4*1024**3 or m['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if elapsed>640:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
    time.sleep(.5)
   code=proc.wait(timeout=30)
  assert code==0 and not stop,(code,stop)
  assert 'V107_SINGLE_POSTROUTE_PHYSOPT_PROBE_FINISHED' in (out/'tool.log').read_text(errors='replace')
  r['route_status']=legal_route(build/'results/route-status.rpt');assert normalized_xdc(build/'results/before-effective-timing.xdc')==normalized_xdc(build/'results/effective-timing.xdc')==normalized_xdc(parent_build/'results/effective-timing.xdc')
  required=['clocks','clock-interaction','check-timing','timing-summary','setup-paths','hold-paths','utilization','capacity','high-fanout','control-sets','complexity','congestion','drc','methodology','cdc','exceptions'];assert all((build/'results'/('route-'+n+'.rpt')).is_file() for n in required)
  r['status']='DIAGNOSTIC_ROUTE_COMPLETED_SIGNOFF_UNASSESSED'
 except BaseException as e:r.update(status='FAIL_OR_BOUNDED_PROBE',error=repr(e));raise
 finally:
  r.update(exit_code=code,wall_seconds=time.monotonic()-start,stop_reason=stop,checkpoint_sha256_after=sha(checkpoint),parent_receipt_sha256_after=sha(PARENT),source_snapshots_unchanged=all(sha(parent_build/'snapshot'/n)==h for n,h in parent['retained_source_snapshot_sha256'].items()))
  r['parent_unchanged']=r['checkpoint_sha256_before']==r['checkpoint_sha256_after'] and r['parent_receipt_sha256']==r['parent_receipt_sha256_after'] and r['source_snapshots_unchanged'];assert r['parent_unchanged']
  artifacts={}
  for p in sorted((build/'results').glob('*')):
   if p.is_file():
    artifacts[p.name]=dict(external_path=str(p),sha256=sha(p),bytes=p.stat().st_size)
    if p.suffix in ('.rpt','.tsv','.txt','.json','.xdc') and p.stat().st_size<16*1024**2:dest=out/'reports'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
  r['artifacts']=artifacts;r['warnings']=[x for x in (out/'tool.log').read_text(errors='replace').splitlines() if 'WARNING:' in x or 'CRITICAL WARNING:' in x];r['retained_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('POSTROUTE_PROBE_FINISHED',r['status'],code,flush=True)
if __name__=='__main__':main()
