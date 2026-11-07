#!/usr/bin/env python3
"""Immutable bounded strict Verilator physical-pin materialization attempts."""
import datetime,gzip,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v96-materialize'
CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
 out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 frozen=[ROOT/p for p in ['fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv','fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv','fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv','fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv','fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv','fpga/experiments/cu66-v91l-shared-service/shared_sdram_timed.sv']]
 rtl=[AREA/n for n in ['tile_materializer.sv','tb_materialize.sv']]
 sources=frozen+rtl+[Path(__file__).resolve()]
 report=dict(schema='cu66-v96-materialize-v1',status='FAIL',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},commands=[],modes=[],backend='Verilator 5.020 / GCC 13.3 standalone timed RTL',physical_hardware_tested=False,native_preload=False,unit_seed_data_writes=True,canonical_aperture_bytes=518400,sample_buffer_bytes=64,full_path_integrated=False)
 started=time.monotonic()
 def command(argv,log,timeout):
  c=dict(argv=argv,log=log,exit_code=None);report['commands'].append(c)
  with (out/log).open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,timeout=timeout)
  c['exit_code']=r.returncode
  if r.returncode:raise RuntimeError(f'command exit {r.returncode}: {out/log}')
 try:
  for p in sources:
   target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  command(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30)
  assert 'Verilator 5.020' in (out/'tool-version.log').read_text()
  command(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
  assert '13.3' in (out/'compiler-version.log').read_text()
  for tac,lanes in [(2,4),(7,4),(2,1)]:
   name=f'timed{tac}-lanes{lanes}';top='tb_materialize';build='/build/v96-materialize-'+stamp+'-'+name
   command(['docker','exec',CONTAINER,'verilator','--binary','--timing','--assert','-Wall','-DSIMULATION','--timescale','1ns/1ps','-j','2','--top-module',top,'-GT_AC_NS='+str(tac)+'.0','-GGEN_LANES='+str(lanes),'--Mdir',build,'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror',*[str(out/'sources'/p.relative_to(ROOT)) for p in frozen+rtl]],f'compile-{name}.log',600)
   log=f'simulation-{name}.jsonl';command(['docker','exec',CONTAINER,build+'/V'+top],log,120)
   events=[json.loads(l) for l in (out/log).read_text().splitlines() if l.startswith('{')]
   verdicts=[e for e in events if e['type']=='verdict'];checks=[e for e in events if e['type']=='check']
   assert len(verdicts)==1 and verdicts[0]['status']=='TEST_PASS' and verdicts[0]['checks']==len(checks) and all(e['status']=='PASS' for e in checks)
   report['modes'].append(dict(mode=name,t_ac_ns=tac,generator_lanes=lanes,status='PASS',verdict=verdicts[0],metrics=[e for e in events if e['type']=='metric'],event_log=log+'.gz'))
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources}
  report['status']='PASS_MATERIALIZE_DIRECTED'
 except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  for p in out.glob('simulation-*.jsonl'):
   raw=p.read_bytes();p.with_suffix('.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0));p.unlink()
  report['wall_seconds']=time.monotonic()-started
  report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
  (AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
  print('MATERIALIZE',report['status'],out,flush=True)
if __name__=='__main__':main()
