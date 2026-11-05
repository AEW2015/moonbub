"""Matched-reference source experiment: no causal claim for alternative history."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import time
import zlib
import numpy as np
import model as e

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];m=e.m
n=m.load_module('entropy29_native',HERE.parent/'python-game-native-motion-v25-study/benchmark.py')
OLD=HERE.parent/'python-game-runtime-v28-study'

def blob(data):
    stored=zlib.compress(data,9);name='objects/'+hashlib.sha256(stored).hexdigest()+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(stored)
    return dict(path=name,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(stored).hexdigest())

def main():
    old=json.loads((OLD/'results.json').read_text());inputs=json.loads((n.V24/'results.json').read_text())['inputs'];cases=[]
    for inp in inputs:
        prior=next(c for c in old['cases'] if c['scene']==inp['scene'] and c['policy']=='exhaustive')
        rows=[];ref=None
        for src,r in zip(inp['rows'][:12],prior['rows'][:12]):
            fid=src['id'];source=n.source(src);original=n.original(src)
            if r['key']:ref=None
            p=m.base.analyze_planes(source,ref,epoch=25,frame_id=fid,reference_id=r['reference_id'],block_size=32,
                motion_mode='zero' if r['selected_kind']=='zero' else 'block',motion_precision='half',penalty=0)
            q=m.roi.declared_map(720,480,n.ROIS,8,r['selected_background']);values={};times={}
            for label in (('baseline','exact_guard') if fid%2==0 else ('exact_guard','baseline')):
                begin=time.perf_counter_ns();values[label]=(m.encode_prepared if label=='baseline' else e.encode_prepared)(p,q)
                times[label]=(time.perf_counter_ns()-begin)/1e6
            packet,baseline,bwork=values['baseline'];candidate,out,work=values['exact_guard']
            assert packet==n.raw(r['base_packet'],OLD)
            assert len(candidate)<=len(packet)
            olddec,oldmeta=m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if r['key'] else r['reference_id'])
            decoded,meta=m.decode(candidate,ref,expected_epoch=25,expected_reference_id=None if r['key'] else r['reference_id'])
            for a,b,srcplane,oldplane in zip(out,decoded,source,baseline):
                np.testing.assert_array_equal(a,b)
                assert int(((srcplane.astype(np.int64)-a)**2).sum())<=int(((srcplane.astype(np.int64)-oldplane)**2).sum())
            patches=tuple(original[y:y+h,x:x+w] for x,y,w,h in n.RECTS)
            before=n.metric(original,n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(baseline)),patches))
            after=n.metric(original,n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(out)),patches))
            counts=[]
            for plane,coeff in enumerate(m.parse(packet)['coefficients']):
                bw=(720 if plane==0 else 360)//8
                for layout in (0,1):
                    begin=time.perf_counter_ns();plan=e.plan_coefficients(coeff,bw,layout=layout);counter_ms=(time.perf_counter_ns()-begin)/1e6
                    begin=time.perf_counter_ns();actual=e.ec.encode_coefficients(coeff,bw,layout=layout);construct_ms=(time.perf_counter_ns()-begin)/1e6
                    assert plan['bytes']==len(actual)
                    counts.append(dict(plane=plane,layout=layout,bytes=len(actual),counter_ms=counter_ms,construct_ms=construct_ms))
            rows.append(dict(id=fid,reference_id=r['reference_id'],key=r['key'],selected_kind=r['selected_kind'],background=r['selected_background'],
                baseline_packet=blob(packet),candidate_packet=blob(candidate),baseline_bytes=len(packet),candidate_bytes=len(candidate),
                hud_bytes=r['hud_bytes'],complete_bytes=len(candidate)+r['hud_bytes']+60,cap_fit=len(candidate)+r['hud_bytes']+60<=49152,
                baseline_hybrid=before,candidate_hybrid=after,times=times,work=work,counter_checks=counts,
                baseline_tag=oldmeta['reconstructed_tag'].hex(),candidate_tag=meta['reconstructed_tag'].hex()))
            ref=olddec
        s=dict(frames=len(rows),baseline_bytes=sum(r['baseline_bytes'] for r in rows),candidate_bytes=sum(r['candidate_bytes'] for r in rows),
            selected_alternative_planes=sum(r['work']['selected_alternative_planes'] for r in rows),
            baseline_mse=sum(r['baseline_hybrid']['active_squared_error'] for r in rows)/sum(r['baseline_hybrid']['active_channel_samples'] for r in rows),
            candidate_mse=sum(r['candidate_hybrid']['active_squared_error'] for r in rows)/sum(r['candidate_hybrid']['active_channel_samples'] for r in rows),
            baseline_encode_ms=sum(r['times']['baseline'] for r in rows)/len(rows),candidate_encode_ms=sum(r['times']['exact_guard'] for r in rows)/len(rows),
            all_cap_fit=all(r['cap_fit'] for r in rows),counter_checks=sum(len(r['counter_checks']) for r in rows),
            counter_ms=sum(c['counter_ms'] for r in rows for c in r['counter_checks'])/sum(len(r['counter_checks']) for r in rows),
            construct_ms=sum(c['construct_ms'] for r in rows for c in r['counter_checks'])/sum(len(r['counter_checks']) for r in rows))
        cases.append(dict(scene=inp['scene'],rows=rows,summary=s));print(json.dumps(dict(scene=inp['scene'],summary=s)),flush=True)
    paths={Path(v.__file__).resolve() for v in list(sys.modules.values()) if hasattr(v,'__file__') and v.__file__ and str(Path(v.__file__).resolve()).startswith(str(ROOT))}
    paths|=set(HERE.glob('*.py'))|{OLD/'results.json',n.V24/'results.json'}
    pins={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    data=dict(schema='gamebub-exact-entropy-v29',source_sha256=pins,cases=cases,
        scope=['Matched old accepted reconstructed refs; alternatives never substituted for next retained reference.',
               'Exact EC26 counter supports both layouts but GM27 selection uses block-major layout0 only.',
               'Original/pruned alternatives are bounded and perplane current-source YUV SSE guarded, RGB SSE measured separately.',
               'All policy work timed; purePython host timings and nominal rate projections are not native/hardware30fps.'])
    (HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
