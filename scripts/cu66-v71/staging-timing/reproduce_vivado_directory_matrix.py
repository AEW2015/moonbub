"""One-factor native path isolation; never modifies/kills other builds."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--output',required=True);p.add_argument('--temp',required=True);a=p.parse_args();parent=Path(a.parent).resolve();o=Path(a.output).resolve();tmp=Path(a.temp).resolve();assert o.is_relative_to(r)or o.is_relative_to(Path('C:/vtmp').resolve());assert tmp.is_relative_to(r)or tmp.is_relative_to(Path('C:/vtmp').resolve());assert not o.exists()and not tmp.exists();o.mkdir(parents=True);tmp.mkdir(parents=True);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();freeze=json.loads((parent/'source-freeze.json').read_text());pins=freeze['inputs']
for name,h in pins.items():
 source=parent/'inputs'/name;assert sha(source)==h;dest=o/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
observer='''# Read-only native directory observer.
proc directory_trace {command operation} {
 if {[lindex $command 1] eq "mkdir"} {puts "OBSERVED_TCL_MKDIR [list $command]";set caller UNKNOWN;catch {set caller [info frame -2]};puts "OBSERVED_TCL_MKDIR_CALLER $caller"}
}
trace add execution ::file enter directory_trace
puts "OBSERVED_NATIVE_CWD [pwd]"
puts "OBSERVED_NATIVE_TEMP $::env(TEMP)"
puts "OBSERVED_NATIVE_TMP $::env(TMP)"
''';body=(parent/'executed.tcl').read_text();(o/'executed.tcl').write_text(observer+body,newline='\n');shutil.copyfile(Path(__file__).resolve(),o/'executed-builder.py');env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp));binding={'parent':str(parent),'parent_Tcl_sha256':sha(parent/'executed.tcl'),'body_unchanged':True,'inputs_sha256':pins,'cwd':str(o),'cwd_length':len(str(o)),'TEMP_TMP':str(tmp),'NoDefaultCurrentDirectoryInExePath':env.get('NoDefaultCurrentDirectoryInExePath'),'machine_environment_changed':False,'observer_only':True,'hardware':False};(o/'source-binding.json').write_text(json.dumps(binding,indent=2)+'\n')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)];start=time.monotonic();captured=False
with(o/'console.log').open('w')as log:
 proc=subprocess.Popen(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT)
 (o/'process.json').write_text(json.dumps({'PID':proc.pid,'command':cmd,'no_other_processes_modified':True},indent=2)+'\n')
 while proc.poll()is None:
  text=(o/'console.log').read_text(errors='replace')
  if 'ERROR: [Common 17-1257]'in text and not captured:
   captured=True;records=[];snapshot=o/'native-runtime-error-snapshot';snapshot.mkdir()
   for f in(o/'.Xil').rglob('*'):
    if f.is_file():
     records.append({'path':str(f),'length':len(str(f)),'bytes':f.stat().st_size})
     if f.suffix in['.tcl','.log','.rpt']:
      try:dest=snapshot/f.relative_to(o/'.Xil');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
      except FileNotFoundError:pass
   (snapshot/'file-list.json').write_text(json.dumps(records,indent=2)+'\n')
  if time.monotonic()-start>1800:
   (o/'timeout.json').write_text(json.dumps({'status':'OWN_CHILD_STILL_RUNNING_NOT_TERMINATED','PID':proc.pid,'hardware':False},indent=2)+'\n');raise RuntimeError('Native process exceeded observation deadline; not killed')
  time.sleep(1)
text=(o/'console.log').read_text();errors=[x for x in text.splitlines()if x.startswith('ERROR:')];complete='TAG_BASE_OOC_COMPLETE_UNPLACED_NOT_BOARD_SIGNOFF'in text;reports=all((o/n).is_file()and(o/n).stat().st_size for n in['synthesized.dcp','timing.rpt','digest-to-working-CE.rpt','utilization.rpt']);result={'status':'CLEAN_CONTROLLED_PATH_REPLAY'if proc.returncode==0 and not errors and complete and reports else'NATIVE_ERROR_OR_INCOMPLETE_CONTROLLED_PATH_REPLAY','returncode':proc.returncode,'seconds':time.monotonic()-start,'native_errors':errors,'completion_marker':complete,'required_reports_present':reports,'runtime_error_metadata_captured':captured,'source_binding_sha256':sha(o/'source-binding.json'),'hardware':False};(o/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert all(sha(o/'inputs'/n)==h for n,h in pins.items());raise SystemExit(0 if result['status']=='CLEAN_CONTROLLED_PATH_REPLAY'else 1)
