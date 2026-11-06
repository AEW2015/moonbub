"""Native exact-device storage inference check; not board timing/image signoff."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[2];src=r/'fpga/experiments/cu66-v71/rows/cu71_tile_rows.sv'
o=r/'fpga/experiments/cu66-v71/rows/evidence/ooc01';o.mkdir(parents=True,exist_ok=False)
shutil.copyfile(src,o/'cu71_tile_rows.sv');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(src)
t='''set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 cu71_rows_ooc
read_verilog -sv [file join $out cu71_tile_rows.sv]
synth_design -top cu71_tile_rows -mode out_of_context -part xc7a100tcsg324-1 -generic STRIP_BANKS=2
create_clock -period 10.0 -name core [get_ports clk]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_timing_summary -report_unconstrained -file [file join $out timing.rpt]
set f [open [file join $out inference.txt] w]
set ram [get_cells -quiet -hier -filter {REF_NAME =~ RAMB*}]
set ff [get_cells -quiet -hier -filter {REF_NAME =~ FD*}]
puts $f "BRAM_CELLS=[llength $ram] FF_CELLS=[llength $ff]"
foreach c $ram {puts $f "$c [get_property REF_NAME $c]"}
close $f
write_checkpoint -force [file join $out synthesized.dcp]
if {[llength $ram]<2||[llength $ff]>3000} {error "Storage inference/resource gate failed"}
puts "CU71_ROWS_BRAM_INFERENCE_PASS_NOT_BOARD_TIMING"
'''
(o/'executed.tcl').write_text(t,newline='\n');(o/'tmp').mkdir()
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)]
start=time.monotonic();p=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')))
assert sha(src)==before and sha(o/'cu71_tile_rows.sv')==before
(o/'result.json').write_text(json.dumps(dict(status='PASS_EXACT_TARGET_BRAM_INFERENCE' if p.returncode==0 else 'FAIL_INFERENCE',returncode=p.returncode,seconds=time.monotonic()-start,source_sha256=before,hardware=False,command=cmd),indent=2)+'\n')
raise SystemExit(p.returncode)
