#!/usr/bin/env python3
"""Record reversible V126-to-V127 adapters without invoking EDA tools."""
import argparse,difflib,hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
RUNNERS={
 'spatial.py':'8727db4da7926042b09fdb07e9708df6ae52be1c778f685149c8ad9f4b4a60a2',
 'peer.py':'fa6e60f99e8d396d7203b896bca9754a4a63b982bc8580f1c0784db8924acb33',
 'live_guard/qualify.py':'9e4b19066bb535ab7b75b2f424120bcd4af648595f8d8a60870e5aa0e2ae0db6',
 'collect_final.py':'6be46f5b1ac636d1321d494facca6338dfc9022153f754c9deccd43cfcd86b5f'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(pairs):
 result=[]
 for original,candidate,digest in pairs:
  before,after=ROOT/original,ROOT/candidate;assert sha(before)==digest
  old,new=before.read_text(),after.read_text();a,b=old.splitlines(keepends=True),new.splitlines(keepends=True)
  for context in (3,5,8,16,32,64,128,1024):
   edits=[];text=old
   for group in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_grouped_opcodes(context):
    x=''.join(a[group[0][1]:group[-1][2]]);y=''.join(b[group[0][3]:group[-1][4]])
    if not x or not y or text.count(x)!=1:break
    edits.append(dict(before=x,after=y,count=1));text=text.replace(x,y,1)
   else:
    if text!=new:continue
    for edit in reversed(edits):
     if text.count(edit['after'])!=1:break
     text=text.replace(edit['after'],edit['before'],1)
    else:
     if text==old:break
   continue
  else:raise AssertionError('No unique reversible derivation: '+candidate)
  counts={label:dict(original=len(re.findall(pattern,old)),candidate=len(re.findall(pattern,new)))for label,pattern in [('assert',r'\bassert\b'),('need',r'\bneed\('),('audit.check',r'\baudit\.check\(')]}
  assert all(v['candidate']>=v['original']for v in counts.values()),(candidate,counts)
  result.append(dict(original=original,original_sha256=digest,candidate=candidate,candidate_sha256=sha(after),edits=edits,context_lines=context,integrity_check_call_counts=counts))
 return result
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
 result=dict(schema='v127-integration-adapters-v1',old_oracle_checks_removed=0,exact_source_B_cycle_delta=0,sources=records([('scripts/cu66-v126/integration/'+n,'scripts/cu66-v127/integration/'+n,h)for n,h in RUNNERS.items()]))
 p=HERE/'derivation.json'
 if args.write:p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 else:assert json.loads(p.read_text())==result
 print('V127_INTEGRATION_ADAPTERS_PREPARED_NOT_RUN',len(result['sources']))
if __name__=='__main__':main()
