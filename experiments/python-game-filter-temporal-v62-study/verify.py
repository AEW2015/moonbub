#!/usr/bin/env python3
"""Independent frozen-filter temporal qualification; no encoding or retuning.

All luma samples are independently calculated one edge at a time. Metrics are
originalRGB565/error57 definitions, not perceptual quality or subjective flicker.
"""
from pathlib import Path
import hashlib,importlib.util,json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=HERE.parent/'python-game-source-v40-study';CUSTOM=HERE.parent/'python-game-temporal-qual-v59-study';NATIVE=HERE.parent/'python-game-native-temporal-v61-study';FILTER=HERE.parent/'python-game-display-filter-v60-study'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
io=module('filter62_independent_error57',HERE.parent/'python-game-error-quality-v57-study/verify.py')
h,m,f,n=io.h,io.h.m,io.h.f,io.h.f.f.n
raw,digest=h.raw,io.digest
PRESETS=(dict(name='identity',alpha=0,beta=0,strength=0),dict(name='weak',alpha=8,beta=4,strength=1),dict(name='medium',alpha=16,beta=8,strength=2),dict(name='strong',alpha=24,beta=12,strength=3))
IDENTITY,STRONG=PRESETS[0],PRESETS[3]

def oracle_filter(plane,excluded,preset):
    if type(plane)is not np.ndarray or plane.shape!=(480,720)or plane.dtype!=np.uint8:raise ValueError('bounded luma input')
    if type(excluded)is not np.ndarray or excluded.shape!=plane.shape or excluded.dtype!=bool:raise ValueError('fixed excluded footprint')
    if preset not in PRESETS:raise ValueError('fixed preset')
    out=plane.astype(np.int32).copy();counts=[]
    for axis in(1,0):
        count=0
        if preset['strength']:
            for edge in range(8,out.shape[axis],8):
                if axis==1:
                    p1,p0,q0,q1=(out[:,edge+offset].copy()for offset in(-2,-1,0,1));blocked=excluded[:,edge-2:edge+2].any(axis=1)
                else:
                    p1,p0,q0,q1=(out[edge+offset,:].copy()for offset in(-2,-1,0,1));blocked=excluded[edge-2:edge+2,:].any(axis=0)
                good=~blocked
                good&=np.abs(q0-p0)<=preset['alpha'];good&=np.abs(p0-p1)<=preset['beta'];good&=np.abs(q1-q0)<=preset['beta']
                delta=(3*(q0-p0)+p1-q1+4)//8
                delta=np.where(good,np.maximum(-preset['strength'],np.minimum(preset['strength'],delta)),0)
                p=np.maximum(0,np.minimum(255,p0+delta));q=np.maximum(0,np.minimum(255,q0-delta));count+=int(np.count_nonzero(delta))
                if axis==1:out[:,edge-1],out[:,edge]=p,q
                else:out[edge-1,:],out[edge,:]=p,q
        counts.append(count)
    out=out.astype(np.uint8);out.setflags(write=False)
    return out,dict(vertical_changed_edges=counts[0],horizontal_changed_edges=counts[1],changed_luma_samples=int(np.count_nonzero(out!=plane)),reference_mutated=False,full_luma_proof_array_staged=True,FPGA_line_buffer_or_timing_implemented=False)

def check_calibration():
    calibration=json.loads((FILTER/'calibration.json').read_text());data=json.loads((FILTER/'results.json').read_text())
    for path,want in calibration['source_sha256'].items():assert h.sha(ROOT/path)==want,path
    cases=[c for c in data['cases']if c['kind']=='custom'and c['policy']=='zero'];assert len(cases)==4
    rows=[]
    for index,preset in enumerate(PRESETS):
        matching=[c['presets'][index]for c in cases];assert all(v['preset']==preset for v in matching)
        assert all([r['id']for r in v['rows']]==list(range(24))for v in matching)
        sse=sum(v['summary']['active_SSE']for v in matching);samples=sum(v['summary']['active_samples']for v in matching)
        rows.append(dict(preset=preset,active_SSE=sse,active_samples=samples,active_MSE=sse/samples))
    assert calibration['candidates']==rows and calibration['source_IDs']==list(range(24))
    assert calibration['calibration_cohorts']==[c['scene']for c in cases]
    winner=min(range(4),key=lambda i:rows[i]['active_SSE']);assert calibration['selected_preset']==rows[winner]['preset']==STRONG
    return calibration

