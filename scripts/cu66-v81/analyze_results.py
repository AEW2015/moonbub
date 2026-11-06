#!/usr/bin/env python3
"""Select immutable completed attempts and compare their actual simulated milestones.

Latest means attempt-name chronology, never the fastest sample. Historical
failures remain listed; no rejected/late source is converted into a success.
"""
import hashlib
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v81'
PASS='PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def stats(values):return dict(min=min(values),median=statistics.median(values),max=max(values))


def compare_control(before,after):
    count=0
    for section in ('frames','timings'):
        assert len(before[section])==len(after[section])
        for old,new in zip(before[section],after[section]):
            for key,value in old.items():
                if key=='native_hud_prepare_wall_ns':continue
                assert new[key]==value,(section,old.get('fid'),key,value,new[key])
                count+=1
    for key,value in before['summary'].items():
        if key=='trace_rows':continue
        assert after['summary'][key]==value,('summary',key,value,after['summary'][key])
        count+=1
    return count


def main():
    completed=[];pending=[];failures=[];pins={};by_config={}
    for path in sorted((AREA/'system').glob('cohort*/attempt*/results.json')):
        d=json.loads(path.read_text())
        if 'wall_seconds' not in d:
            pending.append(str(path.relative_to(ROOT)));continue
        pins[str(path.relative_to(ROOT))]=sha(path)
        if d['status']!=PASS:
            failures.append(dict(path=str(path.relative_to(ROOT)),failure=d.get('failure')));continue
        key=(d['cohort'],d['prefetch'],d['requested_frames'],d['arrival_mode'],d['tac_ns'])
        by_config.setdefault(key,[]).append((path,d))
    selected={key:rows[-1]for key,rows in by_config.items()}
    for key,(path,d)in sorted(selected.items()):
        ts=d['timings'];starts=[t['first_complete_raster_start_ps']for t in ts]
        v=[t['validated_decode_model_cycles']*1e-5 for t in ts]
        assert len({t['fid']for t in ts})==len(ts)
        completed.append(dict(path=str(path.relative_to(ROOT)),cohort=d['cohort'],prefetch=d['prefetch'],
          sources=len(ts),mode=d['arrival_mode'],tac_ns=d['tac_ns'],
          full_history=len(ts)==d['cohort_available_frames'],
          validated_ms=stats(v),transaction_service_ms=stats([f['cycles']*1e-5 for f in d['frames']]),
          ingress_to_first_full_raster_end_ms=stats([(t['first_complete_raster_end_ps']-t['packet_complete_cycle']*10000)/1e9 for t in ts]),
          finite_first_to_last_source_cadence_fps=(len(ts)-1)*1e12/(starts[-1]-starts[0]),
          serial_ack_budget_passes=sum(t['met_serial_30fps_budget']for t in ts),
          strict_validated_under10ms_passes=sum(t['met_validated_under10ms']for t in ts),
          max_queue_ms=max(t['queue_cycles']for t in ts)*1e-5,
          native_pixels_checked=d['summary']['observed_pixels'],
          stream_write_accepts=sum(x['write_accepts']for x in d.get('stream_frames',[]))))
    controls=[]
    pairs=[]
    for cohort in (0,3):
        k=(cohort,2,4,'fixed30',2)
        if k in selected:
            old=ROOT/f'fpga/experiments/cu66-v80/system/cohort{cohort}-frames4-fixed30-prefetch2-tac2'
            parents=sorted(old.glob('attempt*/results.json'))
            old_path=parents[-1];before=json.loads(old_path.read_text())
            path,after=selected[k];pins[str(old_path.relative_to(ROOT))]=sha(old_path)
            controls.append(dict(kind='V80_vs_V81_mode2',cohort=cohort,before=str(old_path.relative_to(ROOT)),after=str(path.relative_to(ROOT)),exact_fields=compare_control(before,after)))
        keys=[(cohort,v,4,'fixed30',2) for v in (2,3)]
        if all(k in selected for k in keys):
            runs=[selected[k] for k in keys]
            assert runs[0][1]['source_sha256']==runs[1][1]['source_sha256'], 'controls must share all producer sources'
            rows=[]
            for c,w in zip(*(d['timings'] for _,d in runs)):
                assert c['fid']==w['fid'] and c['packet_complete_cycle']==w['packet_complete_cycle']
                rows.append(dict(fid=c['fid'],control_validated_ms=c['validated_decode_model_cycles']*1e-5,
                    wide_validated_ms=w['validated_decode_model_cycles']*1e-5,
                    wide_minus_control_ms=(w['validated_decode_model_cycles']-c['validated_decode_model_cycles'])*1e-5))
            pairs.append(dict(cohort=cohort,runs=[str(p.relative_to(ROOT)) for p,_ in runs],frames=rows,same_immutable_releases=True,same_producer_sources=True))
    histories=[]
    for cohort,n in ((0,119),(1,119),(2,119),(3,100)):
        key=(cohort,3,n,'fixed30',2)
        if key not in selected:continue
        new_path,new=selected[key]
        old_paths=sorted((ROOT/f'fpga/experiments/cu66-v80/system/cohort{cohort}-framesfull-fixed30-prefetch2-tac2').glob('attempt*/results.json'))
        old_path=old_paths[-1];old=json.loads(old_path.read_text());pins[str(old_path.relative_to(ROOT))]=sha(old_path)
        assert len(old['timings'])==len(new['timings'])==n
        diffs=[]
        for c,w in zip(old['timings'],new['timings']):
            assert c['fid']==w['fid'] and c['packet_complete_cycle']==w['packet_complete_cycle']
            diffs.append((w['validated_decode_model_cycles']-c['validated_decode_model_cycles'])*1e-5)
        histories.append(dict(cohort=cohort,sources=n,control=str(old_path.relative_to(ROOT)),wide=str(new_path.relative_to(ROOT)),
            validated_delta_ms=stats(diffs),improved=sum(x<0 for x in diffs),equal=sum(x==0 for x in diffs),regressed=sum(x>0 for x in diffs)))
    pins[str(Path(__file__).resolve().relative_to(ROOT))]=sha(Path(__file__))
    result=dict(schema='cu81-selected-simulated-comparison-v1',source_sha256=pins,
          selected_runs=completed,retained_completed_failures=failures,pending=pending,
          control_equivalence=controls,bounded_paired_comparisons=pairs,full_history_comparisons=histories,
          full_history_sources=sum(h['sources']for h in histories),
          limits=['Latest completed attempt is selected by immutable name, not best latency.',
             'Independent histories/reset boundaries are not one sustained60s or600s stream.',
             'All clock conversions assume100MHz; CPU HUD/control is zero-simtime; no liveESP32/fit/route/CDC proof.',
             'Blocked/idle counters overlap other work; differences are not a critical-path speedup decomposition.'])
    (AREA/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print('V81_COMPARISON_GENERATED selected',len(completed),'full_history_sources',result['full_history_sources'],'retained_failures',len(failures),'pending',len(pending))
    for pair in pairs:print('PAIRED',pair['cohort'],json.dumps(pair['frames']))


if __name__=='__main__':main()
