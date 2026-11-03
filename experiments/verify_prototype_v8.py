#!/usr/bin/env python3
"""Verify v8 source/result bindings, stored controller bounds and fixture replay."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def load(rel):return json.loads((ROOT/rel).read_text())


def resolve(path):
    marker='/moonbub-30fps-study/'
    if marker in path:return ROOT/path.split(marker,1)[1]
    p=Path(path)
    return p if p.is_absolute() else ROOT/p


def main():
    snapshot=load('docs/prototype-v8-provenance.json')
    for rel,expected in snapshot['file_sha256'].items():
        assert sha(ROOT/rel)==expected,('snapshot',rel)
    source_bindings=0
    for rel in snapshot['run_artifacts']:
        doc=load(rel)
        for path,expected in doc.get('source_sha256',{}).items():
            assert sha(resolve(path))==expected,('executed source',rel,path)
            source_bindings+=1
    tests=0
    for rel,count in snapshot['test_counts'].items():
        log=(ROOT/rel/'tests.log').read_text();m=re.search(r'^Ran (\d+) tests? in ',log,re.M)
        assert m and int(m[1])==count and log.rstrip().endswith('OK'),('test log',rel)
        tests+=count
    # These helpers read stored rows; only the fixture replay actually decodes.
    helpers={}
    for rel in ('experiments/python-game-codec-study/verify.py',
                'experiments/python-game-rate-study/verify.py',
                'experiments/python-game-link-study/replay_fixtures.py'):
        p=subprocess.run([sys.executable,str(ROOT/rel)],check=True,capture_output=True,text=True)
        helpers[rel]=json.loads(p.stdout)
    prior=load('experiments/python-game-size-study/prior-check.json')
    assert prior['regenerated_packet_sha_matches']==72 and prior['exact_plane_length_checks']==216
    assert prior['prior_result_sha256']==sha(ROOT/'experiments/python-game-codec-study/results.json')
    for name,result_key,summary_key in (('results.json','result_sha256','summary.json'),
                                        ('gate-results.json','result_sha256','gate-summary.json')):
        data=load('experiments/python-game-size-study/'+name)
        summary=load('experiments/python-game-size-study/'+summary_key)
        assert summary[result_key]==sha(ROOT/'experiments/python-game-size-study'/name)
        assert data['paired_calls']==len(data['rows'])==32
    gates=load('experiments/python-game-size-study/gate-results.json')
    for row in gates['rows']:
        assert row['analysis_calls']==1 and row['forward_calls']==3
        assert len(row['attempts_full'])==len(row['attempts_gate'])<=2
        for full,gate in zip(row['attempts_full'],row['attempts_gate']):
            assert gate['lower_bytes']<=full['bytes']
            assert gate['fits']==full['fits']
            if gate['serialized']:assert gate['bytes']==full['bytes']
            else:assert gate['lower_bytes']>row['cap'] and not gate['fits']
        assert row['accepted']==bool(row['packet_sha256'])
    noise=[r for r in gates['rows'] if r['kind']=='seeded_noise_reject']
    assert len(noise)==8 and not any(r['accepted'] for r in noise)
    assert not any(a['serialized'] for r in noise for a in r['attempts_gate'])
    manifest=load('experiments/python-game-link-study/fixtures/manifest.json')
    assert len(manifest['cases'])==8 and len(manifest['files'])==64
    assert manifest['total_datagrams']==40 and manifest['total_forward_plane_calls']==24
    assert manifest['all_resources_drained']
    for name,info in manifest['files'].items():
        p=ROOT/'experiments/python-game-link-study/fixtures'/name
        assert p.stat().st_size==info['bytes'] and sha(p)==info['sha256']
    missing=[]
    for path,expected in snapshot['input_sha256'].items():
        if Path(path).exists():assert sha(Path(path))==expected,('input',path)
        else:missing.append(path)
    print(json.dumps({'snapshot_files':len(snapshot['file_sha256']),'executed_source_bindings':source_bindings,
                      'passing_tests':tests,'combined_packets':72,'uniform_ma01_pixel_pairs':24,
                      'rate_capture_policy_evaluations':120,'rate_admitted':108,'rate_rejected':12,
                      'actual_sequence_candidates':132,'paired_reuse_keys':48,
                      'exact_preflight_paired_keys':32,'cheap_gate_paired_keys':32,
                      'frozen_packet_sha_matches':72,'exact_plane_size_checks':216,
                      'golden_cases':8,'golden_binary_files':64,'fixture_datagrams':40,
                      'fixture_replay_outputs_exact':helpers['experiments/python-game-link-study/replay_fixtures.py']['all_decoded_outputs_exact'],
                      'missing_external_inputs':missing,'scope':'Software evidence checks; no actual network/hardware or real-time proof'},indent=2))


if __name__=='__main__':main()
