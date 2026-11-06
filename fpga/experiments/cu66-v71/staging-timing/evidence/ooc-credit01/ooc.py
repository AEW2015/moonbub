"""Matched DY71 split-bridge staging OOC; unchanged prior clock/IO/CDC budgets."""
from pathlib import Path
import argparse,ast,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/staging-timing';b=r/'fpga/experiments/cu66-v71/bus-split';a=argparse.ArgumentParser();a.add_argument('--variant',choices=['old','credit','safe'],required=True);a.add_argument('--output',required=True);args=a.parse_args();o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);(o/'tmp').mkdir();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
wrapper=b/'cu71_bus_split_ooc.sv';text=wrapper.read_text().replace('module cu71_bus_split_ooc(','module dy71_staging_ooc(').replace('cu71_local_control_split control_plane(','dy71_local_control_'+('split'if args.variant=='old'else args.variant)+' control_plane(');assert 'dy71_local_control_'in text;(o/'dy71_staging_ooc.sv').write_text(text,newline='\n')
control=b/'dy71_local_control_split.sv'if args.variant=='old'else(d/('safety-v002'if args.variant=='safe'else'')/('dy71_local_control_'+args.variant+'.sv'))
stage=r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv'if args.variant=='old'else(d/('safety-v002'if args.variant=='safe'else'')/('cu71_packet_staging_'+args.variant+'.sv'))
sources=[control,stage,b/'cu71_bus_cdc_split.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_arbiter.sv',r/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',Path(__file__).resolve()]
for f in sources:shutil.copyfile(f,o/f.name)
parent_script=r/'scripts/cu66-v71/bus-split/ooc.py';tree=ast.parse(parent_script.read_text());raw=next(n.value for n in ast.walk(tree)if isinstance(n,ast.Constant)and isinstance(n.value,str)and n.value.startswith('set_param general.maxThreads 2'));tcl=raw.replace('TOP','dy71_staging_ooc').replace(chr(92)*2,chr(92))
extra='''
set held [get_cells -hier -regexp {control_plane/staging/held_count_reg.*}]
if {[llength $held]!=3} {error "expected3heldcountFF"}
set held_ce [get_pins -of_objects $held -filter {REF_PIN_NAME == CE}]
report_timing -to $held -max_paths 30 -file [file join $out staging-held-all.rpt]
if {[llength $held_ce]>0} {report_timing -to $held_ce -max_paths 30 -file [file join $out staging-held-enable.rpt]}
set packet_regs [get_cells -hier -regexp {control_plane/staging/(packet_bytes|written_bytes)_reg.*}]
report_timing -from $packet_regs -to $held -max_paths 30 -file [file join $out packet-to-held.rpt]
report_timing -through [get_cells -hier -filter {NAME =~ control_plane/staging/*}] -max_paths 50 -file [file join $out staging-cone.rpt]
set credit_regs [get_cells -quiet -hier -regexp {control_plane/staging/(remaining_bytes|upload_capacity|within_packet)_reg.*}]
if {[llength $credit_regs]>0} {
 report_timing -to $credit_regs -max_paths 30 -file [file join $out credit-update.rpt]
} else {
 set f [open [file join $out credit-update.rpt] w];puts $f "NOT_APPLICABLE_PARENT_HAS_NO_CREDIT_REGISTERS";close $f
}
'''
tcl=tcl.replace('write_checkpoint -force',extra+'\nwrite_checkpoint -force');(o/'executed.tcl').write_text(tcl,newline='\n');shutil.copyfile(parent_script,o/'parent-ooc.py');pins={str(f):sha(f)for f in sources+[wrapper,parent_script]};(o/'source-freeze.json').write_text(json.dumps({'originals':pins,'compiled':{f.name:sha(f)for f in o.glob('*.sv')},'clocks_IO_CDC':'Byte-identical original OOC Tcl after TOP replacement; only observer reports appended','variant':args.variant,'profile':'DY71'},indent=2)+'\n')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)];start=time.monotonic()
with(o/'native.log').open('w')as log:p=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')),stdout=log,stderr=subprocess.STDOUT,timeout=1800)
(o/'execution.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode,'seconds':time.monotonic()-start},indent=2)+'\n');assert p.returncode==0
assert all(sha(Path(n))==h for n,h in pins.items());assert 'BUS_SPLIT_OOC_UNPLACED_ONLY_NOT_BOARD_SIGNOFF'in(o/'native.log').read_text()
(o/'result.json').write_text(json.dumps({'status':'OOC_EXECUTED_NOT_PLACED_TIMING_QUALIFICATION','variant':args.variant,'hardware':False,'BIT':False,'source_freeze_sha256':sha(o/'source-freeze.json')},indent=2)+'\n');print(args.variant,'OOC_COMPLETE')
