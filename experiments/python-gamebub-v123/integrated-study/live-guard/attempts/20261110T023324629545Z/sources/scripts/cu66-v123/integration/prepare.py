#!/usr/bin/env python3
"""Derive V123 integration adapters reversibly from frozen V122; no tools run."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
PINS={'spatial.py':'6138d750f002404fdabe64f429056d7bc6567d26e50c5dc93507d5805bb2a9d1',
      'peer.py':'d572f2e64808f571b96d3ce790bcf0198b847d8a1a30e4c5a3b0912e8f949976',
      'live_guard/qualify.py':'45fb0cc12fffe587565806f4903211f3c3c1b82901b0d948e23783097b8c99b5',
      'collect_final.py':'d805e6bc9723a75907334abbc99f7b8518dd3285de07929bcbed62fc28125e03'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive():
    records=[]
    for name,digest in PINS.items():
        old=ROOT/'scripts/cu66-v122/integration'/name;assert sha(old)==digest
        text=old.read_text();edits=[]
        def edit(before,after,count=None):
            nonlocal text
            n=text.count(before);assert n>0 and (count is None or n==count),(name,before,n,count)
            text=text.replace(before,after);edits.append(dict(before=before,after=after,count=n))
        if name!='collect_final.py':
            edit('scripts/cu66-v122/integration/','scripts/cu66-v123/integration/')
            edit('experiments/python-gamebub-v122/integrated-study/','experiments/python-gamebub-v123/integrated-study/')
            edit('v122-bounds-','v123-rank-')
        if name=='spatial.py':
            edit("B_CANONICAL=ROOT/'experiments/python-gamebub-v121/integrated-study/spatial/results.json'","B_CANONICAL=ROOT/'experiments/python-gamebub-v122/integrated-study/spatial/results.json'",1)
            edit("'fpga/experiments/cu66-v119-scratch/packed_scratch_v91g2.sv'","'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'",1)
            edit("'experiments/python-gamebub-v119/scratch/results.json'","'experiments/python-gamebub-v123/rank/results.json'",1)
            edit("'PASS_V122_FINAL_SPATIAL_CANONICAL'","'PASS_V123_FINAL_SPATIAL_CANONICAL'",1)
            edit("b['status']=='PASS_V121_FINAL_SPATIAL_CANONICAL'","b['status']=='PASS_V122_FINAL_SPATIAL_CANONICAL'",1)
            edit('V122_SPATIAL','V123_SPATIAL')
            edit('V122 full-width prepared admission bounds; only admission changes from qualified V121; the V121 queue is unchanged.','V123 plane-local scratch rank metadata; only scratch changes from qualified V122; V122 bounds and V121 queue are unchanged.',1)
        elif name=='peer.py':
            edit('V122_CONTROL_PEER','V123_CONTROL_PEER')
        elif name=='live_guard/qualify.py':
            edit('PASS_V122_FINAL_SPATIAL_CANONICAL','PASS_V123_FINAL_SPATIAL_CANONICAL',1)
            edit("ROOT/'experiments/python-gamebub-v119/scratch/results.json', ROOT/'fpga/experiments/cu66-v119-scratch/packed_scratch_v91g2.sv'","ROOT/'experiments/python-gamebub-v123/rank/results.json', ROOT/'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'",1)
            edit('experiments/python-gamebub-v121/integrated-study/live-guard/results.json','experiments/python-gamebub-v122/integrated-study/live-guard/results.json',1)
            edit('PASS_V121_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION','PASS_V122_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION',1)
            edit("'PASS_V122_SELECTED_COMPONENT_'","'PASS_V123_SELECTED_COMPONENT_'",1)
            edit('V122_LIVE_PARENT','V123_LIVE_PARENT')
        else:
            edit("AREA = ROOT/'experiments/python-gamebub-v122'","AREA = ROOT/'experiments/python-gamebub-v123'",1)
            edit("('focused','bounds')","('focused','rank')",1)
            edit("queue = 'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'","queue = 'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'",1)
            edit('PASS_V122_FINAL_SPATIAL_CANONICAL','PASS_V123_FINAL_SPATIAL_CANONICAL',1)
            edit('PASS_V122_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION','PASS_V123_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION',1)
            edit('v122-bounds-functional-composition-v1','v123-rank-functional-composition-v1',1)
            edit('PASS_V122_BOUNDS_FULL_FUNCTIONAL','PASS_V123_RANK_FULL_FUNCTIONAL',1)
            edit('baseline_V121_index','baseline_V122_index',1)
            edit('experiments/python-gamebub-v121/integration/results.json','experiments/python-gamebub-v122/integration/results.json',2)
            edit('scripts/cu66-v122/integration/derivation.json','scripts/cu66-v123/integration/derivation.json',1)
        records.append(dict(original=str(old.relative_to(ROOT)),original_sha256=digest,candidate=str((HERE/name).relative_to(ROOT)),candidate_sha256=hashlib.sha256(text.encode()).hexdigest(),edits=edits,text=text))
    return records

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();records=derive()
    data=dict(schema='v123-integration-adapters-v1',old_oracle_checks_removed=0,exact_source_B_cycle_delta=0,sources=[{k:v for k,v in r.items() if k!='text'} for r in records])
    for r in records:
        p=ROOT/r['candidate']
        if a.write:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(r['text'])
        else:assert p.read_text()==r['text']
    p=HERE/'derivation.json'
    if a.write:p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    else:assert json.loads(p.read_text())==data
    print('V123_INTEGRATION_ADAPTERS_PREPARED_NOT_RUN',len(records))
if __name__=='__main__':main()
