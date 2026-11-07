#!/usr/bin/env python3
"""Bounded standalone display lease contract test; no physical memory substitute."""
import datetime,gzip,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v91l-overlap-lease';CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8];out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 sources=[AREA/'display_overlap_lease.sv',AREA/'tb_display_overlap_lease.cpp',Path(__file__).resolve(),AREA/'README.md']
 report=dict(schema='cu66-v91l-overlap-lease-v1',status='FAIL',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},commands=[],modes=[],backend='Verilator 5.020 standalone RTL',hardware_tested=False,payload_memory_bytes=0)
 started=time.monotonic()
 def command(argv,log,timeout):
  c=dict(argv=argv,log=log,exit_code=None);report['commands'].append(c)
  with (out/log).open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,timeout=timeout)
  c['exit_code']=r.returncode
  if r.returncode:raise RuntimeError(f'command exit {r.returncode}: {out/log}')
 try:
  for p in sources:
   t=out/'sources'/p.relative_to(ROOT);t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,t)
  command(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30);assert 'Verilator 5.020' in (out/'tool-version.log').read_text()
  command(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
  build='/build/v91l-overlap-lease-'+stamp
  command(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','--timing','--assert','-Wall','-DSIMULATION','--timescale','1ns/1ps','-j','2','--top-module','display_overlap_lease','--Mdir',build,'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror',*[str(out/'sources'/p.relative_to(ROOT)) for p in sources[:2]]],'compile.log',600)
  log='simulation.jsonl';command(['docker','exec',CONTAINER,build+'/Vdisplay_overlap_lease'],log,120)
  events=[json.loads(l) for l in (out/log).read_text().splitlines() if l.startswith('{')];v=[e for e in events if e['type']=='verdict'];checks=[e for e in events if e['type']=='check']
  assert len(v)==1 and v[0]['status']=='TEST_PASS' and v[0]['checks']==len(checks) and all(e['status']=='PASS' for e in checks)
  report['modes'].append(dict(mode='lease',status='PASS',verdict=v[0],event_log=log+'.gz'))
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources};report['status']='PASS_DISPLAY_OVERLAP_LEASE_DIRECTED'
 except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  for p in out.glob('simulation*.jsonl'):
   p.with_suffix('.jsonl.gz').write_bytes(gzip.compress(p.read_bytes(),mtime=0));p.unlink()
  report['wall_seconds']=time.monotonic()-started;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('OVERLAP_LEASE',report['status'],out,flush=True)
if __name__=='__main__':main()
