"""Native exact-device leaf resource gate; not routed timing or full-board fit."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time,re
r=Path(__file__).resolve().parents[3]
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--variant',choices=['bram','pipe','burst'],default='bram');args=a.parse_args()
top='cu71_painter_strip_burst' if args.variant=='burst' else 'cu71_painter_strip_pipe' if args.variant=='pipe' else 'cu71_painter_strip'
source=r/'fpga/experiments/cu66-v71/display'/(top+'.sv')
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False);(o/'tmp').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copyfile(source,o/source.name);shutil.copyfile(Path(__file__),o/'executed-runner.py')
tcl='''set_param general.maxThreads 2
read_verilog -sv {@SOURCE@}
synth_design -top cu71_painter_strip -part xc7a100tcsg324-1 -mode out_of_context
create_clock -name clk -period 10.000 [get_ports clk]
report_utilization -hierarchical -file {@OUT@/utilization.rpt}
report_timing_summary -delay_type min_max -file {@OUT@/synthesized-timing.rpt}
report_timing -max_paths 10 -file {@OUT@/synthesized-paths.rpt}
write_checkpoint -force {@OUT@/synthesized.dcp}
set f [open {@OUT@/primitive-counts.json} w]
set lut [llength [get_cells -hier -filter {REF_NAME =~ LUT*}]]
set ff [llength [get_cells -hier -filter {REF_NAME =~ FD*}]]
set rb18 [llength [get_cells -hier -filter {REF_NAME =~ RAMB18*}]]
set rb36 [llength [get_cells -hier -filter {REF_NAME =~ RAMB36*}]]
set dsp [llength [get_cells -hier -filter {REF_NAME =~ DSP*}]]
puts $f "{\\"LUT\\":$lut,\\"FF\\":$ff,\\"RAMB18\\":$rb18,\\"RAMB36\\":$rb36,\\"DSP\\":$dsp}"
close $f
puts "CU71_BRAM_PAINTER_SYNTH_COMPLETE LUT=$lut FF=$ff RAMB18=$rb18 RAMB36=$rb36 DSP=$dsp"
'''.replace('synth_design -top cu71_painter_strip ','synth_design -top '+top+' ').replace('@SOURCE@',(o/source.name).as_posix()).replace('@OUT@',o.as_posix())
(o/'run.tcl').write_text(tcl,newline='\n')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'run.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou')]
env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp'))
t=time.monotonic();q=subprocess.run(cmd,cwd=o,env=env)
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-t,hardware=False),indent=2)+'\n')
assert q.returncode==0
assert sha(source)==sha(o/source.name),'Source changed during synthesis'
counts=json.loads((o/'primitive-counts.json').read_text());assert counts['RAMB18']+counts['RAMB36']>=1 and counts['FF']<10000 and counts['LUT']<10000,counts
(o/'result.json').write_text(json.dumps(dict(status='PASS_EXACT_DEVICE_BRAM_PAINTER_RESOURCE_GATE',source_sha256=sha(source),counts=counts,part='xc7a100tcsg324-1',hardware=False,routed_timing=False,scope='Leaf synthesis/resource inference only; no routed timing or full-board fit',artifacts={n:sha(o/n)for n in [source.name,'run.tcl','utilization.rpt','synthesized-timing.rpt','synthesized-paths.rpt','synthesized.dcp','primitive-counts.json']}),indent=2)+'\n')
print('CU71_BRAM_PAINTER_RESOURCE_PASS',counts,flush=True)
