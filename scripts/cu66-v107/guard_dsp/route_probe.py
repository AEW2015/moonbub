#!/usr/bin/env python3
"""Read-only frozen TABLES route exact DSP control launch timing diagnostic."""
import datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/guard-dsp/route-probe';BUILD=Path('/home/lori/gamebub-build/cu66-v69')
PARENT=ROOT/'experiments/python-gamebub-v107/native/20261108T052651848340Z/receipt.json'
TOOLS=Path('/home/lori/acorn-nexys4-ddr/tools');LICENSE=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def main():
 parent=json.loads(PARENT.read_text());d=parent['artifacts']['route.dcp'];checkpoint=Path(d['external_path']);assert sha(checkpoint)==d['sha256'];before=memory();assert before['available_bytes']>=8*1024**3 and before['psi_full_avg10']<1
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir(parents=True);build=BUILD/('v107-guard-route-'+stamp);build.mkdir();mapped=Path('/build')/build.name
 (build/'run.tcl').write_text('''set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
open_checkpoint /parent/route.dcp
report_clocks -file [file join $build results clocks.rpt]
set cell [get_cells -quiet coefficients/child/scratch/error4]
if {[llength $cell]!=1 || [get_property REF_NAME $cell] ne "DSP48E1"} {error "exact scratch/error4 DSP absent"}
set start [get_pins -quiet coefficients/child/scratch/error4/CLK]
if {[llength $start]!=1 || [get_property REF_PIN_NAME $start] ne "CLK"} {error "exact DSP CLK startpoint absent"}
set clock [get_clocks -of_objects $start]
if {[llength $clock]!=1 || abs([get_property PERIOD $clock]-10)>0.001} {error "existing10ns clock changed"}
set f [open [file join $build results dsp.tsv] w]
puts $f "cell\\tprimitive\\tclock\\tperiod\\tAREG\\tBREG\\tMREG\\tPREG"
puts $f "$cell\\t[get_property REF_NAME $cell]\\t$clock\\t[get_property PERIOD $clock]\\t[get_property AREG $cell]\\t[get_property BREG $cell]\\t[get_property MREG $cell]\\t[get_property PREG $cell]"
close $f
report_timing -delay_type max -from $start -max_paths 5 -path_type full_clock_expanded -file [file join $build results dsp-control-routed.rpt]
set paths [get_timing_paths -delay_type max -from $start -max_paths 5]
if {[llength $paths]<1} {error "exact DSP CLK timing source matched no paths"}
set f [open [file join $build results dsp-paths.tsv] w]
puts $f "source\\tendpoint\\tslack\\tdatapath\\tlogic_levels"
foreach path $paths {
 puts $f "[get_property STARTPOINT_PIN $path]\\t[get_property ENDPOINT_PIN $path]\\t[get_property SLACK $path]\\t[get_property DATAPATH_DELAY $path]\\t[get_property LOGIC_LEVELS $path]"
}
close $f
puts V107_READONLY_DSP_PROBE_COMPLETE
''')
 shutil.copyfile(build/'run.tcl',out/'run.tcl');shutil.copyfile(Path(__file__),out/'route_probe.py')
 name='gamebub-v107-guard-route-'+stamp.lower();cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount',f'type=bind,src={TOOLS},dst=/opt/amd-tools,readonly','--mount',f'type=bind,src={LICENSE},dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={checkpoint},dst=/parent/route.dcp,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',str(mapped),'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','300s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source','run.tcl','-tclargs',str(mapped)]
 r=dict(schema='v107-readonly-exact-dsp-control-timing-v1',status='RUNNING',command=cmd,parent_receipt_sha256=sha(PARENT),checkpoint_sha256_before=sha(checkpoint),checkpoint_readonly=True,no_RTL_or_clock_or_exception_edits=True,memory_samples=[]);start=time.monotonic();last=-5;stop=None;code=None
 print('DSP_ROUTE_PROBE_STARTED',out.relative_to(ROOT),flush=True)
 try:
  with (out/'tool.log').open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-start
    if elapsed-last>=5:
     m=dict(elapsed_seconds=elapsed,**memory());r['memory_samples'].append(m);last=elapsed
     if m['available_bytes']<4*1024**3 or m['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if elapsed>340:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
    time.sleep(.5)
   code=proc.wait(timeout=30)
  r['status']='PASS_READONLY_TIMING_EXTRACTION' if code==0 and 'V107_READONLY_DSP_PROBE_COMPLETE' in (out/'tool.log').read_text(errors='replace') else 'FAIL_TOOL_OR_QUERY'
 finally:
  r.update(exit_code=code,wall_seconds=time.monotonic()-start,stop_reason=stop,checkpoint_sha256_after=sha(checkpoint));assert r['checkpoint_sha256_after']==r['checkpoint_sha256_before']
  for p in sorted((build/'results').glob('*')):
   if p.is_file():dst=out/'reports'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(p,dst)
  r['retained_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('DSP_ROUTE_PROBE_FINISHED',r['status'],code,flush=True)
 if r['status']!='PASS_READONLY_TIMING_EXTRACTION':raise SystemExit(1)
if __name__=='__main__':main()
