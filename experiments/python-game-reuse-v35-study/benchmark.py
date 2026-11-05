#!/usr/bin/env python3
"""Rotated paired timings of all 184 causal fields retained by v34."""
from pathlib import Path
import hashlib
import importlib.util
import json
import statistics
import sys
import time
import zlib
import numpy as np
import model
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CONTROL=HERE.parent/'python-game-controller-v34-study'
h=model.load('reuse35_controller_helpers',CONTROL/'helpers.py')


def digest(data):return hashlib.sha256(data).hexdigest()
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True)
    (HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))

def source_pins():
    paths={ROOT/k for k in h.pins()}
    paths.add(CONTROL/'results.json')
    paths.update(HERE.glob('*.py'))
    paths.add(HERE/'README.md')
    return {p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(paths)}

def extract(packet):
    meta=h.m.parse_metadata(packet)
    start=h.m.HEADER.size+meta['qmap_bytes']
    data=packet[start:start+meta['vector_bytes']]
    bs=meta['block_size'];w,ht=meta['width'],meta['height']
    vectors=model.decoder.unpack_gm27(data,(w+bs-1)//bs,(ht+bs-1)//bs)
    return vectors,data

def replace_component(packet,component):
    meta=h.frame.parse_metadata(packet);start=h.frame.HEADER.size+meta['qmap_bytes']
    fields=list(h.frame.HEADER.unpack_from(packet));fields[13]=len(component)
    return h.frame.seal(h.frame.HEADER.pack(*fields)+packet[h.frame.HEADER.size:start]+component+packet[start+meta['vector_bytes']:-4])

def stats(values):
    a=np.asarray(values,dtype=float)
    return dict(mean_ms=float(a.mean()),median_ms=float(np.median(a)),p95_ms=float(np.percentile(a,95)),maximum_ms=float(a.max()))

def main():
    pins=source_pins();inputs=h.load(CONTROL/'results.json');rows=[];repeats=3
    # Warm both code paths using a real component, without storing warm timings.
    warm=next(c for c in inputs['cases'] if c['policy']=='hierarchy_full')['rows'][1]
    pa=next(a for a in warm['attempts'] if a['kind']=='half32')
    ca=next(a for a in warm['attempts'] if a['kind']=='child')
    p,pb=extract(h.raw(pa['base_packet']));c,cb=extract(h.raw(ca['base_packet']))
    model.old.pack(p,c,720,480);model.pack(p,c,720,480,parent_bytes=pb,child_bytes=cb)
    for case in inputs['cases']:
        if case['policy']=='control':continue
        for source in case['rows']:
            if source['key']:continue
            variants=[a for a in source['attempts'] if a['kind'].endswith('_HM34')]
            first=variants[0];bg=first['background']
            pa=next(a for a in source['attempts'] if a['kind']=='half32' and a['background']==bg)
            ca=next(a for a in source['attempts'] if a['kind']=='child' and a['background']==bg)
            p,pb=extract(h.raw(pa['base_packet']));c,cb=extract(h.raw(ca['base_packet']))
            old_packet=h.raw(first['base_packet']);meta=h.frame.parse_metadata(old_packet)
            start=h.frame.HEADER.size+meta['qmap_bytes']
            old_component=old_packet[start:start+meta['vector_bytes']]
            times={'old':[],'new':[]};pairs=[];new_info=None
            for iteration in range(repeats):
                order=('old','new') if (len(rows)+iteration)%2==0 else ('new','old')
                pair={}
                for kind in order:
                    begin=time.perf_counter_ns()
                    if kind=='old':out,info=model.old.pack(p,c,720,480,return_info=True)
                    else:out,info=model.pack(p,c,720,480,parent_bytes=pb,child_bytes=cb,return_info=True);new_info=info
                    elapsed=(time.perf_counter_ns()-begin)/1e6
                    assert out==old_component
                    times[kind].append(elapsed);pair[kind]=elapsed
                pairs.append(dict(order=list(order),**pair))
            assert new_info['candidates']==source['component_info']['candidates']
            np.testing.assert_array_equal(model.decoder.unpack(old_component,720,480),c)
            wrapped=[]
            for variant in variants:
                original=h.raw(variant['base_packet'])
                legacy_kind=variant['kind'][:-5]
                legacy=next(a for a in source['attempts'] if a['kind']==legacy_kind and a['background']==variant['background'])
                legacy_packet=h.raw(legacy['base_packet']);vf,vbytes=extract(legacy_packet)
                np.testing.assert_array_equal(vf,c);assert vbytes==cb
                _,parent_bytes=extract(h.raw(next(a for a in source['attempts'] if a['kind']=='half32' and a['background']==variant['background'])['base_packet']))
                assert parent_bytes==pb
                # Actual GM34 serializer, with independently field-bound old Motion.
                motion=h.frame.Motion(h.frame._OWNER,720,480,c.tobytes(),out)
                result=h.frame.wrap(legacy_packet,motion)
                assert result==original
                assert replace_component(original,out)==original
                wrapped.append(dict(kind=variant['kind'],background=variant['background'],
                                    frame=blob(result),original_base_packet=variant['base_packet'],
                                    legacy_base_packet=legacy['base_packet'],
                                    reconstructed_tag=variant['reconstructed_tag'],
                                    hybrid_sha256=variant['hybrid_sha256']))
            analysis=source['analyses']
            row=dict(scene=case['scene'],policy=case['policy'],id=source['id'],
                     original_component_info=source['component_info'],new_component_info=new_info,
                     parent_bytes=blob(pb),child_bytes=blob(cb),component=blob(old_component),
                     parent_array_sha256=digest(p.tobytes()),child_array_sha256=digest(c.tobytes()),
                     parent_base_packet=pa['base_packet'],child_base_packet=ca['base_packet'],
                     already_charged_analysis=dict(parent_ms=analysis['half32']['wall_ms'],child_ms=analysis['child']['wall_ms'],
                          parent_motion_map=analysis['half32']['work']['motion_map'],child_motion_map=analysis['child']['work']['motion_map']),
                     original_paid_policy_ms=source['paid_policy_ms'],original_component_pack_verify_ms=source['component_ms'],
                     paired_timings_ms=pairs,old_median_ms=statistics.median(times['old']),new_median_ms=statistics.median(times['new']),variants=wrapped)
            rows.append(row)
        print(json.dumps(dict(scene=case['scene'],policy=case['policy'],completed_fields=len(rows))),flush=True)
    assert len(rows)==184 and sum(len(r['variants']) for r in rows)==368
    summary=[]
    for scene,policy in sorted({(r['scene'],r['policy']) for r in rows}):
        rr=[r for r in rows if (r['scene'],r['policy'])==(scene,policy)]
        old=[r['old_median_ms'] for r in rr];new=[r['new_median_ms'] for r in rr]
        summary.append(dict(scene=scene,policy=policy,fields=len(rr),frame_variants=sum(len(r['variants']) for r in rr),
                            old=stats(old),new=stats(new),sum_component_speedup=sum(old)/sum(new),
                            paired_median_saved_ms=statistics.median(a-b for a,b in zip(old,new)),
                            already_charged_parent_child_analysis_ms=sum(r['already_charged_analysis']['parent_ms']+r['already_charged_analysis']['child_ms'] for r in rr),
                            original_paid_policy_ms=sum(r['original_paid_policy_ms'] for r in rr),
                            new_mode_counts={str(mode):sum(r['new_component_info']['selected_mode']==mode for r in rr) for mode in range(3)}))
    assert source_pins()==pins
    result=dict(schema='gamebub-reuse-v35',parent_commit='c50df93e313c9402c3741e5f6c921ee40e6f10a3',source_sha256=pins,
                input_controller_results_sha256=digest((CONTROL/'results.json').read_bytes()),
                repeats=repeats,fields=184,frame_variants=368,rows=rows,summary=summary,
                scope=['Exact bytes/pixels component study; no controller integration or changed pixels.',
                       'Alternating order per iteration; outer timings include validation, setup, canonical cache cost planning, all HM34 size costs, winning bit writes and CRC.',
                       'Original GM27 caches extracted directly at HEADER+qmap_bytes from matching half32 and legacy child frame; arrays syntax-decoded before paired timings for both encoders.',
                       'Original map generation is already charged in each retained root row parent and child analysis; no full-sender speedup claim.',
                       'Every GM34 legacy residual/qmap variant rewrapped by actual frozen frame serializer and asserted byte-identical to original.',
                       'No hardware, physical30fps, heldout content or RF/QSPI claim.'])
    (HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
    print(json.dumps(dict(fields=184,frame_variants=368,summary=summary)),flush=True)

if __name__=='__main__':main()