def select_native(cases,scene,codec,target_sse,target_samples):
    eligible=[c for c in cases if c['scene']==scene and c['codec']==codec and c['supported']and c['summary']['cap_failures']==0 and c['summary']['active_channel_samples']==target_samples and c['summary']['active_squared_error']<=target_sse]
    if not eligible:raise ValueError('no cap-fit matched-quality native point')
    return min(eligible,key=lambda c:(c['summary']['complete_bytes'],c['summary']['active_squared_error'],c['parameter']))

def originals(scene):
    manifest=h.load(SOURCE/'manifest.json');case=next(c for c in manifest['cases']if Path(c['media_file']).stem==scene);result={}
    for source in case['frames'][24:48]:
        canvas=np.frombuffer(raw(source['canvas_rgb24'],SOURCE),np.uint8).reshape(480,720,3);assert digest(canvas.tobytes())==source['canvas_rgb_sha256']
        words=m.C.corpus.rgb565(canvas);assert digest(words.astype('<u2').tobytes())==source['rgb565_sha256']
        result[source['id']]=(source,words,m.C.corpus.expand565(words))
    assert list(result)==list(range(24,48));return result

def normalized_native_points():
    points=[]
    for folder in(NATIVE,HERE.parent/'python-game-native-temporal-cap-v61-study'):
        data=h.load(folder/'results.json')
        for index,case in enumerate(data['cases']):
            summary=dict(case.get('summary',{}));supported=case.get('supported',True)
            if supported:
                rows=case['rows'];assert len(rows)==24
                assert summary['complete_bytes']==sum(r['complete_bytes']for r in rows)and summary['cap_failures']==sum(r['complete_bytes']>49152 for r in rows)
                summary.update(active_squared_error=sum(r['metric']['active_squared_error']for r in rows),active_channel_samples=sum(r['metric']['active_channel_samples']for r in rows))
            normalized=dict(case,summary=summary,scene=case.get('scene',data.get('source_scene')));assert normalized['scene']is not None
            points.append(dict(source=(folder/'results.json').relative_to(ROOT).as_posix(),source_case=index,case=normalized))
    return points

def expected_cases(custom,points):
    cases=[];anchors=[]
    for index,case in enumerate(custom['cases']):
        scene=case['scene'];assert [r['id']for r in case['rows']]==list(range(24,48))
        for policy in('zero','adaptive'):
            rows=[r['zero_qualification']if policy=='zero'else r for r in case['rows']]
            cases.append(dict(kind='custom',scene=scene,policy=policy,codec=None,source=(CUSTOM/'results.json').relative_to(ROOT).as_posix(),source_case=index,
                complete_bytes=sum(r['complete_bytes']for r in rows),cap_failures=sum(r['complete_bytes']>49152 for r in rows)))
        target=sum(r['zero_qualification']['quality']['active_squared_error']for r in case['rows']);samples=sum(r['zero_qualification']['quality']['active_channel_samples']for r in case['rows'])
        for codec in('libx265','libsvtav1'):
            options=[p for p in points if p['case']['scene']==scene and p['case']['codec']==codec];table=[];eligible=[]
            for i,point in enumerate(options):
                c=point['case'];supported=c.get('supported',True);sm=c['summary']
                ok=supported and sm.get('cap_failures')==0 and sm.get('active_channel_samples')==samples and sm.get('active_squared_error',target+1)<=target
                table.append(dict(source=point['source'],source_case=point['source_case'],codec=c['codec'],parameter=c['parameter'],extra_options=c.get('extra_options'),bitrate=c.get('bitrate'),supported=supported,eligible=bool(ok),summary=sm))
                if ok:eligible.append(i)
            selected=min(eligible,key=lambda i:(options[i]['case']['summary']['complete_bytes'],options[i]['case']['summary']['active_squared_error'],options[i]['case']['parameter'],i))if eligible else None
            anchors.append(dict(scene=scene,codec=codec,target_zero_active_SSE=target,target_samples=samples,points=table,selected=selected,
                criterion='supported+cap0+mean originalRGB565SSE<=zero; min(actualcompletebytes,SSE,parameter,inputorder)',anchor_selection_exploratory=True))
            if selected is not None:
                point=options[selected];c=point['case'];sm=c['summary']
                cases.append(dict(kind='native',scene=scene,policy=codec,codec=codec,parameter=c['parameter'],extra_options=c.get('extra_options'),bitrate=c.get('bitrate'),
                    source=point['source'],source_case=point['source_case'],complete_bytes=sm['complete_bytes'],cap_failures=sm['cap_failures'],anchor_selection=len(anchors)-1))
    return cases,anchors

