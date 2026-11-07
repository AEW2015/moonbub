from pathlib import Path
import hashlib,json,os,subprocess,time
p=Path(__file__).resolve().parent;b=Path('C:/mb70/dy71-v025-20261107-v002');o=p/'boundary01';o.mkdir()
sel=json.loads((b/'selection.json').read_text());names=['cu71_packet_staging_safe.sv','cu71_packet_arbiter_cut_v001.sv','cu71_balanced_identity_v019.sv']
sources=[b/'inputs'/n for n in sel['sources'] if Path(n).name in names]+[p/'dy71_hud_bulk_v025.sv']
s=(p/'dy71_local_control_bulk_v025.sv').read_text();assert s.count(' dy71_hud_bulk_v025 bulk(')==1
(o/'control.sv').write_text(s.replace(' dy71_hud_bulk_v025 bulk(', ' (* KEEP_HIERARCHY="TRUE" *) dy71_hud_bulk_v025 bulk('))
sources.append(o/'control.sv');inc=b/'inputs/fpga/experiments/cu66-v70/memory'
t='set_param general.maxThreads 4\nset_property include_dirs {'+inc.as_posix()+'} [current_fileset]\n'
for f in sources:t+='read_verilog -sv {'+f.as_posix()+'}\n'
t+='synth_design -top dy71_local_control_bulk_v025 -part xc7a100tcsg324-1 -mode out_of_context\nwrite_verilog -cell [get_cells bulk] -mode funcsim {'+(o/'bulk-funcsim.v').as_posix()+'}\nputs KEPT_BOUNDARY_COMPLETE\n'
(o/'executed.tcl').write_text(t);(o/'source-freeze.json').write_text(json.dumps({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},indent=2))
tmp=Path('C:/vtmp')/('boundary-'+str(time.time_ns()));tmp.mkdir();cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou')]
with(o/'console.log').open('x') as f:r=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp)),stdout=f,stderr=subprocess.STDOUT)
(o/'execution.json').write_text(json.dumps(dict(cmd=cmd,returncode=r.returncode),indent=2));assert r.returncode==0
net=(o/'bulk-funcsim.v').read_text();assert 'bus_selected'in net and 'command_generation'in net and 'bus_read_address'in net
print('KEPT_BOUNDARY_PORTS_PRESENT',flush=True)
