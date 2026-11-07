from pathlib import Path
import hashlib,json,os,re,subprocess,time
p=Path(__file__).resolve().parent;b=Path('C:/mb70/dy71-v027-20261107-v001');o=b/'reset-mapping01';o.mkdir();tmp=Path('C:/vtmp')/('rst-map-'+str(time.time_ns()));tmp.mkdir()
s='''set_param general.maxThreads 2
open_checkpoint {C:/mb70/dy71-v027-20261107-v001/constrained.dcp}
set out {C:/mb70/dy71-v027-20261107-v001/reset-mapping01}
set buf [get_cells -quiet core_reset_distribution]
if {[llength $buf]!=1 || [get_property REF_NAME $buf] ne "BUFG"} {error "Explicit reset BUFG missing"}
report_property $buf -file [file join $out buffer.rpt]
set stages [get_cells -quiet -hier -regexp {joint_core_reset_reg\[[0-3]\]}]
if {[llength $stages]!=4} {error "Wrong protected reset stage count"}
set f [open [file join $out stages.tsv] w]
foreach c $stages {
 if {[get_property ASYNC_REG $c] ne "1"} {error "Reset stage lost ASYNC_REG"}
 set ck [get_clocks -of_objects [get_pins $c/C]]
 if {[llength $ck]!=1 || abs([get_property PERIOD $ck]-10.0)>0.001} {error "Reset stage clock changed"}
 puts $f "$c\t[get_property REF_NAME $c]\t[get_property ASYNC_REG $c]\t[get_property PERIOD $ck]"
}
close $f
report_property [get_nets -of_objects [get_pins core_reset_distribution/O]] -file [file join $out output-net.rpt]
puts V027_RESET_MAPPING_COMPLETE_NO_BIT_OR_HARDWARE
close_design
'''
(o/'executed.tcl').write_text(s);cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou')]
with(o/'console.log').open('x')as f:q=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp)),stdout=f,stderr=subprocess.STDOUT)
log=(o/'console.log').read_text();passed=q.returncode==0 and 'V027_RESET_MAPPING_COMPLETE_NO_BIT_OR_HARDWARE'in log and not re.search(r'^ERROR:',log,re.M)
(o/'execution.json').write_text(json.dumps(dict(status='PASS_EXPLICIT_BUFG_FOUR_PROTECTED_STAGES'if passed else'FAIL_OR_INCOMPLETE',cmd=cmd,returncode=q.returncode,checkpoint_sha256=hashlib.sha256((b/'constrained.dcp').read_bytes()).hexdigest(),script_sha256=hashlib.sha256((o/'executed.tcl').read_bytes()).hexdigest(),hardware=False),indent=2)+'\n');print('RESET_MAPPING_PASS',passed,flush=True);assert passed
