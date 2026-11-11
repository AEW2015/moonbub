#!/usr/bin/env python3
"""Run the bounded standalone monitor accounting test, with a local receipt."""
from pathlib import Path
import hashlib
import json
import subprocess

root=Path(__file__).resolve().parents[3]
unit=root/'fpga/experiments/cu66-v129-observe'
area=root/'experiments/python-gamebub-v129/latency-monitor'
image='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
inputs=[unit/'monitor.hpp',unit/'test_monitor.cpp',unit/'tb_keyframe.cpp',Path(__file__).resolve(),
        root/'scripts/cu66-v129/latency-monitor/prepare.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p.relative_to(root)):sha(p) for p in inputs}
cmd=['docker','run','--rm','--network','none','--cpus','1','--memory','512m','--memory-swap','512m',
     '--mount',f'type=bind,src={unit},dst=/src,readonly',image,'timeout','30s','sh','-c',
     'g++ -std=c++17 -O2 -Wall -Wextra -Werror -I/src /src/test_monitor.cpp -o /tmp/test-monitor && /tmp/test-monitor']
run=subprocess.run(cmd,text=True,capture_output=True,timeout=40)
assert before=={str(p.relative_to(root)):sha(p) for p in inputs}
record={'schema':'v129-latency-monitor-unit-v1','status':'PASS' if run.returncode==0 else 'FAIL',
        'source_sha256':before,'command':cmd,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,
        'scope':'Standalone monitor math only; generated full-parent adapter was not compiled or run.'}
area.mkdir(parents=True,exist_ok=True)
(area/'unit-result.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(record['status'])
raise SystemExit(0 if run.returncode==0 else 1)
