#!/usr/bin/env python3
"""Offline v32 inventory, source-pin, component and causal replay verification."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent


def path(raw):
    q=Path(raw);assert not q.is_absolute() and '..' not in q.parts
    p=(ROOT/q).resolve();assert p.is_relative_to(ROOT);return p


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(path(p).read_text())


def run(name,*args):
    result=subprocess.run([sys.executable,str(path(name)),*args],capture_output=True,text=True)
    if result.returncode:sys.stderr.write(result.stdout+result.stderr);result.check_returncode()
    return result.stdout.strip()


def main():
    m=load('docs/prototype-v32-provenance.json');assert m['schema']=='gamebub-v32-provenance'
    for p,h in m['file_sha256'].items():assert sha(path(p))==h,('inventory',p)
    for p,h in m['frozen_v31_sha256'].items():assert sha(path(p))==h,('frozen v31',p)
    tests=0
    for p,n in m['passing_test_logs'].items():
        content=path(p).read_text();found=re.search(r'^Ran (\d+) tests? in ',content,re.M)
        assert found and int(found[1])==n and content.rstrip().endswith('OK'),p;tests+=n
    pins=0
    for artifact in m['run_artifacts']:
        for p,h in load(artifact)['source_sha256'].items():assert sha(path(p))==h,('source snapshot',artifact,p);pins+=1
    helpers={}
    for name in m['stored_helpers']:
        print('Replay '+name,flush=True);helpers[name]=run(name)
    audit=run('experiments/python-game-audit-v32-study/audit.py','--check')
    assert audit==run('experiments/python-game-audit-v32-study/audit.py','--check'),'audit nondeterminism'
    for p,h in m['file_sha256'].items():assert sha(path(p))==h,('post-replay inventory',p)
    print(json.dumps(dict(snapshot_files=len(m['file_sha256']),frozen_v31_files=len(m['frozen_v31_sha256']),
                          recorded_passing_tests=tests,source_snapshot_bindings=pins,retained_verifiers=helpers,
                          independent_audit=audit,new_RTL_implemented=False,
                          native_endpoint_FPGA_or_physical_30fps_proven=False,
                          existing_causal_GM27_wire_unchanged=True),indent=2))


if __name__=='__main__':main()
