#!/usr/bin/env python3
"""Bounded before/after component inference; no routed parent timing claim."""
import datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v107-idct-reset';AREA=ROOT/'experiments/python-gamebub-v107/idct-reset/native';BUILD=Path('/home/lori/gamebub-build/cu66-v69')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def main():
 focus=json.loads((AREA.parent/'results.json').read_text());assert focus['status']=='PASS' and focus['actual_RTL_run'];assert sha(SRC/'cu66_idct8x8.sv')==focus['candidate']['sha256']
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir(parents=True);build=BUILD/('v107-idct-native-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=[(ROOT/'fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv','original.sv'),(SRC/'cu66_idct8x8.sv','candidate.sv'),(Path(__file__).resolve(),'native.py')]
 for source,name in files:shutil.copyfile(source,build/name);shutil.copyfile(source,out/name)
 tcl=r'''set build [file normalize [lindex $argv 0]]
proc input_starts {pin} {
 set names {}
 foreach obj [all_fanin -flat -startpoints_only -to $pin] {
  if {[get_property CLASS $obj] eq "port"} {lappend names $obj}
 }
 return [lsort -unique $names]
}
set_param general.maxThreads 2
foreach variant {original candidate} {
 set dst [file join $build results $variant]
 file mkdir $dst
 create_project -in_memory -part xc7a100tcsg324-1
 set_property include_dirs $build [current_fileset]
 read_verilog -sv [file join $build ${variant}.sv]
 synth_design -top cu66_idct8x8 -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt -directive Default
 create_clock -name unit_clk -period 10 [get_ports clk]
 write_checkpoint -force [file join $dst synth.dcp]
 write_verilog -force -mode funcsim [file join $dst mapped.v]
 report_utilization -hierarchical -file [file join $dst utilization.rpt]
 report_timing_summary -delay_type min_max -report_unconstrained -file [file join $dst timing.rpt]
 report_control_sets -verbose -file [file join $dst control-sets.rpt]
 report_high_fanout_nets -max_nets 30 -timing -load_types -file [file join $dst fanout.rpt]
 set f [open [file join $dst payload.tsv] w]
 puts $f "cell\tref\treset_pin\treset_driver\treset_is_ground\tce_driver\tce_port_fanin\treset_port_fanin\tce_register_starts"
 set payload [get_cells -hierarchical -regexp {(^|.*/)(source_tile_reg\[[0-9]+\])}]
 if {[llength $payload] != 1280} {error "payload count expected 1280 got [llength $payload]"}
 foreach c [lsort $payload] {
  set ref [get_property REF_NAME $c]
  set reset [get_pins -quiet $c/R]
  if {[llength $reset]!=1} {error "expected R pin $c"}
  set net [get_nets -of_objects $reset]
  set drivers [get_pins -of_objects $net -filter {DIRECTION == OUT}]
  set resetground 0
  foreach d $drivers {if {[get_property REF_NAME [get_cells -of_objects $d]] eq "GND"} {set resetground 1}}
  set ce [get_pins $c/CE]
  set cedrivers [get_pins -of_objects [get_nets -of_objects $ce] -filter {DIRECTION == OUT}]
  set ceports [input_starts $ce]
  set resetports [input_starts $reset]
  set regstarts {}
  foreach p [all_fanin -flat -startpoints_only -to $ce] {if {[get_property CLASS $p] eq "pin"} {lappend regstarts $p}}
  puts $f [join [list $c $ref $reset $drivers $resetground $cedrivers $ceports $resetports [lsort -unique $regstarts]] \t]
 }
 close $f
 set f [open [file join $dst reset-loads.tsv] w]
 puts $f "port\tregister_reset_endpoints\tall_flat_endpoints"
 foreach port {rst abort_frame in_valid} {
  set ends [all_fanout -flat -endpoints_only -from [get_ports $port]]
  set resets [filter $ends {REF_PIN_NAME == R || REF_PIN_NAME == S || REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}]
  puts $f "$port\t[llength $resets]\t[llength $ends]"
 }
 close $f
 puts "IDCT_COMPONENT_COMPLETE $variant"
 close_project
}
'''
 (build/'run.tcl').write_text(tcl);(build/'run.sh').write_text('#!/bin/bash\nset -euo pipefail\n/opt/amd-tools/2026.1/Vivado/bin/vivado -mode batch -nojournal -nolog -notrace -source run.tcl -tclargs "$PWD"\n')
 for name in ('run.tcl','run.sh'):shutil.copyfile(build/name,out/name)
 gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
 name='gamebub-v107-idct-native-'+stamp.lower();command=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/cache/vivado.lic,dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',mapped,'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','600s','bash','run.sh']
 r=dict(schema='v107-idct-component-inference-v1',status='RUNNING',command=command,source_sha256={str(p.relative_to(ROOT)):sha(p) for p,_ in files},candidate_sha256=sha(SRC/'cu66_idct8x8.sv'),focus_report=str((AREA.parent/'results.json').relative_to(ROOT)),focus_report_sha256=sha(AREA.parent/'results.json'),build_external=str(build),memory_samples=[],timeout_seconds=600,part='xc7a100tcsg324-1',synthetic_unit_clock_ns=10,no_parent_timing_claim=True,tools_and_license_readonly=True)
 write(out/'receipt.json',r);start=time.monotonic();stop=None;code=None;last=-5
 print('IDCT_NATIVE_STARTED',out.relative_to(ROOT),flush=True)
 try:
  with (out/'tool.log').open('w') as log:
   proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-start
    if elapsed-last>=5:
     m=dict(elapsed_seconds=elapsed,**memory());r['memory_samples'].append(m);last=elapsed
     if m['available_bytes']<4*1024**3 or m['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if elapsed>640:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
    time.sleep(.5)
   code=proc.wait(timeout=30)
  assert code==0,(code,stop)
  metrics={}
  import csv
  for variant in ('original','candidate'):
   rows=list(csv.DictReader((build/'results'/variant/'payload.tsv').open(),delimiter='\t'));assert len(rows)==1280
   metrics[variant]=dict(payload_cells=len(rows),payload_grounded_reset=sum(int(x['reset_is_ground']) for x in rows),payload_reset_port_fanin=sum(bool(x['reset_port_fanin']) for x in rows),payload_ce_port_fanin=sum(bool(x['ce_port_fanin']) for x in rows),types=sorted(set(x['ref'] for x in rows)),ce_drivers=sorted(set(x['ce_driver'] for x in rows)),ce_port_fanin=sorted(set(x['ce_port_fanin'] for x in rows)),reset_port_fanin=sorted(set(x['reset_port_fanin'] for x in rows)),ce_register_starts=sorted(set(x['ce_register_starts'] for x in rows)))
  assert metrics['original']['payload_grounded_reset']==0
  assert metrics['candidate']['payload_grounded_reset']==1280
  assert metrics['candidate']['payload_ce_port_fanin']==0
  assert metrics['original']['reset_port_fanin']==['abort_frame rst']
  assert metrics['original']['ce_port_fanin']==['abort_frame in_valid rst']
  assert metrics['candidate']['reset_port_fanin']==['']
  assert metrics['candidate']['ce_port_fanin']==['']
  assert metrics['candidate']['ce_register_starts']!=['']
  r.update(status='PASS_MEASURED_PRIVATE_RESET_AND_INPUT_CONTROL_REMOVAL',metrics=metrics)
 except BaseException as e:r.update(status='FAIL',error=repr(e));raise
 finally:
  r.update(exit_code=code,wall_seconds=time.monotonic()-start,stop_reason=stop,source_unchanged=all(sha(p)==r['source_sha256'][str(p.relative_to(ROOT))] for p,_ in files))
  for p in sorted((build/'results').rglob('*')):
   if p.is_file() and p.suffix in ('.rpt','.tsv','.v'):q=out/'reports'/p.relative_to(build/'results');q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('IDCT_NATIVE_FINISHED',r['status'],flush=True)
if __name__=='__main__':main()
