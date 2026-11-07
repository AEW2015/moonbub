from pathlib import Path
import json,subprocess,os,hashlib
p=Path('C:/mb70/fpga/experiments/cu66-v71/hud-bulk-v025');e=p/'pins04';e.mkdir();parent=Path('C:/mb70/dy71-v023-20261106-v001');sel=json.loads((parent/'selection.json').read_text());names=['cu71_balanced_identity_v019.sv','cu71_packet_staging_safe.sv','cu71_packet_arbiter_cut_v001.sv','moonshine_qspi_endpoint.sv'];src=[parent/'inputs'/x for x in sel['sources']if Path(x).name in names]+[p/x for x in ['dy71_hud_bulk_v025.sv','dy71_local_control_bulk_v025.sv','cu71_bus_cdc_bulk_v025.sv','tb_bulk_pins_v025.sv']];inc=parent/'inputs/fpga/experiments/cu66-v70/memory';assert(inc/'cu70_memory_map.svh').exists();(e/'source-freeze.json').write_text(json.dumps({str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in src+[inc/'cu70_memory_map.svh']},indent=2));env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);rows=[]
for phase in ['0.0','2.3']:
 for half in ['31.25','62.5']:
  label='phase'+phase+'-half'+half;cmds=[['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-I'+str(inc),'-y','C:/Xilinx/2025.2/Vivado/data/verilog/src/unisims','-s','tb_bulk_pins_v025','-s','glbl','-Ptb_bulk_pins_v025.PHASE='+phase,'-Ptb_bulk_pins_v025.HALF='+half,'-o',str(e/(label+'.vvp'))]+[str(f)for f in src]+['C:/Xilinx/2025.2/Vivado/data/verilog/src/glbl.v'],['C:/msys64/ucrt64/bin/vvp.exe',str(e/(label+'.vvp'))]]
  for name,cmd in zip(['compile','run'],cmds):
   q=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=120);(e/(label+'-'+name+'.log')).write_text(q.stdout+q.stderr);rows.append(dict(label=label+'-'+name,cmd=cmd,returncode=q.returncode));(e/'execution.json').write_text(json.dumps(rows,indent=2));print(label,name,q.returncode,flush=True)
   if q.returncode:print(q.stdout+q.stderr);raise SystemExit(1)
  assert 'BULK_PINS_PASS'in(e/(label+'-run.log')).read_text()
(e/'result.json').write_text(json.dumps(dict(status='PASS_NEW_BULK_CSR_PIN_PATH',cases=4,scope='Actual pin endpoint/new CDC/new local control/new bulk engine; synthetic owner and AUX memory; not full decoder/SDRAM or physical result'),indent=2))
