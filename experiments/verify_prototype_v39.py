#!/usr/bin/env python3
"""Portable v39 causal reference/rate/selection/inventory replay."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def path(raw):
    p=Path(raw);assert not p.is_absolute() and '..' not in p.parts
    value=(ROOT/p).resolve();assert value.is_relative_to(ROOT);return value
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name):return json.loads(path(name).read_text())
def run(name,*args):
    result=subprocess.run([sys.executable,str(path(name)),*args],capture_output=True,text=True)
    if result.returncode:sys.stderr.write(result.stdout+result.stderr);result.check_returncode()
    return result.stdout.strip()
def main():
    data=load('docs/prototype-v39-provenance.json');assert data['schema']=='gamebub-v39-provenance'
    for p,h in data['file_sha256'].items():assert sha(path(p))==h,('inventory',p)
    for p,h in data['frozen_v38_sha256'].items():assert sha(path(p))==h,('frozen v38',p)
    tests=inherited=pins=0
    for key in ('passing_test_logs','inherited_codec_test_logs'):
        for p,n in data[key].items():
            content=path(p).read_text();found=re.search(r'^Ran (\d+) tests? in ',content,re.M)
            assert found and int(found[1])==n and content.rstrip().endswith('OK'),p
            if key=='passing_test_logs':tests+=n
            else:inherited+=n
    for name in data['run_artifacts']:
        for p,h in load(name)['source_sha256'].items():assert sha(path(p))==h,('producer',name,p);pins+=1
    results={}
    for name in data['stored_helpers']:
        print('Replay '+name,flush=True);results[name]=run(name)
    comparison=run('experiments/compare_prototype_v39.py','--check')
    for p,h in data['file_sha256'].items():assert sha(path(p))==h,('post-replay inventory',p)
    print(json.dumps(dict(snapshot_files=len(data['file_sha256']),frozen_v38_files=len(data['frozen_v38_sha256']),new_passing_tests=tests,
                          inherited_codec_tests=inherited,source_snapshot_bindings=pins,retained_verifiers=results,comparison=comparison,
                          six_hour_run_complete=False,new_RTL_implemented=False,native_endpoint_FPGA_or_physical_30fps_proven=False,
                          HEVC_AV1_superiority_proven=False),indent=2))
if __name__=='__main__':main()
