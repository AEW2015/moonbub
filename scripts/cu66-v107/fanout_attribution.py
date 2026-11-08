#!/usr/bin/env python3
"""Read-only selected PAYLOAD routed-net exact load attribution; no design changes."""
import datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v107/fanout-attribution';BUILD=Path('/home/lori/gamebub-build/cu66-v69')
PARENT=ROOT/'experiments/python-gamebub-v107/native/20261108T055414848485Z/receipt.json'
TOOLS=Path('/home/lori/acorn-nexys4-ddr/tools');LICENSE=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def main():
 parent=json.loads(PARENT.read_text());d=parent['artifacts']['route.dcp'];checkpoint=Path(d['external_path']);assert sha(checkpoint)==d['sha256'];before=memory();assert before['available_bytes']>=8*1024**3 and before['psi_full_avg10']<1
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir(parents=True);build=BUILD/('v107-fanout-attribution-'+stamp);build.mkdir();mapped=Path('/build')/build.name
 shutil.copyfile(ROOT/'fpga/experiments/cu66-v107-fanout-attribution/query.tcl',build/'run.tcl')
 shutil.copyfile(build/'run.tcl',out/'run.tcl');shutil.copyfile(Path(__file__),out/'fanout_attribution.py')
 name='gamebub-v107-fanout-attribution-'+stamp.lower();cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount',f'type=bind,src={TOOLS},dst=/opt/amd-tools,readonly','--mount',f'type=bind,src={LICENSE},dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={checkpoint},dst=/parent/route.dcp,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',str(mapped),'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','180s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source','run.tcl','-tclargs',str(mapped)]
 shutil.copyfile(PARENT,out/'parent-receipt.json')
 for item in ['route-high-fanout.rpt','route-timing-summary.rpt']:
  artifact=parent['artifacts'][item];p=Path(artifact['external_path']);assert sha(p)==artifact['sha256'];shutil.copyfile(p,out/item)
 parent_inputs=Path(parent['build_external'])/'inputs.json';shutil.copyfile(parent_inputs,out/'parent-inputs.json')
 source_inputs=json.loads(parent_inputs.read_text());sources=source_inputs['source_origins']
 for name,info in sources.items():
  p=Path(parent['build_external'])/'snapshot'/name;assert sha(p)==info['sha256'];target=out/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 r=dict(schema='v107-readonly-payload-three-net-load-attribution-v1',status='RUNNING',command=cmd,parent_receipt_sha256=sha(PARENT),checkpoint_sha256_before=sha(checkpoint),checkpoint_readonly=True,no_RTL_or_clock_or_exception_edits=True,memory_samples=[],timeout_seconds=180,cpus=2,max_threads=2,memory_limit_bytes=8*1024**3,parent_receipt=str(PARENT.relative_to(ROOT)),checkpoint_external=str(checkpoint),source_origins=sources,part='xc7a100tcsg324-1',existing_clock_period_ns=10);start=time.monotonic();last=-5;stop=None;code=None
 print('FANOUT_ATTRIBUTION_STARTED',out.relative_to(ROOT),flush=True)
 try:
  with (out/'tool.log').open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-start
    if elapsed-last>=5:
     m=dict(elapsed_seconds=elapsed,**memory());r['memory_samples'].append(m);last=elapsed
     if m['available_bytes']<4*1024**3 or m['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if elapsed>220:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
    time.sleep(.5)
   code=proc.wait(timeout=30)
  r['status']='PASS_READONLY_LOAD_EXTRACTION' if code==0 and 'V107_READONLY_FANOUT_ATTRIBUTION_COMPLETE' in (out/'tool.log').read_text(errors='replace') else 'FAIL_TOOL_OR_QUERY'
 finally:
  r.update(exit_code=code,wall_seconds=time.monotonic()-start,stop_reason=stop,checkpoint_sha256_after=sha(checkpoint),parent_receipt_sha256_after=sha(PARENT));assert r['parent_receipt_sha256_after']==r['parent_receipt_sha256'];assert r['checkpoint_sha256_after']==r['checkpoint_sha256_before']
  for p in sorted((build/'results').glob('*')):
   if p.is_file():dst=out/'reports'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(p,dst)
  r['retained_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('FANOUT_ATTRIBUTION_FINISHED',r['status'],code,flush=True)
 if r['status']!='PASS_READONLY_LOAD_EXTRACTION':raise SystemExit(1)
if __name__=='__main__':main()
