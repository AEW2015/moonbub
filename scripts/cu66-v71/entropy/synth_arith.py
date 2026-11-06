"""Exact-part100MHz arithmetic-pipeline synthesis diagnostic, no hardware."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--source',type=Path);a=p.parse_args();r=Path(__file__).resolve().parents[3]
src=a.source.resolve()if a.source else r/'fpga/experiments/cu66-v71/entropy/cu71_ab38_decoder_arithpipe.sv';o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);shutil.copy2(src,o/src.name)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before=sha(src)
t='''set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 cu71_entropy_arith_ooc
read_verilog -sv [file join $out cu71_ab38_decoder_arithpipe.sv]
synth_design -top cu71_ab38_decoder_arithpipe -mode out_of_context -part xc7a100tcsg324-1
create_clock -period 10.0 -name core [get_ports clk]
set inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock core -max 1.0 $inputs
set_input_delay -clock core -min 0.0 $inputs
set_output_delay -clock core -max 1.0 [get_ports -filter {DIRECTION == OUT}]
set_output_delay -clock core -min 0.0 [get_ports -filter {DIRECTION == OUT}]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
report_timing -delay_type max -max_paths 30 -file [file join $out setup-paths.rpt]
write_checkpoint -force [file join $out synthesized.dcp]
puts CU71_ARITH_SYNTH_DIAGNOSTIC_NOT_BOARD_TIMING
'''
t=t.replace('cu71_ab38_decoder_arithpipe',src.stem)
(o/'executed.tcl').write_text(t,newline='\n');(o/'tmp').mkdir()
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)]
start=time.monotonic();q=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')))
assert sha(src)==before
(o/'execution.json').write_text(json.dumps({'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start,'source_sha256':before,'scope':'100MHzsyntheticOOCwithsame1nsmaxIOregisterbudgetasparent;notroutedboardtiming','hardware':False},indent=2)+'\n')
raise SystemExit(q.returncode)
