"""Exact board digital replay. No Vivado, hardware or mutation of this bundle."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,time
P=pathlib.Path(__file__).resolve().parent
a=argparse.ArgumentParser();mode=a.add_mutually_exclusive_group(required=True);mode.add_argument('--smoke',action='store_true');mode.add_argument('--full',action='store_true');a.add_argument('--output',required=True);a=a.parse_args()
E=pathlib.Path(a.output).resolve()
try:E.relative_to(P)
except ValueError:pass
else:raise SystemExit('Output must be outside the source bundle')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((P/'package-files.json').read_text())
for n,h in manifest.items():assert sha(P/n)==h,n
selection=json.loads((P/'simulation-selection.json').read_text())
E.mkdir(parents=True,exist_ok=False)
shutil.copytree(P/'sim-inputs',E/'inputs')
for n in selection['assets'].values():shutil.copyfile(P/'sim-assets'/n,E/n)
sources=list(selection['sources'])
if a.smoke:sources[-1]='sim/tb_platform.sv'
def tool(name,variable):
 requested=os.environ.get(variable)
 if requested:
  r=shutil.which(requested)or(str(pathlib.Path(requested).resolve())if pathlib.Path(requested).is_file()else None)
 else:r=shutil.which(name)or shutil.which(name+'.exe')
 if not r:
  fallback=pathlib.Path('C:/msys64/ucrt64/bin')/(name+'.exe')
  if fallback.is_file():r=str(fallback)
 if not r:raise SystemExit('Missing '+name+'; set '+variable+' or PATH')
 return str(pathlib.Path(r).resolve())
iverilog=tool('iverilog','IVERILOG');vvp=tool('vvp','VVP')
env=dict(os.environ);env['PATH']=str(pathlib.Path(iverilog).parent)+os.pathsep+env.get('PATH','')
steps=[]
def run(label,cmd):
 t=time.monotonic()
 with(E/(label+'.log')).open('wb')as f:r=subprocess.run(cmd,cwd=E,env=env,stdout=f,stderr=subprocess.STDOUT)
 steps.append(dict(label=label,command=cmd,returncode=r.returncode,wall_seconds=time.monotonic()-t))
 (E/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
parameters=['-Ptb.LOSS=0']if a.smoke else['-Ptb.SMOKE=0']
cmd=[iverilog,'-g2012','-Wall','-I',str(E),'-s','tb',*parameters,'-o',str(E/'test.vvp'),*[str(E/'inputs'/n)for n in sources]]
assert not any('SIMULATION'in n for n in cmd)
(E/'source-snapshot.json').write_text(json.dumps(dict(sources={n:sha(E/'inputs'/n)for n in sources},runtime_assets={n:sha(E/n)for n in selection['assets'].values()},product_RTL_sha256=selection['product_RTL_sha256'],SIMULATION_define=False,source_package_sha256=sha(P/'package-files.json'),origin='MODELED_DIGITAL_BOARD_NOT_HARDWARE'),indent=2)+'\n')
run('compile',cmd);run('simulation',[vvp,'-i',str(E/'test.vvp')])
log=(E/'simulation.log').read_text()
marker='CPL1_PLATFORM_SOURCE_SMOKE_PASS checks=16'if a.smoke else'CPL1_BOARD_NATIVE_QSPI_OBSERVER_PASS guarded_reads=40 checks=139'
assert marker in log,marker
if a.full:
 run('independent-fixture-checker',[__import__('sys').executable,str(P/'host-checker/cpl1_snapshot.py'),'--log',str(E/'pages.log'),'--expectation',str(P/'host-checker/frame0-expectation.json'),'--require-fixture','--output',str(E/'checker-result.json')])
for n,h in manifest.items():assert sha(P/n)==h,n
(E/'result.json').write_text(json.dumps(dict(status='PASS_MODELED_DIGITAL_BOARD_ONLY',mode='smoke'if a.smoke else'full',marker=marker,hardware=False,Vivado=False,source_unchanged=True),indent=2)+'\n');print(marker)
