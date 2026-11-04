#!/usr/bin/env python3
"""Read-only reconciliation of v14 custom-codec and ownership evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text())
def resolve(raw):
    marker='/moonbub-30fps-study/'
    return ROOT/raw.split(marker,1)[1] if marker in raw else Path(raw)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sunshine-root',type=Path,default=ROOT.parent/'sunshine-30fps-study')
    args=parser.parse_args()
    m=load('docs/prototype-v14-provenance.json')
    for path,expected in m['file_sha256'].items():assert sha(ROOT/path)==expected,('snapshot',path)
    bindings=0
    for path in m['run_artifacts']:
        data=load(path)
        for raw,expected in data['source_sha256'].items():
            assert sha(resolve(raw))==expected,('executed source',path,raw)
            bindings+=1
    count=0
    for folder,expected in m['test_counts'].items():
        log=(ROOT/folder/'tests.log').read_text()
        match=re.search(r'^Ran (\d+) tests? in ',log,re.M)
        assert match and int(match[1])==expected and log.rstrip().endswith('OK'),folder
        count+=expected
    helpers={}
    for folder in m['stored_helpers']:
        result=subprocess.run([sys.executable,str(ROOT/folder/'verify.py')],check=True,capture_output=True,text=True)
        helpers[folder]=result.stdout.strip()
    subprocess.run([sys.executable,str(ROOT/'experiments/python-game-overlap-reference-study/analyze.py'),'--check'],
                   check=True,capture_output=True,text=True)
    audit=load('experiments/python-game-audit-v14-study/audit.json')
    assert all(v['status']=='available' for v in audit['inputs'].values())
    assert all(v['all_match_and_stable'] for v in audit['source_pins_by_input'].values())
    assert all(v is not None for v in audit['studies'].values())
    assert audit['studies']['recent_reference']['attempt_rows_recomputed']==924
    assert audit['studies']['skip_residual']['decisions_recomputed']==770
    finite=load('experiments/python-game-reference-ownership-study/results.json')
    assert finite['case_count']==13 and sum(c['result']['capture_count'] for c in finite['cases'])==1152
    overlap=load('experiments/python-game-overlap-reference-study/results.json')
    assert overlap['case_count']==9 and sum(c['result']['capture_count'] for c in overlap['cases'])==828
    cases={c['profile']:c for c in overlap['cases'] if c['source']=='mass-effect-2600-heldout180'}
    left,right=cases['immutable_initial'],cases['overlap_recent16_initial']
    for field in ('packets','commits','presented'):
        a=[p['id'] for p in left['result'][field]];b=[p['id'] for p in right['result'][field]]
        assert a==b and len(a)==179
    for case in (left,right):
        r=case['result'];ids=[p['id'] for p in r['presented'] if 500<=p['at_ms']<5500]
        assert ids==list(range(13,163)) and len(ids)==150
        hashes={c['id']:c['rgb_sha256'] for c in r['commits']}
        assert len({hashes[i] for i in ids})==150
        assert len({case['manifest']['frame_sha256'][i] for i in ids})==150
        assert [d['id'] for d in r['drops']]==[1]
    wire=[case['result']['forward_ipv4_udp_bytes'] for case in (left,right)]
    assert wire==[3542023,2317634]
    missing=[]
    for raw,expected in m['input_sha256'].items():
        p=Path(raw)
        if p.is_file():assert sha(p)==expected,('external media',raw)
        else:missing.append(raw)
    peer=args.sunshine_root/m['sunshine_readme']['path']
    peer_checked=peer.is_file()
    if peer_checked:assert sha(peer)==m['sunshine_readme']['sha256'],'paired Sunshine README'
    print(json.dumps(dict(snapshot_files=len(m['file_sha256']),executed_source_bindings=bindings,
        recorded_passing_tests=count,read_only_helpers=helpers,matched_delivery_analysis='passed',
        steady_window_distinct_decoded_images=150,steady_window_seconds=5,modeled_ids_per_second=30,
        matched_eventual_ids=179,forward_wire_saving_percent=100*(1-wire[1]/wire[0]),
        missing_external_media=missing,paired_sunshine_readme_checked=peer_checked,
        primary_target='720x480coded,720x405active,30distinctdisplayedfps',physical_30fps_proven=False),indent=2))


if __name__=='__main__':main()
