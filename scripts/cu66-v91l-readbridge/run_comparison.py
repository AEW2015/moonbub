#!/usr/bin/env python3
"""Timed real-controller BL8 bridge and native row-retention comparison."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v91l-readbridge';CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--unit-only',action='store_true');ap.add_argument('--seed',type=int,choices=(912601,912602),action='append');args=ap.parse_args();seeds=args.seed or [912601,912602]
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8];out=AREA/'comparison-attempts'/stamp;out.mkdir(parents=True)
 sv=[ROOT/'fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv',ROOT/'fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv',ROOT/'fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv',AREA/'bl8_read_bridge.sv',AREA/'tb_readbridge.sv']
 sources=sv+[AREA/'generate_fixtures.py',Path(__file__).resolve()]
 inputs=[AREA/'fixtures.json',AREA/'preload.hex.gz',AREA/'native-lines.hex.gz']
 fixtures=json.loads((AREA/'fixtures.json').read_text());inputs += [ROOT/n for n in fixtures['inputs']]
 report=dict(schema='cu66-v91l-readbridge-comparison-v1',status='FAIL',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},commands=[],modes=[],seeds=seeds,native_replay=not args.unit_only,physical_hardware_tested=False,full_live_codec_join=False,actual_converter_rtl_join=False,shared_service_complete=False,sustained_hardware_30fps_proven=False,validated_full_frame_under10ms_proven=False,scope='Tagged aligned BL8 read bridge and static retained/independent native client through unchanged actual controller and timed functional SDRAM pins. Direct model preload outside frame fences, not physical write/live-decode or hardware validation.')
 temporary=[];started=time.monotonic()
 def command(argv,log,timeout):
  c=dict(argv=argv,log=log,exit_code=None);report['commands'].append(c)
  with (out/log).open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,timeout=timeout)
  c['exit_code']=r.returncode
  if r.returncode:raise RuntimeError(f'command exit{r.returncode}: {out/log}')
 try:
  for p in sources:
   target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  for p in inputs:
   target=out/'inputs'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  report['input_expansions']=[]
  if not args.unit_only:
   for name in ('preload','native-lines'):
    p=out/(name+'.hex');p.write_bytes(gzip.decompress((out/'inputs'/(name+'.hex.gz')).read_bytes()));temporary.append(p);report['input_expansions'].append(dict(path=p.name,raw_sha256=sha(p),compressed_path='inputs/'+name+'.hex.gz'))
  command(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30);command(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
  for retain in (0,1):
   for tac in (2,7):
    build='/build/v91l-readbridge-'+stamp+'-'+str(retain)+'-'+str(tac)
    snapshot=[str(out/'sources'/p.relative_to(ROOT)) for p in sv]
    command(['docker','exec',CONTAINER,'verilator','--binary','--timing','--assert','-Wall','-DSIMULATION','-j','2','--top-module','tb_readbridge','-GRETAIN='+str(retain),'-GT_AC_NS='+str(tac)+'.0','--Mdir',build,'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror',*snapshot],f'compile-{retain}-tac{tac}.log',600)
    for seed in seeds:
     native=not args.unit_only and tac==2;name=f'simulation-{retain}-{seed}-tac{tac}.jsonl';mode=dict(retain=retain,seed=seed,t_ac_ns=tac,status='FAIL',native_replay=native,event_log=name+'.gz');report['modes'].append(mode)
     argv=['docker','exec',CONTAINER,build+'/Vtb_readbridge','+SEED='+str(seed)]
     if native:argv+=['+PRELOAD='+str(out/'preload.hex'),'+NATIVE_LINES='+str(out/'native-lines.hex')]
     command(argv,name,1200)
     frames=[];verdict=[];checks=[];begin=None
     with (out/name).open() as f:
      for line in f:
       if not line.startswith('{'):continue
       e=json.loads(line)
       if e['type']=='frame_begin':begin=e
       elif e['type']=='frame_end':
        assert begin is not None and e['bank']==begin['bank'];frames.append(dict(e,first_cycle=begin['cycle'],first_time_ps=begin['time_ps'],cycles=e['cycle']-begin['cycle'],modeled_ms_at100mhz=(e['cycle']-begin['cycle'])/100000));begin=None
       elif e['type']=='verdict':verdict.append(e)
       elif e['type']=='check':assert e['status']=='PASS';checks.append(e['name'])
     assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS' and verdict[0]['seed']==seed and verdict[0]['retain']==retain and verdict[0]['t_ac_ns']==tac
     assert len(frames)==(2 if native else 0) and len(checks)==verdict[0]['checks']
     mode.update(status='PASS_TIMED_BRIDGE_READS_AND_NATIVE_EXACT_CLIENT',verdict=verdict[0],checks=checks,frames=frames)
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources};assert report['inputs_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
  report['comparisons']=[]
  if not args.unit_only:
   for seed in seeds:
    control=next(m for m in report['modes'] if m['seed']==seed and m['retain']==0 and m['t_ac_ns']==2);retained=next(m for m in report['modes'] if m['seed']==seed and m['retain']==1 and m['t_ac_ns']==2)
    for old,new in zip(control['frames'],retained['frames']):report['comparisons'].append(dict(seed=seed,bank=new['bank'],independent_cycles=old['cycles'],retained_cycles=new['cycles'],cycle_reduction_percent=(old['cycles']-new['cycles'])/old['cycles']*100))
  report['status']='PASS_TIMED_BL8_BRIDGE_AND_NATIVE_RETENTION_COMPARISON'
 except BaseException as error:report.update(error_class=type(error).__name__,error=str(error));raise
 finally:
  for p in temporary:
   if p.exists():p.unlink()
  report['compressed_artifacts']={}
  for p in out.glob('simulation-*.jsonl'):
   raw=p.read_bytes();packed=p.with_suffix('.jsonl.gz');packed.write_bytes(gzip.compress(raw,mtime=0));report['compressed_artifacts'][p.name]=dict(path=packed.name,gzip_sha256=sha(packed),raw_sha256=hashlib.sha256(raw).hexdigest(),rows=sum(x.startswith(b'{') for x in raw.splitlines()));p.unlink()
  report['wall_seconds']=time.monotonic()-started;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'comparison-results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('READBRIDGE_COMPARISON',report['status'],out,flush=True)
if __name__=='__main__':main()
