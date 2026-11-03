#!/usr/bin/env python3
"""Validate the v7 evidence snapshot without rerunning heavy benchmarks."""
import hashlib
import json
import math
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(path):
    marker='/moonbub-30fps-study/'
    if marker in path:return ROOT/path.split(marker,1)[1]
    p=Path(path)
    return p if p.is_absolute() else ROOT/p


def load(path):return json.loads((ROOT/path).read_text())


def main():
    snapshot=load('docs/prototype-v7-provenance.json')
    for path,expected in snapshot['file_sha256'].items():
        assert sha(ROOT/path)==expected,('snapshot',path)
    bindings=0
    for rel in snapshot['run_artifacts']:
        doc=load(rel)
        for path,expected in doc['source_sha256'].items():
            assert sha(resolve(path))==expected,('executed source',rel,path)
            bindings+=1
    total=0
    for rel,count in snapshot['test_counts'].items():
        log=(ROOT/rel/'tests.log').read_text();m=re.search(r'^Ran (\d+) tests? in ',log,re.M)
        assert m and int(m[1])==count and log.rstrip().endswith('OK'),('tests',rel)
        total+=count
    word=load('experiments/python-word-decode-study/results.json')
    assert word['paired_packets']==72 and word['paired_planes']==216
    scheduler=load('experiments/python-word-decode-study/scheduler-results.json')
    preps=commits=0
    assert len(scheduler['cases'])==4
    for case in scheduler['cases']:
        r=case['result'];end=r['capture_count']*1000/r['config']['fps']
        assert all(x is None for x in r['unresolved_slots']) and not r['unresolved_pending'] and not r['pending_ids']
        assert r['waiting_at_end'] is None and r['peak_compressed_slots']<=2 and r['peak_pending_credits']<=2
        presented=r['presented'];ids=[x['id'] for x in presented];drops=[x['id'] for x in r['drops']]
        assert ids==sorted(set(ids)) and len(drops)==len(set(drops))
        assert not set(ids)&set(drops) and set(ids)|set(drops)==set(range(r['capture_count']))
        assert r['presented_strict']==sum(x['at_ms']<end-1e-9 for x in presented)
        steady=sum(500<=x['at_ms']<end-500 for x in presented)
        assert r['metrics']['steady_fps']==steady*1000/(end-1000)
        preps+=len(r['packets']);commits+=len(r['commits'])
    roi=load('experiments/python-game-roi-study/results.json')
    summary=load('experiments/python-game-roi-study/summary.json')
    assert summary['result_sha256']==sha(ROOT/'experiments/python-game-roi-study/results.json')
    assert roi['scene_count']==len(roi['scenes'])==18 and summary['actual_encode_decode_calls']==252
    assert summary['selected_profile_records']==126
    selected_over=0
    for scene in roi['scenes']:
        assert scene['input_sha256']==scene['manifest']['frame_sha256'][scene['source_index']]
        profiles=scene['profiles'];policy=scene['budget_policy']
        assert profiles['budget_roi8mix']['bytes']<=profiles['uniform16']['bytes']
        assert policy['attempts']==len(policy['candidates'])<=10
        assert abs(policy['total_reference_and_search_encode_ms']-policy['reference_uniform16_encode_ms']-sum(r['encode_wall_ms'] for r in policy['candidates']))<1e-9
        selected_over+=profiles['budget_roi8mix']['bytes']>49152
        for row in profiles.values():
            info=row['info'];metrics=row['metrics']
            assert row['bytes']==info['bytes'] and info['scale_map_bytes']==338 and info['outer_header_crc_bytes']==34
            a,b=metrics['roi'],metrics['background'];whole=metrics['active']
            assert a['pixels']+b['pixels']==whole['pixels']
            assert abs((a['mse']*a['pixels']+b['mse']*b['pixels'])/whole['pixels']-whole['mse'])<1e-8
    assert selected_over==2
    dirty=load('experiments/python-dirty-tile-study/results.json')
    dirty_records=0
    for scene in dirty['scenes']:
        rows=scene['records'];dirty_records+=len(rows)
        for i,row in enumerate(rows):
            assert row['input_sha256']==scene['manifest']['frame_sha256'][i]
            assert row['dirty']['map_bytes']==44 and row['dirty']['tiles']==345
            for packet in row['packets'].values():
                assert packet['wire_bytes']==packet['bytes']+68*math.ceil(packet['bytes']/1024)
                assert packet['over_48k_cap']==(packet['bytes']>49152)
        for label,s in scene['summary'].items():
            packets=[r['packets'][label] for r in rows]
            assert s['over_48k_cap']==sum(p['over_48k_cap'] for p in packets)
            assert abs(s['packet_mean_bytes']-sum(p['bytes'] for p in packets)/len(packets))<1e-9
    assert dirty_records==48
    missing=[]
    for path,expected in snapshot['input_sha256'].items():
        p=Path(path)
        if p.exists():assert sha(p)==expected,('input',path)
        else:missing.append(path)
    print(json.dumps({'snapshot_files':len(snapshot['file_sha256']),'executed_source_bindings':bindings,
                      'passing_tests':total,'paired_decode_packets':72,'paired_coefficient_planes':216,
                      'service_cases':4,'actual_preparations':preps,'hash_checked_commits':commits,
                      'roi_source_inputs':18,'roi_encode_decode_candidates':252,'roi_selected_records':126,
                      'roi_reference_size_fits':18,'roi_selected_48k_failures':selected_over,
                      'dirty_frames':dirty_records,'missing_external_inputs':missing,
                      'scope':'Checks stored software evidence; no physical/real-time proof'},indent=2))


if __name__=='__main__':main()
