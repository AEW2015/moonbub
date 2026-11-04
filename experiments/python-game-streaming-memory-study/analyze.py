#!/usr/bin/env python3
"""Untimed strict epoch-start/finish reconciliation; frozen model unchanged."""
import argparse
from fractions import Fraction
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def reconcile(r):
    if r['status']!='simulated':return dict(status=r['status'])
    cfg=r['config'];end=r['capture_end_cycle'];horizon=r['horizon_cycle'];clock=cfg['clock_hz'];hz=cfg['scan_hz'];height=cfg['panel_height']
    complete=[];partial=[]
    for c in r['clean_full_panel_epoch_presentations']:
        epoch=c['epoch'];start=round(Fraction(epoch*clock,hz));finish=round(Fraction((epoch+1)*clock,hz))
        last=round(Fraction((epoch*height+height-1)*clock,hz*height))
        assert c['epoch_start_cycle']==start and c['validated_at_cycle']==last
        assert c['id']==c['epoch_frame_id']
        row=dict(id=c['id'],epoch=epoch,buffer_index=c['buffer_index'],epoch_start_cycle=start,
                 epoch_finish_cycle=finish,last_line_deadline_cycle=last)
        if finish<=horizon:complete.append(row)
        else:partial.append(row)
    assert len({c['id'] for c in complete})==len(complete)
    strict_start=[p['id'] for p in r['presented'] if p['at_cycle']<end]
    strict_finish=[p['id'] for p in complete if p['epoch_finish_cycle']<end]
    lo=clock//4;hi=end-clock//4;seconds=max(0,(hi-lo)/clock)
    steady_start=[p['id'] for p in complete if lo<=p['epoch_start_cycle']<hi]
    steady_finish=[p['id'] for p in complete if lo<=p['epoch_finish_cycle']<hi]
    return dict(status='reconciled',strict_logical_epoch_start_ids=strict_start,
        strict_completed_clean_panel_epoch_ids=strict_finish,
        complete_clean_epoch_ids=[p['id'] for p in complete],complete_clean_epochs=complete,
        excluded_partial_epoch_ids=[p['id'] for p in partial],steady_window_cycles=[lo,hi] if seconds else None,
        steady_seconds=seconds,steady_clean_epoch_start_ids=steady_start,
        steady_clean_epoch_finish_ids=steady_finish,
        steady_clean_epoch_start_ids_per_second=None if not seconds else len(steady_start)/seconds,
        steady_clean_epoch_finish_ids_per_second=None if not seconds else len(steady_finish)/seconds)

def build():
    path=HERE/'results.json';d=json.loads(path.read_text());rows=[]
    for group in ['cases','phase_cases']:
        for case in d[group]:rows.append(dict(group=group,name=case['name'],result=reconcile(case['result'])))
    return dict(results_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        analyzer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,
        boundary='Capture/steady windows are halfopen. Logicalstrict usesactualpanel epochstart, notprefetchcommit. Cleanstrict completionrequiresfullpanelexpochfinish<captureend; eventual requiresfinish<=horizon. All480line deadlines andsameFB/sourceID were assertedbyfrozenmodel beforestoredcleanqualification.',
        scope='Untimed retained-evidence reconciliation; sourceIDs are traffic-template labels, not decoded distinctgameplayimages orhardwareproof.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();d=build();out=HERE/'epoch-boundaries.json'
    if args.check:assert json.loads(out.read_text())==d
    else:out.write_text(json.dumps(d,indent=2)+'\n')
    print('PASS:actualpanel epochstart/finish separated;halfopen strict andcomplete-horizon clean counts;result/analyzerhashes;noearlyprefetchFPSclaim')
if __name__=='__main__':main()
