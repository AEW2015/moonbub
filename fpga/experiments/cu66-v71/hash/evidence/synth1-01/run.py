"""Actual original/candidate public-cycle comparison or exact-part synth diagnostic."""
from pathlib import Path
import argparse,hashlib,json,os,shlex,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--mode',choices=['functional','synth'],required=True);p.add_argument('--banks',type=int,choices=[1,2],default=2);a=p.parse_args()
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/hash';old=r/'fpga/experiments/cu66-v69/hash';o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sources=[d/'cu71_sha256_bytes_lookahead.sv',Path(__file__)];steps=[]
if a.mode=='functional':sources += [old/'cu66_sha256_bytes.sv',d/'cu71_sha_pair.sv',d/'tb_hash_pair.cpp',d/'fixtures.tsv',d/'fixtures.json']
for source in sources:shutil.copy2(source,o/source.name)
if a.mode=='functional':
    fixtures=json.loads((d/'fixtures.json').read_text())
    for file,h in fixtures['source_sha256'].items():assert sha(Path(file))==h
    for file,h in fixtures['assets'].items():
        assert sha(d/file)==h;target=o/file;target.parent.mkdir(exist_ok=True);shutil.copy2(d/file,target)
pins={str(source):sha(source)for source in sources}
(o/'source-freeze.json').write_text(json.dumps(dict(originals=pins,actual={str(f.relative_to(o)):sha(f)for f in o.rglob('*')if f.is_file()},mode=a.mode,banks=a.banks,hardware=False),indent=2)+'\n')
def run(label,cmd,env=None,timeout=1200):
    t=time.monotonic()
    with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
if a.mode=='functional':
    linux='/mnt/'+o.drive[0].lower()+o.as_posix()[2:]
    def wsl(command):return ['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && cd '+shlex.quote(linux)+' && '+command]
    run('environment',wsl('verilator --version && g++ --version'))
    cmd='verilator --cc --exe --build -j 2 --Wall -Wno-fatal --x-initial unique --top-module cu71_sha_pair -GBUFFER_BLOCKS='+str(a.banks)+' --Mdir obj -CFLAGS '+shlex.quote('-O2 -std=c++17')+' -LDFLAGS '+shlex.quote('-lz')+' cu71_sha_pair.sv cu66_sha256_bytes.sv cu71_sha256_bytes_lookahead.sv tb_hash_pair.cpp'
    run('build',wsl(cmd))
    for seed,randomize in [(7101,0),(7101,1),(7102,1),(7103,1)]:
        label=f'seed{seed}-random{randomize}'
        run(label,wsl(f'./obj/Vcu71_sha_pair fixtures.tsv {seed} {randomize} +verilator+rand+reset+2 +verilator+seed+{seed}'))
        log=(o/(label+'.log')).read_text();assert 'TEST_PASS'in log and 'ALL_ROUND_CANCEL_PASS aborts=64 resets=64 public_cycle_compare=1'in log and 'CONTROL_PASS'in log and 'TEST_FAIL'not in log
else:
    (o/'tmp').mkdir()
    t='''set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 cu71_sha_ooc
read_verilog -sv [file join $out cu71_sha256_bytes_lookahead.sv]
synth_design -top cu71_sha256_bytes_lookahead -mode out_of_context -part xc7a100tcsg324-1 -generic BUFFER_BLOCKS=BANKS
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
puts CU71_SHA_SYNTH_DIAGNOSTIC_NOT_ROUTED_TIMING
'''.replace('BUFFER_BLOCKS=BANKS','BUFFER_BLOCKS='+str(a.banks))
    (o/'executed.tcl').write_text(t,newline='\n')
    run('synth',['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)],dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')))
assert all(sha(Path(file))==h for file,h in pins.items())
(o/'result.json').write_text(json.dumps(dict(status='PASS_EXECUTED_'+a.mode.upper()+'_SCOPE_ONLY',banks=a.banks,source_sha256=sha(d/'cu71_sha256_bytes_lookahead.sv'),scope='Functional exactpubliccycle comparison+hashlib fixtures, or unplaced exact-device100MHz1nsIO synthesis estimate as selected. No routed board/hardware claim.',hardware=False),indent=2)+'\n')
