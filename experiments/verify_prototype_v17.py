#!/usr/bin/env python3
"""Read-only v17 codec/transport/memory evidence checks, not hardware proof."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parent.parent

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def load(p):return json.loads((ROOT/p).read_text())
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
    m=load('docs/prototype-v17-provenance.json')
    for path,h in m['file_sha256'].items():assert sha(ROOT/path)==h,('inventory',path)
    count=0
    for path in m['run_artifacts']:
        for raw,h in load(path)['source_sha256'].items():assert sha(resolve(raw))==h,('snapshot',path,raw);count+=1
    for path,h in m['frozen_v16_source_sha256'].items():assert sha(ROOT/path)==h,('frozen v16',path)
    tests=0
    for folder,n in m['test_counts'].items():
        text=(ROOT/folder/'tests.log').read_text();match=re.search(r'^Ran (\d+) tests? in ',text,re.M)
        assert match and int(match[1])==n and text.rstrip().endswith('OK'),folder;tests+=n
    helpers={folder:run(folder+'/verify.py') for folder in m['stored_helpers']}
    analyses={folder:run(folder+'/analyze.py','--check') for folder in m['analysis_helpers']}
    audit=load('experiments/python-game-audit-v17-study/audit.json')
    assert audit['status']=='verified' and len(audit['results'])==3
    assert all(x['status']=='verified' for x in audit['results'].values())
    assert audit['final_signal_received']
    for x in audit['results'].values():
        assert x['analysis']['status']=='verified' and not x['errors']
        assert all(pin['matches'] for pin in x['source_pins'])
        assert x['test_log']['status']=='pass'
    code="import json,sys;sys.path.insert(0,sys.argv[1]);import audit;print(json.dumps(audit.load_audit()))"
    result=subprocess.run([sys.executable,'-c',code,str(ROOT/'experiments/python-game-audit-v17-study')],check=True,capture_output=True,text=True)
    current=json.loads(result.stdout);assert current['status']=='verified' and current['final_signal_received']
    assert all(x['analysis']['status']=='verified' and not x['errors'] for x in current['results'].values())
    local=load('experiments/python-game-local-refresh-study/cadence-analysis.json');profiles={r['profile']:r for r in local['profiles']}
    assert profiles['local_refresh30']['eventual']==profiles['local_refresh30_repeat']['eventual']==178
    assert profiles['local_refresh30']['startup_or_other_dropped_ids']==[1,2]
    assert profiles['local_refresh30']['distinct_input_and_decoded_window_ids']==151
    assert profiles['global_refresh30']['eventual']==161
    peer=args.sunshine_root/m['sunshine_readme']['path'];peer_checked=peer.is_file()
    if peer_checked:assert sha(peer)==m['sunshine_readme']['sha256'],'paired Sunshine README'
    missing=[]
    for raw,h in m['input_sha256'].items():
        p=Path(raw)
        if p.is_file():assert sha(p)==h,('external media',raw)
        else:missing.append(raw)
    print(json.dumps(dict(snapshot_files=len(m['file_sha256']),source_snapshot_bindings=count,recorded_passing_tests=tests,
        frozen_v16_files=len(m['frozen_v16_source_sha256']),retained_helpers=helpers,untimed_analyses=analyses,
        fresh_independent_audit='verified',local_refresh_eventual_out_of_180=178,global_refresh_eventual=161,
        local_rolling_window_unique_ids=151,rolling_window_seconds=5,input_schedule_fps=30,
        rolling_count_is_sustained_fps_proof=False,transport_is_sizes_only=True,memory_ids_are_repeated_templates=True,
        joint_native_or_physical_30fps_proven=False,missing_external_media=missing,paired_sunshine_readme_checked=peer_checked),indent=2))
if __name__=='__main__':main()
