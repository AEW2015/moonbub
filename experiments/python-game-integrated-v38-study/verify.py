#!/usr/bin/env python3
"""Independent CS37 integrated sender replay and coefficient-decision proof.

The v38 encoder/analyzer/helpers are never imported. Frozen CS37 parsing and
receive math check actual packets. Frozen original source analysis, quantization,
RDO and original plane-size reversion independently recover the coefficients that
must be selected before hidden blocks are suppressed.
"""
from dataclasses import replace
from pathlib import Path
import hashlib,importlib.util,json,math,statistics,sys
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('integrated38_frozen_cs37',HERE.parent/'python-game-implicit-v37-study/verify.py')
frozen=importlib.util.module_from_spec(spec);sys.modules[spec.name]=frozen;spec.loader.exec_module(frozen)
f,m=frozen.f,frozen.m
OLD=HERE.parent/'python-game-implicit-v37-study'

def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def raw(desc,folder=HERE):return f.frozen.raw(desc,folder)

def ordered(rows,count):
    if (not isinstance(rows,list) or len(rows)!=count or any(type(r.get('id'))is not int for r in rows)
            or [r['id'] for r in rows]!=list(range(count))):raise ValueError('exact ordered causal frame cohort')

def exact_wire(packet,expected):
    if type(packet)is not bytes or type(expected)is not bytes or packet!=expected:
        raise ValueError('all retained CS37 wire bytes must match')
    return frozen.parse(packet)

def timings(row):
    samples=row['paired_timing_ms']
    if (not isinstance(samples,dict) or set(samples)!={'baseline','integrated'} or
            any(not isinstance(v,list) or len(v)!=3 for v in samples.values()) or
            any(type(x)not in (int,float) or not math.isfinite(x) or x<=0 for v in samples.values() for x in v)):
        raise ValueError('three finite positive baseline/integrated pairs')
    medians={k:statistics.median(v) for k,v in samples.items()}
    assert medians==row['paired_median_ms']
    orders=[list(('baseline','integrated') if (row['id']+rep)%2==0 else ('integrated','baseline')) for rep in range(3)]
    assert row['paired_order']==orders
    return medians

def selected_coefficients(source,reference,fid,rid,qmap,motion):
    prepared=m.analyze_planes(source,reference,epoch=25,frame_id=fid,reference_id=rid,
        block_size=32,motion_mode='zero',penalty=0,motion_precision='half')
    if motion and reference is not None:
        vectors=np.empty((15,23,2),np.int8);vectors[:]=(-3,1)
        prediction=m.predict(reference,vectors,32)
        prepared=replace(prepared,motion_mode='block',vector_bytes=m.base.pack_vectors(vectors),
            prediction=prediction,raw_coefficients=m.base.old._forward(source,prediction))
    original=m.base._quantize(prepared.raw_coefficients,qmap,720,480)
    pruned,_=m.counter.rdo_skip(prepared,original,qmap,1)
    selected=[];reversions=[];calls=0;legacy_bytes=[]
    for plane,coeff in enumerate(pruned):
        bw=((720 if plane==0 else 360)+7)//8
        plan=m.legacy_plan(coeff,bw);calls+=1;reverted=False
        if not np.array_equal(coeff,original[plane]):
            other=m.legacy_plan(original[plane],bw);calls+=1
            if other['bytes']<plan['bytes']:coeff=original[plane];plan=other;reverted=True
        selected.append(coeff.copy());reversions.append(reverted);legacy_bytes.append(plan['bytes'])
    removed=0
    for coeff,safe in zip(selected,f.safe_blocks(),strict=True):
        mask=safe.reshape(-1);removed+=int(np.count_nonzero(coeff[mask]));coeff[mask]=0
    return tuple(selected),reversions,calls,legacy_bytes,removed

