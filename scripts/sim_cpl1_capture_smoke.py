"""Candidate top/PLL/bootstrap smoke; deliberately not a rendered-CRC test."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
root=Path(__file__).resolve().parents[1]
p=root/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002'
c=root/'fpga/candidates/cp23-sdram-capture135-20261105-v001'
out=c/'evidence/platform-smoke01';out.mkdir(parents=True,exist_ok=False)
shutil.copytree(p/'sim-inputs',out/'inputs')
selection=json.loads((p/'simulation-selection.json').read_text())
for name in selection['assets'].values():shutil.copyfile(p/'sim-assets'/name,out/name)
for name in ['rtl/moonshine_top_cpl1.sv','core/parents/moonshine_sdram_burst.sv']:
    shutil.copyfile(c/'inputs'/name,out/'inputs'/name)
model=out/'inputs/core/parents/sdram_model_bounded.sv'
shutil.copyfile(root/'evidence/cpl1-sdram-alignment-20261105-v002/model.sv',model)
tb=out/'inputs/sim/tb_platform.sv'
s=tb.read_text().replace('7.749','3.749').replace('7.751','3.751')
s=s.replace('read_phase279=1','read_phase135=1')
s=s.replace('.MEM_WORDS(1572865)', '.MEM_WORDS(1572865),.CLOCK_FLIGHT_NS(0.0)')
# Observe writes after the modeled device edge, not the old 4 ns flight.
s=s.replace('#4.001;', '#0.001;')
tb.write_text(s,newline='\n')
sources=list(selection['sources']);sources[-1]='sim/tb_platform.sv'
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','')
results=[]
for loss in [0,1]:
    image=out/f'loss{loss}.vvp'
    cmd=['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-I',str(out),'-s','tb',f'-Ptb.LOSS={loss}',
         '-o',str(image),*[str(out/'inputs'/n)for n in sources]]
    q=subprocess.run(cmd,capture_output=True,text=True,env=env,cwd=out)
    (out/f'compile-{loss}.log').write_text(q.stdout+q.stderr);assert q.returncode==0,q.stderr
    q=subprocess.run(['C:/msys64/ucrt64/bin/vvp.exe','-i',str(image)],capture_output=True,text=True,env=env,cwd=out,timeout=240)
    (out/f'simulation-{loss}.log').write_text(q.stdout+q.stderr)
    assert q.returncode==0,q.stdout+q.stderr
    results.append(dict(loss=loss,returncode=q.returncode,log=q.stdout[-600:]))
    print('CANDIDATE_PLATFORM_SMOKE',loss,q.returncode,flush=True)
(out/'result.json').write_text(json.dumps(dict(scope='Digital top clock/bootstrap/lock-loss smoke only, not rendered CRC or physical timing',
    product_sources={n:hashlib.sha256((out/'inputs'/n).read_bytes()).hexdigest()for n in sources},
    SIMULATION_define=False,model_clock_flight_ns=0,model_hold_ns=0.5,cases=results),indent=2)+'\n')
