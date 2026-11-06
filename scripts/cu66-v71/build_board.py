"""Exact-source CU71 lab board implementation. No BIT emission or programming."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--board',default='fpga/experiments/cu66-v71/board/source-v002');args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
board=(r/args.board).resolve();v71='fpga/experiments/cu66-v71/'
s=json.loads((r/'fpga/experiments/cu66-v70/system/sources.json').read_text())
replacement={
 'fpga/experiments/cu66-v70/system/cu70_system.sv':v71+'system/cu71_system_bram.sv',
 'fpga/experiments/cu66-v70/receiver/cu70_receiver.sv':v71+'codec/cu71_receiver_bram.sv',
 'fpga/experiments/cu66-v69/integration/cu66_base_pipeline.sv':v71+'codec/cu71_base_pipeline_bram.sv',
 'fpga/experiments/cu66-v69/rows/cu66_tile_rows.sv':v71+'rows/cu71_tile_rows.sv',
 'fpga/experiments/cu66-v69/rows/cu66_rows_sha256.sv':v71+'codec/cu71_rows_sha256_bram.sv',
 'fpga/experiments/cu66-v70/memory/cu70_tile_memory.sv':v71+'memory/cu71_tile_memory.sv',
 'fpga/experiments/cu66-v70/memory/cu70_word_bridge.sv':v71+'memory/cu71_word_bridge.sv',
 'fpga/experiments/cu66-v70/memory/cu70_memory_system.sv':v71+'memory/cu71_memory_system.sv',
 'fpga/experiments/cu66-v70/memory/cu70_sdram_controller.sv':v71+'memory/moonshine_sdram_burst.sv',
 'fpga/experiments/cu66-v70/display/cu70_painter_strip.sv':v71+'display/cu71_painter_strip_pipe.sv',
 'fpga/experiments/cu66-v70/display/cu70_scanout.sv':v71+'display/cu71_scanout_prefetch.sv',
 'fpga/experiments/cu66-v70/display/cu70_lcd_lines.sv':v71+'display/cu71_lcd_lines.sv'}
files=[replacement.get(n,n) for n in s['rtl_sources'] if not n.endswith(('_sim.sv','_model.sv'))]
files.extend(v71+'system/'+n for n in ['cu71_local_control.sv','cu71_packet_staging.sv','cu71_packet_arbiter.sv'])
board_sv=['moonshine_top_cu71.sv','moonshine_qspi_endpoint.sv','moonshine_bus_cdc.sv']
files.extend(str((board/n).relative_to(r)).replace('\\','/') for n in board_sv)
include_dirs=s['include_dirs']
for d in include_dirs:files.extend(str(f.relative_to(r)).replace('\\','/') for f in (r/d).glob('*.svh'))
files.extend(str(f.relative_to(r)).replace('\\','/') for f in (board/'constraints').glob('*') if f.is_file())
files=list(dict.fromkeys(files));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={n:sha(r/n) for n in files}
assert sha(r/(v71+'display/cu71_painter_strip_pipe.sv'))=='9544e09f9fa22dac3332e0b46f07d38c29a2da1d702b9f0923c18de4d40c2f03'
for n in files:
 target=o/'inputs'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,target)
(o/'source-freeze.json').write_text(json.dumps(pins,indent=2)+'\n')
(o/'selection.json').write_text(json.dumps(dict(top='moonshine_top_cu71',part='xc7a100tcsg324-1',files=files,include_dirs=include_dirs,board=str(board),SIMULATION=False,scope='Local scalar-HUD correctness fixture with30s watchdog; not streaming rate qualified'),indent=2)+'\n')
t='''set_param general.maxThreads 4
set out [file normalize [lindex $argv 0]]
set root [file join $out inputs]
create_project -in_memory -part xc7a100tcsg324-1 cu71_board
'''
t+='set_property include_dirs [list '+' '.join('[file join $root '+d+']' for d in include_dirs)+'] [current_fileset]\n'
t+='\n'.join('read_verilog -sv [file join $root '+n+']' for n in files if n.endswith('.sv'))+'\n'
bc=str((board/'constraints').relative_to(r)).replace('\\','/')
for n in ['lcd_pins_rev4.xdc','sdram_pins_rev4.xdc','buttons.xdc','platform.xdc']:t+='read_xdc [file join $root '+bc+'/'+n+']\n'
t+='''synth_design -top moonshine_top_cu71 -part xc7a100tcsg324-1
write_checkpoint -force [file join $out synthesized.dcp]
report_utilization -hierarchical -file [file join $out synthesized-utilization.rpt]
report_clocks -file [file join $out synthesized-clocks.rpt]
'''
t+='source [file join $root '+bc+'/timing-cu71-reviewed.tcl]\n'
t+='''write_checkpoint -force [file join $out constrained.dcp]
check_timing -verbose -file [file join $out check-timing-postsynth.rpt]
opt_design
place_design
phys_opt_design
route_design
phys_opt_design -directive AggressiveExplore
route_design -directive Explore -tns_cleanup
write_checkpoint -force [file join $out routed.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_timing -delay_type max -max_paths 40 -file [file join $out setup-paths.rpt]
report_timing -delay_type min -max_paths 40 -file [file join $out hold-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_route_status -file [file join $out route-status.rpt]
report_drc -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
puts "CU71_BOARD_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE"
'''
(o/'executed.tcl').write_text(t,newline='\n');(o/'tmp').mkdir()
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)]
start=time.monotonic();p=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')))
assert pins=={n:sha(r/n) for n in files},'Selected sources changed during implementation'
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,seconds=time.monotonic()-start,hardware=False,BIT=False),indent=2)+'\n')
raise SystemExit(p.returncode)
