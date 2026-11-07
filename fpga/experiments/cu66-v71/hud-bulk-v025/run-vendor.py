from pathlib import Path
import os,json,subprocess,hashlib,shutil
p=Path('C:/mb70/fpga/experiments/cu66-v71/hud-bulk-v025');e=p/'vendor03';e.mkdir();lib=Path('C:/Xilinx/2025.2/Vivado/data/verilog/src/unisims');glbl=lib.parent/'glbl.v';net=p/'mapping03/funcsim.v';env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);rows=[]
for top in ['tb_hud_bulk_v025','tb_native_bulk_v025']:
 src=p/(top+'.sv');tb=e/src.name;tb.write_text(src.read_text().replace('repeat(4)tick();','repeat(24)tick();'));exe=e/(top+'.vvp');cmds=[['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-y',str(lib),'-s',top,'-s','glbl','-o',str(exe),str(net),str(tb),str(glbl)],['C:/msys64/ucrt64/bin/vvp.exe',str(exe)]]
 for label,cmd in zip(['compile','run'],cmds):
  with(e/(top+'-'+label+'.log')).open('w')as f:q=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
  rows.append(dict(top=top,phase=label,cmd=cmd,returncode=q.returncode));(e/'execution.json').write_text(json.dumps(rows,indent=2));print(top,label,q.returncode,flush=True)
  if q.returncode:print((e/(top+'-'+label+'.log')).read_text()[-1600:]);raise SystemExit(1)
(e/'result.json').write_text(json.dumps(dict(status='PASS_POST_SYNTH_VENDOR_RAM_NATIVE_WORDS',scope='Synthesized standalone bulk engine actual Xilinx primitive models, unit/abort/reset and full original native HUD word readback; not full design timing simulation or physical result',netlist_sha256=hashlib.sha256(net.read_bytes()).hexdigest(),source_sha256=hashlib.sha256((p/'mapping03/dy71_hud_bulk_v025.sv').read_bytes()).hexdigest()),indent=2))
