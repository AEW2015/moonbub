#!/usr/bin/env python3
"""Untimed retained joint-controller delivery/quality reconciliation."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def mean(values):
    return None if not values else sum(values)/len(values)

def quality(commits,ids):
    return mean([commits[i]['active_rgb565_mse'] for i in ids]) if ids and all('active_rgb565_mse' in commits[i] for i in ids) else None

def ingress_diagnosis(r):
    packets={p['id']:p for p in r['packets']}
    errors=Counter(e for p in packets.values() for e in p.get('feed_errors',[]))
    affected=sorted(i for i,p in packets.items() if 'GF03 busy' in p.get('feed_errors',[]))
    nacks=sorted(d['id'] for d in r['drops'] if d['reason']=='receiver_nack')
    feeds={i:[w for w in r['work'] if w['stage']=='fpga_ingress_feed' and w['id']==i] for i in packets}
    examples=[]
    for i in affected[:1]:
        if not feeds[i]:continue
        first=min(w['start_ms'] for w in feeds[i])
        decoding=[];waiting=[]
        for j,p in packets.items():
            begin=p.get('decode_started_ms');done=p.get('decode_done_ms')
            if begin is not None and done is not None and begin<=first<done:
                decoding.append(dict(owner_id=j,decode_started_ms=begin,decode_done_ms=done,remaining_ms=done-first))
            if (j!=i and feeds[j] and not p.get('feed_errors') and begin is not None and first<begin
                    and min(w['start_ms'] for w in feeds[j])<=first):
                waiting.append(dict(owner_id=j,first_feed_start_ms=min(w['start_ms'] for w in feeds[j]),decode_started_ms=begin,decode_done_ms=done))
        examples.append(dict(affected_owner_id=i,first_feed_start_ms=first,feed_call_count=len(feeds[i]),
            busy_feed_count=packets[i]['feed_errors'].count('GF03 busy'),decoding_at_first_feed=decoding,
            nonrejecting_other_frame_feed_started_before_first_feed_decode_starts_later=waiting,
            timestamp_scope='Per-frame error strings are retained without packet indices/timestamps. First feed and decoder overlap are exact work/packet records; the exact failing feed timestamp is not recoverable from these records.'))
    return dict(feed_errors_by_reason=dict(sorted(errors.items())),total_rejected_feed_operations=sum(errors.values()),
        busy_feed_operations=errors['GF03 busy'],busy_affected_owner_ids=affected,receiver_nack_owner_ids=nacks,
        receiver_nack_count=len(nacks),nack_ids_with_busy=sorted(set(nacks)&set(affected)),
        nack_ids_without_busy=sorted(set(nacks)-set(affected)),busy_ids_without_receiver_nack=sorted(set(affected)-set(nacks)),
        observed_peak_ingress_slots=r['peak_ingress'],examples=examples,
        scope='GF03 busy is a retained ingress rejection, not an AR03 entropy error. Feed-operation rejection counts and terminal frame NACK counts differ. Packet-consumed credits do not grant frame ingress capacity. No per-feed slot-state trace is retained; partial-frame occupancy after rejection is a mechanism to test, not proven by these summaries.')

def describe(case):
    r=case['result'];manifest=case['manifest'];packets={p['id']:p for p in r['packets']};commits={p['id']:p for p in r['commits']}
    presented=r['presented'];ids=[p['id'] for p in presented];decoded_ids=sorted(commits)
    end=r['capture_window_ms'][1];strict=[p['id'] for p in presented if p['at_ms']<end]
    assert len(set(ids))==len(ids)==r['presented_eventual']
    assert len(strict)==r['presented_strict']
    assert sorted(ids+[p['id'] for p in r['drops']])==list(range(r['capture_count']))
    assert all(p['id'] in commits and packets[p['id']]['committed'] for p in presented)
    assert all(commits[i]['selected_ui_mismatches']==0 for i in decoded_ids)
    window=r['steady_window_ms']
    steady=[] if window is None else [p for p in presented if window[0]<=p['at_ms']<window[1]]
    steady_ids=[p['id'] for p in steady]
    all_gaps=[b['at_ms']-a['at_ms'] for a,b in zip(presented,presented[1:])]
    steady_gaps=[b['at_ms']-a['at_ms'] for a,b in zip(steady,steady[1:])]
    input_hashes=manifest['frame_sha256']
    def unique_input(subset):return len({input_hashes[i] for i in subset})
    def unique_decoded(subset):return len({commits[i]['rgb_sha256'] for i in subset})
    source_unique=len(set(input_hashes))
    if case['source']=='native-regression':
        assert len(input_hashes)==source_unique==r['capture_count']==90
        assert unique_input(ids)==len(ids)
    seconds=None if window is None else (window[1]-window[0])/1000
    rate=None if seconds is None or seconds==0 else len(steady_ids)/seconds
    assert rate==r['diagnostic_ids_per_second'] or (rate is not None and abs(rate-r['diagnostic_ids_per_second'])<1e-9)
    rejected=[p['id'] for p in r['packets'] if not p['committed']]
    for i in rejected:
        assert not any(w['id']==i for w in r['gateway']['wire'])
        assert not any(f['kind']=='ack_applied' and f['id']==i for f in r['feedback'])
    build_rows=[w for w in r['work'] if w['stage']=='candidate_build']
    rejected_build=[w for w in build_rows if w['id'] in rejected]
    assert all(w['service_ms']>=0 for w in rejected_build)
    return dict(profile=case['profile'],source=case['source'],capture_ids=r['capture_count'],unique_source_hashes=source_unique,
        built_ids=sorted(packets),committed_ids=sorted(i for i,p in packets.items() if p['committed']),precommit_rejected_ids=rejected,
        paid_build_ms=sum(w['service_ms'] for w in build_rows),paid_precommit_rejected_build_ms=sum(w['service_ms'] for w in rejected_build),
        decoded_ids=decoded_ids,unique_decoded_hashes=unique_decoded(decoded_ids),
        strict_presented_ids=strict,eventual_presented_ids=ids,unique_presented_input_hashes=unique_input(ids),unique_presented_decoded_hashes=unique_decoded(ids),
        diagnostic_window_ms=window,diagnostic_window_seconds=seconds,diagnostic_presented_ids=steady_ids,
        diagnostic_unique_input_hashes=unique_input(steady_ids),diagnostic_unique_decoded_hashes=unique_decoded(steady_ids),
        diagnostic_ids_per_second=rate,maximum_all_presentations_gap_ms=max(all_gaps,default=None),maximum_in_window_gap_ms=max(steady_gaps,default=None),
        first_presented_at_ms=None if not presented else presented[0]['at_ms'],maximum_presented_age_ms=max((p['age_ms'] for p in presented),default=None),
        mean_decoded_source_rgb565_mse=quality(commits,decoded_ids),mean_presented_source_rgb565_mse=quality(commits,ids),
        decoded_selected_word_counts=sorted({p['selected_exact_pixels'] for p in commits.values()}),
        selected_word_mismatches=sum(p['selected_ui_mismatches'] for p in commits.values()),
        dropped_source_ids=[p['id'] for p in r['drops']],drops_by_reason=r['drops_by_reason'],
        ingress_diagnosis=ingress_diagnosis(r),
        packet_credit_counters=r['gateway']['counters'],forward_ipv4_udp_bytes=r['forward_ipv4_udp_bytes'],reverse_ipv4_udp_bytes=r['reverse_ipv4_udp_bytes'])

def compare(left,right):
    assert left['source']==right['source']=='native-regression'
    assert left['manifest']['frame_sha256']==right['manifest']['frame_sha256']
    a,b=left['result'],right['result'];ca={c['id']:c for c in a['commits']};cb={c['id']:c for c in b['commits']}
    pa={p['id']:p for p in a['packets']};pb={p['id']:p for p in b['packets']}
    common=sorted(ca.keys()&cb.keys());presented=sorted({p['id'] for p in a['presented']}&{p['id'] for p in b['presented']})
    fields=('key','promoted','reference_bank','reference_id','reference_tag','destination_bank')
    same_reference=[i for i in common if all(pa[i][k]==pb[i][k] for k in fields)]
    config_differences={k:[a['config'].get(k),b['config'].get(k)] for k in sorted(a['config'].keys()|b['config'].keys()) if a['config'].get(k)!=b['config'].get(k)}
    qa,qb=quality(ca,common),quality(cb,common);qpa,qpb=quality(ca,presented),quality(cb,presented)
    return dict(left=left['profile'],right=right['profile'],config_differences=config_differences,
        common_decoded_ids=common,common_presented_ids=presented,same_reference_and_publication_decoded_ids=same_reference,
        common_decoded_source_rgb565_mse_left=qa,common_decoded_source_rgb565_mse_right=qb,
        common_decoded_source_rgb565_mse_delta=None if qa is None or qb is None else qb-qa,
        common_presented_source_rgb565_mse_left=qpa,common_presented_source_rgb565_mse_right=qpb,
        common_presented_source_rgb565_mse_delta=None if qpa is None or qpb is None else qpb-qpa,
        same_reference_source_rgb565_mse_left=quality(ca,same_reference),same_reference_source_rgb565_mse_right=quality(cb,same_reference),
        strict_presentation_delta=b['presented_strict']-a['presented_strict'],eventual_presentation_delta=b['presented_eventual']-a['presented_eventual'],
        limitation='Same input IDs only; remeasured host costs/admission/ref histories may differ. MSE comparison is on declared matched subsets, not source-lossless or causal compression gain. Full wire totals include differing admitted work.')

def build():
    path=HERE/'results.json';d=json.loads(path.read_text());cases=d['cases']
    assert d['case_count']==len(cases)==8
    native=[c for c in cases if c['source']=='native-regression'];assert len(native)==6
    baseline=next(c for c in native if c['profile']=='unbudgeted')
    return dict(results_sha256=sha(path),analyzer_sha256=sha(HERE/'analyze.py'),
        profiles=[describe(c) for c in cases],matched_native_comparisons=[compare(baseline,c) for c in native if c is not baseline],
        source_scope='The90nativeRGBframescome from previouslyusedprecompressed29.88fpsfootageat4seconds,loadedofflineandhypotheticallyscheduled30IDs/s. ActualBOXscalingischarged; livecaptureisnotmeasured. Syntheticflat48faultframesareorderingtests,notdistinctgameplayFPS.',
        timing_scope='Untimed retained-result reconciliation. Host stage costs were measured independently per profile; ESP CPU/QSPI/FIFO/link/vblank remain assumptions. No FPGA entropy-cycle/memory/scanline timing integration, nativeexecution,RFcalibrationorphysical30fps proof.',
        count_scope='Strict presentations occur before capture endpoint; eventual include declared drain. Rolling-window ID rate is neither capture rate nor longrun cadence proof. Source-hash and decoded-hash uniqueness are separately counted. Packet-consumed PC18 and decoded-reference AF03 ACKs remain distinct.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();data=build();out=HERE/'analysis.json'
    if args.check:assert json.loads(out.read_text())==data
    else:out.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print('PASS:joint matchedsource/decoded/presented IDs,quality,gaps,ages,paidprecommitrejects and rolling-window scopes;nohardwarefpsclaim')
if __name__=='__main__':main()
