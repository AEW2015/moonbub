"""Matched unplaced exact-part OOC, short private job/TEMP directories."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/packet-prefix-v002'
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--work',required=True);a=p.parse_args();o=r/a.output;o.mkdir(parents=True,exist_ok=False);w=Path(a.work);w.mkdir(exist_ok=False)
for n in ['focused01','controls01']:assert json.loads((d/'evidence'/n/'result.json').read_text())['status'].startswith('PASS_')
shutil.copyfile(__file__,o/'executed-runner.py');runs=[]
for label in ['baseline','candidate']:
 b=w/label;b.mkdir();(b/'tmp').mkdir();e=o/label;e.mkdir()
 parent=r/'fpga/experiments/cu66-v69/packet/cu66_packet_control.sv';src=parent if label=='baseline'else d/'cu71_packet_presum.sv'
 rtl=src.read_text().replace('module cu66_packet_control (','module cu71_packet_presum (');(b/'parser.sv').write_text(rtl,newline='\n')
 shutil.copyfile(parent.parent/'cu66_profile.svh',b/'cu66_profile.svh')
 tcl='''set_param general.maxThreads 2
create_project -in_memory -part xc7a100tcsg324-1 leaf
set_property include_dirs [list [pwd]] [current_fileset]
read_verilog -sv parser.sv
synth_design -mode out_of_context -top cu71_packet_presum -part xc7a100tcsg324-1
create_clock -period 10 -name core [get_ports clk]
set_input_delay -clock core 1 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock core 1 [get_ports -filter {DIRECTION == OUT}]
write_checkpoint -force synthesized.dcp
report_timing_summary -delay_type min_max -report_unconstrained -file timing.rpt
report_timing -delay_type max -max_paths 25 -file setup-paths.rpt
report_utilization -hierarchical -file utilization.rpt
puts "OOC_WNS [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]"
puts PREFIX_OOC_REPORTS_COMPLETE_UNPLACED_ONLY
'''
 (b/'run.tcl').write_text(tcl,newline='\n');cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source','run.tcl','-log','vivado.log','-journal','vivado.jou'];start=time.monotonic()
 with(b/'console.log').open('wb')as f:q=subprocess.run(cmd,cwd=b,env=dict(os.environ,TEMP=str(b/'tmp'),TMP=str(b/'tmp')),stdout=f,stderr=subprocess.STDOUT)
 run=dict(label=label,command=cmd,cwd=str(b),returncode=q.returncode,seconds=time.monotonic()-start,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest())
 for f in b.iterdir():
  if f.is_file():shutil.copyfile(f,e/f.name)
 runs.append(run);(o/'execution.json').write_text(json.dumps(runs,indent=2)+'\n');print(label,q.returncode,flush=True)
 assert q.returncode==0 and 'PREFIX_OOC_REPORTS_COMPLETE_UNPLACED_ONLY'in(b/'console.log').read_text()
 assert all((e/n).is_file()for n in ['synthesized.dcp','timing.rpt','setup-paths.rpt','utilization.rpt'])
(o/'result.json').write_text(json.dumps(dict(status='PASS_MATCHED_OOC_REPORT_GENERATION_ONLY',runs=runs,part='xc7a100tcsg324-1',clock_ns=10,scalar_io_budget_ns=1,hardware=False,routed_timing=False,scope='Matched unplaced synthesis; report slack explicitly, not routed-board qualification'),indent=2)+'\n')
