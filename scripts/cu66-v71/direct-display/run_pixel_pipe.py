"""Native-oracle component proof for one-pixel/clock YUV/HUD color pipeline."""
from pathlib import Path
import argparse,hashlib,json,shlex,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-display';native=r/'experiments/cu66-native-v69'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[d/'cu71_yuv_pixel_pipe.sv',d/'tb_pixel_pipe.cpp',Path(__file__),*native.glob('*.hpp'),native/'index.tsv',*sorted((native/'fixtures').glob('*.cu66'))]
hashes={str(p.relative_to(r)).replace('\\','/'):sha(p)for p in files}
for p in files:
 f=o/'source-snapshot'/p.relative_to(r);f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,f)
steps=[]
def run(label,cmd,timeout=600):
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=r,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
 return(o/(label+'.log')).read_text(errors='replace')
unix=lambda p:'/mnt/'+p.drive[0].lower()+str(p)[2:].replace('\\','/')
mdir='/tmp/cu71-pixel-pipe-'+str(time.time_ns());script=o/'build.sh'
script.write_text('set -eu\nsource /opt/gamebub-openxc7-20261021/oss-cad-suite/environment\ncd '+shlex.quote(unix(r))+"\nverilator --version\nverilator --cc --exe --build -j 2 --Wall --top-module cu71_yuv_pixel_pipe --Mdir "+mdir+" -CFLAGS '-O2 -std=c++17' "+' '.join(shlex.quote(unix(p))for p in files[:2])+'\n',newline='\n')
run('build',['wsl','-d','MRS-HDL-Research','--','bash',unix(script)])
results=[]
for seed in [0,7311]:
 log=run('seed'+str(seed),['wsl','-d','MRS-HDL-Research','--',mdir+'/Vcu71_yuv_pixel_pipe',unix(native/'index.tsv'),str(seed)])
 assert 'CU71_PIXEL_PIPE_PASS actual_frames=8 patterns=4 recovery=1 compared=4492800' in log and 'FAIL'not in log
 results.append(dict(seed=seed,summary=log.strip().splitlines()[-1]))
assert hashes=={str(p.relative_to(r)).replace('\\','/'):sha(p)for p in files}
(o/'result.json').write_text(json.dumps(dict(status='PASS_EXACT_NATIVE_ONE_PIXEL_PER_CLOCK_COMPONENT',sources=hashes,results=results,compared_canvas_pixels=8985600,
 five_owned_stages=True,hardware=False,routed_timing=False,limits=['Raw neighborhoods/HUDwords supplied as component inputs, not cache/DMA qualification','No complete receiver/physical playback/FPS proof','Deliberate coordinated pipeline reset drops3pendingtestpixels beforefreshnamespace']),indent=2)+'\n')
print('CU71_PIXEL_PIPE_COMPONENT_PASS',o,flush=True)
