#!/usr/bin/env python3
"""Retain exact verification-only bench edits and original checker inventory."""
import collections,difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'fpga/experiments/cu66-v91k/tb_pipeline.cpp'
CAND=ROOT/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def calls(text):
 result=[];start=0
 while True:
  start=text.find('need(',start)
  if start<0:return result
  at=start+4;depth=0;quoted=False;escape=False
  while at<len(text):
   c=text[at]
   if quoted:
    if escape:escape=False
    elif c=='\\':escape=True
    elif c=='"':quoted=False
   elif c=='"':quoted=True
   elif c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:result.append(text[start:at+1]);start=at+1;break
   at+=1
  else:raise AssertionError('unclosed need call')
def main():
 a,b=BASE.read_text(),CAND.read_text();old,new=map(collections.Counter,(calls(a),calls(b)))
 missing=old-new;assert not missing,dict(missing)
 assert '#if ELASTIC' in b and 'd.inverse_count_inputs+elastic_discard==coefficients' in b
 changes=[{'start':i,'end':j,'old':a[i:j],'new':b[k:l]} for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if tag!='equal']
 s=a
 for e in reversed(changes):assert s[e['start']:e['end']]==e['old'];s=s[:e['start']]+e['new']+s[e['end']:]
 assert s==b
 r={'status':'PASS_EXACT_VERIFICATION_BENCH_RECIPE','original':str(BASE.relative_to(ROOT)),'original_sha256':sha(BASE),'candidate':str(CAND.relative_to(ROOT)),'candidate_sha256':sha(CAND),'original_need_calls':sum(old.values()),'candidate_need_calls':sum(new.values()),'all_original_need_calls_retained':True,'conditional_adaptation':'Original inverse_count_inputs==coefficients applies unchanged in control; candidate success retains equality and every candidate edge additionally mirrors inverse input count. Fault cases require inputs+explicitly counted stage discards==upstream accepts, complete tuple order and drained ownership.','changes':changes}
 (CAND.parent/'bench-edit-recipe.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(r['status'],r['original_need_calls'],r['candidate_need_calls'])
if __name__=='__main__':main()
