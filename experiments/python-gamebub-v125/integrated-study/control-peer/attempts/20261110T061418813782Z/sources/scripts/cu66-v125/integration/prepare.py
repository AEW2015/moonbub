#!/usr/bin/env python3
"""Derive V125 integration adapters reversibly from frozen V124; no tools run."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
PINS={'spatial.py':'d50d494d7cf7e7750a8bb48f39ccbea1ecad2af27ac2db31a4d61843652853a4',
      'peer.py':'ae388cd27813fd5ce6e019fc03cf7e76464495d8fa3f2d96f2c160155807946d',
      'live_guard/qualify.py':'885b1d5dcac99c45db65dc33076ebe3656d90d2050e3db8840e3ec4bbde166bc',
      'collect_final.py':'f4457b54c0690dc1d39ed9977675c1098af1975bd59ed55af68008f658c9e7f9'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive():
    records=[]
    for name,digest in PINS.items():
        old=ROOT/'scripts/cu66-v124/integration'/name;assert sha(old)==digest
        text=old.read_text();edits=[]
        def edit(before,after,count=None):
            nonlocal text
            n=text.count(before);assert n>0 and (count is None or n==count),(name,before,n,count)
            text=text.replace(before,after);edits.append(dict(before=before,after=after,count=n))
        if name!='collect_final.py':
            edit('scripts/cu66-v124/integration/','scripts/cu66-v125/integration/')
            edit('experiments/python-gamebub-v124/integrated-study/','experiments/python-gamebub-v125/integrated-study/')
            edit('v124-owner-','v125-tile-')
        if name=='spatial.py':
            edit("B_CANONICAL=ROOT/'experiments/python-gamebub-v123/integrated-study/spatial/results.json'","B_CANONICAL=ROOT/'experiments/python-gamebub-v124/integrated-study/spatial/results.json'",1)
            edit("'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'","'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'",1)
            edit("'experiments/python-gamebub-v122/bounds/results.json'","'experiments/python-gamebub-v125/tile/results.json'",1)
            edit("packaging=ROOT/'fpga/experiments/cu66-v122-bounds/packaging.json'","packaging=ROOT/'fpga/experiments/cu66-v125-tile/packaging.json'",1)
            edit("'PASS_V124_FINAL_SPATIAL_CANONICAL'","'PASS_V125_FINAL_SPATIAL_CANONICAL'",1)
            edit("b['status']=='PASS_V123_FINAL_SPATIAL_CANONICAL'","b['status']=='PASS_V124_FINAL_SPATIAL_CANONICAL'",1)
            edit('V124_SPATIAL','V125_SPATIAL')
            edit('V124 producer owner lanes; only coefficients producer changes from qualified V123; V123 scratch, V122 bounds and V121 queue are unchanged.','V125 admission tile predicates; only admission changes from qualified V124; producer owner lanes, scratch rank and prepared queue remain unchanged.',1)
        elif name=='peer.py':
            edit('V124_CONTROL_PEER','V125_CONTROL_PEER')
        elif name=='live_guard/qualify.py':
            edit('PASS_V124_FINAL_SPATIAL_CANONICAL','PASS_V125_FINAL_SPATIAL_CANONICAL',1)
            edit("ROOT/'experiments/python-gamebub-v122/bounds/results.json', ROOT/'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'","ROOT/'experiments/python-gamebub-v125/tile/results.json', ROOT/'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'",1)
            edit('experiments/python-gamebub-v123/integrated-study/live-guard/results.json','experiments/python-gamebub-v124/integrated-study/live-guard/results.json',1)
            edit('PASS_V123_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION','PASS_V124_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION',1)
            edit("'PASS_V124_SELECTED_COMPONENT_'","'PASS_V125_SELECTED_COMPONENT_'",1)
            edit('V124_LIVE_PARENT','V125_LIVE_PARENT')
        else:
            edit("AREA = ROOT/'experiments/python-gamebub-v124'","AREA = ROOT/'experiments/python-gamebub-v125'",1)
            edit("('focused','owner')","('focused','tile')",1)
            edit("producer = 'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'","admission = 'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'",1)
            edit("raw['source_sha256'][producer] == sha(ROOT/producer)","raw['source_sha256'][admission] == sha(ROOT/admission)",1)
            edit('PASS_V124_FINAL_SPATIAL_CANONICAL','PASS_V125_FINAL_SPATIAL_CANONICAL',1)
            edit('PASS_V124_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION','PASS_V125_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION',1)
            edit('v124-owner-functional-composition-v1','v125-tile-functional-composition-v1',1)
            edit('PASS_V124_OWNER_FULL_FUNCTIONAL','PASS_V125_TILE_FULL_FUNCTIONAL',1)
            edit('baseline_V123_index','baseline_V124_index',1)
            edit('experiments/python-gamebub-v123/integration/results.json','experiments/python-gamebub-v124/integration/results.json',2)
            edit('scripts/cu66-v124/integration/derivation.json','scripts/cu66-v125/integration/derivation.json',1)
        records.append(dict(original=str(old.relative_to(ROOT)),original_sha256=digest,candidate=str((HERE/name).relative_to(ROOT)),candidate_sha256=hashlib.sha256(text.encode()).hexdigest(),edits=edits,text=text))
    return records

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();records=derive()
    data=dict(schema='v125-integration-adapters-v1',old_oracle_checks_removed=0,exact_source_B_cycle_delta=0,sources=[{k:v for k,v in r.items() if k!='text'} for r in records])
    for r in records:
        p=ROOT/r['candidate']
        if a.write:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(r['text'])
        else:assert p.read_text()==r['text']
    p=HERE/'derivation.json'
    if a.write:p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    else:assert json.loads(p.read_text())==data
    print('V125_INTEGRATION_ADAPTERS_PREPARED_NOT_RUN',len(records))
if __name__=='__main__':main()
