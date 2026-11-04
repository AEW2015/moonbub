#!/usr/bin/env python3
"""Read-only stored-source and bounded scheduler evidence replay."""
import hashlib,json
from pathlib import Path
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def check_result(r):
    if r['status']=='address_window_rejected':
        assert not r['allocation']['window_sufficient'];return
    cfg=r['config'];peak=r['peak_bounds']
    assert peak['input_slots']<=2 and peak['display_fifo_slots']<=cfg['prefetch_lines']
    assert peak['decoder_jobs']<=1 and peak['background_requests']<=1 and peak['reference_readers']<=1
    assert not r['physical_proof'] and not r['packet_decode_or_reference_identity_proof']
    assert r['eventual_presentations']==len(r['presented'])
    assert len({p['id'] for p in r['presented']})==len(r['presented'])
    assert len(r['presented'])+len(r['drops'])+len(r['unresolved_ids'])==cfg['frames']
    assert r['clean_eventual_unique_ids']==len(r['clean_full_panel_epoch_presentations'])
    assert len({p['id'] for p in r['clean_full_panel_epoch_presentations']})==r['clean_eventual_unique_ids']
    assert r['clean_eventual_unique_ids']<=r['eventual_presentations']
    assert r['bus_counters']['served_line_epoch_checks']+r['display_line_misses']==r['display_line_deadline_count']
    assert all(x['id']==x['epoch_frame_id'] for x in r['clean_full_panel_epoch_presentations'])
    assert r['strict_presentations']==sum(p['at_cycle']<r['capture_end_cycle'] for p in r['presented'])
    assert all(p['id'] not in r['unresolved_ids'] for p in r['drops'])

def main():
    d=json.loads((HERE/'results.json').read_text())
    for rel,expected in d['source_sha256'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected,rel
    assert len(d['input_traces'])==3 and len(d['cases'])==8 and len(d['phase_cases'])==4
    for group in ['cases','phase_cases']:
        for c in d[group]:
            r=c['result'];check_result(r)
            cfg=model.Config(**r['config'])
            assert r==model.simulate(d['input_traces'][:1]+[d['input_traces'][1] if i%16==0 else d['input_traces'][2] for i in range(1,30)],cfg),c['name']
    print('PASS:8boundedscanlinecases+4phasecases;actualcoefficienttemplates;capacity/ownership/deadlinecounts;conditionalnotphysicalproof')
if __name__=='__main__':main()
