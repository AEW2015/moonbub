#!/usr/bin/env python3
"""Independent full-filter/full-color oracle versus bounded pull scanout.

Audited counts describe unique row-cache loads, not measured physical traffic.
Full YUV/HUD/exclusion inputs and whole-frame verification oracles are external.
"""
from pathlib import Path
from collections.abc import Mapping
import copy,hashlib,importlib.util,json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
subject=module('scan64_subject',HERE/'model.py')
full=module('scan64_frozen_filter60_oracle',HERE.parent/'python-game-display-filter-v60-study/model.py')
io=module('scan64_frozen_decoder57',HERE.parent/'python-game-error-quality-v57-study/verify.py')
independent=module('scan64_independent_filter62',HERE.parent/'python-game-filter-temporal-v62-study/verify.py')
h,m,n=io.h,io.h.m,io.h.f.f.n
raw,digest=h.raw,io.digest
STRONG=dict(name='strong',alpha=24,beta=12,strength=3)
PAUSE_ROWS={0,5,6,7,8,9,14,15,16,17,469,470,471,472,473,478,479}

def guard():
    value=np.repeat(np.repeat(h.f.f.safe_blocks()[0],8,axis=0),8,axis=1);value.setflags(write=False);return value

def vertical_reference(plane,excluded,preset):
    value=plane.astype(np.int32).copy()
    if preset['strength']:
        for x in range(8,720,8):
            p1,p0,q0,q1=(value[:,x+k].copy()for k in(-2,-1,0,1));blocked=excluded[:,x-2:x+2].any(axis=1)
            allowed=(~blocked)&(np.abs(q0-p0)<=preset['alpha'])&(np.abs(p0-p1)<=preset['beta'])&(np.abs(q1-q0)<=preset['beta'])
            d=np.where(allowed,np.clip((3*(q0-p0)+p1-q1+4)//8,-preset['strength'],preset['strength']),0)
            value[:,x-1]=np.clip(p0+d,0,255);value[:,x]=np.clip(q0-d,0,255)
    return value.astype(np.uint8)

def arrays(value,seen=None):
    if seen is None:seen=set()
    if id(value)in seen:return
    seen.add(id(value))
    if isinstance(value,np.ndarray):yield value
    elif isinstance(value,Mapping):
        for v in value.values():yield from arrays(v,seen)
    elif isinstance(value,(tuple,list)):
        for v in value:yield from arrays(v,seen)
    elif hasattr(value,'__dict__')and not isinstance(value,type)and not callable(value):
        yield from arrays(value.__dict__,seen)

def paused(scan):
    before=copy.deepcopy(scan.work());keys=(tuple(scan.luma.cache),tuple(scan.luma.pending),tuple(scan.cb.cache),tuple(scan.cr.cache))
    for _ in range(3):assert scan.work()==before
    assert keys==(tuple(scan.luma.cache),tuple(scan.luma.pending),tuple(scan.cb.cache),tuple(scan.cr.cache))

def audit(scan,planes,patches,excluded,vertical,expectedY,seenY,seenCb,seenCr):
    assert scan.luma.source is planes[0]and scan.luma.excluded is excluded
    assert scan.cb.plane is planes[1]and scan.cr.plane is planes[2]
    assert len(scan.luma.cache)<=4 and len(scan.luma.pending)<=1
    for index,row in scan.luma.cache.items():
        assert 0<=index<480 and row.shape==(720,)and row.dtype==np.uint8 and not row.flags.writeable
        assert index<=scan.y+1;np.testing.assert_array_equal(row,vertical[index]);seenY.add(index)
        assert not np.shares_memory(row,planes[0])
    for index,row in scan.luma.pending.items():
        assert index==scan.y and row.shape==(720,)and row.dtype==np.uint8 and not row.flags.writeable
        np.testing.assert_array_equal(row,expectedY[index]);assert not np.shares_memory(row,planes[0])
        for cached in scan.luma.cache.values():assert not np.shares_memory(row,cached)
    assert scan.luma.loads==len(seenY)
    for cache,source,seen in((scan.cb,planes[1],seenCb),(scan.cr,planes[2],seenCr)):
        assert len(cache.cache)<=2
        for index,row in cache.cache.items():
            assert 0<=index<240 and row.shape==(360,)and row.dtype==np.uint8
            np.testing.assert_array_equal(row,source[index]);assert not np.shares_memory(row,source);seen.add(index)
        assert cache.loads==len(seen)
    external={id(v)for v in(*planes,excluded,*(p['words']for p in patches))}
    retained=[a for a in arrays(scan)if id(a)not in external]
    assert all(a.ndim==1 and len(a)in(360,720)for a in retained)
    assert sum(a.nbytes for a in retained)<=5040
    work=scan.work();assert work['luma']['peak_cached_vertical_rows']<=4 and work['luma']['peak_pending_rows']<=1 and work['luma']['maximum_lookahead_rows']<=2
    assert work['luma']['Y_rows_loaded']==len(seenY)
    assert work['logical_conservative_row_data_bytes']==7200 and work['retained_full_filtered_luma']is work['retained_full_RGB_frame']is False
    return retained

def verify_frame(planes,patches,excluded,preset,expectedY,expectedRGB,expected_work):
    vertical=vertical_reference(planes[0],excluded,preset);scan=subject.Scanout(planes,patches,n.RECTS,excluded,preset)
    assert scan.work()['luma']['Y_rows_loaded']==scan.work()['Cb_row_loads']==scan.work()['Cr_row_loads']==0
    seenY=set();seenCb=set();seenCr=set();yh=hashlib.sha256();rh=hashlib.sha256();held=[];pauses=0
    before=[digest(a.tobytes())for a in(*planes,excluded,*(p['words']for p in patches))]
    for y,(Y,RGB)in enumerate(scan):
        assert Y.shape==RGB.shape==(720,)and Y.dtype==np.uint8 and RGB.dtype==np.uint16
        assert not Y.flags.writeable and not RGB.flags.writeable and not np.shares_memory(Y,RGB)
        np.testing.assert_array_equal(Y,expectedY[y]);np.testing.assert_array_equal(RGB,expectedRGB[y])
        retained=audit(scan,planes,patches,excluded,vertical,expectedY,seenY,seenCb,seenCr)
        for returned in(Y,RGB):
            for external in(*planes,excluded,*(p['words']for p in patches),*retained):assert not np.shares_memory(returned,external)
        for a,b,c,d in held:np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(c,d)
        if y in PAUSE_ROWS:
            paused(scan);held.append((Y,Y.copy(),RGB,RGB.copy()));pauses+=1
        yh.update(Y.tobytes());rh.update(RGB.astype('<u2',copy=False).tobytes())
    assert y==479 and seenY==set(range(480))and seenCb==seenCr==set(range(240))
    paused(scan)
    try:next(scan)
    except StopIteration:pass
    else:raise AssertionError('scanout longer than480')
    assert before==[digest(a.tobytes())for a in(*planes,excluded,*(p['words']for p in patches))]
    work=scan.work();assert work['lines']==work['luma']['lines']==480
    assert work['Y_unique_input_bytes']==345600 and work['Cb_row_loads']==work['Cr_row_loads']==240 and work['chroma_unique_input_bytes']==172800
    assert work['HUD_word_reads']==21120 and work['RGB565_words_written']==345600
    for key in('vertical_changed_edges','horizontal_changed_edges','changed_luma_samples'):assert work['luma'][key]==expected_work[key]
    assert work['full_reference_and_HUD_inputs_excluded']is work['static_exclusion_geometry_and_HUD_and_reference_inputs_excluded']is work['Python_temporaries_not_target_fit']is True
    assert work['target_fit_or_scanout_timing_proven']is False
    return yh.hexdigest(),rh.hexdigest(),work,pauses

def main():
    data=h.load(HERE/'results.json');source=h.load(SOURCE/'results.json');assert data['schema']=='gamebub-filtered-scanout-v64'
    for path,want in data['source_sha256'].items():assert h.sha(ROOT/path)==want,path
    calibration=h.load(HERE.parent/'python-game-display-filter-v60-study/calibration.json');assert data['preset']==calibration['selected_preset']==STRONG
    excluded=guard();frames=lines=words=HUD=Yloads=pauses=0;observed=[]
    assert len(data['cases'])==len(source['cases'])==4
    for case,original in zip(data['cases'],source['cases'],strict=True):
        assert case['scene']==original['scene']and [r['id']for r in case['rows']]==list(range(24,48));rx=io.direct.Receiver()
        for row,prior in zip(case['rows'],original['rows'][24:48],strict=True):
            assert row['id']==prior['id']and row['source_packet']==prior['packet']
            canonical,patches,meta,count=rx.receive(raw(prior['packet'],SOURCE));stamp=m.C.reference_tag(canonical).hex();assert stamp==row['normalized_tag']==prior['normalized_tag']
            original_ref=digest(b''.join(p.astype('<i2').tobytes()for p in canonical));planes=tuple(p.astype(np.uint8)for p in canonical)
            for p in planes:p.setflags(write=False)
            assert digest(b''.join(p.tobytes()for p in planes))==row['input_reference_sha256']
            expectedY,fw=full.filtered_luma(planes[0],excluded,STRONG);otherY,other_work=independent.oracle_filter(planes[0],excluded,STRONG)
            np.testing.assert_array_equal(expectedY,otherY);assert fw==other_work
            expectedRGB=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb((expectedY,planes[1],planes[2]))),tuple(p['words']for p in patches))
            yh,rh,work,pause_count=verify_frame(planes,patches,excluded,STRONG,expectedY,expectedRGB,fw)
            assert yh==row['filtered_Y_sha256']and rh==row['display_sha256']and work==row['work']
            assert digest(b''.join(p.astype('<i2').tobytes()for p in canonical))==original_ref and m.C.reference_tag(rx.ref).hex()==stamp
            assert type(row['scanout_plus_checks_ms'])in(int,float)and math.isfinite(row['scanout_plus_checks_ms'])and row['scanout_plus_checks_ms']>0
            frames+=1;lines+=480;words+=345600;HUD+=21120;Yloads+=480;pauses+=pause_count;observed.append(row)
        print(json.dumps(dict(scene=case['scene'],exact_frames=24,full_luma_and_RGB565_lines=True)),flush=True)
    summary=dict(frames=frames,lines=lines,exact_RGB565_words=words,exact_HUD_words=HUD,source_Y_rows_loaded=Yloads,
        maximum_cached_vertical_rows=max(r['work']['luma']['peak_cached_vertical_rows']for r in observed),maximum_pending_rows=max(r['work']['luma']['peak_pending_rows']for r in observed),maximum_lookahead_rows=max(r['work']['luma']['maximum_lookahead_rows']for r in observed),mean_scanout_plus_checks_ms=sum(r['scanout_plus_checks_ms']for r in observed)/len(observed))
    assert data['summary']==summary and frames==96
    print(json.dumps(dict(frames=frames,exact_filtered_luma_samples=words,exact_RGB565_words=words,exact_HUD_words=HUD,source_pins=len(data['source_sha256']),
        unique_luma_cache_rows=Yloads,deterministic_pull_pause_checks=pauses,owned_readonly_outputs=True,source_canonical_HUD_and_mask_immutable=True,
        maximum_vertical_cache_rows=summary['maximum_cached_vertical_rows'],maximum_pending_rows=summary['maximum_pending_rows'],maximum_lookahead_rows=summary['maximum_lookahead_rows'],
        retained_full_filtered_Y_or_RGB=False,logical_row_data_bytes=7200,total_physical_bus_reads_measured=False,RTL_BRAM_ports_clock_or_FPS_proven=False)))
if __name__=='__main__':main()
