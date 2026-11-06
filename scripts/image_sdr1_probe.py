"""Qualify SDR1 routed reports and generate a volatile-use BIT/LTX, never load it."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,time
r=Path(__file__).resolve().parents[1];c=r/'fpga/diagnostics/sdr1-20261105';origin=c/'implementation03'
a=argparse.ArgumentParser();a.add_argument('--result',default='implementation03');a.add_argument('--output',default='image03');args=a.parse_args();p=c/args.result
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert json.loads((origin/'execution.json').read_text())['returncode']==0
run=json.loads((p/'execution.json').read_text());assert run['returncode']==0
if p!=origin:
 assert run['parent_sha256']==sha(origin/'routed.dcp') and run['parent_unchanged']
 assert run['RTL_changed'] is False and run['constraints_changed'] is False
assert 'ERROR:' not in (p/'vivado.log').read_text()
for n,h in json.loads((origin/'source-freeze.json').read_text()).items():
 assert sha(origin/n)==h,n
for name in ['simulation04','simulation05']:
 m=json.loads((c/name/'result.json').read_text());assert m['status']=='PASS_NATIVE_PAD_MODEL_ONLY'
 for n in ['engine.sv','controller.sv']:assert sha(origin/'inputs'/n)==m['sources'][n],n
s=(p/'timing-summary.rpt').read_text()
rows=s.split('WNS(ns)',1)[1].splitlines();v=next(x.split()for x in rows if re.match(r'^\s*-?\d+\.\d+',x))
assert len(v)==12,v
assert all(float(v[i])>0 for i in [0,4,8]),v
assert all(int(v[i])==0 for i in [2,6,10]),v
route=(p/'route-status.rpt').read_text()
get=lambda name:int(re.search(re.escape(name)+r'\.*\s*:\s*(\d+)',route)[1])
assert get('# of routable nets')==get('# of fully routed nets')>0
assert get('# of nets with routing errors')==0
checks=(p/'check-timing.rpt').read_text()
expected=dict(no_clock=0,constant_clock=0,pulse_width_clock=0,unconstrained_internal_endpoints=0,
 no_input_delay=17,no_output_delay=2,multiple_clock=0,generated_clocks=0,loops=0,
 partial_input_delay=1,partial_output_delay=0,latch_loops=0)
for k,vv in expected.items():assert re.search(r'checking '+k+r' \('+str(vv)+r'\)',checks),k
assert not re.search(r'\|\s*\S+\s*\|\s*Error\s*\|',(p/'drc.rpt').read_text())
cdc=(p/'cdc.rpt').read_text();assert not re.search(r'^CDC-\d+\s+(Critical|Warning)\s+[1-9]',cdc,re.M)
o=c/args.output;o.mkdir(exist_ok=False);(o/'tmp').mkdir()
gate=dict(status='PASS_REPORT_AND_NATIVE_MODEL_GATES_NOT_HARDWARE',checkpoint_sha256=sha(p/'routed.dcp'),
 setup_ns=float(v[0]),hold_ns=float(v[4]),pulse_ns=float(v[8]),coverage=expected,
 reports={n:sha(p/n)for n in ['timing-summary.rpt','route-status.rpt','drc.rpt','cdc.rpt','check-timing.rpt']},
 simulation_results={n:sha(c/n/'result.json')for n in ['simulation04','simulation05']},hardware=False)
(o/'gate.json').write_text(json.dumps(gate,indent=2)+'\n')
script='''set cp [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
open_checkpoint $cp
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "Wrong part"}
foreach type {max min} {
 set paths [get_timing_paths -delay_type $type -max_paths 1]
 if {[llength $paths]!=1||[get_property SLACK $paths]<=0} {error "Timing failure"}
}
report_drc -no_waivers -file [file join $out drc-native.rpt]
foreach violation [get_drc_violations] {
 if {[get_property SEVERITY $violation] eq "Error"} {error "Native DRC error"}
}
set_property BITSTREAM.CONFIG.USERID 0x53445231 [current_design]
set_property BITSTREAM.CONFIG.USR_ACCESS 0x53445231 [current_design]
write_debug_probes -force [file join $out moonbub-sdr1.ltx]
write_bitstream -force [file join $out moonbub-sdr1.bit]
puts "SDR1_BIT_LTX_ONLY_NO_HARDWARE"
close_design
'''
(o/'executed.tcl').write_text(script,newline='\n')
env=dict(os.environ);env['TEMP']=str(o/'tmp');env['TMP']=str(o/'tmp')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(p/'routed.dcp'),str(o)]
t=time.monotonic();q=subprocess.run(cmd,cwd=o,env=env)
assert sha(p/'routed.dcp')==gate['checkpoint_sha256']
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-t,hardware=False),indent=2)+'\n')
assert q.returncode==0
assert 'ERROR:' not in (o/'vivado.log').read_text()
(o/'image-hashes.json').write_text(json.dumps({n:sha(o/n)for n in ['moonbub-sdr1.bit','moonbub-sdr1.ltx','executed.tcl','gate.json']},indent=2)+'\n')
print('SDR1_IMAGE_GENERATED_NOT_PROGRAMMED',o)
