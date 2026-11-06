"""Build a small, distinct JTAG SDRAM diagnostic. Never connects to hardware."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[1];c=r/'fpga/diagnostics/sdr1-20261105';s=c/'source-v005'
assert json.loads((c/'simulation03/result.json').read_text())['status']=='PASS_NATIVE_PAD_MODEL_ONLY'
o=c/'implementation03';o.mkdir(exist_ok=False);shutil.copytree(s,o/'inputs');(o/'tmp').mkdir()
# Exact unchanged numeric I/O budgets, only with the smaller design's hierarchy.
p=r/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002/inputs/constraints/timing-cpl1-reviewed.tcl'
t=p.read_text().split('proc required_cells',1)[0].replace('diagnostic/core/memory/controller','controller')
t+='''
set captures [get_cells -hier -regexp {^controller/dq_capture_reg\[[0-9]+\]$}]
if {[llength $captures]!=16} {error "Expected 16 input capture FFs"}
set rc [get_clocks -of_objects [get_pins read_clock/O]]
if {[get_property PERIOD $rc]!=10.0 || abs([lindex [get_property WAVEFORM $rc] 0]-7.625)>0.001} {error "Wrong receive clock"}
set_multicycle_path 2 -setup -from [get_ports {sdram_dq[*]}] -to [get_pins -of_objects $captures -filter {REF_PIN_NAME == D}]
set ep [get_cells -hier -regexp {^endpoint/(sck_sync_reg\[0\]|cs_sync_reg\[0\]|dq_meta_reg\[[0-3]\]|buttons_meta_reg\[[0-9]+\]|vblank_sync_reg\[0\])$}]
if {[llength $ep]!=19} {error "Unexpected endpoint synchronizer prefix count"}
set_false_path -to [get_pins -of_objects $ep -filter {REF_PIN_NAME == D}]
set panel [get_cells -hier -regexp {^panel_(done|bad)_reg\[0\]$}]
if {[llength $panel]!=2} {error "Missing panel status synchronizers"}
set_false_path -to [get_pins -of_objects $panel -filter {REF_PIN_NAME == D}]
set resets [get_cells -hier -regexp {^rst(100|200|pixel)_reg.*}]
set_false_path -to [get_pins -of_objects $resets -filter {REF_PIN_NAME == PRE || REF_PIN_NAME == CLR}]
set_max_delay -datapath_only 10.0 -from [all_registers -clock_pins] -to [get_ports {mcu_spi_d[*] mcu_irq_n}]
set_max_delay -datapath_only 10.0 -from [get_ports mcu_spi_cs_n] -to [get_ports {mcu_spi_d[*]}]
'''
(o/'memory-timing.tcl').write_text(t,newline='\n')
script='''set out [file normalize [lindex $argv 0]]
set src [file join $out inputs]
set_param general.maxThreads 2
create_project sdr1 [file join $out project] -part xc7a100tcsg324-1
set_property target_language Verilog [current_project]
foreach name {top.sv engine.sv controller.sv endpoint.sv} {add_files [file join $src $name]}
foreach name {lcd_pins_rev4.xdc sdram_pins_rev4.xdc buttons.xdc platform.xdc} {add_files -fileset constrs_1 [file join $src constraints $name]}
create_ip -name vio -vendor xilinx.com -library ip -module_name sdr1_vio
set config [list CONFIG.C_NUM_PROBE_IN {9} CONFIG.C_NUM_PROBE_OUT {1} CONFIG.C_PROBE_OUT0_WIDTH {1}]
foreach i {0 1 2 6 7 8} {lappend config CONFIG.C_PROBE_IN${i}_WIDTH {32}}
foreach i {3 4 5} {lappend config CONFIG.C_PROBE_IN${i}_WIDTH {128}}
set_property -dict $config [get_ips sdr1_vio]
generate_target all [get_ips sdr1_vio]
set_property top sdr1_top [current_fileset]
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis did not complete"}
open_run synth_1
source [file join $out memory-timing.tcl]
write_checkpoint [file join $out constrained.dcp]
opt_design
place_design
phys_opt_design
route_design
write_checkpoint [file join $out routed.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_route_status -file [file join $out route-status.rpt]
report_timing -delay_type max -max_paths 20 -file [file join $out setup.rpt]
report_timing -delay_type min -max_paths 20 -file [file join $out hold.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
report_drc -no_waivers -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_utilization -file [file join $out utilization.rpt]
puts "SDR1_ROUTED_REPORTS_ONLY_NO_IMAGE_NO_HARDWARE"
close_design
close_project
'''
(o/'build.tcl').write_text(script,newline='\n')
freeze={str(f.relative_to(o)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest()for f in o.rglob('*')if f.is_file()}
(o/'source-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
env=dict(os.environ);env['TEMP']=str(o/'tmp');env['TMP']=str(o/'tmp')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'build.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)]
start=time.monotonic();q=subprocess.run(cmd,cwd=o,env=env)
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=q.returncode,wall_seconds=time.monotonic()-start,BIT=False,hardware=False),indent=2)+'\n')
raise SystemExit(q.returncode)
