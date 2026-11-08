#!/usr/bin/env python3
"""Portable retained-expression traces, exact recipes and routed evidence audit."""
import csv,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/guard-dsp'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=json.loads((AREA/'results.json').read_text());assert r['status']=='PASS' and r['actual_RTL_run'];receipt=ROOT/r['selected_report'];snapshot=receipt.parent
 for rel,digest in r['artifacts_sha256'].items():assert sha(snapshot/rel)==digest,rel
 for rel,digest in r['source_sha256'].items():assert sha(ROOT/rel)==sha(snapshot/'sources'/rel)==digest,rel
 recipe=json.loads((snapshot/'sources/fpga/experiments/cu66-v107-guard-dsp/edit-recipe.json').read_text());unit=(snapshot/'sources/fpga/experiments/cu66-v107-guard-dsp/guard_probe.sv').read_text()
 for entry in recipe['files']:
  original=(snapshot/'sources'/entry['original']).read_text();candidate=(snapshot/'sources'/entry['candidate']).read_text();text=original
  for e in entry['edits']:assert text.count(e['before'])==e['expected_occurrences']==1;text=text.replace(e['before'],e['after'],1)
  assert text==candidate
  for e in reversed(entry['edits']):assert text.count(e['after'])==1;text=text.replace(e['after'],e['before'],1)
  assert text==original
  lines=[line for line in candidate.splitlines() if f'logic [31:0] {entry["signal"]};' in line or line.startswith(f'    assign {entry["signal"]}=')];assert len(lines)==2 and all(line+'\n' in unit for line in lines)
 counts=[0]*(1<<17);rows=high=0
 with gzip.open(snapshot/'trace.csv.gz','rt') as f:
  for row in csv.reader(f):
   x,y,a,b,p,q,ar,br=map(int,row);assert x==rows//9 and y==(1<<17)-1-x;assert p==x*43 and q==y*43
   assert ar==int(a>p) and br==int(b>q) and 0<=a<=0xffffffff and 0<=b<=0xffffffff
   corner=rows%9
   if corner<8:
    expected=lambda limit:(0,(limit-1)&0xffffffff,limit,limit+1,0x7fffffff,0x80000000,0xfffffffe,0xffffffff)[corner]
    assert a==expected(p) and b==expected(q)
   counts[x]+=1;rows+=1;high+=a>=0x80000000
 assert rows==r['verdict']['rows']==1179648 and all(n==9 for n in counts) and high==r['verdict']['high32_scratch_counts']
 chosen=json.loads((AREA/'route-probe/results.json').read_text());path=ROOT/chosen['selected_receipt'];assert sha(path)==chosen['sha256'];probe=json.loads(path.read_text());assert probe['status']=='PASS_READONLY_TIMING_EXTRACTION';assert probe['checkpoint_sha256_before']==probe['checkpoint_sha256_after'];assert probe['checkpoint_readonly'] and probe['no_RTL_or_clock_or_exception_edits']
 for rel,digest in probe['retained_sha256'].items():assert sha(path.parent/rel)==digest,rel
 paths=list(csv.DictReader((path.parent/'reports/dsp-paths.tsv').open(),delimiter='\t'));assert len(paths)==5 and all(x['source']=='coefficients/child/scratch/error4/CLK' for x in paths);slack=min(float(x['slack']) for x in paths);assert slack<0
 bind=AREA/'attribution/receipt.json';e=json.loads(bind.read_text());assert e['status']=='PASS_EXACT_MAPPED_CONSTANT43_ATTRIBUTION' and e['B_constant']==43 and e['A_nonconstant_bits']==17 and e['A_high_bits_grounded']==13;assert e['checkpoint_sha256_before']==e['checkpoint_sha256_after']
 for rel,digest in e['artifacts_sha256'].items():assert sha(bind.parent/rel)==digest,rel
 result=dict(schema='v107-guard-expression-portable-audit-v1',status='PASS_EXTRACTED_EXPRESSION_SOURCE_RECIPES_AND_ROUTED_MOTIVATION',actual_RTL_expression_rows=rows,all17bit_operands_per_product=len(counts),full32_count_cases_per_operand=9,high32_scratch_counts=high,production_files=r['production_files'],source_bound_expression_receipt_sha256=sha(receipt),routed_probe_receipt_sha256=sha(path),routed_original_DSP_worst_slack_ns=slack,routed_original_DSP_paths=paths,attribution_receipt_sha256=sha(bind),full_module_or_new_native_mapping_claim=False,scope='Original×43 DSP routed violation and standalone extracted old/new expression proof only. Actual complete candidate production controller canonical and new native mapping/timing remain parent tasks.')
 (AREA/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'],rows,slack)
if __name__=='__main__':main()
