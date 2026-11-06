"""Native exact-device resource and internal synthesis timing for cache+color."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-display'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False);(o/'tmp').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['cu71_direct_cache.sv','cu71_yuv_pixel_pipe.sv','cu71_cache_pixel_test.sv']
for n in names:shutil.copyfile(d/n,o/n)
before={n:sha(o/n)for n in names};(o/'source-freeze.json').write_text(json.dumps(before,indent=2)+'\n');shutil.copyfile(Path(__file__),o/'executed-runner.py')
tcl='set_param general.maxThreads 2\n'+''.join('read_verilog -sv {'+(o/n).as_posix()+'}\n'for n in names)+'''synth_design -top cu71_cache_pixel_test -part xc7a100tcsg324-1 -mode out_of_context
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
puts "CU71_CACHE_SYNTH_COMPLETE LUT=$lut FF=$ff RAMB18=$rb18 RAMB36=$rb36 DSP=$dsp"
'''.replace('@OUT@',o.as_posix())
(o/'run.tcl').write_text(tcl,newline='\n')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'run.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou')]
env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp'));t=time.monotonic();q=subprocess.run(cmd,cwd=o,env=env)
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-t,hardware=False),indent=2)+'\n')
assert q.returncode==0;assert before=={n:sha(d/n)for n in names}
counts=json.loads((o/'primitive-counts.json').read_text());assert counts['RAMB36']+counts['RAMB18']>=1 and counts['FF']<10000 and counts['LUT']<10000,counts
(o/'result.json').write_text(json.dumps(dict(status='PASS_EXACT_DEVICE_CACHE_RESOURCE_COMPONENT',sources=before,counts=counts,hardware=False,routed_timing=False,scope='Cache+color internal synthesis timing/resource only; full owner/DMA/upstream timing and board fit remain separate'),indent=2)+'\n')
print('CU71_DIRECT_CACHE_RESOURCE_PASS',counts,flush=True)
