#!/usr/bin/env python3
"""Portable v38 inventory, exact integration/arithmetic/spatial and native check."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def path(raw):
    p=Path(raw);assert not p.is_absolute() and '..' not in p.parts
    result=(ROOT/p).resolve();assert result.is_relative_to(ROOT);return result
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(raw):return json.loads(path(raw).read_text())
def run(name,*args):
    value=subprocess.run([sys.executable,str(path(name)),*args],capture_output=True,text=True)
    if value.returncode:sys.stderr.write(value.stdout+value.stderr);value.check_returncode()
    return value.stdout.strip()

def main():
    data=load('docs/prototype-v38-provenance.json');assert data['schema']=='gamebub-v38-provenance'
    for p,h in data['file_sha256'].items():assert sha(path(p))==h,('inventory',p)
    for p,h in data['frozen_v37_sha256'].items():assert sha(path(p))==h,('frozen v37',p)
    tests=pins=0
    for p,n in data['passing_test_logs'].items():
        text=path(p).read_text();found=re.search(r'^Ran (\d+) tests? in ',text,re.M)
        assert found and int(found[1])==n and text.rstrip().endswith('OK'),p;tests+=n
    for name in data['run_artifacts']:
        for p,h in load(name)['source_sha256'].items():assert sha(path(p))==h,('producer',name,p);pins+=1
    results={}
    for name in data['stored_helpers']:
        print('Replay '+name,flush=True);results[name]=run(name)
    comparison=run('experiments/compare_prototype_v38.py','--check')
    for p,h in data['file_sha256'].items():assert sha(path(p))==h,('post-replay inventory',p)
    print(json.dumps(dict(snapshot_files=len(data['file_sha256']),frozen_v37_files=len(data['frozen_v37_sha256']),
                          recorded_passing_tests=tests,source_snapshot_bindings=pins,retained_verifiers=results,
                          native_prefix_comparison=comparison,new_profiles=['CS38 arithmetic','SP38 spatial'],
                          six_hour_run_complete=False,new_RTL_implemented=False,native_endpoint_FPGA_or_physical_30fps_proven=False,
                          HEVC_AV1_superiority_proven=False),indent=2))

if __name__=='__main__':main()
