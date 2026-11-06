#!/usr/bin/env python3
import datetime,hashlib,json,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent

def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'test-attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
 sources=[Path(__file__).resolve(),AREA/'test_trace.cpp',AREA/'trace.hpp',ROOT/'experiments/python-gamebub-v88/entropy/codec.hpp']
 pins={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
 for p in sources:(out/p.name).write_bytes(p.read_bytes())
 commands=[['docker','exec','gamebub-cu66-v69-build','g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'test_trace.cpp'),'-o','/build/v89-observer-tests-'+stamp],['docker','exec','gamebub-cu66-v69-build','/build/v89-observer-tests-'+stamp]]
 results=[]
 for i,command in enumerate(commands):
  r=subprocess.run(command,text=True,capture_output=True);(out/f'command{i}.log').write_text(r.stdout+r.stderr);results.append(dict(argv=command,observed_exit_code=r.returncode));assert r.returncode==0,r.stdout+r.stderr
 marker=next(line for line in r.stdout.splitlines() if line.startswith('V89_OBSERVER_TEST_PASS'));count=int(marker.split('checks=')[1])
 report=dict(schema='cu66-v89-observer-tests-v1',status='PASS_NATIVE_LOOKAHEAD_RAW_AND_PRIMITIVE_COUNTS',checks_count=count,commands=results,source_sha256=pins,scope='Synthetic actual Rice parser/decode and work-attribution tests, not elapsed hardware cycles.')
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'tests.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print(report['status'],count)
if __name__=='__main__':main()
