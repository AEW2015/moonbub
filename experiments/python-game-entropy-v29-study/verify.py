"""Verify retained size proofs, source pixels, exact old refs and replayed choices."""
from pathlib import Path
import hashlib
import json
import numpy as np
import model as e

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];m=e.m
b=m.load_module('entropy29_benchmark_verify',HERE/'benchmark.py');n=b.n

def main():
    data=json.loads((HERE/'results.json').read_text())
    for p,h in data['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    inputs=json.loads((n.V24/'results.json').read_text())['inputs'];frames=checks=0
    for case in data['cases']:
        inp=next(v for v in inputs if v['scene']==case['scene']);ref=None
        for r,srcrow in zip(case['rows'],inp['rows']):
            if r['key']:ref=None
            old=n.raw(r['baseline_packet'],HERE);packet=n.raw(r['candidate_packet'],HERE)
            oldout,oldmeta=m.decode(old,ref,expected_epoch=25,expected_reference_id=None if r['key'] else r['reference_id'])
            out,meta=m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if r['key'] else r['reference_id'])
            assert oldmeta['reconstructed_tag'].hex()==r['baseline_tag'] and meta['reconstructed_tag'].hex()==r['candidate_tag']
            source=n.source(srcrow);original=n.original(srcrow)
            for plane in range(3):assert int(((source[plane].astype(np.int64)-out[plane])**2).sum())<=int(((source[plane].astype(np.int64)-oldout[plane])**2).sum())
            p=m.base.analyze_planes(source,ref,epoch=25,frame_id=r['id'],reference_id=r['reference_id'],block_size=32,
                motion_mode='zero' if r['selected_kind']=='zero' else 'block',motion_precision='half',penalty=0)
            q=m.roi.declared_map(720,480,n.ROIS,8,r['background'])
            replay,out2,w=e.encode_prepared(p,q);assert replay==packet
            for a,c in zip(out,out2):np.testing.assert_array_equal(a,c)
            # Work ledger must preserve exact non-timing candidate decisions.
            assert w['planes']==r['work']['planes'] and w['ec26_size_counter_calls']==r['work']['ec26_size_counter_calls']
            assert len(packet)<=len(old) and len(packet)+r['hud_bytes']+60==r['complete_bytes']<=49152
            patches=tuple(original[y:y+h,x:x+w] for x,y,w,h in n.RECTS)
            for result,expected in ((oldout,r['baseline_hybrid']),(out,r['candidate_hybrid'])):
                assert n.metric(original,n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(result)),patches))==expected
            coeff=m.parse(old)['coefficients']
            for c in r['counter_checks']:
                bw=90 if c['plane']==0 else 45
                plan=e.plan_coefficients(coeff[c['plane']],bw,layout=c['layout'])
                assert plan['bytes']==c['bytes']==len(e.ec.encode_coefficients(coeff[c['plane']],bw,layout=c['layout']))
                checks+=1
            ref=oldout;frames+=1
    print(json.dumps(dict(frames=frames,exact_counter_checks=checks,source_pins=len(data['source_sha256']),all_source_SSE_and_policy_choices_replayed=True,GM27_wire_unchanged=True,hardware_30fps_proven=False)))
if __name__=='__main__':main()
