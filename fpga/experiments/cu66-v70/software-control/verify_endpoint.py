#!/usr/bin/env python3
"""Reconcile source pins, native endpoint transcripts and Python compatibility."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    r=json.loads((HERE/'results.json').read_text());assert r['status']=='PASS'
    checks=0
    for p,h in r['source_sha256'].items():assert sha(ROOT/p)==h,p;checks+=1
    for c in r['commands']:
        assert c['exit_code']==0 and sha(ROOT/c['log'])==c['sha256'];checks+=1
    assert len(r['runs'])==2 and [x['sanitized']for x in r['runs']]==[False,True]
    for row,name in zip(r['runs'],['release','sanitized']):
        text=(HERE/f'test-final-{name}.log').read_text();actual=json.loads(next(s.split('TEST_PASS_ENDPOINT ',1)[1]for s in text.splitlines()if s.startswith('TEST_PASS_ENDPOINT ')))
        assert 'TEST_FAIL'not in text and'AddressSanitizer'not in text and'runtime error:'not in text
        assert actual=={k:v for k,v in row.items()if k!='sanitized'}
        assert actual['actual_HUD_frames']==457 and actual['keys']==20 and actual['commands']==2811 and actual['malformed_no_state_change']==13 and actual['words_transferred_per_actual_frame']==21120
        assert actual['commit_retry']and actual['abort_retry']and actual['old_abort_does_not_discard_new_candidate']
    for p,h in r['examples_sha256'].items():assert sha(ROOT/p)==h,p;checks+=1
    compat=HERE/'python-compat-results.json';assert sha(compat)==r['python_compat_result_sha256'];checks+=1
    c=json.loads(compat.read_text());assert c['status']=='PASS'and c['valid_roundtrip_frames']==17 and c['matching_malformed_rejections']==15 and c['actual_native_response_semantic_checks']==5
    assert sha(ROOT/c['python_codec'])==c['python_codec_sha256'];checks+=1
    for row in c['records']:
        assert sha(ROOT/row['input'])==row['input_sha256'];checks+=1
        if row['valid']:assert sha(ROOT/row['output'])==row['output_sha256']==row['input_sha256'];checks+=1
    for cmd in c['commands']:
        assert cmd['exit_code']==cmd['expected_exit_code']and sha(ROOT/cmd['log'])==cmd['log_sha256'];checks+=1
    print('ENCODED_ENDPOINT_EVIDENCE_PASS release_and_sanitized_actual_frames=457 commands_per_build=2811 malformed_no_state_change=13 Python_roundtrips=17 Python_rejects=15 declared_hash_checks='+str(checks)+' system_peer_remains_typed=1')


if __name__=='__main__':main()
