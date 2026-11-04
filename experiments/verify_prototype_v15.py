#!/usr/bin/env python3
"""Read-only verification of the v15 artifact snapshot and finite claims."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def load(p):
    return json.loads((ROOT/p).read_text())

def resolve(raw):
    marker = '/moonbub-30fps-study/'
    return ROOT/raw.split(marker,1)[1] if marker in raw else Path(raw)

def run(path,*args):
    result = subprocess.run([sys.executable,str(ROOT/path),*args],check=True,capture_output=True,text=True)
    return result.stdout.strip()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sunshine-root',type=Path,default=ROOT.parent/'sunshine-30fps-study')
    args=parser.parse_args()
    m=load('docs/prototype-v15-provenance.json')
    for path, expected in m['file_sha256'].items():
        assert sha(ROOT/path)==expected,('snapshot',path)
    bindings=0
    for path in m['run_artifacts']:
        data=load(path)
        for raw, expected in data['source_sha256'].items():
            assert sha(resolve(raw))==expected,('executed source',path,raw)
            bindings+=1
    assert bindings==94
    total_tests=0
    for folder, expected in m['test_counts'].items():
        log=(ROOT/folder/'tests.log').read_text()
        count=re.search(r'^Ran (\d+) tests? in ',log,re.M)
        assert count and int(count[1])==expected and log.rstrip().endswith('OK'),folder
        total_tests+=expected
    assert total_tests==49
    helpers={folder:run(folder+'/verify.py') for folder in m['stored_helpers']}
    analyses={folder:run(folder+'/analyze.py','--check') for folder in m['analysis_helpers']}
    audit=load('experiments/python-game-audit-v15-study/audit.json')
    assert audit['status']=='verified'
    assert len(audit['inputs'])==len(audit['results'])==4
    assert all(v['status']=='verified' for v in audit['inputs'].values())
    assert all(v['status']=='verified' for v in audit['results'].values())
    assert all(v=='verified' for v in audit['checks'].values())
    # Recompute finite cadence and exact UI assertions rather than trusting prose.
    stream=load('experiments/python-game-unified-stream-study/results.json')
    assert stream['case_count']==14 and sum(c['result']['capture_count'] for c in stream['cases'])==1248
    long={c['profile']:c for c in stream['cases'] if c['source']=='mass-effect-2600-heldout180'}
    gm=long['gm_ui']; r=gm['result']; decoded={c['id']:c for c in r['commits']}
    ids=[p['id'] for p in r['presented'] if 500<=p['at_ms']<5500]
    assert ids==list(range(12,162))
    assert len({decoded[i]['rgb_sha256'] for i in ids})==150
    assert len({gm['manifest']['frame_sha256'][i] for i in ids})==150
    assert (r['presented_strict'],r['presented_eventual'])==(175,178)
    assert [p['id'] for p in r['drops']]==[1,2]
    assert all(c['selected_exact_pixels']==21120 and c['selected_ui_mismatches']==0 for c in decoded.values())
    gate=load('experiments/python-game-cadence-gate-study/gate-analysis.json')
    assert sum(c['gate_evaluated'] for c in gate['rows'])==174
    assert sum(c['eligible'] for c in gate['rows'])==0
    assert sum(c['matched_control_saved_inner_bytes'] for c in gate['rows'])==19400
    missing=[]
    for raw, expected in m['input_sha256'].items():
        path=Path(raw)
        if path.is_file():
            assert sha(path)==expected,('external media',raw)
        else:
            missing.append(raw)
    # Fresh audit requires media; retained hash-bound audit remains available elsewhere.
    fresh_audit=False
    if not missing:
        current=json.loads(run('experiments/python-game-audit-v15-study/audit.py'))
        assert current['status']=='verified' and all(v=='verified' for v in current['checks'].values())
        fresh_audit=True
    peer=args.sunshine_root/m['sunshine_readme']['path']
    peer_checked=peer.is_file()
    if peer_checked:
        assert sha(peer)==m['sunshine_readme']['sha256'],'paired Sunshine README'
    print(json.dumps(dict(snapshot_files=len(m['file_sha256']),executed_source_bindings=bindings,
        recorded_passing_tests=total_tests,retained_helpers=helpers,matched_analyses=analyses,
        independent_audit='verified',fresh_independent_audit=fresh_audit,
        gm_plus_four_ui_modeled_ids_per_second=30,steady_window_seconds=5,
        distinct_input_and_decoded_images=150,strict_presentations=175,eventual_presentations=178,
        configured_exact_ui_words_per_frame=21120,fixed_gate_recommendation='negative experiment; prefer GM+UI here',
        missing_external_media=missing,paired_sunshine_readme_checked=peer_checked,
        physical_30fps_proven=False),indent=2))

if __name__=='__main__':
    main()
