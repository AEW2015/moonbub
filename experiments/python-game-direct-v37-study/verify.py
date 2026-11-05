#!/usr/bin/env python3
"""Independent direct-sender packet parity and causal replay.

No v37 encoder or helper is imported. Frozen v36 independent framing/receiver
checks the actual wire. Exact parity is against retained CN36 skip bytes, not
merely equal frame sizes or equality hidden by the opaque HUD.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import statistics
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('direct37_independent_frozen36',HERE.parent/'python-game-canonical-v36-study/verify.py')
frozen=importlib.util.module_from_spec(spec);sys.modules[spec.name]=frozen;spec.loader.exec_module(frozen)
OLD=HERE.parent/'python-game-canonical-v36-study'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def raw(desc,folder=HERE):return frozen.frozen.raw(desc,folder)


def exact_packet(packet,expected):
    if type(packet)is not bytes or type(expected)is not bytes or packet!=expected:
        raise ValueError('direct sender must reproduce every retained wire byte')
    return frozen.parse(packet)


def ordered(rows,count):
    if (not isinstance(rows,list) or any(type(r.get('id'))is not int for r in rows)
            or [r.get('id') for r in rows]!=list(range(count))):
        raise ValueError('exact ordered frame cohort')


def validate_samples(samples):
    """Validate finite positive paired clocks without making speed thresholds."""
    if not isinstance(samples,dict) or set(samples)!={'proof','direct'}:
        raise ValueError('paired proof/direct timing samples')
    if not samples['proof'] or len(samples['proof'])!=len(samples['direct']):
        raise ValueError('equal nonempty timing sample counts')
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<=0
           for values in samples.values() for x in values):
        raise ValueError('finite positive wall clocks')
    return {name:statistics.median(values) for name,values in samples.items()}


def check_timings(row):
    medians=validate_samples(row['paired_timing_ms'])
    assert all(len(values)==3 for values in row['paired_timing_ms'].values())
    for name,value in medians.items():assert row['paired_median_ms'][name]==value
    orders=[list(('proof','direct') if (row['id']+rep)%2==0 else ('direct','proof')) for rep in range(3)]
    assert row['paired_order']==orders
    work=row['direct_work']
    for key,value in dict(full_packet_encode_calls=0,coefficient_parse_calls=0,
                          skip_entropy_plane_constructions=3,output_inverse_reconstructions=1,
                          normalization_passes=1,wrappers=1).items():assert work[key]==value
    assert type(work['legacy_selection_plan_calls'])is int and 3<=work['legacy_selection_plan_calls']<=6
    assert len(work['original_rdo_reversions'])==3 and all(type(v)is bool for v in work['original_rdo_reversions'])
    assert work['raw_forward_and_RDO_work_retained']is True
    assert work['compiled_mask_plan_setup_paid_once']is True
    assert math.isfinite(work['direct_encode_ms']) and work['direct_encode_ms']>0
    assert work['direct_encode_ms']<=row['paired_timing_ms']['direct'][-1]
    assert math.isfinite(row['receiver_ms']) and row['receiver_ms']>0
    return medians


def check_row(row,expected,source,receiver,old_receiver,*,motion=False):
    fid=row['id'];key=expected['key'];rid=expected['reference_id']
    assert row['source_sha256']==source['common_yuv420_u8_sha256']==expected['source_sha256']
    assert row['key']==key and row['reference_id']==rid
    packet=raw(row['packet']);historical=raw(expected['skip']['packet'],OLD)
    meta=exact_packet(packet,historical)
    assert meta['skip'] and meta['key']==key and meta['frame_id']==fid and meta['reference_id']==rid
    before=bytes(16) if key else frozen.m.C.reference_tag(receiver.reference)
    assert meta['reference_tag']==before
    if 'reference_tag' in row:assert row['reference_tag']==before.hex()
    planes,patches,parsed=receiver.receive(packet)
    old_planes,old_patches,_=old_receiver.receive(historical)
    for a,b in zip(planes,old_planes,strict=True):np.testing.assert_array_equal(a,b)
    assert frozen.m.C.reference_tag(planes).hex()==row['normalized_tag']==expected['skip']['normalized_tag']
    assert len(packet)==row['complete_bytes']==expected['skip']['complete_bytes']<=49152
    assert len(packet)==len(meta['base'])+len(meta['hud'])+80
    if 'inner' in row:assert raw(row['inner'])==meta['base']
    if 'inner_bytes' in row:assert row['inner_bytes']==len(meta['base'])
    if 'hud_bytes' in row:assert row['hud_bytes']==len(meta['hud'])
    if 'binding_bytes' in row:assert row['binding_bytes']==80
    original=frozen.n.original(source)
    expected_patches=tuple(original[y:y+h,x:x+w] for x,y,w,h in frozen.n.RECTS)
    for actual,historical_patch,expected_patch in zip(patches,old_patches,expected_patches,strict=True):
        np.testing.assert_array_equal(actual['words'],expected_patch)
        np.testing.assert_array_equal(actual['words'],historical_patch['words'])
    quality,tag=frozen.metric(planes,original,patches)
    assert quality==row['hybrid']==expected['skip']['hybrid']
    assert tag==row['display_sha256']==expected['skip']['display_sha256']
    inner=frozen.m.parse(meta['base'],expected_epoch=25)
    for c,safe in zip(inner['coefficients'],frozen.safe_blocks(),strict=True):assert not np.any(c[safe.reshape(-1)])
    assert inner['block_size']==32
    if motion and not key:
        np.testing.assert_array_equal(inner['vectors'],np.broadcast_to([-3,1],inner['vectors'].shape))
        if 'configured_vector_halfpel' in row:assert row['configured_vector_halfpel']==[-3,1]
    else:assert not np.any(inner['vectors'])
    np.testing.assert_array_equal(inner['scale_map'],frozen.m.roi.declared_map(720,480,frozen.n.ROIS,8,expected.get('background',16)))
    assert row['background']==expected.get('background',16)
    original_full=frozen.m.parse(frozen.parse(raw(expected['full']['packet'],OLD))['base'],expected_epoch=25)
    removed=0
    for a,b,safe in zip(original_full['coefficients'],inner['coefficients'],frozen.safe_blocks(),strict=True):
        safe=safe.reshape(-1)
        np.testing.assert_array_equal(a[~safe],b[~safe]);assert not np.any(b[safe])
        removed+=int(np.count_nonzero(a[safe]))
    assert row['direct_work']['removed_nonzero_coefficients']==removed
    medians=check_timings(row)
    return dict(packet_bytes=len(packet),hud_words=sum(v['words'].size for v in patches),quality=quality,
                removed=removed,medians=medians)


def check_summary(case,checks):
    summary=case['summary'];rows=case['rows'];count=len(rows)
    assert summary['frames']==count
    assert summary['complete_bytes']==sum(v['packet_bytes'] for v in checks)
    assert summary['maximum_complete_bytes']==max(v['packet_bytes'] for v in checks)
    assert summary['removed_nonzero_coefficients']==sum(v['removed'] for v in checks)
    means={name:statistics.mean(v['medians'][name] for v in checks) for name in ('proof','direct')}
    for name,value in means.items():assert math.isclose(summary['mean_paired_medians_ms'][name],value,abs_tol=1e-10)
    assert math.isclose(summary['paired_sender_ratio'],means['proof']/means['direct'],abs_tol=1e-10)
    samples=sum(v['quality']['active_channel_samples'] for v in checks)
    sse=sum(v['quality']['active_squared_error'] for v in checks)
    assert summary['active_mse']==sse/samples


def main():
    data=load(HERE/'results.json')
    assert data['schema']=='gamebub-direct-v37'
    assert data['physical_30fps_proven'] is False and data['new_RTL_implemented'] is False
    assert data['HEVC_AV1_superiority_proven'] is False
    for name,tag in data['source_sha256'].items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts
        assert sha(ROOT/path)==tag,('producer pin',name)
    prior=load(OLD/'results.json');inputs=load(frozen.n.V24/'results.json')['inputs']
    scenes=['mass-effect-2600','mass-effect-7200']
    assert [c['scene'] for c in data['cases']]==scenes
    verified=main_bytes=hud_words=0
    for case in data['cases']:
        old=next(v for v in prior['cases'] if v['scene']==case['scene'])
        sources=next(v for v in inputs if v['scene']==case['scene'])['rows']
        ordered(case['rows'],48);rx=frozen.Receiver();old_rx=frozen.Receiver()
        checks=[]
        for row,expected,source in zip(case['rows'],old['rows'],sources,strict=True):
            checks.append(check_row(row,expected,source,rx,old_rx));verified+=1
        check_summary(case,checks)
        main_bytes+=sum(v['packet_bytes'] for v in checks);hud_words+=sum(v['hud_words'] for v in checks)
    probe=data['motion_probe'];old=prior['motion_probe']
    assert probe['scene']==old['scene'];ordered(probe['rows'],6)
    sources=next(v for v in inputs if v['scene']==probe['scene'])['rows'][:6]
    rx=frozen.Receiver();old_rx=frozen.Receiver();motion_frames=0;checks=[]
    for row,expected,source in zip(probe['rows'],old['rows'],sources,strict=True):
        checked=check_row(row,expected,source,rx,old_rx,motion=True)
        checks.append(checked);motion_frames+=1;hud_words+=checked['hud_words']
    check_summary(probe,checks)
    assert verified==96 and motion_frames==6 and hud_words==102*21120
    print(json.dumps(dict(exact_main_CN36_packets=verified,exact_fractional_motion_packets=motion_frames,
                          exact_main_complete_bytes=main_bytes,exact_HUD_words=hud_words,
                          whole_normalized_reference_parity=True,new_encoder_imported=False,
                          source_pins=len(data['source_sha256']),physical_30fps_proven=False)))

if __name__=='__main__':main()
