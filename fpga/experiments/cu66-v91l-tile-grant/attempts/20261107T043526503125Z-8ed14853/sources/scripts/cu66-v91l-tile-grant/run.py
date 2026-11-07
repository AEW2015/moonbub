#!/usr/bin/env python3
"""Strict bounded policy tests and exact legacy REF_LINES1 control."""
import datetime,gzip,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v91l-tile-grant';CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8];out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 old=ROOT/'fpga/experiments/cu66-v91l-reference-reader/reader_client_mux.sv'
 sources=[old,*[AREA/n for n in ('tile_reader_mux.sv','tile_mux_unit.sv','tb_tile_mux.cpp','tile_grant_shared_timed.sv')],Path(__file__).resolve()]
 report=dict(schema='cu66-v91l-tile-grant-unit-v1',status='FAIL',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},commands=[],modes=[],hardware_tested=False,payload_memory_bytes=0,gap_cycles=8)
 began=time.monotonic()
 def cmd(argv,log,timeout):
  e=dict(argv=argv,log=log,exit_code=None);report['commands'].append(e)
  with (out/log).open('w') as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  e['exit_code']=r.returncode
  if r.returncode:raise RuntimeError(f'command exit {r.returncode}: {out/log}')
 try:
  for p in sources:
   target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  cmd(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30);cmd(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
  for lines in (1,4):
   build='/build/v91l-tile-grant-unit-'+stamp+'-n'+str(lines)
   files=[old,AREA/'tile_reader_mux.sv',AREA/'tile_mux_unit.sv',AREA/'tb_tile_mux.cpp']
   cmd(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','--timing','--assert','-Wall','-DSIMULATION','--timescale','1ns/1ps','-j','2','--top-module','tile_mux_unit','-GREF_LINES='+str(lines),'--Mdir',build,'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror -DTEST_REF_LINES='+str(lines),*[str(out/'sources'/p.relative_to(ROOT)) for p in files]],'compile-n'+str(lines)+'.log',600)
   log='simulation-n'+str(lines)+'.jsonl';cmd(['docker','exec',CONTAINER,build+'/Vtile_mux_unit'],log,120)
   events=[json.loads(l) for l in (out/log).read_text().splitlines() if l.startswith('{')];v=[e for e in events if e['type']=='verdict'];checks=[e for e in events if e['type']=='check'];assert len(v)==1 and v[0]['status']=='TEST_PASS' and v[0]['checks']==len(checks)
   report['modes'].append(dict(mode='mux'+str(lines),reference_lines=lines,event_log=log+'.gz',verdict=v[0],status='PASS'))
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources};report['status']='PASS_BOUNDED_REFERENCE_TILE_GRANTS'
 except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  for p in out.glob('simulation*.jsonl'):
   p.with_suffix('.jsonl.gz').write_bytes(gzip.compress(p.read_bytes(),mtime=0));p.unlink()
  report['wall_seconds']=time.monotonic()-began;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('TILE_GRANT_UNIT',report['status'],out,flush=True)
if __name__=='__main__':main()
