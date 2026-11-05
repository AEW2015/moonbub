"""Exact candidate full-board digital fixture, with explicit timing assumptions."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time,sys,re
from cpl1_sdram_models import strict_hold_text
root=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--flight',type=float,required=True);a.add_argument('--access',type=float,required=True);a.add_argument('--hold',type=float,default=0.5);a.add_argument('--candidate',default='fpga/candidates/cp23-sdram-capture135-20261105-v001');a.add_argument('--output',required=True);args=a.parse_args()
p=root/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002'
c=(root/args.candidate).resolve()
out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
selection=json.loads((p/'simulation-selection.json').read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for name,record in json.loads((c/'candidate.json').read_text())['changes'].items():
    assert sha(c/'inputs'/name)==record['candidate_sha256'],name
shutil.copytree(p/'sim-inputs',out/'inputs')
for n in selection['assets'].values():shutil.copyfile(p/'sim-assets'/n,out/n)
sources=list(selection['sources'])
for n in sources:
    if (c/'inputs'/n).is_file():shutil.copyfile(c/'inputs'/n,out/'inputs'/n)
model=out/'inputs/core/parents/sdram_model_bounded.sv'
model.write_text(strict_hold_text(model.read_text()))
tb=out/'inputs/sim/tb_board_full.sv'
phase=float(re.search(r'\.CLKOUT2_PHASE\(([0-9.]+)\)',(c/'inputs/rtl/moonshine_top_cpl1.sv').read_text())[1])/36.0
s=tb.read_text().replace('7.749',f'{phase-0.001:.3f}').replace('7.751',f'{phase+0.001:.3f}')
assert s.count('.MEM_WORDS(1572865)')==1
s=s.replace('.MEM_WORDS(1572865)',f'.MEM_WORDS(1572865),.CLOCK_FLIGHT_NS({args.flight}),.T_AC_NS({args.access}),.T_OH_NS({args.hold})')
tb.write_text(s,newline='\n')
(out/'source-snapshot.json').write_text(json.dumps(dict(
    scope='MODELED_DIGITAL_BOARD_ONLY',SIMULATION_define=False,flight_ns=args.flight,access_ns=args.access,hold_ns=args.hold,phase_ns=phase,
    sources={n:sha(out/'inputs'/n)for n in sources},assets={n:sha(out/n)for n in selection['assets'].values()}),indent=2)+'\n')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','');steps=[]
def run(label,cmd):
    started=time.monotonic()
    with (out/(label+'.log')).open('wb')as stream:
        q=subprocess.run(cmd,env=env,cwd=out,stdout=stream,stderr=subprocess.STDOUT,timeout=5400)
    steps.append(dict(label=label,command=cmd,returncode=q.returncode,wall_seconds=time.monotonic()-started))
    (out/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
    print(label,q.returncode,flush=True)
    assert q.returncode==0,(label,str(out/(label+'.log')))
run('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-Wall','-I',str(out),'-s','tb','-Ptb.SMOKE=0',
    '-o',str(out/'test.vvp'),*[str(out/'inputs'/n)for n in sources]])
run('simulation',['C:/msys64/ucrt64/bin/vvp.exe','-i',str(out/'test.vvp')])
log=(out/'simulation.log').read_text()
assert 'CPL1_BOARD_NATIVE_QSPI_OBSERVER_PASS guarded_reads=40 checks=139' in log
run('fixture-checker',[sys.executable,str(p/'host-checker/cpl1_snapshot.py'),'--log',str(out/'pages.log'),
    '--expectation',str(p/'host-checker/frame0-expectation.json'),'--require-fixture','--output',str(out/'checker-result.json')])
(out/'result.json').write_text(json.dumps(dict(status='PASS_MODELED_DIGITAL_BOARD_ONLY',CRC='4c5725e5',
    hardware=False,routed_timing=False,flight_ns=args.flight,access_ns=args.access,hold_ns=args.hold),indent=2)+'\n')
print('CANDIDATE_COMPLETE_FIXTURE_PASS',args.flight,args.access,flush=True)
