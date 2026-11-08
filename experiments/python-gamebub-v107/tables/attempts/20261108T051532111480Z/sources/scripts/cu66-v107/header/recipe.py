#!/usr/bin/env python3
"""Audit and retain exact staged header sum edits; reproduce all adapters losslessly."""
import difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'fpga/experiments/cu66-v107-quant/cs88_admission_v91i2a.sv'
CAND=ROOT/'fpga/experiments/cu66-v107-header/cs88_admission_v91i2a.sv'
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 a,b=BASE.read_text(),CAND.read_text();p=CAND.parent
 changes=[{'start':i,'end':j,'old':a[i:j],'new':b[k:l]} for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if tag!='equal']
 rebuilt=a
 for e in reversed(changes):
  assert rebuilt[e['start']:e['end']]==e['old'];rebuilt=rebuilt[:e['start']]+e['new']+rebuilt[e['end']:]
 assert rebuilt==b
 adapter=json.loads((p/'adapter.json').read_text())
 for variant,production in [('original',a),('candidate',b)]:
  t=(p/f'admission_{variant}.sv').read_text().replace(' /* verilator public_flat_rw */','').replace(f'module admission_{variant} (','module cs88_admission_v91i2a (',1)
  t=t.replace(adapter['extra_ports'],'\n);',1).replace(adapter['assignments'][variant],'',1)
  assert t==production,variant
 report={'status':'PASS_EXACT_RECIPE_AND_ADAPTERS','baseline':str(BASE.relative_to(ROOT)),'baseline_sha256':digest(a),'candidate':str(CAND.relative_to(ROOT)),'candidate_sha256':digest(b),'changes':changes,'offset_units':'ASCII offsets; apply in reverse order'}
 (p/'edit-recipe.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(report['status'],report['candidate_sha256'])
if __name__=='__main__':main()