def presentations(case,source_originals):
    folder=(ROOT/case['source']).parent;source=h.load(ROOT/case['source'])['cases'][case['source_case']]
    if case['kind']=='custom':
        rx=io.direct.Receiver()
        for source_row in source['rows']:
            fid=source_row['id'];entry=source_row['zero_qualification']if case['policy']=='zero'else source_row
            packet=raw(entry['packet'],folder);canonical,patches,meta,count=rx.receive(packet)
            assert m.C.reference_tag(canonical).hex()==entry['normalized_tag'];assert meta['frame_id']==fid
            planes=tuple(p.astype(np.uint8)for p in canonical)
            for p in planes:p.setflags(write=False)
            display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(planes)),tuple(p['words']for p in patches));assert digest(display.astype('<u2').tobytes())==entry['display_sha256']
            stamp=digest(b''.join(p.astype('<i2').tobytes()for p in canonical))
            yield fid,None,planes,patches,canonical,len(packet),entry['packet'],entry['quality'],entry['display_sha256']
            assert digest(b''.join(p.astype('<i2').tobytes()for p in rx.ref))==stamp
    else:
        std=io.std;codec=std.av.CodecContext.create('hevc'if case['codec']=='libx265'else'libdav1d','r');codec.thread_count=1
        extra=raw(source['extradata'],folder)
        if extra:codec.extradata=extra
        assert len(source['rows'])==24
        control=h.load((HERE.parent/'python-game-control-qual-v40-study')/'results.json');controls=next(c for c in control['cases']if c['scene']==case['scene'])
        for index,row in enumerate(source['rows']):
            fid=24+index;original,words,expanded=source_originals[fid]
            assert row['id']==row['pts']==row['dts']==index and row['source_id']==fid
            assert row['source_sha256']==original['common_yuv420_u8_sha256']and row['source_pts']==original['pts']and row['source_time_base']==original['time_base']
            data=raw(row['access_unit'],folder);packet=std.av.Packet(data);packet.pts,packet.dts,packet.time_base=index,index,std.TB
            frames=codec.decode(packet);assert len(frames)==1 and frames[0].pts==index
            planes=std.planes_from_frame(frames[0])
            for p in planes:p.setflags(write=False)
            patches=[]
            for rect in n.RECTS:
                x,y,w,hh=rect;view=words[y:y+hh,x:x+w].view();view.setflags(write=False);patches.append(dict(rect=rect,words=view))
            hud=raw(controls['rows'][fid]['hud_packets']['HX33_selected'],HERE.parent/'python-game-control-qual-v40-study')
            assert row['access_unit_bytes']==len(data)and row['extradata_bytes_charged']==(len(extra)if index==0 else 0)and row['binding_bytes']==80 and row['hud_bytes']==len(hud)
            assert row['complete_bytes']==len(data)+len(hud)+80+(len(extra)if index==0 else 0)and row['cap_fit']==(row['complete_bytes']<=49152)
            display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(planes)),tuple(p['words']for p in patches));assert digest(display.astype('<u2').tobytes())==row['display_sha256']
            yield fid,index,planes,tuple(patches),None,row['complete_bytes'],row['access_unit'],row['metric'],row['display_sha256']
        assert not codec.decode(None)

