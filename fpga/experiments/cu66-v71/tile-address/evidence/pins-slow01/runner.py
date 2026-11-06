"""Isolated original-map tile-address proof and exact-device OOC diagnostic."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--mode',choices=['unit','pins','synth'],required=True);p.add_argument('--slow',action='store_true');a=p.parse_args()
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/tile-address';m=r/'fpga/experiments/cu66-v71/memory';o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();pins={};derivation=[]
def copy(src,name=None):
    target=o/(name or src.name);shutil.copy2(src,target);pins[str(src)]=sha(src);return target
copy(d/'cu71_tile_memory_address_pipe.sv');copy(r/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh');copy(Path(__file__),'runner.py')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
def run(label,command,timeout=900):
    start=time.monotonic()
    with(o/(label+'.log')).open('wb')as f:q=subprocess.run(command,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    steps.append(dict(label=label,command=command,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
    print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
sources=['cu71_tile_memory_address_pipe.sv']
if a.mode=='unit':
    copy(m/'cu71_tile_memory.sv');copy(d/'tb_tile_address.sv');sources+=['cu71_tile_memory.sv','tb_tile_address.sv'];top='tb_tile_address'
elif a.mode=='pins':
    parent=m/'evidence/rgb-reference-fast01';freeze=json.loads((parent/'source-freeze.json').read_text())
    for name,h in freeze.items():assert sha(parent/name)==h
    for name in ['cu71_word_bridge_burst.sv','moonshine_sdram_burst.sv','model.sv','primitives.sv']:
        copy(parent/name);sources.append(name)
    wrapper=parent/'cu71_memory_system_burst.sv';text=wrapper.read_text();assert text.count('cu71_tile_memory tiles(')==1
    (o/wrapper.name).write_text(text.replace('cu71_tile_memory tiles(','cu71_tile_memory_address_pipe tiles('),newline='\n');sources.append(wrapper.name)
    derivation.append(dict(parent=str(wrapper),parent_sha256=sha(wrapper),replacement='One module instance type only: cu71_tile_memory to cu71_tile_memory_address_pipe',candidate_sha256=sha(o/wrapper.name)))
    tb=copy(parent/'tb.sv')
    if a.slow:
        text=tb.read_text();assert text.count('.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757)')==1
        tb.write_text(text.replace('.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757)','.T_AC_NS(8.489),.CLOCK_FLIGHT_NS(3.768)'),newline='\n')
        derivation.append(dict(parent=str(parent/'tb.sv'),parent_sha256=sha(parent/'tb.sv'),replacement='Qualified slow model flight/access tuple only',candidate_sha256=sha(tb)))
    sources.append('tb.sv');top='tb_memory'
(o/'source-freeze.json').write_text(json.dumps(dict(original_sources=pins,actual_inputs={f.name:sha(f)for f in o.iterdir()if f.is_file()},derivation=derivation,mode=a.mode,slow=a.slow,hardware=False),indent=2)+'\n')
if a.mode in('unit','pins'):
    run('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s',top,'-I',str(o),'-o','test.vvp',*sources])
    run('simulation',['C:/msys64/ucrt64/bin/vvp.exe','test.vvp'])
    marker='CU71_TILE_ADDRESS_PASS'if a.mode=='unit'else'CU71_MEMORY_RGB_BURST_PASS'
    log=(o/'simulation.log').read_text();assert marker in log and 'FATAL'not in log
else:
    (o/'tmp').mkdir();env.update(TEMP=str(o/'tmp'),TMP=str(o/'tmp'))
    t='''set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 cu71_tile_address_ooc
set_property include_dirs $out [current_fileset]
read_verilog -sv [file join $out cu71_tile_memory_address_pipe.sv]
synth_design -top cu71_tile_memory_address_pipe -mode out_of_context -part xc7a100tcsg324-1
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
puts CU71_TILE_ADDRESS_OOC_SYNTH_NOT_BOARD_TIMING
'''
    (o/'executed.tcl').write_text(t,newline='\n')
    run('synthesis',['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)])
assert all(sha(Path(f))==h for f,h in pins.items())
(o/'result.json').write_text(json.dumps(dict(status='PASS_EXECUTED_'+a.mode.upper()+'_SCOPE_ONLY',mode=a.mode,slow=a.slow,source_sha256=sha(d/'cu71_tile_memory_address_pipe.sv'),hardware=False,scope='Original row-major map. Unit BFM/full memory contents or actual unchanged SDR2 controller/qualified pin model, or unplaced exact-part100MHz1nsIO synthesis estimate as selected; not routed board timing or hardware'),indent=2)+'\n')
