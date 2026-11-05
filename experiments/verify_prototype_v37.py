#!/usr/bin/env python3
"""Verify portable v37 inventory, byte identity, new grammar and comparison."""
import hashlib,json,re,subprocess,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def path(raw):
    p=Path(raw);assert not p.is_absolute() and '..' not in p.parts
    value=(ROOT/p).resolve();assert value.is_relative_to(ROOT);return value
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(raw):return json.loads(path(raw).read_text())

def run(name,*args):
    value=subprocess.run([sys.executable,str(path(name)),*args],capture_output=True,text=True)
    if value.returncode:sys.stderr.write(value.stdout+value.stderr);value.check_returncode()
    return value.stdout.strip()

def main():
    data=load('docs/prototype-v37-provenance.json');assert data['schema']=='gamebub-v37-provenance'
    for p,h in data['file_sha256'].items():assert sha(path(p))==h,('inventory',p)
    for p,h in data['frozen_v36_sha256'].items():assert sha(path(p))==h,('frozen v36',p)
    tests=pins=0
    for p,n in data['passing_test_logs'].items():
        content=path(p).read_text();found=re.search(r'^Ran (\d+) tests? in ',content,re.M)
        assert found and int(found[1])==n and content.rstrip().endswith('OK'),p;tests+=n
    for name in data['run_artifacts']:
        for p,h in load(name)['source_sha256'].items():assert sha(path(p))==h,('producer',name,p);pins+=1
    results={}
    for name in data['stored_helpers']:
        print('Replay '+name,flush=True);results[name]=run(name)
    comparison=run('experiments/compare_prototype_v37.py','--check')
    profile=load('docs/prototype-v37-sender-profile.json');assert profile['frames']==6
    direct=load('experiments/python-game-direct-v37-study/results.json')
    assert direct['cases'][1]['scene']==profile['scene']
    packet_tags=[]
    for row in direct['cases'][1]['rows'][:6]:
        desc=row['packet'];stored=path('experiments/python-game-direct-v37-study/'+desc['path']).read_bytes()
        assert hashlib.sha256(stored).hexdigest()==desc['stored_sha256']
        raw=zlib.decompress(stored);tag=hashlib.sha256(raw).hexdigest()
        assert tag==desc['raw_sha256'] and len(raw)==desc['raw_bytes'];packet_tags.append(tag)
    assert packet_tags==profile['wire_sha256']
    assert profile['total_instrumented_seconds']>0 and len(profile['top_self_time'])==30
    for p,h in data['file_sha256'].items():assert sha(path(p))==h,('post-replay inventory',p)
    print(json.dumps(dict(snapshot_files=len(data['file_sha256']),frozen_v36_files=len(data['frozen_v36_sha256']),
                          recorded_passing_tests=tests,source_snapshot_bindings=pins,retained_verifiers=results,
                          comparison=comparison,profile_exact_frames=6,new_profile='CS37 research only',
                          new_RTL_implemented=False,native_endpoint_FPGA_or_physical_30fps_proven=False,
                          HEVC_AV1_superiority_proven=False),indent=2))

if __name__=='__main__':main()
