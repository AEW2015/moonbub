"""Pinned full-vector dequant equivalence and exact-device OOC diagnostics."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--synth',action='store_true');a=p.parse_args()
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/dequant';old=r/'fpga/experiments/cu66-v69/inverse'
o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
sources=[d/'cu71_dequant_pipe.sv',d/'tb_dequant.sv',old/'cu66_dequant.sv',old/'cu66_quant_rom.svh',old/'dequant.hex',old/'math-fixtures.json',Path(__file__)]
for f in sources:shutil.copy2(f,o/f.name)
pins={str(f):sha(f)for f in sources}
assert sha(old/'dequant.hex')=='c92934394acaab59b36b93bcd4dcc16256d0be4d525a238caa57687957db2935'
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'])
commands=[]
def run(cmd,name):
    start=time.monotonic();q=subprocess.run(cmd,cwd=o,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (o/name).write_text(q.stdout);commands.append(dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-start,log=name));assert q.returncode==0,(name,q.stdout[-4000:])
run(['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_dequant','-I',str(o),'-o','test.vvp','cu71_dequant_pipe.sv','cu66_dequant.sv','tb_dequant.sv'],'compile.log')
for fixture in ['dequant.hex','gameplay.hex','directed.hex']:
    if fixture!='dequant.hex':
        shutil.copy2(d/fixture,o/fixture);pins[str(d/fixture)]=sha(d/fixture)
    run(['C:/msys64/ucrt64/bin/vvp.exe','test.vvp','+FIXTURE='+fixture],fixture+'.log')
if a.synth:
    (o/'tmp').mkdir();env.update(TEMP=str(o/'tmp'),TMP=str(o/'tmp'))
    t='''set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 cu71_dequant_ooc
set_property include_dirs $out [current_fileset]
read_verilog -sv [file join $out cu71_dequant_pipe.sv]
synth_design -top cu71_dequant_pipe -mode out_of_context -part xc7a100tcsg324-1
create_clock -period 10.0 -name core [get_ports clk]
set inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock core -max 1.0 $inputs
set_input_delay -clock core -min 0.0 $inputs
set_output_delay -clock core -max 1.0 [get_ports -filter {DIRECTION == OUT}]
set_output_delay -clock core -min 0.0 [get_ports -filter {DIRECTION == OUT}]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
report_timing -delay_type max -max_paths 30 -file [file join $out setup-paths.rpt]
write_checkpoint -force [file join $out synthesized.dcp]
puts CU71_DEQUANT_SYNTH_DIAGNOSTIC_NOT_BOARD_TIMING
'''
    (o/'executed.tcl').write_text(t)
    run(['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)],'synth-console.log')
assert all(sha(Path(f))==h for f,h in pins.items())
(o/'execution.json').write_text(json.dumps(dict(sources=pins,commands=commands,part='xc7a100tcsg324-1',clock_ns=10,io_max_ns=1,scope='RTL full-vector correctness; optional synthesis OOC timing estimate only, not routed board timing; no hardware',hardware=False),indent=2)+'\n')
print(json.dumps(commands,indent=2))
