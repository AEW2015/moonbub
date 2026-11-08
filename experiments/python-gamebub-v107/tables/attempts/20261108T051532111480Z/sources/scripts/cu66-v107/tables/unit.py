#!/usr/bin/env python3
"""Bounded actual-mapped scale TDP / UNISIM collision qualification."""
import argparse,datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v107-tables';AREA=ROOT/'experiments/python-gamebub-v107/tables/unit';BUILD=Path('/home/lori/gamebub-build/cu66-v69')
TOOLS=Path('/home/lori/acorn-nexys4-ddr/tools');LICENSE=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};line=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(line.split('avg10=')[1].split()[0]))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=SRC/'cs88_admission_v91i2a.sv');a=p.parse_args();source=a.source.resolve();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir(parents=True);build=BUILD/('v107-tables-unit-'+stamp);build.mkdir();mapped=Path('/build')/build.name
 for src,name in [(source,'candidate.sv'),(SRC/'tb_tables_unit.sv','tb_tables_unit.sv'),(SRC/'cu66_tables_unit_v107.sv','unit_wrapper.sv'),(Path(__file__).resolve(),'unit.py')]:shutil.copyfile(src,build/name);shutil.copyfile(src,out/name)
 (build/'unit.xdc').write_text('create_clock -name scale_clk -period 10 [get_ports clk]\n')
 (build/'run.tcl').write_text('''set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
create_project -in_memory -part xc7a100tcsg324-1
set_property verilog_define SYNTHESIS [current_fileset]
read_verilog -sv [list [file join $build candidate.sv] [file join $build unit_wrapper.sv]]
read_xdc [file join $build unit.xdc]
synth_design -top cu66_tables_unit_v107 -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt -directive Default
write_checkpoint -force [file join $build results synth.dcp]
write_verilog -force -mode funcsim [file join $build results mapped.v]
report_utilization -hierarchical -file [file join $build results utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $build results timing.rpt]
set f [open [file join $build results ram-modes.tsv] w]
set properties {REF_NAME RAM_MODE READ_WIDTH_A READ_WIDTH_B WRITE_WIDTH_A WRITE_WIDTH_B WRITE_MODE_A WRITE_MODE_B DOA_REG DOB_REG}
puts $f "cell\\t[join $properties \\t]"
foreach c [get_cells -hierarchical -filter {REF_NAME =~ RAMB*}] {
 set row [list $c]
 foreach p $properties {lappend row [get_property $p $c]}
 puts $f [join $row \\t]
}
close $f
puts TABLES_MAPPING_COMPLETE
''')
 (build/'run.sh').write_text('''#!/bin/bash
set -euo pipefail
export XILINX_VIVADO=/opt/amd-tools/2026.1/Vivado
"$XILINX_VIVADO/bin/vivado" -mode batch -nojournal -nolog -notrace -source run.tcl -tclargs "$PWD"
cd results
"$XILINX_VIVADO/bin/xvlog" --sv mapped.v ../tb_tables_unit.sv "$XILINX_VIVADO/data/verilog/src/glbl.v" >xvlog.log 2>&1
"$XILINX_VIVADO/bin/xelab" tb_tables_unit glbl -L unisims_ver -s tables_snapshot -mt 2 >xelab.log 2>&1
"$XILINX_VIVADO/bin/xsim" tables_snapshot -runall -log xsim.log
if ! grep -q TEST_PASS_TABLES_UNIT xsim.log; then exit 2; fi
''')
 for name in ('unit.xdc','run.tcl','run.sh'):shutil.copyfile(build/name,out/name)
 before=memory();assert before['available_bytes']>=8*1024**3 and before['psi_full_avg10']<1,before
 name='gamebub-v107-tables-unit-'+stamp.lower();command=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount',f'type=bind,src={TOOLS},dst=/opt/amd-tools,readonly','--mount',f'type=bind,src={LICENSE},dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',str(mapped),'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','600s','bash','run.sh']
 r=dict(schema='v107-tables-mapped-unisim-unit-v1',status='RUNNING',command=command,source=dict(path=str(source.relative_to(ROOT)),sha256=sha(source)),build_external=str(build),mode='post-synthesis functional mapped actual UNISIM, no SDF',no_clock_relaxation=True,no_collision_warning_disable=True,actual_native_parameters_and_models=True,memory_samples=[],tools_and_license_readonly=True,timeout_seconds=600,cpus=2,memory_limit_bytes=8*1024**3);write(out/'receipt.json',r);began=time.monotonic();last=-5;stop=None;code=None
 print('TABLES_UNIT_STARTED',out.relative_to(ROOT),flush=True)
 try:
  with (out/'tool.log').open('w') as log:
   proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-began
    if elapsed-last>=5:
     m=dict(elapsed_seconds=elapsed,**memory());r['memory_samples'].append(m);last=elapsed
     if m['available_bytes']<4*1024**3 or m['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if elapsed>640:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
    time.sleep(.5)
   code=proc.wait(timeout=30)
  text=(out/'tool.log').read_text(errors='replace');sim=build/'results/xsim.log';passed=code==0 and sim.exists() and 'TEST_PASS_TABLES_UNIT' in sim.read_text(errors='replace')
  r['status']='PASS_MAPPED_UNISIM_TABLES_COLLISIONS' if passed else 'STOPPED_RESOURCE_OR_TIME' if stop else 'FAIL_TOOL_OR_PHYSICAL_COLLISION'
 finally:
  r.update(exit_code=code,wall_seconds=time.monotonic()-began,stop_reason=stop,source_unchanged=sha(source)==r['source']['sha256'])
  artifacts={}
  for q in sorted((build/'results').glob('*')):
   if not q.is_file():continue
   artifacts[q.name]=dict(sha256=sha(q),bytes=q.stat().st_size,external_path=str(q))
   if q.suffix in ('.log','.rpt','.tsv','.v','.sv','.txt') and q.stat().st_size<8*1024**2:
    dst=out/'reports'/q.name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(q,dst)
  r['artifacts']=artifacts;r['retained_sha256']={str(q.relative_to(out)):sha(q) for q in sorted(out.rglob('*')) if q.is_file() and q.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('TABLES_UNIT_FINISHED',r['status'],code,flush=True)
 if r['status']!='PASS_MAPPED_UNISIM_TABLES_COLLISIONS':raise SystemExit(1)
if __name__=='__main__':main()
