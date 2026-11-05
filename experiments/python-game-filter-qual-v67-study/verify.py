#!/usr/bin/env python3
"""Independent full-plane extended fixed-filter qualification.

Uses the frozen independent edge oracle from 62, never the producer filter or
aggregation. Encoded video/reference histories remain unchanged. Metrics are
original RGB565 squared error, not subjective quality or temporal flicker.
"""
from pathlib import Path
from fractions import Fraction
import hashlib,importlib.util,json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
oracle=module('filter67_independent62',HERE.parent/'python-game-filter-temporal-v62-study/verify.py')
io,h,m,n=oracle.io,oracle.h,oracle.m,oracle.n
SOURCE=HERE.parent/'python-game-source-v40-study';PACKETS=HERE.parent/'python-game-binary-qual-v40-study'
raw=oracle.raw
def digest(data):return hashlib.sha256(data).hexdigest()

def expand(words):
    if words.dtype!=np.uint16 or words.shape!=(480,720):raise ValueError('RGB565 full canvas')
    r=(words>>11)&31;g=(words>>5)&63;b=words&31
    return np.stack(((r*8)|(r>>2),(g*4)|(g>>4),(b*8)|(b>>2)),axis=2).astype(np.int32)

def quality(original,display):
    e=expand(display)-expand(original);square=e.astype(np.int64)**2;sse=int(square[37:442].sum());samples=874800
    mse=sse/samples;errors=hsse=0
    for x,y,w,hh in n.RECTS:
        errors+=int(np.count_nonzero(original[y:y+hh,x:x+w]!=display[y:y+hh,x:x+w]));hsse+=int(square[y:y+hh,x:x+w].sum())
    return dict(active_squared_error=sse,active_channel_samples=samples,active_mse=mse,active_psnr_db=None if not sse else 10*math.log10(65025/mse),
        hud_word_errors=errors,hud_squared_channel_error=hsse,hud_channel_samples=63360)

def aggregate(rows):
    if not rows:raise ValueError('nonempty window')
    ids=[r['id']for r in rows]
    if ids!=list(range(ids[0],ids[-1]+1)):raise ValueError('contiguous IDs')
    a=[];b=[];weights=[]
    for r in rows:
        aa=r['identity']['active_squared_error'];bb=r['strong']['active_squared_error'];nn=r['identity']['active_channel_samples']
        if type(aa)is not int or type(bb)is not int or min(aa,bb)<0 or type(nn)is not int or nn<=0 or nn!=r['strong']['active_channel_samples']:raise ValueError('integer paired SSE/samples')
        a.append(aa);b.append(bb);weights.append(nn)
    deltas=[bb-aa for aa,bb in zip(a,b)];relative=[Fraction(0)]+[Fraction(bb-aa,aa)for aa,bb in zip(a,b)if aa]
    return dict(frames=len(rows),first_id=ids[0],last_id=ids[-1],complete_bytes=sum(r['complete_bytes']for r in rows),active_samples=sum(weights),
        identity_SSE=sum(a),strong_SSE=sum(b),identity_MSE=sum(a)/sum(weights),strong_MSE=sum(b)/sum(weights),
        improved_frames=sum(d<0 for d in deltas),regressed_frames=sum(d>0 for d in deltas),tied_frames=deltas.count(0),
        zero_identity_error_regressed_frames=sum(aa==0 and bb>0 for aa,bb in zip(a,b)),maximum_positive_frame_SSE_delta=max([0]+deltas),
        worst_relative_SSE_increase=float(max(relative)),identity_peak_frame_MSE=float(max(Fraction(aa,nn)for aa,nn in zip(a,weights))),
        strong_peak_frame_MSE=float(max(Fraction(bb,nn)for bb,nn in zip(b,weights))))

