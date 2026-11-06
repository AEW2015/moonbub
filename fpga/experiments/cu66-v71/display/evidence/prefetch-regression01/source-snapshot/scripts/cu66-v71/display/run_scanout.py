"""Source-bound asynchronous BL8 scanout component tests; no hardware/FPS claim."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time,shlex,shutil
r=Path(__file__).resolve().parents[3]
d=r/'fpga/experiments/cu66-v71/display'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--variant',choices=['baseline','prefetch'],default='baseline');args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
top='cu71_scanout_prefetch' if args.variant=='prefetch' else 'cu71_scanout'
tb='tb_scanout_prefetch.cpp' if args.variant=='prefetch' else 'tb_scanout.cpp'
files=[d/(top+'.sv'),d/'cu71_lcd_lines.sv',d/tb,Path(__file__)]
before={str(p.relative_to(r)).replace('\\','/'):sha(p) for p in files}
for p in files:
 copy=o/'source-snapshot'/p.relative_to(r);copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,copy)
commands=[]
def run(label,cmd,timeout):
 started=time.monotonic()
 with (o/(label+'.log')).open('wb') as f:
  p=subprocess.run(cmd,cwd=r,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 commands.append(dict(label=label,command=cmd,returncode=p.returncode,seconds=time.monotonic()-started))
 (o/'execution.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert p.returncode==0,(label,str(o/(label+'.log')))
 return (o/(label+'.log')).read_text(errors='replace')
stamp=str(time.time_ns());mdir='/tmp/cu71-bl8-scanout-'+stamp
win_to_wsl=lambda p:'/mnt/'+p.drive[0].lower()+str(p)[2:].replace('\\','/')
script=o/'build.sh'
paths=' '.join(shlex.quote(win_to_wsl(p)) for p in files[:3])
script.write_text('set -eu\nsource /opt/gamebub-openxc7-20261021/oss-cad-suite/environment\ncd '+shlex.quote(win_to_wsl(r))+'\nverilator --version\nverilator --cc --exe --build -j 2 --Wall -Wno-PROCASSINIT --top-module '+top+' --Mdir '+mdir+" -CFLAGS '-O2 -std=c++17' "+paths+'\n',newline='\n')
run('build',['wsl','-d','MRS-HDL-Research','--','bash',win_to_wsl(script)],600)
results=[]
for seed,starve in [(0,False),(7101,False),(7102,False),(7103,True)]:
 label='seed'+str(seed)+('-starve' if starve else '')
 cmd=['wsl','-d','MRS-HDL-Research','--',mdir+'/V'+top,str(seed),*(['--starve'] if starve else [])]
 log=run(label,cmd,300)
 assert 'TEST_PASS_BL8_SCANOUT' in log and 'FAIL' not in log
 results.append(dict(seed=seed,starvation=starve,summary=log.strip()))
assert before=={str(p.relative_to(r)).replace('\\','/'):sha(p) for p in files},'Source changed while tests ran'
(o/'result.json').write_text(json.dumps(dict(status='PASS_ASYNCHRONOUS_BL8_SCANOUT_COMPONENT',sources=before,results=results,
 complete_rasters=8,compared_pixels=3072000,hardware=False,routed_timing=False,
 waiver='PROCASSINIT only: newer Verilator warning for unchanged FPGA initialization plus explicit reset in copied v70 line endpoint; other Wall warnings fatal',
 limits=['Memory response is functional synthetic BL8, not pin/controller timing','Starvation runs intentionally lose whole lines','Panel/PHY/timing/CDC hardware qualification separate','Not unique-source-frame or30fps proof']),indent=2)+'\n')
print('CU71_BL8_SCANOUT_COMPONENT_PASS',o)
