from pathlib import Path
import argparse,hashlib,json,shlex,shutil,subprocess,time
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-display';native=r/'experiments/cu66-native-v69'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--seeds',default='0,7311');a.add_argument('--variant',choices=['base','pipe'],default='base');args=a.parse_args();o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
top='cu71_direct_scanout_syncsafe'
rtl=[d/'cdc/cu71_direct_scanout_syncsafe.sv',d/'cu71_cache_dma.sv',d/'cu71_direct_cache.sv',d/'cu71_yuv_pixel_pipe.sv',d/'cdc/cu71_lcd_lines_syncsafe.sv'];tb=d/'tb_direct_scanout.cpp';inc=r/'fpga/experiments/cu66-v71/memory/evidence/direct-fast01'
files=[*rtl,tb,inc/'cu70_memory_map.svh',Path(__file__),*native.glob('*.hpp'),native/'index.tsv',*sorted((native/'fixtures').glob('*.cu66'))];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={str(p.relative_to(r)).replace('\\','/'):sha(p)for p in files}
for p in files:
 f=o/'source-snapshot'/p.relative_to(r);f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,f)
if True:
 adapted=o/'tb_direct_scanout_pipe.cpp';adapted.write_text(tb.read_text().replace('Vcu71_direct_scanout','Vcu71_direct_scanout_syncsafe').replace('../../../../experiments/cu66-native-v69/decoder.hpp','/mnt/c/mb70/experiments/cu66-native-v69/decoder.hpp'),newline='\n');tb=adapted
steps=[]
def run(label,cmd,timeout=1200):
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=r,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
 return(o/(label+'.log')).read_text(errors='replace')
unix=lambda p:'/mnt/'+p.drive[0].lower()+str(p)[2:].replace('\\','/')
mdir='/tmp/cu71-direct-owner-'+str(time.time_ns());script=o/'build.sh';script.write_text('set -eu\nsource /opt/gamebub-openxc7-20261021/oss-cad-suite/environment\ncd '+shlex.quote(unix(r))+"\nverilator --version\nverilator --cc --exe --build -j 2 --Wall -Wno-PROCASSINIT --top-module "+top+" --Mdir "+mdir+" -CFLAGS '-O2 -std=c++17' -I"+unix(inc)+' '+' '.join(shlex.quote(unix(p))for p in [*rtl,tb])+'\n',newline='\n');run('build',['wsl','-d','MRS-HDL-Research','--','bash',unix(script)])
run('controls',['wsl','-d','MRS-HDL-Research','--',mdir+'/V'+top,unix(native/'index.tsv'),'7311','control'])
assert 'CU71_DIRECT_OWNER_CONTROL_PASS' in (o/'controls.log').read_text()
results=[]
for seed in args.seeds.split(','):
 log=run('seed'+seed,['wsl','-d','MRS-HDL-Research','--',mdir+'/V'+top,unix(native/'index.tsv'),seed]);assert 'CU71_DIRECT_OWNER_PASS'in log and 'FAIL'not in log;results.append(log.strip().splitlines()[-1])
assert hashes=={str(p.relative_to(r)).replace('\\','/'):sha(p)for p in files}
(o/'result.json').write_text(json.dumps(dict(status='PASS_NATIVE_KEY_P_DIRECT_OWNER_RASTERS',sources=hashes,results=results,hardware=False,actual_sdram_pin_model=False,limits=['Synthetic held-response BL8 adapter; actual pin-model and contention integration pending','No complete decoder/root-owner verification or routed CDC/timing qualification']),indent=2)+'\n')
