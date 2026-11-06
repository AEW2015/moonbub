"""Matched full-base OOC, actual dependencies and error-feedback cone retained."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/tag-equality-v001';p=argparse.ArgumentParser();p.add_argument('--variant',choices=['old','balanced'],required=True);p.add_argument('--output',required=True);a=p.parse_args();o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);(o/'tmp').mkdir();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();manifest=(r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003/sources.json')if a.variant=='old'else d/'sources.json';m=json.loads(manifest.read_text());pins={}
for name,h in m['sources_sha256'].items():
 assert sha(r/name)==h;dest=o/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/name,dest);pins[name]=h
for inc in m['include_dirs']:
 for f in(r/inc).glob('*.svh'):
  name=f.relative_to(r).as_posix();dest=o/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);pins[name]=sha(f)
shutil.copyfile(Path(__file__),o/'executed-builder.py');(o/'source-freeze.json').write_text(json.dumps({'inputs':pins,'manifest_path':str(manifest),'manifest_sha256':sha(manifest),'builder_sha256':sha(Path(__file__)),'variant':a.variant,'top':'cu71_base_pipeline_math'},indent=2)+'\n')
t='set_param general.maxThreads 2\nset out [file normalize [lindex $argv 0]]\nset root [file join $out inputs]\ncreate_project -in_memory -part xc7a100tcsg324-1 tag_base\n';t+='set_property include_dirs [list '+' '.join('[file join $root '+n+']'for n in m['include_dirs'])+'] [current_fileset]\n';t+='\n'.join('read_verilog -sv [file join $root '+n+']'for n in m['sources'])+'\n'
t+=r'''
synth_design -top cu71_base_pipeline_math -mode out_of_context -part xc7a100tcsg324-1 -flatten_hierarchy none
create_clock -period 10.0 -name core [get_ports clk]
set_input_delay -clock core -max 1.0 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock core -min 0.0 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock core -max 1.0 [get_ports -filter {DIRECTION == OUT}]
set_output_delay -clock core -min 0.0 [get_ports -filter {DIRECTION == OUT}]
set digest_regs [get_cells -quiet -hier -regexp {^canonical/sha/hash_state_reg\[[0-7]\]\[[0-9]+\]$}]
set work_regs [get_cells -quiet -hier -regexp {^canonical/sha/[a-h]_reg\[[0-9]+\]$}]
if {[llength $digest_regs]!=256 || [llength $work_regs]!=256} {error "Exact actual SHA source/destination FF count differs"}
set digest_C [get_pins -of_objects $digest_regs -filter {REF_PIN_NAME == C}]
set work_CE [get_pins -of_objects $work_regs -filter {REF_PIN_NAME == CE}]
if {[llength $digest_C]!=256 || [llength $work_CE]!=256} {error "SHA timing endpoint roles differ"}
report_timing -from $digest_C -to $work_CE -max_paths 40 -file [file join $out digest-to-working-CE.rpt]
set f [open [file join $out target-counts.txt] w];puts $f "DIGEST_C=[llength $digest_C] WORKING_CE=[llength $work_CE]";close $f
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
report_timing -delay_type max -max_paths 40 -file [file join $out setup-paths.rpt]
report_timing -delay_type min -max_paths 30 -file [file join $out hold-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
write_checkpoint -force [file join $out synthesized.dcp]
puts TAG_BASE_OOC_COMPLETE_UNPLACED_NOT_BOARD_SIGNOFF
'''.replace(chr(92)*2,chr(92))
(o/'executed.tcl').write_text(t,newline='\n');cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)];start=time.monotonic()
with(o/'console.log').open('w')as log:q=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')),stdout=log,stderr=subprocess.STDOUT,timeout=2400)
(o/'execution.json').write_text(json.dumps({'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start},indent=2)+'\n');assert q.returncode==0
assert 'TAG_BASE_OOC_COMPLETE_UNPLACED_NOT_BOARD_SIGNOFF'in(o/'console.log').read_text();assert all(sha(r/n)==h and sha(o/'inputs'/n)==h for n,h in pins.items())
(o/'result.json').write_text(json.dumps({'status':'MATCHED_FULL_BASE_OOC_EXECUTED_NO_BOARD_QUALIFICATION','variant':a.variant,'hardware':False,'BIT':False,'source_freeze_sha256':sha(o/'source-freeze.json')},indent=2)+'\n');print(a.variant,'FULL_BASE_OOC_COMPLETE')
