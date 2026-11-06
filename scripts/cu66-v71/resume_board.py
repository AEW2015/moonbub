"""Resume exact synthesized CU71 after obsolete ROM presence-guard correction."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[2];p=r/'fpga/experiments/cu66-v71/board/implementation01'
o=r/'fpga/experiments/cu66-v71/board/implementation02';o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((p/'execution.json').read_text())['returncode']!=0
assert 'Missing CDC objects: actual_rom (diagnostic/loader/rom.*)' in (p/'vivado.log').read_text()
old=p/'inputs/fpga/experiments/cu66-v71/board/source-v002/constraints/timing-cu71-reviewed.tcl'
new=r/'fpga/experiments/cu66-v71/board/source-v003/constraints/timing-cu71-reviewed.tcl'
assert old.read_text().replace('required_cells actual_rom {diagnostic/loader/rom.*}\n','')==new.read_text(),'Only obsolete object guard may change'
pins=json.loads((p/'source-freeze.json').read_text())
for n,h in pins.items():assert sha(p/'inputs'/n)==h,n
checkpoint=p/'synthesized.dcp';before=sha(checkpoint)
shutil.copyfile(new,o/'corrected-timing.tcl')
original=(p/'executed.tcl').read_text();tail=original.split('opt_design\n',1)[1]
text='set_param general.maxThreads 4\nset out [file normalize [lindex $argv 0]]\n'
text+='open_checkpoint {'+checkpoint.as_posix()+'}\nsource [file join $out corrected-timing.tcl]\n'
text+='write_checkpoint -force [file join $out constrained.dcp]\ncheck_timing -verbose -file [file join $out check-timing-postsynth.rpt]\nopt_design\n'+tail
(o/'executed.tcl').write_text(text,newline='\n');(o/'tmp').mkdir()
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)]
start=time.monotonic();q=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')))
assert sha(checkpoint)==before
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-start,parent_checkpoint=str(checkpoint),parent_sha256=before,parent_source_freeze_sha256=sha(p/'source-freeze.json'),corrected_constraints_sha256=sha(o/'corrected-timing.tcl'),
 RTL_changed=False,numeric_STA_commands_changed=False,change='Removed only obsolete CP23 ROM object-presence check; real CU71 packet RAM guard retained',hardware=False,BIT=False),indent=2)+'\n')
raise SystemExit(q.returncode)
