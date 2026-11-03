#!/usr/bin/env python3
"""Reconcile frozen v11 software/provenance evidence; no timed codec rerun."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text())

def resolve(path):
    marker='/moonbub-30fps-study/'
    return ROOT/path.split(marker,1)[1] if marker in path else Path(path)


def main():
    snapshot=load('docs/prototype-v11-provenance.json')
    for rel,expected in snapshot['file_sha256'].items():assert sha(ROOT/rel)==expected,('inventory',rel)
    bindings=0
    for rel in snapshot['run_artifacts']:
        d=load(rel)
        for path,expected in d.get('source_sha256',{}).items():
            assert sha(resolve(path))==expected,('executed source',rel,path);bindings+=1
    tests=0
    for rel,count in snapshot['test_counts'].items():
        text=(ROOT/rel/'tests.log').read_text();match=re.search(r'^Ran (\d+) tests? in ',text,re.M)
        assert match and int(match[1])==count and text.rstrip().endswith('OK'),rel
        tests+=count
    helpers={}
    for folder,script in (('python-game-hybrid-study','verify.py'),('python-game-block-study','check_stored_results.py'),
                          ('python-game-hybrid-link-study','verify.py'),('python-game-decoder-architecture-study','verify.py')):
        subprocess.run([sys.executable,str(ROOT/'experiments'/folder/script)],check=True,capture_output=True,text=True)
        helpers[folder]='passed'
    audit=load('experiments/python-game-audit-v11-study/audit.json')
    assert not audit['inputs_missing'] and not audit['evidence_gaps']
    assert audit['source_pins_match_before_and_after'] and audit['media_hashes_match_before_and_after']
    for row in audit['source_pins_before']['rows']:
        assert row['matches'] and sha(resolve(row['path']))==row['expected'],row['path']
    assert len(audit['source_pins_before']['rows'])==34
    h=load('experiments/python-game-hybrid-study/results.json')
    assert h['source_inputs']==140 and h['selector_decisions']==560
    b=load('experiments/python-game-block-study/results.json')
    assert b['packet_count']==sum(len(s['records']) for s in b['scenes'])==612
    link=load('experiments/python-game-hybrid-link-study/results.json')
    assert len(link['cases'])==12
    assert sum(c['result']['capture_count'] for c in link['cases'])==720
    assert sum(c['result']['prepared'] for c in link['cases'])==670
    assert sum(len(c['result']['commits']) for c in link['cases'])==669
    prepared={f:sum(p.get('format')==f for c in link['cases'] for p in c['result']['packets']) for f in ('GM01','HG01')}
    decoded={f:sum(p['format']==f for c in link['cases'] for p in c['result']['commits']) for f in ('GM01','HG01')}
    assert prepared=={'GM01':231,'HG01':439} and decoded=={'GM01':231,'HG01':438}
    a=audit['independent_rederivations']['hybrid_link']
    assert a['outer_inner_feedback_binding_proven'] and a['runs_with_unresolved_work_at_end']==0
    assert not a['hardware_30fps_proven'] and not a['new_custom_formats_are_standard_conformant']
    reduced=[]
    for c in link['cases']:
        if c['kind']=='baseline' and c['coded_width']==512:
            r=c['result'];reduced.append({'source':c['source'],'target':c['target_ids_per_second'],'mode':c['mode'],
                'strict':r['presented_strict'],'eventual':r['presented_eventual'],'diagnostic_ids_per_second':r['metrics']['steady_fps']})
    probe=load('experiments/python-game-hybrid-link-study/refresh-results.json')
    assert len(probe['cases'])==2
    assert sum(c['result']['prepared'] for c in probe['cases'])==119
    assert sum(len(c['result']['commits']) for c in probe['cases'])==119
    assert [c['result']['metrics']['steady_fps'] for c in probe['cases']]==[30,30]
    assert [c['result']['presented_strict'] for c in probe['cases']]==[58,59]
    assert [c['result']['presented_eventual'] for c in probe['cases']]==[59,60]
    manifest=load('experiments/python-game-decoder-architecture-study/sources.json')
    for row in manifest['local_inputs']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    missing=[]
    for path,expected in snapshot['input_sha256'].items():
        if Path(path).exists():assert sha(Path(path))==expected,('external media',path)
        else:missing.append(path)
    print(json.dumps({'snapshot_files':len(snapshot['file_sha256']),'executed_source_bindings':bindings,
        'passing_tests':tests,'stored_helpers':helpers,'independent_unique_source_pins':34,
        'hybrid_policy_decisions':560,'bm_and_gm_algorithm_decodes':612,'main_link_case_count':12,
        'main_capture_policy_events':720,'prepared_formats':prepared,'decoded_formats':decoded,
        'reduced_canvas_operating_points':reduced,'separate_refresh_probe_decodes':119,
        'separate_refresh_probe_diagnostic_ids_per_second':[30,30],
        'pinned_openav1_commit':manifest['openav1_pinned_readme']['commit'],
        'missing_external_inputs':missing,
        'scope':'Software evidence and parameterized architecture only; no target hardware, live capture or sustained30fps proof'},indent=2))


if __name__=='__main__':main()
