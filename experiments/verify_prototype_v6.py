#!/usr/bin/env python3
"""Check the iteration6 snapshot, run bindings, finite accounting and test logs."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recorded_path(path):
    marker='/moonbub-30fps-study/'
    if marker in path:
        return ROOT/path.split(marker,1)[1]
    p=Path(path)
    return p if p.is_absolute() else ROOT/p


def main():
    snapshot=json.loads((ROOT/'docs/prototype-v6-provenance.json').read_text())
    for path,expected in snapshot['file_sha256'].items():
        assert sha(ROOT/path)==expected,('snapshot',path)
    bindings=0
    for rel in snapshot['run_artifacts']:
        result=json.loads((ROOT/rel).read_text())
        for path,expected in result['source_sha256'].items():
            assert sha(recorded_path(path))==expected,('executed source',rel,path)
            bindings+=1
    total_tests=0
    for rel,count in snapshot['test_counts'].items():
        log=(ROOT/rel/'tests.log').read_text()
        m=re.search(r'^Ran (\d+) tests? in ',log,re.M)
        assert m and int(m[1])==count and log.rstrip().endswith('OK'),('tests',rel)
        total_tests+=count
    cases=preparations=commits=0
    for rel in snapshot['service_artifacts']:
        result=json.loads((ROOT/rel).read_text())
        for case in result['cases']:
            r=case['result'];end=r['capture_count']*1000/r['config']['fps']
            assert all(x is None for x in r['unresolved_slots'])
            assert not r['unresolved_pending'] and not r['pending_ids'] and r['waiting_at_end'] is None
            assert r['peak_compressed_slots']<=2 and r['peak_pending_credits']<=2 and r['peak_framebuffers']<=3
            assert r['peak_retained_packet_bytes']<=2*49152
            presented=r['presented'];ids=[x['id'] for x in presented];dropped=[x['id'] for x in r['drops']]
            assert ids==sorted(set(ids)) and len(dropped)==len(set(dropped))
            assert not set(ids)&set(dropped) and set(ids)|set(dropped)==set(range(r['capture_count']))
            assert r['presented_eventual']==len(presented)
            assert r['presented_strict']==sum(x['at_ms']<end-1e-9 for x in presented)
            steady=sum(500<=x['at_ms']<end-500 for x in presented)
            assert r['steady_count']==steady and r['metrics']['steady_fps']==steady*1000/(end-1000)
            rows={x['id']:x for x in r['packets']}
            for row in rows.values():
                assert row['encode_service_ms']==row['encode_wall_ms']>=0
            for row in r['commits']:
                p=rows[row['id']]
                assert abs(row['at_ms']-p['decode_started_ms']-p['decode_service_ms'])<1e-9
                expected=p['decode_wall_ms'] if r['config']['decoder_service']=='python_wall' else r['config']['decode_ms']
                assert p['decode_service_ms']==expected
            cases+=1;preparations+=len(rows);commits+=len(r['commits'])
    key=json.loads((ROOT/'experiments/python-key-prepare-study/results.json').read_text())
    assert sum(x['paired_triples'] for x in key['scenes']+key['independent_key_cases'])==96
    token=json.loads((ROOT/'experiments/python-token-entropy-study/results.json').read_text())
    assert token['byte_checked_key_pairs']==24 and token['byte_checked_plane_pairs']==72
    values=[row['prepare_ms']['token'] for case in token['cases'] for row in case['records']]
    assert sum(x>1000/30 for x in values)==token['summary']['whole_key_over_33_333_ms']['token']==2
    arithmetic=json.loads((ROOT/'experiments/python-arithmetic-study/results.json').read_text())
    assert sum(x['paired_checks'] for x in arithmetic['scenes'])==48
    assert arithmetic['domain_bounds']['inverse_int32_max_abs']==18779
    audit=json.loads((ROOT/'experiments/python-evidence-v6-study/audit.json').read_text())
    assert len(audit['result_files'])==7 and audit['source_inputs_unchanged_during_audit']
    for result in audit['result_files'].values():
        assert result['all_declared_source_pins_stable']
        for phase in ('source_pin_audit','source_pin_audit_after'):
            assert not result[phase]['missing'] and not result[phase]['mismatched']
    missing=[]
    for path,expected in snapshot['input_sha256'].items():
        if Path(path).exists():
            assert sha(Path(path))==expected,('input',path)
        else:
            missing.append(path)
    print(json.dumps({'snapshot_files':len(snapshot['file_sha256']),'executed_source_bindings':bindings,
                      'passing_tests':total_tests,'actual_service_cases':cases,
                      'actual_preparations':preparations,'hash_checked_commits':commits,
                      'key_triples':96,'token_key_pairs':24,'token_plane_pairs':72,
                      'arithmetic_stage_pairs':48,'missing_external_inputs':missing,
                      'scope':'Recorded software evidence checks, not another codec run or hardware qualification'},indent=2))


if __name__=='__main__':
    main()
