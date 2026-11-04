#!/usr/bin/env python3
"""Read-only verification of v16 portable contracts and conditional models."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parent.parent

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def load(path):return json.loads((ROOT/path).read_text())
def resolve(raw):
    marker='/moonbub-30fps-study/'
    if marker in raw:return ROOT/raw.split(marker,1)[1]
    p=Path(raw)
    return p if p.is_absolute() else ROOT/p
def run(path,*args):
    r=subprocess.run([sys.executable,str(ROOT/path),*args],capture_output=True,text=True)
    if r.returncode:
        sys.stderr.write(r.stdout+r.stderr)
        r.check_returncode()
    return r.stdout.strip()
def main():
    p=argparse.ArgumentParser();p.add_argument('--sunshine-root',type=Path,default=ROOT.parent/'sunshine-30fps-study');args=p.parse_args()
    m=load('docs/prototype-v16-provenance.json')
    for path,expected in m['file_sha256'].items():assert sha(ROOT/path)==expected,('inventory',path)
    bindings=0
    for path in m['run_artifacts']:
        for raw,expected in load(path)['source_sha256'].items():
            assert sha(resolve(raw))==expected,('source snapshot',path,raw);bindings+=1
    for path,expected in m['frozen_v15_source_sha256'].items():assert sha(ROOT/path)==expected,('frozen v15 source',path)
    count=0
    for folder,expected in m['test_counts'].items():
        text=(ROOT/folder/'tests.log').read_text();match=re.search(r'^Ran (\d+) tests? in ',text,re.M)
        assert match and int(match[1])==expected and text.rstrip().endswith('OK'),folder
        count+=expected
    helpers={folder:run(folder+'/verify.py') for folder in m['stored_helpers']}
    analysis=run('experiments/python-game-refresh-v16-study/analyze.py','--check')
    audit=load('experiments/python-game-audit-v16-study/audit.json')
    assert audit['status']=='verified'
    assert len(audit['inputs'])==len(m['run_artifacts'])
    assert all(x['status']=='verified' for x in audit['results'].values())
    assert all(x['status']=='verified' for x in audit['inputs'].values())
    assert all(x=='verified' for x in audit['checks'].values()),audit['checks']
    # Recompute audit in a fresh interpreter without rewriting retained artifacts.
    code="import json,sys;sys.path.insert(0,sys.argv[1]);import audit;print(json.dumps(audit.load_audit()))"
    result=subprocess.run([sys.executable,'-c',code,str(ROOT/'experiments/python-game-audit-v16-study')],check=True,capture_output=True,text=True)
    current=json.loads(result.stdout)
    assert current['status']=='verified' and all(x=='verified' for x in current['checks'].values())
    refresh=load('experiments/python-game-refresh-v16-study/matched-refresh.json')
    assert refresh['matched_key_total_regular_bytes']==152754 and refresh['matched_key_total_coarse_bytes']==128210
    assert len(refresh['matched_independent_key_pairs'])==5
    peer=args.sunshine_root/m['sunshine_readme']['path'];peer_checked=peer.is_file()
    if peer_checked:assert sha(peer)==m['sunshine_readme']['sha256'],'paired Sunshine README'
    missing=[]
    for raw,expected in m['input_sha256'].items():
        path=Path(raw)
        if path.is_file():assert sha(path)==expected,('external media',raw)
        else:missing.append(raw)
    print(json.dumps(dict(snapshot_files=len(m['file_sha256']),source_snapshot_bindings=bindings,
        frozen_v15_source_files=len(m['frozen_v15_source_sha256']),recorded_passing_tests=count,
        retained_helpers=helpers,matched_refresh_analysis=analysis,fresh_independent_audit='verified',
        matched_coarser_key_body_saving_percent=refresh['matched_key_complete_body_saving_percent'],
        primary_target='720x480coded/720x405active/30fps',
        conditional_planning_is_hardware_proof=False,esp32_native_or_live_30fps_proven=False,
        missing_external_media=missing,paired_sunshine_readme_checked=peer_checked),indent=2))
if __name__=='__main__':main()
