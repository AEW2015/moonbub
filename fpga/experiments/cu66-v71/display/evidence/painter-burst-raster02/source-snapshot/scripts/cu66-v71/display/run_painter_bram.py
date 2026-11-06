"""Exact native-raster proof for the synchronous BRAM strip painter."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time,shlex,shutil,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/display';native=r/'experiments/cu66-native-v69'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--variant',choices=['bram','pipe','burst'],default='bram');args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
top='cu71_painter_burst_test' if args.variant=='burst' else 'cu71_painter_strip_pipe' if args.variant=='pipe' else 'cu71_painter_strip'
tb='tb_painter_burst.cpp' if args.variant=='burst' else 'tb_painter_bram_pipe.cpp' if args.variant=='pipe' else 'tb_painter_bram.cpp'
extra=[d/'cu71_painter_strip_burst.sv'] if args.variant=='burst' else []
files=[d/(top+'.sv'),d/tb,Path(__file__),*extra,*native.glob('*.hpp'),native/'index.tsv',*sorted((native/'fixtures').glob('*.cu66'))]
before={str(p.relative_to(r)).replace('\\','/'):sha(p)for p in files}
for p in files:
 dest=o/'source-snapshot'/p.relative_to(r);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
steps=[]
def run(label,cmd,timeout=600):
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=r,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
 return(o/(label+'.log')).read_text(errors='replace')
unix=lambda p:'/mnt/'+p.drive[0].lower()+str(p)[2:].replace('\\','/')
mdir='/tmp/cu71-painter-bram-'+str(time.time_ns());script=o/'build.sh'
script.write_text('set -eu\nsource /opt/gamebub-openxc7-20261021/oss-cad-suite/environment\ncd '+shlex.quote(unix(r))+"\nverilator --version\nverilator --cc --exe --build -j 2 --Wall --top-module "+top+" --Mdir "+mdir+" -CFLAGS '-O2 -std=c++17 -DUSE_STRIP' "+' '.join(shlex.quote(unix(p))for p in [files[0],*extra,files[1]])+'\n',newline='\n')
run('build',['wsl','-d','MRS-HDL-Research','--','bash',unix(script)])
runs=[]
for seed in [0,7101]:
 log=run('seed'+str(seed),['wsl','-d','MRS-HDL-Research','--',mdir+'/V'+top,unix(native/'index.tsv'),str(seed)])
 assert f'PASS actual_frames=8 patterns=4 recovery=1 fault_probes={5 if seed else 0} seed={seed}' in log and 'FAIL'not in log
 rows=[dict((k,int(v))for k,v in re.findall(r'(\w+)=(\d+)',s))for s in log.splitlines()if s.startswith('CASE_PASS')]
 good=[x for x in rows if x['mode']==0]
 assert len(good)==13 and all(x['read_words']==280320 and x['write_words']==384000 and x['painted']==345600 and x['canvas_runs']==43200 and x['aligned8_runs']==43200 for x in good)
 runs.append(dict(seed=seed,full_rasters=13,fault_probes=5 if seed else 0,min_cycles=min(x['cycles']for x in good),max_cycles=max(x['cycles']for x in good),cases=rows))
assert before=={str(p.relative_to(r)).replace('\\','/'):sha(p)for p in files},'Source changed during proof'
(o/'result.json').write_text(json.dumps(dict(status='PASS_BRAM_PAINTER_EXACT_NATIVE_RASTERS',source_sha256=before,runs=runs,full_rasters=26,compared_words=9984000,hardware=False,routed_timing=False,resource_fit='Separate native synthesis required',scope='Exact independent native RGB/HUD output, scalar memory handshakes, no physical FPS claim'),indent=2)+'\n')
print('CU71_BRAM_PAINTER_EXACT_RASTERS_PASS',o,flush=True)
