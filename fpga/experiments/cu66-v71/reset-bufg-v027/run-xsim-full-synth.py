from pathlib import Path
import os,subprocess,json,shutil,time,hashlib
p=Path('C:/mb70/fpga/experiments/cu66-v71/hud-bulk-v025');e=Path('C:/mb70/fpga/experiments/cu66-v71/reset-bufg-v027/xsim-full-synth01');e.mkdir();work=Path('C:/vtmp')/('bulk_xsim_'+str(time.time_ns()));work.mkdir();shutil.copyfile(Path('C:/mb70/dy71-v027-20261107-v001/bulk-funcsim.v'),work/'bulk-net.v');env=dict(os.environ,TEMP=str(work),TMP=str(work));env.pop('NoDefaultCurrentDirectoryInExePath',None);bin=Path('C:/Xilinx/2025.2/Vivado/bin');rows=[]
for top in ['tb_hud_bulk_v025','tb_native_bulk_v025']:
 case=work/top;case.mkdir();tb=case/(top+'.sv');tb.write_text((p/(top+'.sv')).read_text().replace('repeat(4)tick();','repeat(24)tick();'));shutil.copyfile(work/'bulk-net.v',case/'bulk-net.v');commands=[('compile',[str(bin/'xvlog.bat'),'--sv','bulk-net.v',tb.name,'C:/Xilinx/2025.2/Vivado/data/verilog/src/glbl.v']),('elaborate',[str(bin/'xelab.bat'),'-L','unisims_ver','-s','bulk_test',top,'glbl']),('run',[str(bin/'xsim.bat'),'bulk_test','-runall'])]
 for label,cmd in commands:
  start=time.monotonic()
  with(e/(top+'-'+label+'.log')).open('x')as f:q=subprocess.run(cmd,cwd=case,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
  rows.append(dict(top=top,phase=label,cmd=cmd,cwd=str(case),returncode=q.returncode,seconds=time.monotonic()-start));(e/'execution.json').write_text(json.dumps(rows,indent=2));print(top,label,q.returncode,flush=True)
  if q.returncode:print((e/(top+'-'+label+'.log')).read_text()[-2000:]);raise SystemExit(1)
 log=(e/(top+'-run.log')).read_text(errors='replace');marker='HUD_BULK_PASS'if top=='tb_hud_bulk_v025'else'NATIVE_BULK_PASS';assert marker in log and 'Fatal:'not in log and 'FATAL:'not in log,log[-1800:]
(e/'result.json').write_text(json.dumps(dict(status='PASS_XSIM_POST_SYNTH_BULK_NATIVE_WORDS',scope='Exact V026 full-synthesis exported bulk engine / AMD unisims_ver; complete unit and native HU word checks, no SDF/whole-system/hardware claim',netlist_sha256=hashlib.sha256((Path('C:/mb70/dy71-v027-20261107-v001/bulk-funcsim.v')).read_bytes()).hexdigest(),source_sha256=hashlib.sha256((Path('C:/mb70/dy71-v027-20261107-v001/inputs/fpga/experiments/cu66-v71/hud-bulk-v025/dy71_hud_bulk_v025.sv')).read_bytes()).hexdigest(),work=str(work)),indent=2))
