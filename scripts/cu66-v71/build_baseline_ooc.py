"""Source-pinned exact-target CU70 resource baseline; synthesis only, no image/HW."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[2]
o=r/'fpga/experiments/cu66-v71/build/baseline-synth01';o.mkdir(parents=True,exist_ok=False)
s=json.loads((r/'fpga/experiments/cu66-v70/system/sources.json').read_text())
files=[n for n in s['rtl_sources'] if not n.endswith(('_sim.sv','_model.sv'))]
for d in s['include_dirs']:
 files.extend(str(f.relative_to(r)).replace('\\','/') for f in (r/d).glob('*.svh'))
files=list(dict.fromkeys(files));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={n:sha(r/n) for n in files}
for n in files:
 f=o/'inputs'/n;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,f)
(o/'source-freeze.json').write_text(json.dumps(pins,indent=2)+'\n')
t='set_param general.maxThreads 2\nset out [file normalize [lindex $argv 0]]\nset root [file join $out inputs]\n'
t+='set part xc7a100tcsg324-1\nif {[llength [get_parts -quiet $part]]!=1} {error "Exact target unavailable"}\ncreate_project -in_memory -part $part cu70_resource\n'
t+='set_property include_dirs [list '+ ' '.join('[file join $root '+d+']' for d in s['include_dirs'])+'] [current_fileset]\n'
t+='\n'.join('read_verilog -sv [file join $root '+n+']' for n in files if n.endswith('.sv'))+'\n'
t+='synth_design -top cu70_system -part $part -mode out_of_context -generic USE_STRIP=1\n'
t+='report_utilization -hierarchical -file [file join $out utilization.rpt]\nwrite_checkpoint -force [file join $out synthesized.dcp]\nputs "CU71_BASELINE_SYNTHESIS_COMPLETE_NO_BOARD_TIMING_OR_HARDWARE_CLAIM"\n'
(o/'executed.tcl').write_text(t,newline='\n');(o/'tmp').mkdir()
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)]
start=time.monotonic();p=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')))
assert pins=={n:sha(r/n) for n in files},'Frozen baseline changed'
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,seconds=time.monotonic()-start,hardware=False,scope='Exact-target synthesis/resource baseline only'),indent=2)+'\n')
raise SystemExit(p.returncode)
