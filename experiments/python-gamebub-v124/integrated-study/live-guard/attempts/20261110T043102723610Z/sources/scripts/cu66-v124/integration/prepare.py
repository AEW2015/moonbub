#!/usr/bin/env python3
"""Derive V124 integration adapters reversibly from frozen V123; no tools run."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
PINS={'spatial.py':'a952cde3f79cce7109ba18c5109563fa8b77e280bc908a402221eec36ca5434f',
      'peer.py':'166e29c252ae141e12ad2342882c771116ffb5e8725b7925fa7fd021997f5bd1',
      'live_guard/qualify.py':'cb515762793c8c1584e14f96d99be9cd7316c640ff714101db92cd9d47c393b3',
      'collect_final.py':'d8244dc784de02d8a91b504c0d06f853aaf0e4365d5821d7a3d20e15733f63fb'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive():
    records=[]
    for name,digest in PINS.items():
        old=ROOT/'scripts/cu66-v123/integration'/name;assert sha(old)==digest
        text=old.read_text();edits=[]
        def edit(before,after,count=None):
            nonlocal text
            n=text.count(before);assert n>0 and (count is None or n==count),(name,before,n,count)
            text=text.replace(before,after);edits.append(dict(before=before,after=after,count=n))
        if name!='collect_final.py':
            edit('scripts/cu66-v123/integration/','scripts/cu66-v124/integration/')
            edit('experiments/python-gamebub-v123/integrated-study/','experiments/python-gamebub-v124/integrated-study/')
            edit('v123-rank-','v124-owner-')
        if name=='spatial.py':
            edit("B_CANONICAL=ROOT/'experiments/python-gamebub-v122/integrated-study/spatial/results.json'","B_CANONICAL=ROOT/'experiments/python-gamebub-v123/integrated-study/spatial/results.json'",1)
            edit("'fpga/experiments/cu66-v119-owner/cs88_coefficients_v91k.sv'","'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'",1)
            edit("'experiments/python-gamebub-v119/owner/producer/results.json'","'experiments/python-gamebub-v124/owner/results.json'",1)
            edit("'PASS_V123_FINAL_SPATIAL_CANONICAL'","'PASS_V124_FINAL_SPATIAL_CANONICAL'",1)
            edit("b['status']=='PASS_V122_FINAL_SPATIAL_CANONICAL'","b['status']=='PASS_V123_FINAL_SPATIAL_CANONICAL'",1)
            edit('V123_SPATIAL','V124_SPATIAL')
            edit('V123 plane-local scratch rank metadata; only scratch changes from qualified V122; V122 bounds and V121 queue are unchanged.','V124 producer owner lanes; only coefficients producer changes from qualified V123; V123 scratch, V122 bounds and V121 queue are unchanged.',1)
        elif name=='peer.py':
            edit('V123_CONTROL_PEER','V124_CONTROL_PEER')
        elif name=='live_guard/qualify.py':
            edit('PASS_V123_FINAL_SPATIAL_CANONICAL','PASS_V124_FINAL_SPATIAL_CANONICAL',1)
            edit("for selector, source in [(ROOT/'experiments/python-gamebub-v116/rice/results.json'", "for selector, source in [(ROOT/'experiments/python-gamebub-v124/owner/results.json', ROOT/'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'),\n                                 (ROOT/'experiments/python-gamebub-v116/rice/results.json'",1)
            edit('experiments/python-gamebub-v122/integrated-study/live-guard/results.json','experiments/python-gamebub-v123/integrated-study/live-guard/results.json',1)
            edit('PASS_V122_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION','PASS_V123_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION',1)
            edit("'PASS_V123_SELECTED_COMPONENT_'","'PASS_V124_SELECTED_COMPONENT_'",1)
            edit('V123_LIVE_PARENT','V124_LIVE_PARENT')
        else:
            edit("AREA = ROOT/'experiments/python-gamebub-v123'","AREA = ROOT/'experiments/python-gamebub-v124'",1)
            edit("('focused','rank')","('focused','owner')",1)
            edit("queue = 'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'","producer = 'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'",1)
            edit("raw['source_sha256'][queue] == sha(ROOT/queue)","raw['source_sha256'][producer] == sha(ROOT/producer)",1)
            edit('PASS_V123_FINAL_SPATIAL_CANONICAL','PASS_V124_FINAL_SPATIAL_CANONICAL',1)
            edit('PASS_V123_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION','PASS_V124_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION',1)
            edit('v123-rank-functional-composition-v1','v124-owner-functional-composition-v1',1)
            edit('PASS_V123_RANK_FULL_FUNCTIONAL','PASS_V124_OWNER_FULL_FUNCTIONAL',1)
            edit('baseline_V122_index','baseline_V123_index',1)
            edit('experiments/python-gamebub-v122/integration/results.json','experiments/python-gamebub-v123/integration/results.json',2)
            edit('scripts/cu66-v123/integration/derivation.json','scripts/cu66-v124/integration/derivation.json',1)
        records.append(dict(original=str(old.relative_to(ROOT)),original_sha256=digest,candidate=str((HERE/name).relative_to(ROOT)),candidate_sha256=hashlib.sha256(text.encode()).hexdigest(),edits=edits,text=text))
    return records

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();records=derive()
    data=dict(schema='v124-integration-adapters-v1',old_oracle_checks_removed=0,exact_source_B_cycle_delta=0,sources=[{k:v for k,v in r.items() if k!='text'} for r in records])
    for r in records:
        p=ROOT/r['candidate']
        if a.write:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(r['text'])
        else:assert p.read_text()==r['text']
    p=HERE/'derivation.json'
    if a.write:p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    else:assert json.loads(p.read_text())==data
    print('V124_INTEGRATION_ADAPTERS_PREPARED_NOT_RUN',len(records))
if __name__=='__main__':main()
