"""Exact-part, 100 MHz leaf setup estimate, not routed board signoff."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
root=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args()
out=(root/args.output).resolve();out.mkdir(parents=True,exist_ok=False)
source=root/'fpga/experiments/cu66-v71/inverse-index/cu71_idct_indexed.sv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();original=sha(source)
shutil.copyfile(source,out/source.name);(out/'tmp').mkdir()
tcl='''set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 idct_indexed
read_verilog -sv [file join $out cu71_idct_indexed.sv]
synth_design -mode out_of_context -top cu71_idct_indexed -part xc7a100tcsg324-1
create_clock -period 10 -name core [get_ports clk]
set_input_delay -clock core 1 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock core 1 [get_ports -filter {DIRECTION == OUT}]
write_checkpoint -force [file join $out synthesized.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
report_timing -delay_type max -max_paths 20 -file [file join $out setup-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
puts IDCT_INDEXED_LEAF_REPORTS_ONLY_NO_BIT_OR_HARDWARE
'''
(out/'executed.tcl').write_text(tcl,newline='\n')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(out/'executed.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(out)]
start=time.monotonic();p=subprocess.run(cmd,cwd=out,env=dict(os.environ,TEMP=str(out/'tmp'),TMP=str(out/'tmp')))
assert sha(source)==original==sha(out/source.name)
(out/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,seconds=time.monotonic()-start,source_sha256=original,
 scope='Unplaced diagnostic clock/input/output budget; positive setup does not establish hold/routed timing',hardware=False,BIT=False),indent=2)+'\n')
raise SystemExit(p.returncode)
