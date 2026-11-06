"""Hash-frozen single-file OOC report, never a routed-board qualification."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,time
r=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--source',required=True);p.add_argument('--top',required=True)
p.add_argument('--output',required=True);p.add_argument('--proof',action='append',required=True)
p.add_argument('--include-file',action='append',default=[])
p.add_argument('--temp-dir',type=Path)
a=p.parse_args();source=(r/a.source).resolve();out=(r/a.output).resolve()
assert source.is_relative_to(r) and out.is_relative_to(r)
assert a.top.replace('_','').isalnum()
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
original=sha(source);proofs={}
for name in a.proof:
 q=(r/name).resolve();d=json.loads(q.read_text());assert d['status'].startswith('PASS_'),name
 proofs[name]=sha(q)
out.mkdir(parents=True,exist_ok=False);shutil.copyfile(source,out/source.name)
headers={}
for name in a.include_file:
 q=(r/name).resolve();assert q.is_relative_to(r) and q.is_file()
 assert not(out/q.name).exists(),'Header basename collision'
 headers[name]=sha(q);shutil.copyfile(q,out/q.name)
shutil.copyfile(__file__,out/'executed-builder.py');(out/'tmp').mkdir()
native_temp=a.temp_dir.resolve()if a.temp_dir else out/'tmp'
if a.temp_dir:native_temp.mkdir(parents=True,exist_ok=False)
tcl='''set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 leaf
set_property include_dirs [list $out] [current_fileset]
'''
tcl+='read_verilog -sv [file join $out '+source.name+']\n'
tcl+='synth_design -mode out_of_context -top '+a.top+' -part xc7a100tcsg324-1\n'
tcl+='''create_clock -period 10 -name core [get_ports clk]
set_input_delay -clock core 1 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock core 1 [get_ports -filter {DIRECTION == OUT}]
write_checkpoint -force [file join $out synthesized.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
report_timing -delay_type max -max_paths 25 -file [file join $out setup-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
puts LEAF_REPORTS_COMPLETE_NOT_ROUTED_BOARD_SIGNOFF
'''
(out/'executed.tcl').write_text(tcl,newline='\n')
(out/'source-freeze.json').write_text(json.dumps(dict(source=a.source,sha256=original,proofs=proofs,include_files=headers),indent=2)+'\n')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(out/'executed.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(out)]
start=time.monotonic()
with(out/'console.log').open('w')as log:
 proc=subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,TEMP=str(native_temp),TMP=str(native_temp)))
assert original==sha(source)==sha(out/source.name)
assert proofs=={n:sha(r/n)for n in proofs}
assert headers=={n:sha(r/n)for n in headers}
assert headers=={n:sha(out/Path(n).name)for n in headers}
complete='LEAF_REPORTS_COMPLETE_NOT_ROUTED_BOARD_SIGNOFF' in(out/'console.log').read_text()
errors=re.findall(r'^ERROR:.*$',(out/'console.log').read_text(),re.M)
reports=all((out/n).is_file()and(out/n).stat().st_size for n in['synthesized.dcp','timing.rpt','setup-paths.rpt','utilization.rpt'])
result=dict(command=cmd,returncode=proc.returncode,seconds=time.monotonic()-start,source_sha256=original,
            completion_marker=complete,reports_present=reports,hardware=False,BIT=False,
            TEMP_TMP=str(native_temp),native_errors=errors,
            scope='Unplaced exact-part synthesis at100MHz with1ns scalarIO budgets; not routed board or hold signoff')
(out/'execution.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
raise SystemExit(0 if proc.returncode==0 and complete and reports and not errors else(proc.returncode or 1))
