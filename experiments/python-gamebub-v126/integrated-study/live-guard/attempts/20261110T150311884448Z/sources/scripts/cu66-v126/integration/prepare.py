#!/usr/bin/env python3
"""Reversibly derive frozen V125 full runners; no preparation invokes EDA tools."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
PINS={'spatial.py':'b207cc850c1ba8ee1a703169497e3cae72a248abb789e2b0b514962467a05fac','peer.py':'2017931fb1c5044c6972f41b932e1c39b01088f4fa92570e44ccc7363a4ecf23','live_guard/qualify.py':'afd11ffd3ff53279344c8bc5f489f232df6709fd052444dd7a2e3176bf95df76','collect_final.py':'cd72ca0fccbba3b798b59499d0c60076f3bf4bdc9eee0d726b1ee5ecaadf2aa4'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive():
 records=[]
 for name,digest in PINS.items():
  old=ROOT/'scripts/cu66-v125/integration'/name;assert sha(old)==digest
  text=old.read_text();edits=[]
  def edit(before,after,count=None):
   nonlocal text
   n=text.count(before);assert n>0 and(count is None or n==count),(name,before,n,count)
   text=text.replace(before,after);edits.append(dict(before=before,after=after,count=n))
  if name!='collect_final.py':
   edit('scripts/cu66-v125/integration/','scripts/cu66-v126/integration/')
   edit('experiments/python-gamebub-v125/integrated-study/','experiments/python-gamebub-v126/integrated-study/')
   edit('v125-tile-','v126-producer-')
   edit('V125_','V126_')
  if name=='spatial.py':
   edit("B_CANONICAL=ROOT/'experiments/python-gamebub-v124/integrated-study/spatial/results.json'","B_CANONICAL=ROOT/'experiments/python-gamebub-v125/integrated-study/spatial/results.json'",1)
   edit("'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'","'fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv'",1)
   edit("'experiments/python-gamebub-v124/owner/results.json'","'experiments/python-gamebub-v126/producer/results.json'",1)
   edit("b['status']=='PASS_V124_FINAL_SPATIAL_CANONICAL'","b['status']=='PASS_V125_FINAL_SPATIAL_CANONICAL'",1)
   edit('V125 admission tile predicates; only admission changes from qualified V124; producer owner lanes, scratch rank and prepared queue remain unchanged.','V126 producer pipeline; only producer changes from frozen V125; admission tile predicates, scratch rank and prepared queue remain unchanged.',1)
  elif name=='live_guard/qualify.py':
   edit("ROOT/'experiments/python-gamebub-v124/owner/results.json', ROOT/'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'","ROOT/'experiments/python-gamebub-v126/producer/results.json', ROOT/'fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv'",1)
   edit('experiments/python-gamebub-v124/integrated-study/live-guard/results.json','experiments/python-gamebub-v125/integrated-study/live-guard/results.json',1)
   edit('PASS_V124_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION','PASS_V125_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION',1)
   edit("assert args.root_grant, 'Root heavy-slot grant required'","assert args.root_grant=='ROOT_V126_PRODUCER_PARENT', 'Exact Root heavy-slot grant required'",1)
  elif name=='collect_final.py':
   edit("AREA = ROOT/'experiments/python-gamebub-v125'","AREA = ROOT/'experiments/python-gamebub-v126'",1)
   edit("('focused','tile')","('focused','producer')",1)
   edit("admission = 'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'","producer = 'fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv'",1)
   edit("raw['source_sha256'][admission] == sha(ROOT/admission)","raw['source_sha256'][producer] == sha(ROOT/producer)",1)
   edit('V125_','V126_')
   edit('v125-tile-functional-composition-v1','v126-producer-functional-composition-v1',1)
   edit('PASS_V126_TILE_FULL_FUNCTIONAL','PASS_V126_PRODUCER_FULL_FUNCTIONAL',1)
   edit('baseline_V124_index','baseline_V125_index',1)
   edit('experiments/python-gamebub-v124/integration/results.json','experiments/python-gamebub-v125/integration/results.json',2)
   edit('scripts/cu66-v125/integration/derivation.json','scripts/cu66-v126/integration/derivation.json',1)
  records.append(dict(original=str(old.relative_to(ROOT)),original_sha256=digest,candidate=str((HERE/name).relative_to(ROOT)),candidate_sha256=hashlib.sha256(text.encode()).hexdigest(),edits=edits,text=text))
 return records

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();records=derive()
 data=dict(schema='v126-integration-adapters-v1',old_oracle_checks_removed=0,exact_source_B_cycle_delta=0,sources=[{k:v for k,v in r.items()if k!='text'}for r in records])
 for r in records:
  p=ROOT/r['candidate']
  if a.write:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(r['text'])
  else:assert p.read_text()==r['text']
 p=HERE/'derivation.json'
 if a.write:p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 else:assert json.loads(p.read_text())==data
 print('V126_INTEGRATION_ADAPTERS_PREPARED_NOT_RUN',len(records))
if __name__=='__main__':main()
