#!/usr/bin/env python3
"""Paired exact encoder optimization and full causal sampled-search runs."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys
import time
import zlib
import numpy as np
import model as m
import protocol as p

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=HERE.parent/'python-game-unified-v27-study'
n=m.load_module('runtime28_native',HERE.parent/'python-game-native-motion-v25-study/benchmark.py')
search=m.load_module('runtime28_search',HERE.parent/'python-game-search-v28-study/model.py')


def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def raw(d,folder=HERE):return n.raw(d,folder)


def blob(data):
    compressed=zlib.compress(data,9);name='objects/'+hashlib.sha256(compressed).hexdigest()+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(compressed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(compressed).hexdigest())


def pins():
    old=load(OLD/'results.json');paths={ROOT/q for q in old['source_sha256']}
    paths|={OLD/'results.json',n.V24/'results.json'}|set(HERE.glob('*.py'))|{HERE/'README.md',HERE/'SCHEMA.md'}
    paths|={HERE.parent/folder/'model.py' for folder in ('python-game-search-v28-study','python-game-taps-v28-study')}
    for c in old['cases']:
        if c['policy']!='unified_causal':continue
        for r in c['rows']:
            paths|={OLD/r[k]['path'] for k in ('packet','base_packet','ack')}
            paths.add(ROOT/r['hud_packet']['directory']/r['hud_packet']['path'])
    return {q.relative_to(ROOT).as_posix():sha(q) for q in sorted(paths)}


def elapsed(fn):
    begin=time.perf_counter_ns();out=fn();return out,(time.perf_counter_ns()-begin)/1e6


def parity_case(inp,old):
    ref=None;rows=[]
    for src,prior in zip(inp['rows'],old['rows']):
        fid=src['id'];key=prior['key']
        if key:ref=None
        source=n.source(src);kind=prior['selected_kind'];q=m.roi.declared_map(720,480,n.ROIS,8,prior['selected_background'])
        prepared=m.base.analyze_planes(source,ref,epoch=25,frame_id=fid,reference_id=prior['reference_id'],block_size=32,
                                       motion_mode='zero' if kind=='zero' else 'block',motion_precision='half',penalty=0)
        values={};times={}
        for name in (('frozen','lazy') if fid%2==0 else ('lazy','frozen')):
            values[name],times[name]=elapsed(lambda:(m.base.encode_prepared if name=='frozen' else m.encode_prepared)(prepared,q,rdo_lambda=1))
        frozen,oldout,oldwork=values['frozen'];new,out,work=values['lazy']
        retained=raw(prior['base_packet'],OLD);assert frozen==new==retained
        for a,b in zip(oldout,out):np.testing.assert_array_equal(a,b)
        decoded,meta=m.decode(new,ref,expected_epoch=25,expected_reference_id=None if key else prior['reference_id'])
        for a,b in zip(out,decoded):np.testing.assert_array_equal(a,b)
        bare=m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded));original=n.original(src)
        hybrid=n.overlay(bare,tuple(original[y:y+h,x:x+w] for x,y,w,h in n.RECTS))
        assert n.digest(hybrid)==prior['hybrid_rgb565_sha256'] and meta['reconstructed_tag'].hex()==prior['reconstructed_tag']
        rows.append(dict(id=fid,key=key,reference_id=prior['reference_id'],selected_kind=kind,background=prior['selected_background'],
                         packet=blob(new),analysis_ms=prepared.work['analysis_wall_ms'],frozen_ms=times['frozen'],lazy_ms=times['lazy'],
                         frozen_work=oldwork,lazy_work=work,packet_bytes_equal=True,reference_tag=meta['reference_tag'].hex(),reconstructed_tag=meta['reconstructed_tag'].hex()))
        ref=decoded
    a=sum(r['frozen_ms'] for r in rows);b=sum(r['lazy_ms'] for r in rows)
    summary=dict(frames=48,mean_frozen_encode_ms=a/48,mean_lazy_encode_ms=b/48,encode_speedup=a/b,
                 frozen_cp02_constructions=sum(r['frozen_work']['legacy_cp02_encode_calls'] for r in rows),
                 lazy_cp02_constructions=sum(r['lazy_work']['actual_cp02_encode_calls'] for r in rows),
                 frozen_sp01_constructions=sum(r['frozen_work']['legacy_sp01_construct_calls'] for r in rows),
                 lazy_sp01_constructions=sum(r['lazy_work']['actual_sp01_construct_calls'] for r in rows),
                 lazy_size_counter_calls=sum(r['lazy_work']['legacy_size_counter_calls'] for r in rows),
                 complete_packet_parity=True)
    result=dict(scene=inp['scene'],rows=rows,summary=summary);print(json.dumps(dict(parity=inp['scene'],summary=summary)),flush=True);return result


def attempt(prepared,qmap,kind,bg,hud,original,ref,refid,slot):
    (base,expected,work),encode_ms=elapsed(lambda:m.encode_prepared(prepared,qmap,rdo_lambda=1))
    (decoded,meta),debug_ms=elapsed(lambda:m.decode(base,ref,expected_epoch=25,expected_reference_id=None if prepared.key else refid))
    for a,b in zip(decoded,expected):np.testing.assert_array_equal(a,b)
    began=time.perf_counter_ns();bare=m.C.corpus.rgb565(m.ft.planes_to_rgb(expected))
    hybrid=n.overlay(bare,tuple(original[y:y+h,x:x+w] for x,y,w,h in n.RECTS));quality=n.metric(original,hybrid)
    quality_ms=(time.perf_counter_ns()-began)/1e6
    began=time.perf_counter_ns();flags=p.PUBLISH|(p.KEY if prepared.key else 0)
    pair=p.seal(p.PAIR.pack(b'CP27',1,flags,25,prepared.frame_id,p.NO_SLOT if prepared.key else slot,0 if prepared.key else 1-slot,
                          len(base),len(hud),p.digest(base),p.digest(hud))+base+hud)
    fits=len(pair)<=49152
    if fits:p.parse_pair(pair)
    else:
        try:p.parse_pair(pair)
        except ValueError:pass
        else:raise AssertionError('overcap accepted')
    bind_ms=(time.perf_counter_ns()-began)/1e6
    item=dict(kind=kind,background=bg,base_packet=blob(base),packet=blob(pair),base_bytes=len(base),complete_bytes=len(pair),cap_fit=fits,
              work=work,encode_ms=encode_ms,offline_debug_decode_ms=debug_ms,quality_ms=quality_ms,bind_ms=bind_ms,
              hybrid=quality,hybrid_rgb565_sha256=n.digest(hybrid),reconstructed_tag=meta['reconstructed_tag'].hex())
    return item,pair,expected,hybrid


def summarize(rows,baseline):
    count=len(rows);total=sum(r['body_bytes'] for r in rows);sse=sum(r['hybrid']['active_squared_error'] for r in rows);samples=sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=count,complete_bytes=total,coded_body_Mbps_at30=total*240/count/1e6,
                base_bytes=sum(r['base_bytes'] for r in rows),hud_bytes=sum(r['hud_bytes'] for r in rows),binding_bytes=60*count,
                maximum_complete_bytes=max(r['body_bytes'] for r in rows),cap_fit_frames=sum(r['body_bytes']<=49152 for r in rows),
                active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples,active_psnr_db=10*math.log10(65025/(sse/samples)),
                hud_word_errors=sum(r['hybrid']['hud_word_errors'] for r in rows),exact_hud_words=21120*count,
                paid_candidate_encodes=sum(len(r['attempts']) for r in rows),paid_analyses=sum(len(r['analyses']) for r in rows),
                mean_paid_base_encode_ms=sum(r['paid_base_encode_ms'] for r in rows)/count,
                mean_base_policy_service_ms=sum(r['base_policy_service_ms'] for r in rows)/count,
                mean_receiver_ms=sum(r['receive_ms'] for r in rows)/count,
                mean_ack_validation_ms=sum(r['ack_ms'] for r in rows)/count,
                sad_sample_operations=sum(v['search']['sad_sample_operations'] for r in rows for v in r['analyses'].values()),
                search_reference_fetches=sum(v['search'].get('reference_sample_fetches',0) for r in rows for v in r['analyses'].values()),
                selected_decoder_reference_fetches=sum(next(a for a in r['attempts'] if a['selected'])['work']['decoder_reference_sample_reads'] for r in rows),
                selected_half32_frames=sum(r['selected_kind']=='half32' for r in rows),
                coarse_fallback_frames=[r['id'] for r in rows if r['selected_background']==32],
                actual_cp02_constructions=sum(a['work']['actual_cp02_encode_calls'] for r in rows for a in r['attempts']),
                baseline_complete_bytes=baseline['summary']['complete_bytes'],baseline_active_mse=baseline['summary']['active_mse'],
                byte_ratio_to_v27=total/baseline['summary']['complete_bytes'],mse_ratio_to_v27=(sse/samples)/baseline['summary']['active_mse'])


def campaign(inp,old,policy):
    rx=p.Receiver(epoch=25);ref=None;refid=m.NO_REF;slot=0;rows=[]
    for srcrow,prior in zip(inp['rows'],old['rows']):
        fid=srcrow['id'];key=fid%24==0
        if key:ref=None;refid=m.NO_REF;slot=0
        source=n.source(srcrow);original=n.original(srcrow);hud=raw(prior['hud_packet'],ROOT/prior['hud_packet']['directory'])
        kinds=('zero',) if key else ('zero','half32');prepared={};analyses={}
        for kind in kinds:
            kwargs=dict(epoch=25,frame_id=fid,reference_id=refid,block_size=32,motion_mode='zero' if kind=='zero' else 'block',motion_precision='half',penalty=0)
            prepared[kind]=(m.base.analyze_planes(source,ref,**kwargs) if policy=='exhaustive' else
                            search.analyze_with(m.base,source,ref,search_policy=policy,**kwargs))
            analyses[kind]=prepared[kind].work
        attempts=[];selected=None
        for bg in (16,32):
            qmap=m.roi.declared_map(720,480,n.ROIS,8,bg);group=[]
            for kind in kinds:
                result=attempt(prepared[kind],qmap,kind,bg,hud,original,ref,refid,slot);attempts.append(result[0]);group.append(result)
            zero_sse=group[0][0]['hybrid']['active_squared_error']
            for a,*_ in group:a['quality_eligible']=a['hybrid']['active_squared_error']<=zero_sse
            eligible=[a for a in group if a[0]['cap_fit'] and a[0]['quality_eligible']]
            if eligible:selected=min(eligible,key=lambda a:a[0]['complete_bytes']);break
        assert selected is not None
        info,pair,expected,expected_hybrid=selected
        for a in attempts:a['selected']=a is info
        (decoded,patches,ack),receive_ms=elapsed(lambda:rx.receive(pair))
        ackmeta,ack_ms=elapsed(lambda:p.validate_ack(ack,pair))
        for a,b in zip(decoded,expected):np.testing.assert_array_equal(a,b)
        for patch,(x,y,w,h) in zip(patches,n.RECTS):np.testing.assert_array_equal(patch['words'],original[y:y+h,x:x+w])
        hybrid=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded)),tuple(v['words'] for v in patches));np.testing.assert_array_equal(hybrid,expected_hybrid)
        if policy=='exhaustive':
            assert pair==raw(prior['packet'],OLD) and ack==raw(prior['ack'],OLD)
            assert n.digest(hybrid)==prior['hybrid_rgb565_sha256'] and info['hybrid']==prior['hybrid']
        paid=sum(v['analysis_wall_ms'] for v in analyses.values())+sum(a['encode_ms'] for a in attempts)
        service=paid+sum(a['quality_ms']+a['bind_ms'] for a in attempts)
        rows.append(dict(id=fid,key=key,reference_id=refid,source_slot=p.NO_SLOT if key else slot,destination_slot=0 if key else 1-slot,
                         source_common_yuv_sha256=srcrow['common_yuv420_u8_sha256'],selected_kind=info['kind'],selected_background=info['background'],
                         packet=info['packet'],base_packet=info['base_packet'],body_bytes=len(pair),base_bytes=info['base_bytes'],hud_bytes=len(hud),binding_bytes=60,
                         hud_packet=prior['hud_packet'],ack=blob(ack),ack_meta=ackmeta,attempts=attempts,analyses=analyses,
                         paid_base_encode_ms=paid,base_policy_service_ms=service,receive_ms=receive_ms,ack_ms=ack_ms,
                         hybrid=info['hybrid'],hybrid_rgb565_sha256=n.digest(hybrid),reconstructed_tag=info['reconstructed_tag'],
                         exact_v27_wire_parity=policy=='exhaustive'))
        ref,refid,slot=decoded,fid,0 if key else 1-slot
    result=dict(scene=inp['scene'],policy=policy,rows=rows,summary=summarize(rows,old))
    print(json.dumps(dict(scene=inp['scene'],policy=policy,summary=result['summary'])),flush=True);return result


def main():
    before=pins();old=load(OLD/'results.json');inputs=load(n.V24/'results.json')['inputs']
    parity=[parity_case(inp,next(c for c in old['cases'] if c['scene']==inp['scene'] and c['policy']=='unified_causal')) for inp in inputs]
    assert pins()==before
    (HERE/'parity.json').write_text(json.dumps(dict(schema='gamebub-lazy-parity-v28',source_sha256=before,cases=parity,
            scope='Same actual Prepared/decoded v27 references, rotated old/new encode timing; all selected96 packets exact.'),separators=(',',':'))+'\n')
    cases=[]
    for inp in inputs:
        prior=next(c for c in old['cases'] if c['scene']==inp['scene'] and c['policy']=='unified_causal')
        for policy in ('exhaustive','sample4_refine2','sample2'):
            cases.append(campaign(inp,prior,policy));assert pins()==before
            data=dict(schema='gamebub-runtime-v28',source_sha256=before,cases=cases,
                scope=['Same GM27/CP27 wire; exhaustive optimized reproduces exact v27 accepted bytes/ACKs/pixels.',
                       'Sampled search changes source-side choices and later reconstructed refs; original source is never a decoder reference.',
                       'Complete49,152 cap and exact21,120 HUD words; all losing attempts/quality/bind work paid.',
                       'Nominal30IDs/s byte projections on96reused29.88fps sourceimages; no native/FPGA/RF/physical30FPS.',
                       'Basepolicy service includes analysis,encode,sourceSSEquality andbinding; excludesoffline decoder checks,blobIO,HUDcapture/encode,networkwait andpresentation.'])
            (HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')


if __name__=='__main__':main()