def check_plans(meta):
    """Recompute both real plane payloads with frozen entropy, ties to plain."""
    entropy=f.frozen.shared.entropy;records=[]
    for plane,(coeff,safe,actual) in enumerate(zip(meta['coefficients'],f.safe_blocks(),meta['plane_payloads'],strict=True)):
        bw=((720 if plane==0 else 360)+7)//8
        normal_plan=entropy._plane_plan(coeff,bw,m)
        normal,*_=entropy._construct(coeff,bw,normal_plan,m)
        visible=coeff[~safe.reshape(-1)]
        compact_plan=entropy._plane_plan(visible,1,m)
        compact,*_=entropy._construct(visible,1,compact_plan,m);compact=b'\x04'+compact
        winner=compact if len(compact)<len(normal) else normal
        assert actual==winner
        records.append(dict(plane=plane,plain_bytes=len(normal),compact_bytes=len(compact),selected_bytes=len(actual),implicit_selected=len(compact)<len(normal)))
    return records

def check_work(row,plans,reversions,calls,legacy_bytes,removed):
    work=row['integrated_work']
    assert work['original_rdo_reversions']==reversions
    assert work['legacy_selection_plan_calls']==calls
    assert work['removed_nonzero_coefficients']==removed
    assert work['original_global_RDO_reversion_before_hidden']is True
    counts=dict(fullgrid_plane_plans=3,compact_plane_plans=3,selected_plane_constructions=3,
        discarded_plane_constructions=0,CN36_intermediate_packets=0,coefficient_parse_calls=0,
        transcoder_calls=0,output_inverse_reconstructions=1,normalization_passes=1,CS37_wrappers=1)
    for k,v in counts.items():assert type(work[k])is int and work[k]==v
    assert len(work['planes'])==3
    for plane,(detail,plan,safe,oldbytes,rev) in enumerate(zip(work['planes'],plans,f.safe_blocks(),legacy_bytes,reversions,strict=True)):
        assert detail['plane']==plane and detail['original_legacy_bytes']==oldbytes and detail['rdo_reverted']is rev
        assert detail['full_blocks']==safe.size and detail['hidden_blocks']==int(safe.sum())
        assert detail['visible_blocks']==safe.size-int(safe.sum())
        assert (detail['fullgrid_payload_bytes'],detail['compact_payload_bytes'],detail['selected_payload_bytes'])==(plan['plain_bytes'],plan['compact_bytes'],plan['selected_bytes'])
        assert detail['implicit_selected']is plan['implicit_selected']
    assert math.isfinite(work['integrated_encode_ms']) and 0<work['integrated_encode_ms']<=row['paired_timing_ms']['integrated'][-1]
    baseline=row['baseline_work'];direct,transcode=baseline['direct'],baseline['transcode']
    assert direct['full_packet_encode_calls']==direct['coefficient_parse_calls']==0
    assert transcode['old_encode_already_paid']is True
    assert transcode['hidden_bitmap_bytes']==0 and transcode['new_outer_bytes']==80
    assert transcode['output_complete_bytes']==row['complete_bytes']<=transcode['input_complete_bytes']
    assert 0<direct['direct_encode_ms']+transcode['transcode_ms']<=row['paired_timing_ms']['baseline'][-1]
    assert math.isfinite(row['receiver_ms']) and row['receiver_ms']>0

