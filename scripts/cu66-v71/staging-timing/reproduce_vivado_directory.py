"""Exact archived-source/Tcl replay with isolated short cwd/TEMP/TMP only."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/tag-equality-v001';p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--output',required=True);a=p.parse_args();parent=Path(a.parent).resolve();o=Path(a.output).resolve();assert o.is_relative_to(Path('C:/vtmp').resolve());assert not o.exists();o.mkdir(parents=True);(o/'t').mkdir();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();freeze=json.loads((parent/'source-freeze.json').read_text());pins=freeze['inputs']
for name,h in pins.items():
 f=parent/'inputs'/name;assert sha(f)==h,name;dest=o/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);assert sha(dest)==h
body=(parent/'executed.tcl').read_text();(o/'parent-executed.tcl').write_bytes((parent/'executed.tcl').read_bytes())
observer='''# Observation only: no design/clock/budget or exception settings.
proc directory_trace {command operation} {
 if {[lindex $command 1] eq "mkdir"} {puts "OBSERVED_TCL_MKDIR [list $command]";puts "OBSERVED_TCL_MKDIR_CALLER [info frame -2]"}
}
trace add execution ::file enter directory_trace
puts "OBSERVED_NATIVE_CWD [pwd]"
puts "OBSERVED_NATIVE_TEMP $::env(TEMP)"
puts "OBSERVED_NATIVE_TMP $::env(TMP)"
''';(o/'executed.tcl').write_text(observer+body,newline='\n');assert(o/'executed.tcl').read_text()[len(observer):]==body
environment=dict(os.environ,TEMP=str(o/'t'),TMP=str(o/'t'));record={'parent':str(parent),'parent_Tcl_sha256':sha(parent/'executed.tcl'),'body_unchanged':True,'input_sha256':pins,'changes':['Short unique cwd','Short private childTEMP/TMP','Read-only Tcl mkdir trace and cwd/TEMP/TMP prints'],'NoDefaultCurrentDirectoryInExePath_unchanged':environment.get('NoDefaultCurrentDirectoryInExePath')==os.environ.get('NoDefaultCurrentDirectoryInExePath'),'NoDefaultCurrentDirectoryInExePath':environment.get('NoDefaultCurrentDirectoryInExePath'),'machine_environment_changed':False,'builder_sha256':sha(Path(__file__).resolve()),'hardware':False};(o/'source-binding.json').write_text(json.dumps(record,indent=2)+'\n');shutil.copyfile(Path(__file__).resolve(),o/'executed-builder.py')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)];start=time.monotonic()
with(o/'console.log').open('w')as log:q=subprocess.run(cmd,cwd=o,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
text=(o/'console.log').read_text();errors=[x for x in text.splitlines()if x.startswith('ERROR:')];complete='TAG_BASE_OOC_COMPLETE_UNPLACED_NOT_BOARD_SIGNOFF'in text;reports=all((o/f).is_file()and(o/f).stat().st_size for f in['synthesized.dcp','timing.rpt','digest-to-working-CE.rpt','utilization.rpt']);result={'status':'CLEAN_SHORT_PATH_EXACT_SOURCE_REPLAY'if q.returncode==0 and not errors and complete and reports else'INCOMPLETE_OR_NATIVE_ERROR_REPRODUCED','command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start,'native_errors':errors,'completion_marker':complete,'required_reports_present':reports,'Tcl_mkdir_observations':[x for x in text.splitlines()if x.startswith('OBSERVED_TCL_MKDIR')],'source_binding_sha256':sha(o/'source-binding.json'),'hardware':False,'BIT':False};(o/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert all(sha(o/'inputs'/n)==h and sha(parent/'inputs'/n)==h for n,h in pins.items());raise SystemExit(0 if result['status']=='CLEAN_SHORT_PATH_EXACT_SOURCE_REPLAY'else 1)
