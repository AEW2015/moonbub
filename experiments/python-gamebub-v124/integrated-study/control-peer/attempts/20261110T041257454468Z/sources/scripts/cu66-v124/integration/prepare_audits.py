#!/usr/bin/env python3
"""Record and verify reversible V123-to-V124 independent-auditor derivations."""
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
PINS={'audit_functional.py':'d19d7f6c397eef627445d74a6dd12f83980feaccb7bcb998af20d0d0588bbf2b',
      'audit_terminal.py':'4b982fa53df60102d6685cfec78079e47f588742399e1fed8ebc070f5c1d3303'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive():
    records=[]
    for name,digest in PINS.items():
        old=ROOT/'scripts/cu66-v123'/name;new=ROOT/'scripts/cu66-v124'/name
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
        for label,pattern in [('need',r'\bneed\('),('audit_check',r'\baudit\.check\(')]:
            a=len(re.findall(pattern,original));b=len(re.findall(pattern,candidate));assert b>=a,(name,label,a,b)
            check_counts[label]=dict(original=a,candidate=b)
        records.append(dict(original=str(old.relative_to(ROOT)),original_sha256=digest,
                            candidate=str(new.relative_to(ROOT)),candidate_sha256=sha(new),
                            edits=edits,context_lines=context,integrity_check_call_counts=check_counts))
    return dict(schema='v124-independent-auditor-derivation-v1',old_integrity_check_calls_removed=0,sources=records)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    recipe=derive();path=HERE/'audit-derivation.json'
    if args.write:path.write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
    else:assert json.loads(path.read_text())==recipe
    print('V124_AUDITOR_DERIVATIONS_PREPARED_NOT_RUN',[(Path(r['candidate']).name,len(r['edits'])) for r in recipe['sources']])
if __name__=='__main__':main()
