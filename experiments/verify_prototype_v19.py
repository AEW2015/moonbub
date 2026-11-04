#!/usr/bin/env python3
"""Read-only v19 frame admission and conditional sparse decoder evidence checks."""
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
    path=Path(raw);return path if path.is_absolute() else ROOT/path
def run(path,*args):
    result=subprocess.run([sys.executable,str(ROOT/path),*args],capture_output=True,text=True)
    if result.returncode:
        sys.stderr.write(result.stdout+result.stderr);result.check_returncode()
    return result.stdout.strip()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sunshine-root',type=Path,default=ROOT.parent/'sunshine-30fps-study');args=parser.parse_args()
    m=load('docs/prototype-v19-provenance.json')
    for path,h in m['file_sha256'].items():assert sha(ROOT/path)==h,('inventory',path)
    bindings=0
    for path in m['run_artifacts']:
        for raw,h in load(path)['source_sha256'].items():assert sha(resolve(raw))==h,('snapshot',path,raw);bindings+=1
    for path,h in m['frozen_v18_source_sha256'].items():assert sha(ROOT/path)==h,('frozen v18',path)
    tests=0
    for folder,n in m['test_counts'].items():
        txt=(ROOT/folder/'tests.log').read_text();match=re.search(r'^Ran (\d+) tests? in ',txt,re.M)
        assert match and int(match[1])==n and txt.rstrip().endswith('OK'),folder;tests+=n
    helpers={folder:run(folder+'/verify.py') for folder in m['stored_helpers']}
    analyses={folder:run(folder+'/analyze.py','--check') for folder in m['analysis_helpers']}
    audit_folder='experiments/python-game-audit-v19-study'
    audit=load(audit_folder+'/audit.json')
    assert audit['status']=='verified' and audit['final_signals_received']
    assert set(audit['results'])=={'frame_grant','causal_stripe'}
    assert all(x['status']=='verified' and not x['errors'] for x in audit['results'].values())
    run(audit_folder+'/audit.py','--check')
    peer=args.sunshine_root/m['sunshine_readme']['path'];peer_checked=peer.is_file()
    if peer_checked:assert sha(peer)==m['sunshine_readme']['sha256'],'paired Sunshine README'
    missing=[]
    for raw,h in m['input_sha256'].items():
        path=Path(raw)
        if path.is_file():assert sha(path)==h,('external media',raw)
        else:missing.append(raw)
    print(json.dumps(dict(snapshot_files=len(m['file_sha256']),source_snapshot_bindings=bindings,
        frozen_v18_files=len(m['frozen_v18_source_sha256']),recorded_passing_tests=tests,
        retained_helpers=helpers,untimed_analyses=analyses,fresh_independent_audit='verified',
        esp32_isa_or_rf_calibrated=False,fpga_placed_or_routed=False,
        joint_native_or_physical_30fps_proven=False,missing_external_media=missing,
        paired_sunshine_readme_checked=peer_checked),indent=2))
if __name__=='__main__':main()
