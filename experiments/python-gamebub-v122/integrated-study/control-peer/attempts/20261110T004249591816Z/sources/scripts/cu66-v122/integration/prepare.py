#!/usr/bin/env python3
"""Reversibly derive V122 runners from frozen V121; no heavy jobs."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def derive():
    pins = {'spatial.py':'f8abd493c2c2d09c1bb3c9c25d6abc881efa4bd5e969fee59c8a5b25163b71a4',
            'peer.py':'2c18be7dac5e869f7dd810d757333f1db991ca7ad55cf7dccf2e9ac2a2956e71',
            'live_guard/qualify.py':'db8965062321a42271258b42b63c40ce78348eb3fe1b0088989bebd5b82b682f',
            'collect_final.py':'93af6c5c87f5593592cc578a928e762de8c638865b72925573da814587766d4a'}
    records = []
    for name, digest in pins.items():
        old = ROOT/'scripts/cu66-v121/integration'/name
        assert sha(old) == digest
        text = old.read_text()
        edits = []
        def edit(before, after, count=None):
            nonlocal text
            actual = text.count(before)
            assert actual > 0 and (count is None or actual == count), (name,before,actual,count)
            edits.append(dict(before=before,after=after,count=actual))
            text = text.replace(before,after)
        edit('scripts/cu66-v121/integration/', 'scripts/cu66-v122/integration/') if name != 'collect_final.py' else None
        edit('experiments/python-gamebub-v121/integrated-study/', 'experiments/python-gamebub-v122/integrated-study/') if name != 'collect_final.py' else None
        if name in ('spatial.py','peer.py','live_guard/qualify.py'):
            edit('v121-request-', 'v122-bounds-')
        if name == 'spatial.py':
            edit("B_CANONICAL=ROOT/'experiments/python-gamebub-v120/repair-study/spatial/results.json'", "B_CANONICAL=ROOT/'experiments/python-gamebub-v121/integrated-study/spatial/results.json'",1)
            edit("'fpga/experiments/cu66-v120-admission-match/cs88_admission_v91i2a.sv'", "'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'",1)
            edit("'experiments/python-gamebub-v120/admission-match/results.json'", "'experiments/python-gamebub-v122/bounds/results.json'",1)
            edit("packaging=ROOT/'fpga/experiments/cu66-v120-admission-match/packaging.json'", "packaging=ROOT/'fpga/experiments/cu66-v122-bounds/packaging.json'",1)
            edit("b['status']=='PASS_V120_FINAL_SPATIAL_CANONICAL'", "b['status']=='PASS_V121_FINAL_SPATIAL_CANONICAL'",1)
            edit("'PASS_V121_FINAL_SPATIAL_CANONICAL'", "'PASS_V122_FINAL_SPATIAL_CANONICAL'",2)
            edit("b['status']=='PASS_V122_FINAL_SPATIAL_CANONICAL'", "b['status']=='PASS_V121_FINAL_SPATIAL_CANONICAL'",1)
            edit('V121_SPATIAL','V122_SPATIAL')
            edit('V121 full32 accepted-request cursor; only refill queue changes from qualified Source B.', 'V122 full-width prepared admission bounds; only admission changes from qualified V121; the V121 queue is unchanged.',1)
        elif name == 'peer.py':
            edit('V121_CONTROL_PEER','V122_CONTROL_PEER')
        elif name == 'live_guard/qualify.py':
            edit("ROOT/'experiments/python-gamebub-v120/admission-match/results.json', ROOT/'fpga/experiments/cu66-v120-admission-match/cs88_admission_v91i2a.sv'", "ROOT/'experiments/python-gamebub-v122/bounds/results.json', ROOT/'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'",1)
            edit('experiments/python-gamebub-v120/repair-study/live-guard/results.json','experiments/python-gamebub-v121/integrated-study/live-guard/results.json',1)
            edit('PASS_V120_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION','PASS_V121_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION',1)
            edit('PASS_V121_FINAL_SPATIAL_CANONICAL','PASS_V122_FINAL_SPATIAL_CANONICAL',1)
            edit("'PASS_V121_SELECTED_COMPONENT_'", "'PASS_V122_SELECTED_COMPONENT_'",1)
            edit('V121_LIVE_PARENT','V122_LIVE_PARENT')
        else:
            edit("AREA = ROOT/'experiments/python-gamebub-v121'", "AREA = ROOT/'experiments/python-gamebub-v122'",1)
            edit("('focused','request')", "('focused','bounds')",1)
            edit("queue = 'fpga/experiments/cu66-v121-request/byte_refill_queue_v91i2b.sv'", "queue = 'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'",1)
            edit('PASS_V121_FINAL_SPATIAL_CANONICAL','PASS_V122_FINAL_SPATIAL_CANONICAL',1)
            edit('PASS_V121_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION','PASS_V122_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION',1)
            edit('v121-request-functional-composition-v1','v122-bounds-functional-composition-v1',1)
            edit('PASS_V121_REQUEST_FULL_FUNCTIONAL','PASS_V122_BOUNDS_FULL_FUNCTIONAL',1)
            before=text[text.index("    result['collector_derivation']"):text.index("    target = AREA")]
            edit(before,"    result['baseline_V121_index'] = dict(path='experiments/python-gamebub-v121/integration/results.json', sha256=sha(ROOT/'experiments/python-gamebub-v121/integration/results.json'))\n    result['adapter_derivation'] = dict(path='scripts/cu66-v122/integration/derivation.json', sha256=sha(Path(__file__).with_name('derivation.json')))\n",1)
        records.append(dict(original=str(old.relative_to(ROOT)),original_sha256=digest,candidate=str((HERE/name).relative_to(ROOT)),candidate_sha256=hashlib.sha256(text.encode()).hexdigest(),edits=edits,text=text))
    return records

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    records=derive()
    recipe=dict(schema='v122-integration-adapters-v1',old_oracle_checks_removed=0,exact_source_B_cycle_delta=0,sources=[{k:v for k,v in r.items() if k!='text'} for r in records])
    for r in records:
        p=ROOT/r['candidate']
        if args.write:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(r['text'])
        else:assert p.read_text()==r['text']
    p=HERE/'derivation.json'
    if args.write:p.write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
    else:assert json.loads(p.read_text())==recipe
    print('V122_INTEGRATION_ADAPTERS_PREPARED_NOT_RUN',len(records))
if __name__=='__main__':main()
