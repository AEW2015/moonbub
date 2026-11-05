"""Optional portable Icarus tests; actual design only, no stub mode/hardware."""
import argparse,hashlib,json,os,re,shutil,subprocess,time
from pathlib import Path
p=Path(__file__).resolve().parent
tops={'controls':'tb','collisions':'tb_collisions','fixture':'tb','feeder':'tb_feeder','platform':'tb_platform','resets':'tb_audio_top_reset','natural':'tb_natural','job':'tb_job_qspi','ordering':'tb_ordering'}
ap=argparse.ArgumentParser();ap.add_argument('--test',choices=tops,required=True);ap.add_argument('--iverilog',default=os.getenv('IVERILOG_BIN'));ap.add_argument('--vvp',default=os.getenv('VVP_BIN'));ap.add_argument('--run-name',default='001');a=ap.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_name):raise SystemExit('Use an alphanumeric run name')
iv=a.iverilog or shutil.which('iverilog');vvp=a.vvp or shutil.which('vvp')
if not iv or not vvp:raise SystemExit('Install Icarus or supply --iverilog and --vvp executable paths')
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
for manifest in ['design-inputs.json','verification-inputs.json']:
 for b in json.loads((p/manifest).read_text())['files']:assert sha(p/b['path'])==b['sha256'],b['path']
direct=a.test in {'controls','collisions','fixture','feeder'}
sources=([p/'rtl/ar03_fixture_diagnostic.sv']+sorted((p/'compute').glob('*.sv'))) if direct else sorted((p/'rtl').glob('*.sv'))+sorted((p/'compute').glob('*.sv'))
sources+=[p/'verification'/('tb_'+a.test+'.sv')]
if not direct:sources+=[p/'verification/support-primitives.sv']
if a.test=='feeder':sources+=[p/'verification/parent_fixture_diagnostic.sv']
payloads=[p/'rtl/fixture.hex',p/'rtl/quantizers.hex',p/'verification/pcm.hex',p/'verification/expected.hex']
inputs=sources+payloads+[Path(__file__).resolve()]+([p/'verification/top-harness.svh'] if a.test in {'natural','job','ordering'} else [])
before={x.relative_to(p).as_posix():sha(x) for x in inputs}
out=p/'verification-runs'/(a.test+'-'+a.run_name);out.mkdir(parents=True)
for x in payloads:shutil.copyfile(x,out/x.name)
env=dict(os.environ);env['PATH']=os.pathsep.join([str(Path(iv).resolve().parent),str(Path(vvp).resolve().parent),env.get('PATH','')]);start=time.time()
compile_cmd=[iv,'-g2012','-I',str(p/'verification'),'-s',tops[a.test],'-o','test.vvp',*[str(x) for x in sources]]
with (out/'compile.log').open('wb') as f:c=subprocess.run(compile_cmd,cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
simulation_code=None
if c.returncode==0:
 with (out/'simulation.log').open('wb') as f:r=subprocess.run([vvp,'-i','test.vvp',*(['+natural'] if a.test=='natural' else [])],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
 simulation_code=r.returncode
assert before=={x.relative_to(p).as_posix():sha(x) for x in inputs}
for x in payloads:assert sha(x)==sha(out/x.name)
(out/'execution.json').write_text(json.dumps({'test':a.test,'compile_returncode':c.returncode,'simulation_returncode':simulation_code,'wall_seconds':time.time()-start,'sha256':before,'compile_command':compile_cmd,'tool_paths':{'iverilog':iv,'vvp':vvp},'inputs_unchanged':True,'actual_design':True,'stub':False},indent=2)+'\n')
if c.returncode or simulation_code:raise SystemExit(c.returncode or simulation_code)
print('Actual-source optional simulation PASS:',a.test)
