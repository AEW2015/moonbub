"""Four-state native Icarus proof of unreset strip/cache data ownership."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/display'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--variant',choices=['bram','pipe'],default='bram');args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['cu71_painter_strip_pipe.sv','tb_painter_pipe_control.sv'] if args.variant=='pipe' else ['cu71_painter_strip.sv','tb_painter_bram_control.sv']
top='tb_painter_pipe_control' if args.variant=='pipe' else 'tb_painter_bram_control'
for n in names:shutil.copyfile(d/n,o/n)
before={n:sha(o/n)for n in names};(o/'source-freeze.json').write_text(json.dumps(before,indent=2)+'\n')
shutil.copyfile(Path(__file__),o/'executed-runner.py')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','');steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s',top,'-o',str(o/'test.vvp'),*[str(o/n)for n in names]]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','-i',str(o/'test.vvp')])]:
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
assert 'TEST_PASS_BRAM_STRIP_CONTROL' in(o/'simulation.log').read_text()
assert before=={n:sha(d/n)for n in names}
(o/'result.json').write_text(json.dumps(dict(status='PASS_FOUR_STATE_BRAM_PAINTER_CONTROL',sources=before,hardware=False,routed_timing=False,scope='Invalid start,dirty strip abort,accepted write drain,coordinated reset/newgeneration,newsourcebias; external model flushed onreset'),indent=2)+'\n')
print('CU71_BRAM_PAINTER_CONTROL_PASS',o,flush=True)
