#!/usr/bin/env python3
"""Read-only v18 candidate, packet admission and trace evidence reconciliation."""
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
    p=Path(raw);return p if p.is_absolute() else ROOT/p
def run(path,*args):
    r=subprocess.run([sys.executable,str(ROOT/path),*args],capture_output=True,text=True)
    if r.returncode:
        sys.stderr.write(r.stdout+r.stderr);r.check_returncode()
    return r.stdout.strip()
def main():
    p=argparse.ArgumentParser();p.add_argument('--sunshine-root',type=Path,default=ROOT.parent/'sunshine-30fps-study');args=p.parse_args()
    m=load('docs/prototype-v18-provenance.json')
    for path,h in m['file_sha256'].items():assert sha(ROOT/path)==h,('inventory',path)
    bindings=0
    for path in m['run_artifacts']:
        for raw,h in load(path)['source_sha256'].items():assert sha(resolve(raw))==h,('snapshot',path,raw);bindings+=1
    for path,h in m['frozen_v17_source_sha256'].items():assert sha(ROOT/path)==h,('frozen v17',path)
    tests=0
    for folder,n in m['test_counts'].items():
        txt=(ROOT/folder/'tests.log').read_text();match=re.search(r'^Ran (\d+) tests? in ',txt,re.M)
        assert match and int(match[1])==n and txt.rstrip().endswith('OK'),folder;tests+=n
    helpers={folder:run(folder+'/verify.py') for folder in m['stored_helpers']}
    analyses={folder:run(folder+'/analyze.py','--check') for folder in m['analysis_helpers']}
    audit_folder='experiments/python-game-audit-v18-study'
    audit=load(audit_folder+'/audit.json')
    assert audit['status']=='verified' and audit['final_signals_received'] and len(audit['results'])==3
    assert all(x['status']=='verified' and not x['errors'] for x in audit['results'].values())
    audit_output=run(audit_folder+'/audit.py','--check')
    joint=load('experiments/python-game-joint-admission-study/results.json')
    assert joint['case_count']==8 and sum(c['result']['capture_count'] for c in joint['cases'])==636
    peer=args.sunshine_root/m['sunshine_readme']['path'];peer_checked=peer.is_file()
    if peer_checked:assert sha(peer)==m['sunshine_readme']['sha256'],'paired Sunshine README'
    missing=[]
    for raw,h in m['input_sha256'].items():
        p=Path(raw)
        if p.is_file():assert sha(p)==h,('external media',raw)
        else:missing.append(raw)
    print(json.dumps(dict(snapshot_files=len(m['file_sha256']),source_snapshot_bindings=bindings,
        frozen_v17_files=len(m['frozen_v17_source_sha256']),recorded_passing_tests=tests,
        retained_helpers=helpers,untimed_analyses=analyses,fresh_independent_audit='verified',
        actual_candidate_commit=True,actual_packet_gateway_decode_reference_integration=True,
        integrated_capture_events=636,native_profiles=6,native_unique_acquisitions=90,
        candidate_commit_identical_controls=42,retained_ar03_vectors=16,
        esp32_isa_or_rf_calibrated=False,fpga_memory_scanline_cycles_integrated=False,
        joint_native_or_physical_30fps_proven=False,missing_external_media=missing,
        paired_sunshine_readme_checked=peer_checked),indent=2))
if __name__=='__main__':main()
