#!/usr/bin/env python3
"""Read-only frozen Elastic route lookup endpoint timing diagnostic."""
import datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/scale/lookup-probe';BUILD=Path('/home/lori/gamebub-build/cu66-v69')
PARENT=ROOT/'experiments/python-gamebub-v107/native/20261108T042607353046Z/receipt.json'
TOOLS=Path('/home/lori/acorn-nexys4-ddr/tools');LICENSE=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def main():
 parent=json.loads(PARENT.read_text());d=parent['artifacts']['route.dcp'];checkpoint=Path(d['external_path']);assert sha(checkpoint)==d['sha256'];before=memory();assert before['available_bytes']>=8*1024**3 and before['psi_full_avg10']<1
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir(parents=True);build=BUILD/('v107-scale-lookups-'+stamp);build.mkdir();mapped=Path('/build')/build.name
 (build/'run.tcl').write_text('''set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
open_checkpoint /parent/route.dcp
report_clocks -file [file join $build results clocks.rpt]
set f [open [file join $build results endpoints.tsv] w]
puts $f "kind\\tcell\\tprimitive\\tclock\\tperiod"
foreach kind {mode scale} {
 set c [get_cells -hierarchical -regexp [format {^coefficients/admission/lookup_%s_reg\\[[01]\\]$} $kind]]
 if {[llength $c] != 2} {error "exact two lookup endpoint registers missing: $kind"}
 set d [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]
 if {[llength $d] != 2} {error "exact two D pins missing: $kind"}
 foreach cell $c {
  set clock [get_clocks -of_objects [get_pins -of_objects $cell -filter {REF_PIN_NAME == C}]]
  if {[llength $clock] != 1 || abs([get_property PERIOD $clock]-10)>0.001} {error "original10ns lookup clock changed"}
  puts $f "$kind\\t$cell\\t[get_property REF_NAME $cell]\\t$clock\\t[get_property PERIOD $clock]"
 }
 report_timing -delay_type max -to $d -max_paths 10 -path_type full_clock_expanded -file [file join $build results lookup-${kind}-routed.rpt]
 set q [open [file join $build results lookup-${kind}-paths.tsv] w]
 puts $q "source\\tendpoint\\tslack\\tdatapath\\tlogic_levels"
 foreach path [get_timing_paths -delay_type max -to $d -max_paths 10] {
  puts $q "[get_property STARTPOINT_PIN $path]\\t[get_property ENDPOINT_PIN $path]\\t[get_property SLACK $path]\\t[get_property DATAPATH_DELAY $path]\\t[get_property LOGIC_LEVELS $path]"
 }
 close $q
}
close $f
puts V107_READONLY_LOOKUP_PROBE_COMPLETE
''')
 shutil.copyfile(build/'run.tcl',out/'run.tcl');shutil.copyfile(Path(__file__),out/'lookup_probe.py')
 name='gamebub-v107-lookup-'+stamp.lower();cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount',f'type=bind,src={TOOLS},dst=/opt/amd-tools,readonly','--mount',f'type=bind,src={LICENSE},dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={checkpoint},dst=/parent/route.dcp,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',str(mapped),'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','300s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source','run.tcl','-tclargs',str(mapped)]
 r=dict(schema='v107-readonly-lookup-timing-probe-v1',status='RUNNING',command=cmd,parent_receipt_sha256=sha(PARENT),checkpoint_sha256_before=sha(checkpoint),checkpoint_readonly=True,no_RTL_or_clock_or_exception_edits=True,memory_samples=[]);start=time.monotonic();last=-5;stop=None;code=None
 print('LOOKUP_PROBE_STARTED',out.relative_to(ROOT),flush=True)
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
  r['status']='PASS_READONLY_TIMING_EXTRACTION' if code==0 and 'V107_READONLY_LOOKUP_PROBE_COMPLETE' in (out/'tool.log').read_text(errors='replace') else 'FAIL_TOOL_OR_QUERY'
 finally:
  r.update(exit_code=code,wall_seconds=time.monotonic()-start,stop_reason=stop,checkpoint_sha256_after=sha(checkpoint));assert r['checkpoint_sha256_after']==r['checkpoint_sha256_before']
  for p in sorted((build/'results').glob('*')):
   if p.is_file():dst=out/'reports'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(p,dst)
  r['retained_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('LOOKUP_PROBE_FINISHED',r['status'],code,flush=True)
 if r['status']!='PASS_READONLY_TIMING_EXTRACTION':raise SystemExit(1)
if __name__=='__main__':main()
