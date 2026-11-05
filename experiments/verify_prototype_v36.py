#!/usr/bin/env python3
"""Replay v36 against a hash-frozen portable dependency inventory."""
import hashlib,json,re,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent

def path(raw):
    q=Path(raw);assert not q.is_absolute() and '..' not in q.parts
    value=(ROOT/q).resolve();assert value.is_relative_to(ROOT);return value

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    manifest=json.loads(path('docs/prototype-v36-provenance.json').read_text())
    assert manifest['schema']=='gamebub-v36-provenance'
    for raw,tag in manifest['file_sha256'].items():assert sha(path(raw))==tag,('inventory',raw)
    for raw,tag in manifest['frozen_v35_sha256'].items():assert sha(path(raw))==tag,('frozen v35',raw)
    tests=0;pins=0
    for raw,n in manifest['passing_test_logs'].items():
        content=path(raw).read_text();found=re.search(r'^Ran (\d+) tests? in ',content,re.M)
        assert found and int(found[1])==n and content.rstrip().endswith('OK'),raw;tests+=n
    for raw in manifest['run_artifacts']:
        for source,tag in json.loads(path(raw).read_text())['source_sha256'].items():
            assert sha(path(source))==tag,('producer source',raw,source);pins+=1
    results={}
    for helper in manifest['stored_helpers']:
        print('Replay '+helper,flush=True)
        value=subprocess.run([sys.executable,str(path(helper))],capture_output=True,text=True)
        if value.returncode:sys.stderr.write(value.stdout+value.stderr);value.check_returncode()
        results[helper]=value.stdout.strip()
    for raw,tag in manifest['file_sha256'].items():assert sha(path(raw))==tag,('post-replay inventory',raw)
    print(json.dumps(dict(snapshot_files=len(manifest['file_sha256']),frozen_v35_files=len(manifest['frozen_v35_sha256']),
                          recorded_passing_tests=tests,source_snapshot_bindings=pins,retained_verifiers=results,
                          new_profile='CN36 research only',new_RTL_implemented=False,
                          native_endpoint_FPGA_or_physical_30fps_proven=False,HEVC_AV1_superiority_proven=False),indent=2))

if __name__=='__main__':main()
