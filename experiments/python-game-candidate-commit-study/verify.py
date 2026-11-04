#!/usr/bin/env python3
"""Read-only retained candidate/commit evidence reconciliation."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def main():
    d=json.loads((HERE/'results.json').read_text())
    for p,h in d['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    assert len(d['rows'])==d['native_decisions']==48
    commits=[x for x in d['rows'] if x['action']=='commit'];drops=[x for x in d['rows'] if x['action']=='discard']
    assert len(commits)==d['native_commits']==42 and len(drops)==d['native_discards']==6
    assert d['native_selected_exact_words']==42*21120
    for x in d['rows']:
        assert x['state_before']==x['state_after_build'] and x['build_ms']>0
        assert (x['analyze_calls'],x['forward_calls'])==(1,3) and x['readers_after']==0
        assert x['source_pin_during_build']==(0 if x['key'] else 1)
        if x['action']=='commit':
            assert x['byte_identical_frozen'] and x['decoded_sha256']==x['frozen_decoded_sha256']
            assert x['selected_words']==21120 and x['selected_word_errors']==0 and x['commit_ms']>0
            assert x['state_after']['last_issued']==x['id']
        else:assert x['state_before']==x['state_after'] and x['discard_ms']>0
    assert len(d['cap_rejections'])==4
    for x in d['cap_rejections']:
        assert x['complete_attempted_bytes']>x['cap']==128 and x['build_ms']>0 and x['discard_ms']>0
        assert x['state_before']==x['state_after'] and x['readers_after']==0
    for mode in ('gm','exact'):
        for policy in ('all_commit','reject0_3_5'):
            rows=[x for x in d['rows'] if x['mode']==mode and x['policy']==policy]
            assert [x['id'] for x in rows]==list(range(12))
            assert len({x['input_sha256'] for x in rows})==12
    print('PASS:48nativecandidates42exact-wire/pixelcommits6paidtransportdiscards4paidcaprejects;unchangedidentity/banksandreleasedsourcepins;noFPS/hardwareclaim')
if __name__=='__main__':main()
