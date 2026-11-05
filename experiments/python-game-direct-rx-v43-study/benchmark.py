#!/usr/bin/env python3
"""Whole-receive paired timing; actual retained CS38 packets, fixed causal states."""
import json,platform,statistics,time
import numpy as np
import helpers as h
import receiver as direct

def fork(rx,kind):
    result=h.adapter.Receiver()if kind=='adapter'else direct.Receiver()
    src=rx.frozen if kind=='adapter'else rx;dst=result.frozen if kind=='adapter'else result
    dst.ref,dst.rid,dst.hud,dst.last=src.ref,src.rid,src.hud,src.last
    return result

def equal(a,b):
    for left,right in zip(a[0],b[0],strict=True):np.testing.assert_array_equal(left,right)
    for left,right in zip(a[1],b[1],strict=True):
        assert tuple(left['rect'])==tuple(right['rect']);np.testing.assert_array_equal(left['words'],right['words'])
    for name in('key','frame_id','reference_id','reference_tag','output_tag','base_tag','block_size'):
        assert a[2][name]==b[2][name],name
    for name in('qmap','vectors'):np.testing.assert_array_equal(a[2][name],b[2][name])
    for left,right in zip(a[2]['coefficients'],b[2]['coefficients'],strict=True):np.testing.assert_array_equal(left,right)
    assert a[2]['hud']==b[2]['hud']and a[3]==b[3]

def summary(rows):
    means={key:statistics.mean(row['paired_median_ms'][key]for row in rows)for key in('adapter','direct')}
    return dict(frames=len(rows),complete_bytes=sum(row['complete_bytes']for row in rows),
        mean_paired_median_ms=means,direct_to_adapter_ratio=means['direct']/means['adapter'],
        receive_time_reduction_percent=100*(1-means['direct']/means['adapter']),
        dispatch_counts=[sum(row['decode_work']['dispatch_counts'][i]for row in rows)for i in range(7)],
        arithmetic_planes=sum(row['binary_planes']for row in rows))

def main():
    began=time.time();cases=[]
    for foldername in h.FOLDERS:
        folder=h.HERE.parent/foldername;archive=h.load(folder/'results.json')
        for source_case in archive['cases']:
            old=h.adapter.Receiver();new=direct.Receiver();rows=[]
            for source_row in source_case['rows']:
                packet=h.raw(source_row['packet'],folder);fid=source_row['id']
                timings={'adapter':[],'direct':[]};orders=[]
                for rep in range(3):
                    order=['adapter','direct']if(fid+rep)%2==0 else['direct','adapter'];orders.append(order)
                    forks={'adapter':fork(old,'adapter'),'direct':fork(new,'direct')};outputs={}
                    for kind in order:
                        start=time.perf_counter_ns();outputs[kind]=forks[kind].receive(packet)
                        timings[kind].append((time.perf_counter_ns()-start)/1e6)
                    equal(outputs['adapter'],outputs['direct'])
                    # Publication is accepted only after both complete paths agree.
                    accepted_old,accepted_new=forks['adapter'],forks['direct'];result=outputs['direct']
                old,new=accepted_old,accepted_new;pixels,patches,meta,count=result
                assert h.m.C.reference_tag(pixels).hex()==source_row['normalized_tag']
                display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),tuple(p['words']for p in patches))
                assert h.f.f.n.digest(display)==source_row['display_sha256']
                row=dict(id=fid,source_packet=source_row['packet'],source_packet_sha256=h.digest(packet),packet=h.blob(packet),
                    complete_bytes=len(packet),normalized_tag=source_row['normalized_tag'],display_sha256=source_row['display_sha256'],
                    binary_planes=count,paired_timing_ms=timings,paired_order=orders,
                    paired_median_ms={key:statistics.median(values)for key,values in timings.items()},decode_work=meta['decode_work'])
                rows.append(row)
                if fid%20==0:print(json.dumps(dict(source=foldername,scene=source_case['scene'],frame=fid,timing=row['paired_median_ms'])),flush=True)
            case=dict(source_folder=foldername,scene=source_case['scene'],rows=rows,summary=summary(rows));cases.append(case)
            print(json.dumps(dict(source=foldername,scene=source_case['scene'],summary=case['summary'])),flush=True)
    allrows=[r for c in cases for r in c['rows']];assert len(allrows)==577
    result=dict(schema='gamebub-direct-rx-v43',source_sha256=h.pins(),cases=cases,summary=summary(allrows),
        environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        scope=dict(clock='Entire receive(packet), including validation, entropy decode, prediction, Q14 reconstruction, normalization, HUD validation. Constructors/state forks, comparisons, output metrics and I/O excluded identically.',
            repetitions=3,order='adapter/direct if (frame_id+repeat)%2==0; reverse otherwise',
            change='Eliminate proof-adapter entropy planning/construction and synthetic CS37 rebuilding; keep original prediction, reconstruction and HUD primitives.',
            ownership='Read-only full coefficient and normalized YUV arrays plus privately owned read-only HUD words. Full arrays remain; this is Python host timing, not hardware memory/throughput proof.',
            baseline_extra_validation='Frozen proof adapter constructs converted CS37 and parses it before the frozen receive path parses again; direct receive validates original CS38 once.',
            elapsed_campaign_seconds=time.time()-began))
    (h.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']),flush=True)
if __name__=='__main__':main()
