#!/usr/bin/env python3
"""Matched reconstructed-reference and first12-frame closed-loop ablations."""
from pathlib import Path
import importlib.util,sys,json,hashlib,time,zlib,math
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
NATIVE=HERE.parent/'python-game-native-motion-v25-study'
CAPPED=HERE.parent/'python-game-capped-key-v25-study'
spec=importlib.util.spec_from_file_location('prediction26_native',NATIVE/'benchmark.py')
n=importlib.util.module_from_spec(spec);sys.modules[spec.name]=n;spec.loader.exec_module(n)
FRAMES=12
VARIANTS={'zero':dict(motion_mode='zero',motion_precision='coarse'),
          'integer':dict(motion_mode='block',motion_precision='integer'),
          'half':dict(motion_mode='block',motion_precision='half')}

def blob(data):
    stored=zlib.compress(data,9);name='objects/'+hashlib.sha256(stored).hexdigest()+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(stored)
    return dict(path=name,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(stored).hexdigest())

def pins():
    prior=n.load(CAPPED/'results.json'); paths={ROOT/p for p in prior['source_sha256']}
    paths|={CAPPED/'results.json',NATIVE/'benchmark.py'}
    paths|=set(HERE.glob('*.py'))
    for case in prior['cases']:
        if case['profile']=='capped_key_zero_rdo1':
            for row in case['rows'][:FRAMES]:paths.add(CAPPED/row['base_packet']['path'])
    old=n.load(n.V24/'results.json')
    for inp in old['inputs']:
        for row in inp['rows'][:FRAMES]:
            for key in ('common_yuv420_u8','original_rgb565'):paths.add(n.V24/row[key]['path'])
    return {p.relative_to(ROOT).as_posix():n.sha(p) for p in sorted(paths)}

def summary(rows):
    error=sum(r['hybrid']['active_squared_error'] for r in rows);samples=sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=len(rows),base_bytes=sum(r['base_bytes'] for r in rows),base_Mbps_at30=sum(r['base_bytes'] for r in rows)*240/len(rows)/1e6,
                active_mse=error/samples,active_squared_error=error,active_channel_samples=samples,
                active_psnr_db=10*math.log10(65025/(error/samples)),hud_word_errors=sum(r['hybrid']['hud_word_errors'] for r in rows),
                mv_bytes=sum(r['work']['vector_bytes'] for r in rows),coefficient_bytes=sum(r['work']['coefficient_bytes'] for r in rows),
                mean_encoder_ms=sum(r['work']['encoder_wall_ms'] for r in rows)/len(rows),
                search_sample_operations=sum(r['work']['analysis']['search']['sad_sample_operations'] for r in rows),
                search_reference_fetches=sum(r['work']['analysis']['search'].get('reference_sample_fetches',0) for r in rows),
                decoder_reference_fetches=sum(r['work']['decoder_reference_sample_reads'] for r in rows))

def campaign(inp,frozen,kind,variant):
    ref=None;refid=m.NO_REF;frozen_ref=None;rows=[]
    for srcrow,oldrow in zip(inp['rows'][:FRAMES],frozen['rows'][:FRAMES]):
        fid=srcrow['id'];key=fid==0
        packet25=n.raw(oldrow['base_packet'],CAPPED)
        oldmeta=m.v25.parse(packet25)
        oldout,_=m.v25.decode(packet25,frozen_ref,expected_epoch=25,expected_reference_id=None if key else oldrow['reference_id'])
        if kind=='matched':ref=frozen_ref;refid=oldrow['reference_id']
        src=n.source(srcrow);orig=n.original(srcrow)
        packet,out,work=m.encode_planes(src,ref,oldmeta['scale_map'],epoch=26,frame_id=fid,reference_id=refid,
                                       block_size=16,penalty=0,rdo_lambda=1,**VARIANTS[variant])
        began=time.perf_counter_ns();decoded,meta=m.decode(packet,ref,expected_epoch=26,expected_reference_id=None if key else refid)
        decode_ms=(time.perf_counter_ns()-began)/1e6
        for a,b in zip(out,decoded):np.testing.assert_array_equal(a,b)
        patches=tuple(orig[y:y+h,x:x+w] for x,y,w,h in n.RECTS)
        bare=m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded));hybrid=n.overlay(bare,patches)
        metric=n.metric(orig,hybrid);assert metric['hud_word_errors']==0
        row=dict(id=fid,reference_id=refid,key=key,base_packet=blob(packet),base_bytes=len(packet),work=work,decode_ms=decode_ms,
                 hybrid=metric,bare=n.metric(orig,bare),bare_rgb565_sha256=n.digest(bare),hybrid_rgb565_sha256=n.digest(hybrid),
                 reconstructed_tag=meta['reconstructed_tag'].hex(),reference_tag=meta['reference_tag'].hex(),
                 frozen_base_bytes=oldrow['base_bytes'],frozen_hybrid=oldrow['hybrid'])
        if fid in (0,1):
            row['golden_yuv420_i16']=blob(b''.join(p.astype('<i2').tobytes() for p in decoded))
            row['golden_hybrid_rgb565']=blob(hybrid.astype('<u2').tobytes())
        rows.append(row)
        if kind=='closed':ref=decoded;refid=fid
        frozen_ref=oldout
        print(json.dumps(dict(kind=kind,scene=inp['scene'],variant=variant,id=fid,bytes=len(packet),mse=metric['active_mse'])),flush=True)
    result=dict(kind=kind,scene=inp['scene'],variant=variant,rows=rows,summary=summary(rows))
    return result

def main():
    before=pins();old=n.load(n.V24/'results.json');prior=n.load(CAPPED/'results.json')
    result=dict(schema='gamebub-prediction-v26',source_sha256=before,frames_per_scene=FRAMES,cases=[],
                scope=['First12 retained frames per scene; 720x480coded, active rows37:442; no new captures.',
                       'Matched uses exact decoded capped_key_zero_rdo1 GM25 bank for every attempt; closed uses own prior decoded GM26 bank.',
                       'Each ablation uses the exact selected GM25 quantizer map, frozen coefficient entropy and RDO lambda1, no SAD-to-bits inference.',
                       'ExactHUD overlay from retained source; HUD transport is excluded from base-only rates.',
                       'Fixed policies independently pay every search,transform,entropy,RDO call; these are not an actual-byte fallback policy.',
                       'Rates are nominal30fps projections; no native hardware fit/timing or physical30fps evidence.'])
    for kind in ('matched','closed'):
        for inp in old['inputs']:
            frozen=next(c for c in prior['cases'] if c['scene']==inp['scene'] and c['profile']=='capped_key_zero_rdo1')
            for variant in VARIANTS:
                result['cases'].append(campaign(inp,frozen,kind,variant))
                assert before==pins(),'dependency changed'
                (HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
    (HERE/'sourcepins.json').write_text(json.dumps(before,indent=2)+'\n')
if __name__=='__main__':main()