def overlap_records():
    out={}
    for foldername,window in(('python-game-display-filter-v60-study',range(24)),('python-game-filter-temporal-v62-study',range(24,48))):
        data=json.loads((HERE.parent/foldername/'results.json').read_text())
        for case in data['cases']:
            if case['kind']!='custom'or case['policy']!='zero':continue
            for p in case['presets']:
                if p['preset']['name']not in('identity','strong'):continue
                assert [r['id']for r in p['rows']]==list(window)
                for r in p['rows']:out[(case['scene'],r['id'],p['preset']['name'])]=r
    return out

def main():
    oracle.check_calibration();data=json.loads((HERE/'results.json').read_text());assert data['schema']=='gamebub-filter-qual-v67'
    assert data['preset']==oracle.STRONG and data['physical_30fps_proven']is data['new_RTL_implemented']is False
    pins=data['source_sha256']
    for path,want in pins.items():assert digest((ROOT/path).read_bytes())==want,path
    for path in(SOURCE/'manifest.json',PACKETS/'results.json',HERE/'helpers.py',HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py'):
        assert path.relative_to(ROOT).as_posix()in pins
    sources=json.loads((SOURCE/'manifest.json').read_text());encoded=json.loads((PACKETS/'results.json').read_text());assert len(sources['cases'])==len(encoded['cases'])==len(data['cases'])==4
    mask=np.repeat(np.repeat(oracle.f.f.safe_blocks()[0],8,axis=0),8,axis=1);assert mask.shape==(480,720)and int(mask.sum())==16384;mask.setflags(write=False)
    overlap=overlap_records();overlapchecks=frames=keys=0;reports=[];allrows=[]
    for src,case,record in zip(sources['cases'],encoded['cases'],data['cases'],strict=True):
        assert src['name']==case['scene']==record['scene'];assert len(src['frames'])==len(case['rows'])==len(record['rows'])
        rx=io.direct.Receiver();checked=[]
        for source,old,row in zip(src['frames'],case['rows'],record['rows'],strict=True):
            fid=source['id'];assert fid==old['id']==row['id']==len(checked)
            assert row['source_packet']==old['packet']and row['source_canvas']==source['canvas_rgb24']
            for base,desc in((PACKETS,old['packet']),(SOURCE,source['canvas_rgb24'])):assert (base/desc['path']).relative_to(ROOT).as_posix()in pins
            packet=raw(old['packet'],PACKETS);assert row['complete_bytes']==len(packet)==old['complete_bytes']<=49152
            canonical,patches,meta,_=rx.receive(packet);assert row['key']==meta['key']and meta['frame_id']==fid
            assert row['canonical_tag']==old['normalized_tag']==m.C.reference_tag(canonical).hex()
            canonicalstamp=digest(b''.join(p.astype('<i2').tobytes()for p in canonical))
            planes=tuple(p.astype(np.uint8)for p in canonical)
            for p in planes:p.setflags(write=False)
            inputstamp=digest(b''.join(p.tobytes()for p in planes));assert inputstamp==row['reference_input_sha256']
            rgb=np.frombuffer(raw(source['canvas_rgb24'],SOURCE),np.uint8).reshape(480,720,3);assert digest(rgb.tobytes())==source['canvas_rgb_sha256']
            original=m.C.corpus.rgb565(rgb);assert digest(original.astype('<u2').tobytes())==source['rgb565_sha256']
            filtered,work=oracle.oracle_filter(planes[0],mask,oracle.STRONG);assert work==row['work']and digest(filtered.tobytes())==row['filtered_luma_sha256']
            for name,Y in(('identity',planes[0]),('strong',filtered)):
                display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb((Y,planes[1],planes[2]))),tuple(p['words']for p in patches))
                q=quality(original,display);assert set(row[name])=={'active_squared_error','active_channel_samples','active_mse','active_psnr_db','hud_word_errors'};assert {key:q[key]for key in row[name]}==row[name]
                stamp=digest(display.astype('<u2').tobytes());assert stamp==row[name+'_display_sha256']
                for patch,(x,y,w,hh)in zip(patches,n.RECTS,strict=True):
                    np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w]);np.testing.assert_array_equal(display[y:y+hh,x:x+w],patch['words'])
                assert q['hud_word_errors']==q['hud_squared_channel_error']==0
                if name=='identity':assert row[name]==old['quality']and stamp==old['display_sha256']
                if fid<48:
                    previous=overlap[(case['scene'],fid,name)];assert previous['display_sha256']==stamp and previous['reference_input_sha256']==inputstamp
                    assert previous['diagnostic']['active_SSE']==q['active_squared_error']and previous['diagnostic']['active_samples']==q['active_channel_samples']
                    assert previous['work']==(work if name=='strong'else oracle.oracle_filter(planes[0],mask,oracle.IDENTITY)[1])
                    if 'filtered_luma_sha256'in previous:assert previous['filtered_luma_sha256']==digest(Y.tobytes())
                    overlapchecks+=1
            assert digest(b''.join(p.tobytes()for p in planes))==inputstamp and digest(b''.join(p.astype('<i2').tobytes()for p in rx.ref))==canonicalstamp
            assert m.C.reference_tag(rx.ref).hex()==row['canonical_tag'];assert all(not p.flags.writeable for p in rx.ref)
            checked.append(row);frames+=1;keys+=int(meta['key'])
        assert record['summary']==aggregate(checked)
        parts={name:aggregate([r for r in checked if lo<=r['id']<hi])for name,lo,hi in(('calibration_0_23',0,24),('later_24_47',24,48),('remaining_48_plus',48,10**9))}
        assert record['partitions']==parts
        report=dict(scene=case['scene'],frames=len(checked),identity_SSE=record['summary']['identity_SSE'],strong_SSE=record['summary']['strong_SSE'],
            improved_ids=[r['id']for r in checked if r['strong']['active_squared_error']<r['identity']['active_squared_error']],
            regression_ids=[r['id']for r in checked if r['strong']['active_squared_error']>r['identity']['active_squared_error']],
            tie_ids=[r['id']for r in checked if r['strong']['active_squared_error']==r['identity']['active_squared_error']],
            zero_error_regression_ids=[r['id']for r in checked if r['identity']['active_squared_error']==0 and r['strong']['active_squared_error']>0],remaining_48_plus=parts['remaining_48_plus'])
        reports.append(report);allrows.extend(checked);print(json.dumps(report),flush=True)
    aggregateall={key:sum(c['summary'][key]for c in data['cases'])for key in('improved_frames','regressed_frames','tied_frames','complete_bytes','identity_SSE','strong_SSE')}
    assert data['summary']==dict(frames=frames,display_variants=2*frames,additional_temporal_canvases_beyond_first48=frames-192,**aggregateall)
    assert frames==457 and overlapchecks==384
    for v in list(sys.modules.values()):
        path=getattr(v,'__file__',None)
        assert path is None or Path(path).resolve()not in{HERE/'model.py',oracle.FILTER/'model.py'}
    print(json.dumps(dict(causal_frames=frames,display_variants=2*frames,full_plane_independent_luma_samples=frames*480*720,source_pins=len(pins),key_frames=keys,
        previous_filter_overlap_variants=overlapchecks,additional_temporal_canvases_beyond_first48=frames-192,
        source_weighted_identity_MSE=aggregateall['identity_SSE']/(frames*874800),source_weighted_strong_MSE=aggregateall['strong_SSE']/(frames*874800),
        improved_frames=aggregateall['improved_frames'],regressed_frames=aggregateall['regressed_frames'],tied_frames=aggregateall['tied_frames'],
        exact_HUD_words=frames*21120,all_canonical_references_and_encoded_bytes_unchanged=True,filter_retuned=False,new_capture_or_unseen_game_claim=False,
        physical_30fps_or_subjective_quality_proven=False)),flush=True)
if __name__=='__main__':main()
