#!/usr/bin/env python3
"""Exact canonical-top integration recipe and explicit additional-source contract."""
import difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv'
FPGA=ROOT/'fpga/experiments/cu66-v107-elastic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=BASE.read_text();b=(FPGA/BASE.name).read_text();assert a.split(');',1)[0]==b.split(');',1)[0],'public top signature changed'
 changes=[{'start':i,'end':j,'old':a[i:j],'new':b[k:l]} for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if tag!='equal']
 s=a
 for e in reversed(changes):
  assert s[e['start']:e['end']]==e['old'];s=s[:e['start']]+e['new']+s[e['end']:]
 assert s==b
 assert b.count('cu66_coefficient_elastic coefficient_boundary (')==1
 assert '.in_valid(staged_valid),.in_ready(staged_ready)' in b
 assert '.out_valid(coefficient_valid)' in b and '.out_ready(coefficient_ready)' in b
 assert '.in_child_epoch(staged_child_epoch)' in b
 r={'status':'PASS_EXACT_TOP_RECIPE_SIGNATURE_UNCHANGED','baseline':str(BASE.relative_to(ROOT)),'baseline_sha256':sha(BASE),'replacement':str((FPGA/BASE.name).relative_to(ROOT)),'replacement_sha256':sha(FPGA/BASE.name),'additional_sources':[{'path':str((FPGA/'cu66_coefficient_elastic.sv').relative_to(ROOT)),'sha256':sha(FPGA/'cu66_coefficient_elastic.sv')}],'source_count_contract':'Add one RTL module to historical17-source closure; explicit18-source list required. Never omit new module or replace an unrelated historical source to keep count17.','offset_units':'ASCII offsets applied in reverse order','changes':changes,'latency_contract':'One registered coefficient token, minimum one full clock between upstream accept and downstream accept. Continuous replacement permits one token per clock. End fence follows every accepted token and is sticky until flush. Parent time/counter traces may differ; compare ordered payload/error/ownership outcomes.'}
 (FPGA/'edit-recipe.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(r['status'],r['replacement_sha256'],r['additional_sources'][0]['sha256'])
if __name__=='__main__':main()
