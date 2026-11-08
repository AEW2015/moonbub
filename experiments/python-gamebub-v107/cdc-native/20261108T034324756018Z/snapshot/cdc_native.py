#!/usr/bin/env python3
"""Prepare/run a source-frozen, bounded isolated CDC fabric physical screen."""
import argparse,datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v107/cdc-native'
RTL=ROOT/'fpga/experiments/cu66-v107-cdc'
FLOW=ROOT/'fpga/experiments/cu66-v107-cdc-flow'
BUILD=Path('/home/lori/gamebub-build/cu66-v69')
TOOLS=Path('/home/lori/acorn-nexys4-ddr/tools')
LICENSE=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def resources():
    mem={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()}
    full=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    return dict(MemAvailable_bytes=mem['MemAvailable'],PSI_full_avg10=float(full.split('avg10=')[1].split()[0]))
def prepare(constraint):
    selection=json.loads((ROOT/'experiments/python-gamebub-v107/cdc/results.json').read_text());passed=ROOT/selection['selected_receipt'];assert sha(passed)==selection['sha256']
    proof=json.loads(passed.read_text());assert proof['status']=='PASS_BEHAVIORAL_CDC_FABRIC'
    sources=[RTL/(x+'.sv') for x in ('v107_reset_release','v107_async_fifo','v107_cdc_fabric')]
    for p in sources:assert sha(p)==proof['source_sha256'][str(p.relative_to(ROOT))]
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir(parents=True)
    build=BUILD/('v107-cdc-native-'+stamp);build.mkdir();mapped=Path('/build')/build.name
    copied={}
    for source in [*sources,constraint,*[FLOW/x for x in ('run.tcl','report.tcl','unit-clocks.xdc')],Path(__file__).resolve()]:
        name='gray-constraints.tcl' if source==constraint else source.name
        target=build/name;shutil.copyfile(source,target);copy=out/'snapshot'/name;copy.parent.mkdir(exist_ok=True);shutil.copyfile(source,copy)
        copied[name]=dict(path=str(source.relative_to(ROOT)),sha256=sha(source))
    (build/'inputs.tcl').write_text('set rtl_sources [list '+' '.join('{'+str(mapped/p.name)+'}' for p in sources)+']\n')
    shutil.copyfile(build/'inputs.tcl',out/'snapshot/inputs.tcl')
    inputs=dict(schema='v107-cdc-unit-physical-inputs-v1',status='PREPARED',build_external=str(build),mapped_build=str(mapped),source_origins=copied,snapshot_sha256={p.name:sha(p) for p in sorted((out/'snapshot').iterdir())},behavioral_receipt=dict(path=str(passed.relative_to(ROOT)),sha256=sha(passed)),part='xc7a100tcsg324-1',top='v107_cdc_fabric',synthetic_unit_clock_periods_ns=dict(transport=5,decoder=10,memory=10,display=16.667),actual_board_clocks_or_IO_qualified=False,source_RTL_changes=False)
    write(out/'inputs.json',inputs);write(build/'inputs.json',inputs)
    print('V107_CDC_NATIVE_PREPARED',out.relative_to(ROOT),flush=True)
    return out

def run(out):
    out=out.resolve();out.relative_to(AREA);assert not (out/'receipt.json').exists(),'prepared attempt already executed; prepare a new attempt'
    inputs=json.loads((out/'inputs.json').read_text());build=Path(inputs['build_external']);mapped=Path(inputs['mapped_build']);name='gamebub-v107-cdc-native-'+out.name.lower()
    for n,h in inputs['snapshot_sha256'].items():assert sha(build/n)==sha(out/'snapshot'/n)==h,n
    before=resources();assert before['MemAvailable_bytes']>=8*1024**3 and before['PSI_full_avg10']<1,before
    assert TOOLS.is_dir() and LICENSE.is_file()
    command=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount',f'type=bind,src={TOOLS},dst=/opt/amd-tools,readonly','--mount',f'type=bind,src={LICENSE},dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',str(mapped),'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','1200s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source',str(mapped/'run.tcl'),'-tclargs',str(mapped)]
    r=dict(schema='v107-cdc-unit-physical-receipt-v1',status='RUNNING',command=command,input_manifest_sha256=sha(out/'inputs.json'),part=inputs['part'],top=inputs['top'],synthetic_unit_clock_periods_ns=inputs['synthetic_unit_clock_periods_ns'],build_external=str(build),container=name,max_threads=2,timeout_seconds=1200,memory_limit_bytes=8*1024**3,resource_before=before,memory_samples=[],tools_readonly=True,existing_legitimate_license_readonly=True,license_contents_logged=False,hostid_or_MAC_changed=False,actual_board_clock_or_IO_qualified=False,hardware_contact=False,source_RTL_changes=False,default_flow='OOC synthesis rebuilt hierarchy then opt/place/route Default',exact_gray_constraints_applied_after_synthesis=True,blanket_async_clock_groups=False)
    write(out/'receipt.json',r);start=time.monotonic();last=-5;stop=None;code=None
    print('V107_CDC_NATIVE_STARTED',out.relative_to(ROOT),flush=True)
    try:
        with (out/'vivado.log').open('w') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            while proc.poll() is None:
                elapsed=time.monotonic()-start
                if elapsed-last>=5:
                    sample=dict(elapsed_seconds=elapsed,**resources());r['memory_samples'].append(sample);last=elapsed
                    if sample['MemAvailable_bytes']<4*1024**3 or sample['PSI_full_avg10']>=5:stop='HOST_MEMORY_GATE'
                if elapsed>1245:stop='HOST_WALL_TIMEOUT'
                if stop:
                    subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
                time.sleep(1)
            code=proc.wait(timeout=30)
        text=(out/'vivado.log').read_text(errors='replace')
        finished=code==0 and 'V107_CDC_UNIT_ROUTE_FINISHED' in text
        r['status']='MAPPED_CDC_UNIT_ROUTE_FINISHED_REVIEW_REQUIRED' if finished else 'STOPPED_TIME_OR_RESOURCE_GATE' if stop or code in (124,137) else 'TOOL_OR_CONSTRAINT_FAILED'
    except BaseException as e:r.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        r.update(observed_exit_code=code,wall_seconds=time.monotonic()-start,monitor_stop_reason=stop,source_snapshot_unchanged=all(sha(build/n)==h for n,h in inputs['snapshot_sha256'].items()))
        artifacts={}
        for p in sorted((build/'results').glob('*')):
            if not p.is_file():continue
            artifacts[p.name]=dict(sha256=sha(p),bytes=p.stat().st_size,external_path=str(p))
            if p.suffix in ('.rpt','.txt','.tsv','.xdc') and p.stat().st_size<8*1024**2:
                dst=out/'reports'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(p,dst)
        r['artifacts']=artifacts;r['retained_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'}
        write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')))
        print('V107_CDC_NATIVE_FINISHED',r['status'],code,flush=True)
    assert r['source_snapshot_unchanged']
    if r['status']!='MAPPED_CDC_UNIT_ROUTE_FINISHED_REVIEW_REQUIRED':raise SystemExit(1)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,help='Run an existing prepared attempt only after shared heavy-job slot approval');p.add_argument('--constraint-file',type=Path,default=RTL/'constraints.tcl',help='New candidate constraint copy; frozen original never edited');a=p.parse_args()
    if a.run:run(a.run)
    else:prepare(a.constraint_file.resolve())
if __name__=='__main__':main()
