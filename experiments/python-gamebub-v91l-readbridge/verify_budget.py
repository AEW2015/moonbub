#!/usr/bin/env python3
"""Independent batch operation/refresh work check of the source-side ideal model."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def command_work(bursts):
    # One row-hit BL8 occupies IDLE1+RW_CMD1+READ_WAIT6+READ_BURST7=15.
    # PRE and ACT each add1 command+3 WAITING edges. Refresh blocks15 edges,
    # resetting its counter at its sixth edge and leaving9 elapsed at IDLE.
    rows={};cycles=refresh_phase=reads=acts=pres=refs=hits=conflicts=0
    for address in bursts:
        if refresh_phase>=750:
            cycles+=15;refresh_phase=9;rows.clear();refs+=1;pres+=1
        bank=address>>23;row=(address>>10)&8191
        work=15
        if rows.get(bank)==row:hits+=1
        else:
            if bank in rows:pres+=1;conflicts+=1;work+=4
            acts+=1;rows[bank]=row;work+=4
        cycles+=work;refresh_phase+=work;reads+=1
    assert cycles==15*reads+4*acts+4*(pres-refs)+15*refs
    return dict(physical_bl8_reads=reads,row_activates=acts,row_precharges=pres,
                refresh_commands=refs,row_hits=hits,row_conflicts=conflicts,
                response_word_beats=reads*8,source_fsm_cycles_after_init=cycles)

def main():
    report=json.loads((AREA/'read-budget-results.json').read_text())
    assert report['generator_sha256']==sha(AREA/'read_budget.py')
    for name,h in report['source_sha256'].items():assert sha(ROOT/name)==h
    # The frozen prior geometric oracle supplies independently checked burst actions.
    spec=importlib.util.spec_from_file_location('read_audit',AREA/'verify_readbridge.py')
    lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
    _,frames,tiles,forward,schedule=lib.fixture_check()
    sequences={'raster_control':schedule,'tile_independent':[],'tile_retained':[]}
    for retain,name in ((0,'tile_independent'),(1,'tile_retained')):
        oracle=lib.gatherlib.GatherOracle(retain,tiles['actual_001'],forward)
        for a in schedule:sequences[name].extend(oracle.request(a)[0])
    results={}
    for name,sequence in sequences.items():
        checked=command_work(sequence)
        for k,v in checked.items():assert report['scenarios'][name][k]==v,(name,k,v)
        results[name]=checked
    result=dict(status='PASS_INDEPENDENT_READ_OPERATION_AND_REFRESH_WORK_COUNTS',verifier_sha256=sha(Path(__file__)),
                report_sha256=sha(AREA/'read-budget-results.json'),scenarios=results,
                starting_refresh_phase=0,scope='Ideal controller operation-work replay, not actual bridge/converter timing. No request backpressure, physical clock/PVT, native producer, hash/publication, shared memory or hardware proof.')
    (AREA/'audit-budget.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
