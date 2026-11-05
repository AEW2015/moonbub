from pathlib import Path
import subprocess,os,json,hashlib,time,sys,shutil
p=Path(__file__).resolve().parent;e=p/'evidence'/sys.argv[1];e.mkdir(parents=True,exist_ok=False)
tb=(p/'tb_address_equivalence.sv').read_text();core=(p/'cp23_key_composite_scanout_v008.sv').read_text();g=(p/'parents/ar03_yuv_line_gather.sv').read_text()
for line in tb.splitlines():
 if 'wire[15:0]hud_' in line:assert line in core,line
for name in ['stride120','stride240']:
 start=g.index(' function automatic [23:0] '+name);end=g.index(' endfunction',start)+len(' endfunction');assert g[start:end] in tb
files=['tb_address_equivalence.sv','cp23_key_composite_scanout_v008.sv','parents/ar03_yuv_line_gather.sv'];hashes={n:hashlib.sha256((p/n).read_bytes()).hexdigest()for n in files}
(e/'source-snapshot.json').write_text(json.dumps(hashes,indent=2)+'\n');(e/'tb.sv').write_text(tb)
env=dict(os.environ);steps=[]
def tool(name):
 value=os.environ.get(name.upper()) or shutil.which(name) or shutil.which(name+'.exe')
 fallback=Path('C:/msys64/ucrt64/bin')/(name+'.exe')
 if not value and fallback.exists():value=str(fallback)
 if not value:raise SystemExit('Missing '+name+' on PATH')
 env['PATH']=str(Path(value).resolve().parent)+os.pathsep+env.get('PATH','')
 return value
for label,cmd in [('compile',[tool('iverilog'),'-g2012','-s','tb','-o',str(e/'test.vvp'),str(e/'tb.sv')]),('simulation',[tool('vvp'),str(e/'test.vvp')])]:
 t=time.monotonic()
 with(e/(label+'.log')).open('w')as log:r=subprocess.run(cmd,cwd=e,env=env,stdout=log,stderr=subprocess.STDOUT)
 steps.append({'label':label,'command':cmd,'returncode':r.returncode,'wall_seconds':time.monotonic()-t});assert r.returncode==0
(e/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');assert 'ADDRESS_STRENGTH_COMPILED_EQUIVALENCE_PASS' in(e/'simulation.log').read_text();print((e/'simulation.log').read_text())