def main():
    calibration=check_calibration();data=h.load(HERE/'results.json');assert data['schema']=='gamebub-filter-temporal-v62'
    assert data['source_window']==[24,48]and data['calibration_source']==(FILTER/'calibration.json').relative_to(ROOT).as_posix()and data['missing_declared_inputs']==[]
    for name in('physical_30fps_proven','new_RTL_implemented','HEVC_AV1_superiority_proven'):assert data[name]is False
    for path,want in data['source_sha256'].items():assert h.sha(ROOT/path)==want,path
    custom=h.load(CUSTOM/'results.json');points=normalized_native_points();descriptors,anchors=expected_cases(custom,points)
    assert data['anchor_selection']==anchors and len(data['cases'])==len(descriptors)
    guard=np.repeat(np.repeat(f.f.safe_blocks()[0],8,axis=0),8,axis=1)
    assert int(guard.sum())==data['excluded_luma_samples']and digest(guard.tobytes())==data['excluded_luma_sha256']
    variants=decoded=native_count=canonical_count=0;cache={};changes=[]
    for case,descriptor in zip(data['cases'],descriptors,strict=True):
        assert {k:v for k,v in case.items()if k!='presets'}==descriptor
        assert [p['preset']for p in case['presets']]==[IDENTITY,STRONG]
        if case['scene']not in cache:cache[case['scene']]=originals(case['scene'])
        source_originals=cache[case['scene']];previous={p['name']:None for p in(IDENTITY,STRONG)};metrics={p['name']:[]for p in(IDENTITY,STRONG)};total=cap=0
        for index,item in enumerate(presentations(descriptor,source_originals)):
            fid,pts,planes,patches,canonical,complete,packet,quality,baseline_hash=item;assert fid==index+24
            source,words,original=source_originals[fid];input_hash=digest(b''.join(p.astype('u1',copy=False).tobytes()for p in planes))
            canonical_hash=None if canonical is None else digest(b''.join(p.astype('<i2').tobytes()for p in canonical))
            for pi,preset in enumerate((IDENTITY,STRONG)):
                record=case['presets'][pi]['rows'][index];assert record['id']==fid and record['native_pts']==pts and record['source_packet']==packet and record['complete_bytes']==complete
                assert record['reference_input_sha256']==input_hash and record['canonical_reference_sha256']==canonical_hash
                filtered,work=oracle_filter(planes[0],guard,preset)
                assert digest(filtered.tobytes())==record['filtered_luma_sha256']and work==record['work']
                assert digest(b''.join(p.astype('u1',copy=False).tobytes()for p in planes))==input_hash
                if canonical is not None:assert digest(b''.join(p.astype('<i2').tobytes()for p in canonical))==canonical_hash
                display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb((filtered,planes[1],planes[2]))),tuple(p['words']for p in patches))
                for patch,(x,y,w,hh)in zip(patches,n.RECTS,strict=True):np.testing.assert_array_equal(display[y:y+hh,x:x+w],words[y:y+hh,x:x+w]);np.testing.assert_array_equal(patch['words'],words[y:y+hh,x:x+w])
                stamp=digest(display.astype('<u2').tobytes());assert stamp==record['display_sha256']
                error,diagnostic=io.equations(original,m.C.corpus.expand565(display),previous[preset['name']]);previous[preset['name']]=error
                assert diagnostic==record['diagnostic'];metrics[preset['name']].append(diagnostic)
                if preset['name']=='identity':assert stamp==baseline_hash and diagnostic['active_SSE']==quality['active_squared_error']and diagnostic['active_samples']==quality['active_channel_samples']
                assert type(record['filter_ms'])in(int,float)and math.isfinite(record['filter_ms'])and record['filter_ms']>0
                variants+=1
            total+=complete;cap+=complete>49152;decoded+=1;native_count+=case['kind']=='native';canonical_count+=canonical is not None
        assert index==23 and total==descriptor['complete_bytes']and cap==descriptor['cap_failures']
        for profile in case['presets']:assert io.summarize(metrics[profile['preset']['name']])==profile['summary']
        identity=case['presets'][0]['summary'];strong=case['presets'][1]['summary']
        changes.append(dict(scene=case['scene'],policy=case['policy'],source=case['source'],parameter=case.get('parameter'),identity_MSE=identity['active_MSE'],strong_MSE=strong['active_MSE'],source_SSE_delta=strong['active_SSE']-identity['active_SSE']))
        print(json.dumps(changes[-1]),flush=True)
    expected_summary=dict(source_cases=len(descriptors),unique_source_canvases=96,decoded_presentations=24*len(descriptors),display_variants=48*len(descriptors),selected_native_anchors=sum(c['kind']=='native'for c in descriptors),unsupported_native_anchors=sum(a['selected']is None for a in anchors))
    assert data['summary']==expected_summary and variants==2*decoded
    print(json.dumps(dict(calibration_only_zero_prefixes=4,calibration_source_IDs=[0,23],qualification_source_IDs=[24,47],fixed_filter=STRONG,
        selected_cases=len(descriptors),decoded_presentations=decoded,display_variants=variants,independent_full_luma_samples=variants*480*720,
        fresh_native_decodes=native_count,immutable_custom_reference_presentations=canonical_count,all_HUD_words_exact=True,all_error57_equations_rederived=True,
        encoded_bytes_unchanged=True,encoding_called=False,native_anchor_choice_exploratory=True,source_pins=len(data['source_sha256']),subjective_flicker_or_hardware_FPS_proven=False)))
if __name__=='__main__':main()
