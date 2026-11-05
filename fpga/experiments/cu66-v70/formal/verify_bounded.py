#!/usr/bin/env python3
"""Check source/transcript/witness binding and precise bounded verdicts."""
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    r=json.loads((HERE/'results.json').read_text())
    assert r['status']=='PASS_BOUNDED'and len(r['runs'])==len(r['commands'])==8
    assert r['backend']==(HERE/'tool-version.log').read_text().strip()
    for p,h in r['source_sha256'].items():assert sha(ROOT/p)==h,p
    assert r['resource_limits']=={'total_runner_seconds':115,'per_process_wall_seconds_max':28,'per_process_address_space_bytes':1610612736}
    assert r['elapsed_seconds']<120
    proof=[];covers=[]
    for job,cmd in zip(r['runs'],r['commands']):
        assert cmd['exit_code']==0
        assert sha(ROOT/cmd['script'])==cmd['script_sha256']
        assert sha(ROOT/cmd['log'])==cmd['log_sha256']
        script=(ROOT/cmd['script']).read_text();log=(ROOT/cmd['log']).read_text()
        assert '-set rst 0 -set-at 1 rst 1'in script
        assert '-set-def-inputs -set-init-def'in script
        assert '-ignore_unknown_cells'not in script and'chformal'not in script
        assert re.search(r'^\s+\$assert\s+16\s*$',log,re.M)
        assert 'ERROR:'not in log and job['assertions_elaborated']==16
        if job['kind']=='proof':
            assert '-prove-asserts -verify'in script
            assert 'SAT proof finished - no model found: SUCCESS!'in log
            assert job['status']=='PASS_BOUNDED';proof.append(job['solver_steps'])
        else:
            assert f'-set-at 16 {job["cover_signal"]} 1'in script
            assert 'SAT solving finished - model found:'in log
            assert sha(ROOT/job['witness'])==job['witness_sha256']
            assert job['status']=='REACHABLE'and job['solver_steps']==16
            covers.append(job['cover_signal'])
    assert proof==[8,16,24]
    assert covers==['cover_active','cover_read','cover_pending','cover_front','cover_abort_and_present']
    print('BOUNDED_FORMAL_EVIDENCE_PASS bounds=8,16,24 assertions=16 reachable_witnesses=5 source_and_transcript_hashes_match=1 no_unbounded_claim=1')


if __name__=='__main__':main()
