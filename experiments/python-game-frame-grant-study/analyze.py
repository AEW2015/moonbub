#!/usr/bin/env python3
"""Untimed policy, ownership and actual selected-UI coverage reconciliation."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def avg(values):return None if not values else sum(values)/len(values)
def coverage(case):
    r=case['result'];requested=[tuple(x) for x in r['config']['ui_rectangles']];rows=[]
    for c in r['commits']:
        selected=[tuple(p['rect']) for p in c['info']['patches']];omitted=[x for x in requested if x not in selected]
        assert all(x in requested for x in selected) and len(set(selected))==len(selected)
        assert c['selected_exact_pixels']==sum(w*h for _,_,w,h in selected) and c['selected_ui_mismatches']==0
        rows.append(dict(id=c['id'],requested_rectangles=requested,selected_rectangles=selected,omitted_rectangles=omitted,
            requested_words=sum(w*h for _,_,w,h in requested),selected_words=c['selected_exact_pixels'],
            omitted_words=sum(w*h for _,_,w,h in omitted),selected_word_mismatches=c['selected_ui_mismatches']))
    return dict(profile=case['profile'],decoded_count=len(rows),full_declared_ui_frames=sum(not x['omitted_rectangles'] for x in rows),
        partial_declared_ui_frames=sum(bool(x['omitted_rectangles']) for x in rows),rows=rows)
def comparison(a,b,label):
    ra,rb=a['result'],b['result'];pa={p['id']:p for p in ra['packets']};pb={p['id']:p for p in rb['packets']}
    ca={p['id']:p for p in ra['commits']};cb={p['id']:p for p in rb['commits']};ids=sorted(ca.keys()&cb.keys())
    assert a['manifest']['frame_sha256']==b['manifest']['frame_sha256']
    differences={k:[ra['config'][k],rb['config'][k]] for k in ra['config'] if ra['config'][k]!=rb['config'][k]}
    if label=='FINISHED-overlap':assert set(differences)=={'frame_finish_ack'}
    same_wire=[i for i in ids if pa[i]['packet_sha256']==pb[i]['packet_sha256']]
    return dict(comparison=label,left=a['profile'],right=b['profile'],config_differences=differences,
        shared_source_ids=ids,shared_packet_identical_ids=same_wire,
        left_matched_rgb565_mse=avg([ca[i]['active_rgb565_mse'] for i in ids]),right_matched_rgb565_mse=avg([cb[i]['active_rgb565_mse'] for i in ids]),
        left_eventual=ra['presented_eventual'],right_eventual=rb['presented_eventual'],
        left_diagnostic_ids_per_second=ra['diagnostic_ids_per_second'],right_diagnostic_ids_per_second=rb['diagnostic_ids_per_second'],
        meaning='Same historicalfixedstagecosts andsameinput; controllerpolicyaltersadmitted IDs/referencehistory. MatchedIDsdoNOTimplysamepredictionhistory. No compressionquality/nativeperformancegain claimed.')
def build():
    d=json.loads((HERE/'results.json').read_text());cases=d['cases'];by={c['profile']:c for c in cases}
    native=[c for c in cases if c['source']=='native-regression'];cov=[coverage(c) for c in cases]
    hashes=set().union(*(set(c['manifest']['frame_sha256']) for c in native));sourcefiles={c['manifest']['source']:c['manifest']['source_sha256'] for c in native}
    a=by['mass-effect-2600/fixed_serialized_grants5'];b=by['mass-effect-2600/fixed_grants5']
    comparisons=[comparison(a,b,'FINISHED-overlap'),comparison(by['mass-effect-2600/fixed_base6'],by['mass-effect-2600/fixed_partition5'],'mailbox-partition-only')]
    stopped=[]
    for c in cases:
        r=c['result'];f=r['frame_grants']
        if f and f['safe_stop']:
            assert f['peak_receiver']<=2 and f['peak_host']<=2 and r['gateway']['peak_tokens']<=5 and r['gateway']['peak_mailbox']<=6
            stopped.append(dict(profile=c['profile'],reason=f['safe_stop_reason'],receiver_owned=len(f['receiver_owned']),host_owned=len(f['host_owned']),
                request_pending=f['pending'],packet_tokens=r['gateway']['outstanding_tokens'],unresolved_capture_ids=r['unresolved_ids'],
                interpretation='Explicitboundedstopwithunknownownershipretained;notfullydrainedorrecovered'))
    assert len(stopped)==3 and len(cases)==12 and sum(c['result']['capture_count'] for c in cases)==790
    primary=[r for r in cov if r['profile'].startswith('mass-effect-2600/')]
    assert all(r['partial_declared_ui_frames']==0 for r in primary)
    secondary=[r for r in cov if r['profile'].startswith('mass-effect-7200/')]
    assert all(r['partial_declared_ui_frames']>0 for r in secondary)
    return dict(results_sha256=sha(HERE/'results.json'),analyzer_sha256=sha(HERE/'analyze.py'),case_count=len(cases),capture_events=790,
        native_unique_acquisitions=len(hashes),native_source_files=sourcefiles,native_profile_count=len(native),
        fixed_cost_comparisons=comparisons,ui_coverage=cov,explicit_safe_stops=stopped,
        scope='Retainedposthocanalysis; selectedUIisexact,notfullsourcelossless. 7200sometimesomitsfourthdeclaredHUDpatchunder49152completecap. No newdecode/timingbenchmark. Existing29.88fpssourcehypotheticallyscheduled30IDs/s; nativewindows2seconds,syntheticwindowonly66.7msandnotFPSproof. NoESPISA/RForFPGAfit/physical30fps qualification.')
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();out=build();path=HERE/'analysis.json'
    if args.check:assert json.loads(path.read_text())==json.loads(json.dumps(out))
    else:path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print('PASS:fixedcostFINISHEDoverlap/partitioncomparison,perdecodedUIomissions,180nativeacquisitions,boundedunknowncontrolstops;nohardwarefpsclaim')
if __name__=='__main__':main()
