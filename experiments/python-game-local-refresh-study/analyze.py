#!/usr/bin/env python3
"""Read-only matched-ID refresh/cadence analysis; no new timed work."""
import argparse
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    p=HERE/'results.json';d=json.loads(p.read_text());cases={c['profile']:c for c in d['cases']}
    global_=cases['global_refresh30'];local=cases['local_refresh30'];repeat=cases['local_refresh30_repeat']
    assert local['manifest']==repeat['manifest']==global_['manifest']
    assert local['manifest']['unique_frame_count']==180
    rows=[]
    for c in (global_,local,repeat,cases['local_initial_only']):
        r=c['result'];commits={x['id']:x for x in r['commits']};presented=r['presented']
        window=[x for x in presented if 500<=x['at_ms']<5500];ids=[x['id'] for x in window]
        assert len(ids)==len(set(ids))==len({commits[i]['rgb_sha256'] for i in ids})==len({c['manifest']['frame_sha256'][i] for i in ids})
        gaps=[b['at_ms']-a['at_ms'] for a,b in zip(window,window[1:])]
        assert all(commits[i]['selected_exact_pixels']==21120 and commits[i]['selected_ui_mismatches']==0 for i in commits)
        keys=[x for x in r['packets'] if x['admitted'] and x['key']]
        local_continuity=[]
        if r['config']['refresh_policy']=='local':
            for key in keys:
                candidates=[x for x in r['packets'] if x['id']>key['id'] and x['encode_started_ms']<key['released_ms']]
                for x in candidates:
                    assert x['refresh_deferred'] and not x['key'] and x['reference_bank']==1
                if candidates:local_continuity.append(dict(key_id=key['id'],bank1_P_ids=[x['id'] for x in candidates]))
        rows.append(dict(profile=c['profile'],strict=r['presented_strict'],eventual=r['presented_eventual'],steady_ids=ids,
            distinct_input_and_decoded_window_ids=len(ids),diagnostic_window_seconds=5,diagnostic_ids_per_second=len(ids)/5,
            maximum_in_window_gap_ms=max(gaps),maximum_presented_age_ms=max(x['age_ms'] for x in presented),
            startup_or_other_dropped_ids=[x['id'] for x in r['drops']],key_ids=[x['id'] for x in keys],
            key0_pending_bank1_continuity=local_continuity))
    aa={x['id']:x for x in global_['result']['commits']};bb={x['id']:x for x in local['result']['commits']};common=sorted(aa.keys()&bb.keys())
    qa=sum(aa[i]['active_rgb565_mse'] for i in common)/len(common);qb=sum(bb[i]['active_rgb565_mse'] for i in common)/len(common)
    for field in ('presented','drops'):
        assert [x['id'] for x in local['result'][field]]==[x['id'] for x in repeat['result'][field]],field
    assert [x['packet_sha256'] for x in local['result']['packets'] if x['admitted']]==[x['packet_sha256'] for x in repeat['result']['packets'] if x['admitted']]
    assert local['result']['presented_eventual']==repeat['result']['presented_eventual']==178
    assert [p['id'] for p in local['result']['drops']]==[1,2]
    return dict(results_sha256=sha(p),analyzer_sha256=sha(HERE/'analyze.py'),profiles=rows,
        common_decoded_ids=common,common_decoded_source_rgb565_mse_global=qa,common_decoded_source_rgb565_mse_local=qb,
        source_quality_delta_on_common_ids=qb-qa,
        local_repeat_same_packet_hashes_and_presented_ids=True,local_repeat_same_presented_times=local["result"]["presented"]==repeat["result"]["presented"],
        input_schedule_fps=30,distinct_native_source_ids=180,
        scope='The151ID/5s rolling count isphase/catchup under30scheduledIDs/s, not>30capture or longrunphysicalfps. Gaps/ages retained. Fixedmap/fullUI but histories differ; notlosslesssame-output bytecomparison. Reusedprecompressedregression, notfreshvalidation. NojointESP32/FPGA/nativeCPUproof.')
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();d=build();path=HERE/'cadence-analysis.json'
    if a.check:assert json.loads(path.read_text())==d
    else:path.write_text(json.dumps(d,indent=2)+'\n')
    print('PASS:matched native IDs/sourcequality/exactUI,178of180localrepeat,bank1continuity,window-phase/gap limits;nohardwareproof')
if __name__=='__main__':main()
