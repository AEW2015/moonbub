"""Native entropy timing diagnostic with explicit upstream/downstream register budget."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[2];d=r/'fpga/experiments/cu66-v71/entropy';src=d/'cu71_ab38_decoder_cfgpipe.sv'
o=d/'evidence/ooc01';o.mkdir(parents=True,exist_ok=False);shutil.copyfile(src,o/src.name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(src)
t='''set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 cu71_entropy_ooc
read_verilog -sv [file join $out cu71_ab38_decoder_cfgpipe.sv]
synth_design -top cu71_ab38_decoder_cfgpipe -mode out_of_context -part xc7a100tcsg324-1
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
puts CU71_ENTROPY_OOC_DIAGNOSTIC_NOT_BOARD_TIMING
'''
(o/'executed.tcl').write_text(t,newline='\n');(o/'tmp').mkdir()
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)]
start=time.monotonic();p=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')))
assert sha(src)==before
(o/'execution.json').write_text(json.dumps(dict(returncode=p.returncode,seconds=time.monotonic()-start,command=cmd,source_sha256=before,
 scope='Synthesis timing with1ns max input/output register budget, not routed board or changed board constraints',hardware=False),indent=2)+'\n')
raise SystemExit(p.returncode)
