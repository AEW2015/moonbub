#!/usr/bin/env python3
"""Synthetic observer tests only; no DUT or actual hardware fault injection."""
import hashlib, json, subprocess, time, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v79/system'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=AREA/'monitor-tests';out.mkdir(exist_ok=True)
 paths=[AREA/'monitor.hpp',AREA/'monitor_tb.cpp',Path(__file__).resolve()]
 pins={str(p.relative_to(ROOT)):sha(p) for p in paths};commands=[]
 binary='/build/v79-monitor-unit-'+uuid.uuid4().hex
 try:
  for argv,name in [(['docker','exec','gamebub-cu66-v69-build','g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'monitor_tb.cpp'),'-o',binary],'build.log'),(['docker','exec','gamebub-cu66-v69-build',binary],'run.log')]:
   begin=time.monotonic()
   with(out/name).open('w')as stream:r=subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT,timeout=60,cwd=ROOT)
   commands.append(dict(argv=argv,log=str((out/name).relative_to(ROOT)),exit_code=r.returncode,wall_seconds=time.monotonic()-begin,sha256=sha(out/name)))
   assert r.returncode==0,(out/name).read_text()
 finally:
  subprocess.run(['docker','exec','gamebub-cu66-v69-build','rm','-f',binary],check=True,timeout=30)
 log=(out/'run.log').read_text();assert 'MONITOR_UNIT_PASS tests=9 observer_unit_only=1 hardware_fault_injection=0' in log
 assert pins=={p:sha(ROOT/p)for p in pins}
 (out/'results.json').write_text(json.dumps(dict(schema='cu79-observer-unit-v1',status='PASS',tests=9,observer_unit_only=True,hardware_fault_injection=False,source_sha256=pins,commands=commands),indent=2)+'\n')
 print('V79_MONITOR_UNIT_PASS tests=9 observer_unit_only=1 hardware_fault_injection=0')
if __name__=='__main__':main()