def check_case(case,oldcase,sources,*,motion=False):
    count=6 if motion else 48;ordered(case['rows'],count)
    rx=frozen.Receiver();oldrx=frozen.Receiver();checks=[]
    for row,old,src in zip(case['rows'],oldcase['rows'],sources[:count],strict=True):
        fid=row['id'];key=fid%24==0;rid=m.NO_REF if key else fid-1
        assert row['key']==key and row['reference_id']==rid and row['source_sha256']==src['common_yuv420_u8_sha256']
        packet=raw(row['packet']);prior=raw(old['packet'],OLD);meta=exact_wire(packet,prior)
        assert (meta['key'],meta['frame_id'],meta['reference_id'])==(key,fid,rid)
        assert row['reference_tag']==meta['reference_tag'].hex()
        assert meta['reference_tag']==(bytes(16) if key else m.C.reference_tag(rx.ref))
        expected,rev,calls,legacy_bytes,removed=selected_coefficients(f.n.source(src),None if key else rx.ref,fid,rid,meta['qmap'],motion)
        for actual,wanted in zip(meta['coefficients'],expected,strict=True):np.testing.assert_array_equal(actual,wanted)
        plans=check_plans(meta)
        pixels,parts,decoded=rx.receive(packet);oldpixels,oldparts,_=oldrx.receive(prior)
        for a,b in zip(pixels,oldpixels,strict=True):np.testing.assert_array_equal(a,b)
        original=f.n.original(src);patches=tuple(original[y:y+h,x:x+w] for x,y,w,h in f.n.RECTS)
        for a,b,c in zip(parts,oldparts,patches,strict=True):
            np.testing.assert_array_equal(a['words'],b['words']);np.testing.assert_array_equal(a['words'],c)
        quality,tag=f.metric(pixels,original,parts)
        assert quality==row['hybrid']==old['hybrid'] and tag==row['display_sha256']==old['display_sha256']
        assert m.C.reference_tag(pixels).hex()==row['normalized_tag']==old['normalized_tag']
        assert len(packet)==row['complete_bytes']==old['complete_bytes']<=49152
        fields=frozen.HEADER.unpack_from(packet)
        assert len(packet)==fields[11]+fields[12]+80
        if 'inner_bytes'in row:assert row['inner_bytes']==fields[11]
        if 'hud_bytes'in row:assert row['hud_bytes']==fields[12]
        if 'binding_bytes'in row:assert row['binding_bytes']==80
        np.testing.assert_array_equal(meta['qmap'],m.roi.declared_map(720,480,f.n.ROIS,8,16))
        if motion and not key:np.testing.assert_array_equal(meta['vectors'],np.broadcast_to([-3,1],meta['vectors'].shape))
        else:assert not np.any(meta['vectors'])
        medians=timings(row)
        check_work(row,plans,rev,calls,legacy_bytes,removed)
        checks.append(dict(bytes=len(packet),quality=quality,medians=medians,plans=plans,reversions=rev,legacy_calls=calls))
    summary=case['summary'];assert summary['frames']==count
    assert summary['complete_bytes']==sum(c['bytes'] for c in checks)
    assert summary['maximum_complete_bytes']==max(c['bytes'] for c in checks)
    assert summary['implicit_planes']==sum(p['implicit_selected'] for c in checks for p in c['plans'])
    means={k:statistics.mean(c['medians'][k] for c in checks) for k in ('baseline','integrated')}
    for k,v in means.items():assert math.isclose(summary['mean_paired_medians_ms'][k],v,abs_tol=1e-10)
    assert math.isclose(summary['paired_sender_ratio'],means['baseline']/means['integrated'],abs_tol=1e-10)
    assert summary['active_mse']==sum(c['quality']['active_squared_error'] for c in checks)/sum(c['quality']['active_channel_samples'] for c in checks)
    return checks

def main():
    data=load(HERE/'results.json');assert data['schema']=='gamebub-integrated-v38'
    assert data['physical_30fps_proven']is False and data['new_RTL_implemented']is False
    for name,tag in data['source_sha256'].items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts
        assert sha(ROOT/path)==tag,('producer pin',name)
    old=load(OLD/'results.json');inputs=load(f.n.V24/'results.json')['inputs']
    assert [c['scene'] for c in data['cases']]==['mass-effect-2600','mass-effect-7200']
    main_count=motion_count=implicit=0
    for case in data['cases']:
        prior=next(c for c in old['cases'] if c['kind']=='main' and c['scene']==case['scene'])
        sources=next(c for c in inputs if c['scene']==case['scene'])['rows']
        checks=check_case(case,prior,sources);main_count+=len(checks)
        implicit+=sum(p['implicit_selected'] for c in checks for p in c['plans'])
    if 'motion_probe'in data:
        probe=data['motion_probe'];prior=next(c for c in old['cases'] if c['kind']=='fractional_motion')
        assert probe['scene']==prior['scene']
        sources=next(c for c in inputs if c['scene']==probe['scene'])['rows']
        checks=check_case(probe,prior,sources,motion=True);motion_count=len(checks)
        implicit+=sum(p['implicit_selected'] for c in checks for p in c['plans'])
    assert main_count==96 and motion_count in (0,6)
    print(json.dumps(dict(exact_main_CS37_packets=main_count,exact_fractional_motion_packets=motion_count,
        original_RDO_reversion_frames_checked=main_count+motion_count,independent_plane_alternatives=6*(main_count+motion_count),
        selected_implicit_planes=implicit,whole_causal_reference_parity=True,source_pins=len(data['source_sha256']),
        new_encoder_or_analyzer_imported=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
