#!/usr/bin/env python3
"""Record and verify the reversible V125-to-V126 focused-runner derivation."""
import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
ORIGINAL=ROOT/'scripts/cu66-v125/tile/qualify.py'
CANDIDATE=ROOT/'scripts/cu66-v126/producer/qualify.py'
ORIGINAL_SHA='39814e729ad63b93014f60c8682121cf197194434f3c18e9e4279042f46b42cd'
OWNER=ROOT/'scripts/cu66-v124/owner/qualify.py'
OWNER_SHA='d822922c0d978c6d537996eca40c3920240c528b43a8ab6c23664479a8a62af8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive():
    records=[]
    for name,digest in [('qualify.py',ORIGINAL_SHA)]:
        old=ORIGINAL;new=CANDIDATE
        assert sha(old)==digest
        original=old.read_text();candidate=new.read_text()
        before_lines=original.splitlines(keepends=True);after_lines=candidate.splitlines(keepends=True)
        for context in (3,5,8,16,32,64,128,1024):
            edits=[];text=original
            for group in difflib.SequenceMatcher(a=before_lines,b=after_lines,autojunk=False).get_grouped_opcodes(context):
                before=''.join(before_lines[group[0][1]:group[-1][2]])
                after=''.join(after_lines[group[0][3]:group[-1][4]])
                if not before or not after or text.count(before)!=1:break
                edits.append(dict(before=before,after=after,count=1));text=text.replace(before,after,1)
            else:
                if text!=candidate:continue
                for edit in reversed(edits):
                    if text.count(edit['after'])!=1:break
                    text=text.replace(edit['after'],edit['before'],1)
                else:
                    if text==original:break
            continue
        else:raise AssertionError('Could not produce unique reversible auditor edits: '+name)
        check_counts={}
        records.append(dict(original=str(old.relative_to(ROOT)),original_sha256=digest,
                            candidate=str(new.relative_to(ROOT)),candidate_sha256=sha(new),
                            edits=edits,context_lines=context,integrity_check_call_counts=check_counts))
    assert sha(OWNER)==OWNER_SHA
    return dict(schema='v126-focused-runner-derivation-v1',sources=records,caller_runner_provenance=dict(path=str(OWNER.relative_to(ROOT)),sha256=OWNER_SHA),old_Cpp_require_checks_removed=0,all_inherited_replay_oracles_retained=True,raw_counter_contract='Retained V124 old generic counters unchanged; new actual writer/cancel/primer clocks are recorded separately, never natural packet cycles.')
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    recipe=derive();path=HERE/'focused-runner-derivation.json'
    if args.write:path.write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
    else:assert json.loads(path.read_text())==recipe
    print('V126_FOCUSED_RUNNER_DERIVATION_PREPARED_NOT_RUN',[(Path(r['candidate']).name,len(r['edits'])) for r in recipe['sources']])
if __name__=='__main__':main()
