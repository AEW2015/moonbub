#!/usr/bin/env python3
"""One 600-second post-route physical headroom probe; preserve its routed parent."""
import datetime,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v106/postroute';FLOW=ROOT/'fpga/experiments/cu66-v106-postroute'
PARENT=ROOT/'experiments/python-gamebub-v106/native/20261108T013032873883Z/receipt.json';DCP=Path('/home/lori/gamebub-build/cu66-v69/v106-closure-20261108T013032719249Z-8cf646/results/route.dcp');DCP_SHA='7c626d0f79ba2c9546d4ac69557fc5541623f4592c7c848c7b65800961efbfd0'
TOOLS=Path('/home/lori/acorn-nexys4-ddr/tools');LICENSE=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic');BUILD_ROOT=Path('/home/lori/gamebub-build/cu66-v69')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def memory():
    info={line.split(':',1)[0]:int(line.split(':',1)[1].split()[0])*1024 for line in Path('/proc/meminfo').read_text().splitlines()}
    full=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));avg=float(next(x.split('=')[1] for x in full.split() if x.startswith('avg10=')))
    return dict(MemAvailable_bytes=info['MemAvailable'],PSI_full_avg10=avg)
def main():
    AREA.mkdir(parents=True,exist_ok=True);assert not list(AREA.glob('*/receipt.json')),'one strategy attempt already retained; no retry authorized'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir();build=BUILD_ROOT/('v106-postroute-'+stamp);build.mkdir();mapped=Path('/build')/build.name;name='gamebub-v106-postroute-'+stamp.lower();parent=json.loads(PARENT.read_text())
    assert parent['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and parent['artifacts']['route.dcp']['sha256']==DCP_SHA==sha(DCP)
    shutil.copyfile(PARENT,out/'parent-receipt.json');shutil.copyfile(PARENT.parent/'inputs.json',out/'parent-inputs.json');shutil.copyfile(Path(__file__),out/'postroute_probe.py');shutil.copyfile(FLOW/'run.tcl',out/'run.tcl');shutil.copyfile(FLOW/'run.tcl',build/'run.tcl')
    cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount',f'type=bind,src={TOOLS},dst=/opt/amd-tools,readonly','--mount',f'type=bind,src={LICENSE},dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={DCP},dst=/parent/route.dcp,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',str(mapped),'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','600s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source',str(mapped/'run.tcl'),'-tclargs',str(mapped)]
    r=dict(schema='v106-postroute-physical-diagnostic-v1',status='PREPARED',parent_receipt=dict(path=str(PARENT.relative_to(ROOT)),sha256=sha(PARENT)),parent_checkpoint=dict(path=str(DCP),sha256_before=sha(DCP),readonly_mount=True),parent_source_alias='closure; existing paired qualification; no new RTL source selection',command=cmd,build_external=str(build),part='xc7a100tcsg324-1',clock_period_ns=10.0,strategy='phys_opt_design -directive AggressiveExplore',route_default_only_if_incomplete=True,explicit_retime=False,clock_or_exception_edits=False,blanket_fanout_directive=False,source_changes=False,hardware_contact=False,selected_or_promoted=False,board_IO_CDC_qualified=False,hardware_30fps=False,validated_complete_decode_under10ms=False,timeout_seconds=600,max_threads=2,memory_limit_bytes=8*1024**3,tools_readonly=True,existing_legitimate_license_readonly=True,license_contents_logged=False,hostid_or_MAC_changed=False,source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str((FLOW/'run.tcl').relative_to(ROOT)):sha(FLOW/'run.tcl')},resource_before=memory(),memory_samples=[],observed_exit_code=None)
    write(out/'receipt.json',r);start=time.monotonic();code=None;stop=None
    try:
        assert r['resource_before']['MemAvailable_bytes']>=8*1024**3 and r['resource_before']['PSI_full_avg10']<1,'launch resource gate denied'
        r['status']='RUNNING';write(out/'receipt.json',r);print('V106_POSTROUTE_STARTED',out,flush=True);high=0
        with (out/'vivado.log').open('w') as log,(out/'memory.jsonl').open('w') as monitor:
            process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);last=-30.0
            while process.poll() is None:
                elapsed=time.monotonic()-start
                if elapsed-last>=30:
                    sample=dict(elapsed_seconds=elapsed,**memory());stats=subprocess.run(['docker','exec',name,'cat','/sys/fs/cgroup/memory.current'],capture_output=True,text=True,timeout=8);sample['container_memory_bytes']=int(stats.stdout.strip()) if stats.returncode==0 and stats.stdout.strip().isdigit() else None
                    r['memory_samples'].append(sample);monitor.write(json.dumps(sample)+'\n');monitor.flush();print('V106_POSTROUTE_MONITOR',json.dumps(sample),flush=True);last=elapsed;high=high+1 if sample['PSI_full_avg10']>=5 else 0
                    if sample['MemAvailable_bytes']<4*1024**3:stop='HOST_AVAILABLE_BELOW_4GIB'
                    if high>=2:stop='SUSTAINED_HIGH_MEMORY_PRESSURE'
                if elapsed>645:stop='HOST_WALL_TIMEOUT'
                if stop:subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
                time.sleep(1)
            try:code=process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                subprocess.run(['docker','kill',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);code=process.wait(timeout=15)
        text=(out/'vivado.log').read_text(errors='replace');r['diagnostic_finished']=code==0 and 'V106_POSTROUTE_DIAGNOSTIC_FINISHED' in text
        r['status']='DIAGNOSTIC_FINISHED_REVIEW_REQUIRED' if r['diagnostic_finished'] else 'STOPPED_RESOURCE_OR_TIME_GATE' if stop or code in (124,137) else 'TOOL_OR_BUILD_FAILED'
    except BaseException as e:r.update(status='STOPPED_OR_FAILED',error_class=type(e).__name__,error=str(e));raise
    finally:
        r.update(observed_exit_code=code,monitor_stop_reason=stop,wall_seconds=time.monotonic()-start);r['parent_checkpoint']['sha256_after']=sha(DCP);r['parent_checkpoint']['unchanged']=r['parent_checkpoint']['sha256_before']==r['parent_checkpoint']['sha256_after']
        artifacts={}
        for p in sorted((build/'results').glob('*')):
            if p.is_file():
                artifacts[p.name]=dict(sha256=sha(p),bytes=p.stat().st_size,external_path=str(p))
                if p.suffix in ('.rpt','.txt','.json','.xdc','.tsv') and p.stat().st_size<8*1024**2:
                    dest=out/'reports'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
        r['artifacts']=artifacts;r['retained_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'}
        write(out/'receipt.json',r);write(AREA/'results.json',dict(r,selected_receipt=str((out/'receipt.json').relative_to(ROOT))));print('V106_POSTROUTE_FINISHED',r['status'],code,flush=True)
    assert r['parent_checkpoint']['unchanged'],'parent checkpoint changed'
    if r['status']!='DIAGNOSTIC_FINISHED_REVIEW_REQUIRED':raise SystemExit(1)
if __name__=='__main__':main()
