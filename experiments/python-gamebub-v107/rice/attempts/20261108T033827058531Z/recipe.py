#!/usr/bin/env python3
"""Reconstruct exact candidate edits from pinned baseline offsets and hashes."""
import difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'fpga/experiments/cu66-v106-suffix24/br88_rice_elastic.sv'
CAND=ROOT/'fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv'
OUT=CAND.parent/'edit-recipe.json'
def sha(x):return hashlib.sha256(x.encode()).hexdigest()
def main():
 a,b=BASE.read_text(),CAND.read_text()
 changes=[{'start':i,'end':j,'old':a[i:j],'new':b[k:l]} for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if tag!='equal']
 rebuilt=a
 for edit in reversed(changes):
  assert rebuilt[edit['start']:edit['end']]==edit['old']
  rebuilt=rebuilt[:edit['start']]+edit['new']+rebuilt[edit['end']:]
 assert rebuilt==b
 report={'status':'PASS_EXACT_SOURCE_RECIPE','baseline':str(BASE.relative_to(ROOT)),'baseline_sha256':sha(a),'candidate':str(CAND.relative_to(ROOT)),'candidate_sha256':sha(b),'offset_units':'ASCII characters; apply reverse order after checking baseline hash','changes':changes}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(report['status'],report['baseline_sha256'],report['candidate_sha256'])
if __name__=='__main__':main()
