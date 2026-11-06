"""Four-state command/DMA/cache completion and abort ownership proof."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-display'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['cu71_cache_dma.sv','cu71_direct_cache.sv','tb_cache_dma.sv']
for n in names:shutil.copyfile(d/n,o/n)
map_source=r/'fpga/experiments/cu66-v71/memory/evidence/direct-fast01/cu70_memory_map.svh';shutil.copyfile(map_source,o/'cu70_memory_map.svh')
before={n:sha(o/n)for n in [*names,'cu70_memory_map.svh']};(o/'source-freeze.json').write_text(json.dumps(before,indent=2)+'\n');shutil.copyfile(Path(__file__),o/'executed-runner.py')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','');steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_cache_dma','-I',str(o),'-o',str(o/'test.vvp'),*[str(o/n)for n in names]]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','-i',str(o/'test.vvp')])]:
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
log=(o/'simulation.log').read_text();assert 'CU71_CACHE_DMA_PASS' in log
assert all(sha(d/n)==before[n]for n in names)
(o/'result.json').write_text(json.dumps(dict(status='PASS_FOUR_STATE_TAGGED_CACHE_DMA_COMPONENT',sources=before,summary=log.strip(),hardware=False,routed_timing=False,
 limits=['Synthetic BL8 service model, not SDRAM command/physical throughput','No top PREPARE/COMMIT/CDC owner yet','Unsequenced backend requires no late response after acknowledged abort/drain; arbitrary stale reply during a new pending request needs an echo-tagged interface to detect']),indent=2)+'\n')
print('CU71_CACHE_DMA_COMPONENT_PASS',o,flush=True)
