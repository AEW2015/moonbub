#!/usr/bin/env python3
"""Actual RG01 packet/quality comparisons; offline bounded ROI budget search."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import av
import numpy as np
import PIL
from PIL import Image,ImageDraw,ImageFont
import roi_codec as rc

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus
INDICES=(0,2,4,6,8,10,12,14)
RECTS=((16,48,192,80),(160,352,400,80))
MAX_MIDPOINT_TRIALS=8


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psnr(mse):return None if mse==0 else float(10*np.log10(65025/mse))


def roi_mask(w,h,rects):
    mask=np.zeros((h,w),bool)
    for x,y,rw,rh in rects:mask[y:y+rh,x:x+rw]=True
    return mask


def metric(source,decoded,rects,active,synthetic=False):
    reconstructed=corpus.expand565(corpus.rgb565(decoded))
    delta=source.astype(np.float64)-reconstructed.astype(np.float64)
    squared=np.mean(delta*delta,axis=2)
    h,w=squared.shape;roi=roi_mask(w,h,rects);active_mask=np.zeros((h,w),bool)
    x,y,rw,rh=active;active_mask[y:y+rh,x:x+rw]=True
    masks={'active':active_mask,'roi':active_mask&roi,'background':active_mask&~roi}
    out={}
    for key,mask in masks.items():
        mse=float(np.mean(squared[mask]));out[key]={'mse':mse,'psnr':psnr(mse),'pixels':int(mask.sum())}
    def luma(a):
        b=a.astype(np.int32);return (77*b[...,0]+150*b[...,1]+29*b[...,2]+128)>>8
    sy,ry=luma(source),luma(reconstructed)
    errors=[]
    for axis in (0,1):
        sd,rd=np.diff(sy,axis=axis),np.diff(ry,axis=axis)
        m=(masks['roi'][1:]&masks['roi'][:-1]) if axis==0 else (masks['roi'][:,1:]&masks['roi'][:,:-1])
        m &= np.abs(sd)>=16
        errors.extend(np.abs(sd-rd)[m].tolist())
    out['roi_edge_gradient_mae']=float(np.mean(errors)) if errors else None
    out['roi_edge_samples']=len(errors)
    if synthetic:
        out['synthetic_roi_threshold_error_rate']=float(np.mean(((sy>=160)!=(ry>=160))[masks['roi']]))
    return out


def synthetic_fixtures():
    yy,xx=np.mgrid[:480,:720];rng=np.random.default_rng(0x707)
    for i in range(2):
        texture=rng.integers(-20,21,(480,720),dtype=np.int16)
        source=np.stack(((xx//4+yy//3+texture+i*31)%256,(xx//3+texture+51)%256,
                         (yy//2+texture+93)%256),axis=-1).astype(np.uint8)
        image=Image.fromarray(source);draw=ImageDraw.Draw(image)
        for x,y,w,h in RECTS:draw.rectangle((x,y,x+w-1,y+h-1),fill=(12,16,24))
        font=ImageFont.load_default(size=18 if i==0 else 14)
        draw.text((22,54),'HP 097 / 100',font=font,fill=(238,244,250))
        draw.text((22,78),'SHIELD 042',font=font,fill=(180,230,250))
        draw.rectangle((24,106,184,112),fill=(70,200,130))
        draw.text((168,361),'MISSION: REACH THE CITADEL',font=font,fill=(245,242,218))
        draw.text((168,389),'AMMO 024   ENERGY 087%',font=font,fill=(220,230,245))
        yield f'seeded-HUD-{i}',np.asarray(image).copy()


def activity_order(rgb,roi_scale_map):
    # Current-frame source luma activity only: no future frame/error/size oracle.
    p=rc.ft.rgb_to_planes(rgb)[0].astype(np.int32)
    ph,pw=((p.shape[0]+15)//16)*16,((p.shape[1]+15)//16)*16
    p=np.pad(p,((0,ph-p.shape[0]),(0,pw-p.shape[1])),mode='edge')
    blocks=p.reshape(ph//16,16,pw//16,16).transpose(0,2,1,3)
    score=(np.abs(np.diff(blocks,axis=2)).mean((2,3))+
           np.abs(np.diff(blocks,axis=3)).mean((2,3))).reshape(-1)
    eligible=np.flatnonzero(roi_scale_map.reshape(-1)!=8)
    return eligible[np.lexsort((eligible,score[eligible]))]


def evaluate(rgb,scale_map,rects,active,synthetic):
    begin=time.perf_counter_ns();packet=rc.encode(rgb,scale_map)
    encode_ms=(time.perf_counter_ns()-begin)/1e6
    begin=time.perf_counter_ns();decoded=rc.decode(packet)
    decode_ms=(time.perf_counter_ns()-begin)/1e6
    coeffs=rc.quantized(rgb,scale_map);h,w=rgb.shape[:2]
    golden=rc.ft.planes_to_rgb(rc.reconstruct_planes(coeffs,scale_map,w,h))
    np.testing.assert_array_equal(decoded,golden)
    info=rc.info(packet)
    return dict(packet=packet,map=scale_map,bytes=len(packet),encode_wall_ms=encode_ms,decode_wall_ms=decode_ms,
                metrics=metric(rgb,decoded,rects,active,synthetic),info=info,
                packet_sha256=hashlib.sha256(packet).hexdigest(),rgb_sha256=hashlib.sha256(decoded.tobytes()).hexdigest())


def serial(row):return {k:v for k,v in row.items() if k not in ('packet','map')}


def budget_policy(rgb,base16,roi8bg16,roi8bg32,rects,active,synthetic):
    cap=base16['bytes'];order=activity_order(rgb,roi8bg16['map']);n=len(order)
    candidate_rows=[dict(coarsened_background_blocks=0,bytes=roi8bg16['bytes'],encode_wall_ms=roi8bg16['encode_wall_ms']),
                    dict(coarsened_background_blocks=n,bytes=roi8bg32['bytes'],encode_wall_ms=roi8bg32['encode_wall_ms'])]
    best=roi8bg32 if roi8bg32['bytes']<=cap else None
    if roi8bg16['bytes']<=cap:best=roi8bg16
    lo,hi=0,n
    extra=[]
    for _ in range(MAX_MIDPOINT_TRIALS):
        if lo>hi:break
        mid=(lo+hi)//2
        m=roi8bg16['map'].copy();m.reshape(-1)[order[:mid]]=32
        row=evaluate(rgb,m,rects,active,synthetic)
        candidate_rows.append(dict(coarsened_background_blocks=mid,bytes=row['bytes'],encode_wall_ms=row['encode_wall_ms']))
        extra.append(row)
        if row['bytes']<=cap:
            if best is None or row['bytes']>best['bytes']:best=row
            hi=mid-1
        else:lo=mid+1
    # Best observed feasible packet, not a proof of monotonicity or RD optimality.
    return best,dict(cap_bytes=cap,admitted=best is not None,attempts=len(candidate_rows),
                     max_midpoint_trials=MAX_MIDPOINT_TRIALS,candidates=candidate_rows,
                     total_charged_encode_ms=sum(r['encode_wall_ms'] for r in candidate_rows),
                     reference_uniform16_encode_ms=base16['encode_wall_ms'],
                     total_reference_and_search_encode_ms=base16['encode_wall_ms']+sum(r['encode_wall_ms'] for r in candidate_rows),
                     extra_candidate_decode_ms=sum(r['decode_wall_ms'] for r in extra),
                     budget_utilization=None if best is None else best['bytes']/cap,
                     scope='Offline candidate rate search. Endpoint encoding is charged even though benchmark reused it; transform/color/activity/map construction and all candidate decodes/quality checks add work. No real-time bound or optimality guarantee.')


def main():
    paths=[HERE/'benchmark.py',HERE/'roi_codec.py',HERE/'test_roi_codec.py',Path(rc.ft.__file__),Path(rc.cc.__file__),
           Path(rc.token_coeff.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in paths};scenes=[]
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    inputs=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=16,start_seconds=4)
        for i in INDICES:
            inputs.append((f'{clip}-frame{i}',frames[i],manifest,i,tuple(manifest['active_rects'][i]),False))
    for name,rgb in synthetic_fixtures():
        manifest={'source':'synthetic:'+name,'seed':'0x707','frame_sha256':[hashlib.sha256(rgb.tobytes()).hexdigest()],
                  'active_rects':[(0,0,720,480)],'frame_count':1,'synthetic':True}
        inputs.append((name,rgb,manifest,0,(0,0,720,480),True))
    for name,rgb,manifest,index,active,synthetic in inputs:
        h,w=rgb.shape[:2];mw,mh=rc.geometry(w,h)
        maps={f'uniform{s}':np.full((mh,mw),s,np.uint8) for s in rc.SCALES}
        maps.update(roi8bg16=rc.declared_map(w,h,RECTS,8,16),roi8bg32=rc.declared_map(w,h,RECTS,8,32),
                    roi16bg32=rc.declared_map(w,h,RECTS,16,32))
        rows={label:evaluate(rgb,m,RECTS,active,synthetic) for label,m in maps.items()}
        best,policy=budget_policy(rgb,rows['uniform16'],rows['roi8bg16'],rows['roi8bg32'],RECTS,active,synthetic)
        if best is not None:rows['budget_roi8mix']=best
        comparisons=[]
        for label in ('roi8bg16','roi8bg32','roi16bg32','budget_roi8mix'):
            if label not in rows:continue
            roi=rows[label];baseline=rows['uniform16'];relative=roi['bytes']/baseline['bytes']-1
            comparisons.append(dict(profile=label,baseline='uniform16',byte_delta=roi['bytes']-baseline['bytes'],
                                    relative_byte_delta=relative,within_5_percent_bytes=abs(relative)<=.05,
                                    active_psnr_delta=roi['metrics']['active']['psnr']-baseline['metrics']['active']['psnr'],
                                    roi_psnr_delta=roi['metrics']['roi']['psnr']-baseline['metrics']['roi']['psnr'],
                                    background_psnr_delta=roi['metrics']['background']['psnr']-baseline['metrics']['background']['psnr'],
                                    roi_edge_gradient_mae_delta=roi['metrics']['roi_edge_gradient_mae']-baseline['metrics']['roi_edge_gradient_mae']))
        scenes.append(dict(name=name,manifest=manifest,source_index=index,input_sha256=manifest['frame_sha256'][index],
                           synthetic=synthetic,declared_rectangles=RECTS,profiles={k:serial(v) for k,v in rows.items()},
                           budget_policy=policy,comparisons=comparisons))
        match=next((r for r in comparisons if r['profile']=='budget_roi8mix'),None)
        print(name,'budget',policy['admitted'],policy['budget_utilization'],'quality',match,flush=True)
    assert hashes=={str(p):digest(p) for p in paths},'sources changed'
    result=dict(evidence='Actual independent-frame RG01 packets, frozen reconstruction and offline ROI rate/quality comparison; no temporal/hardware/FPS qualification',
                versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
                source_sha256=hashes,declared_real_roi_scope='Fixed rectangles are declared priorities, not detected or verified game HUD locations.',
                corpus_scope='Eight predeclared native frame indices per related precompressed clip at4s; no interpolation, content may repeat. Two separately labeled synthetic HUD fixtures.',
                indices=INDICES,scene_count=len(scenes),scenes=scenes,
                syntax=dict(magic='RG01',map='16x16 luma /8x8chroma, explicit2bit scale8/16/32',map_bytes_720x480=338,
                            outer_header_crc_bytes=rc.HEADER.size+4,full_cp02_header_crc_charged=True),
                metric_scope='Active/ROI/backgroundRGB565PSNR and luma edgegradienterror. No OCR/visual acceptance. Quality trades background against declaredROI; no perceptualfloor.',
                budget_scope='All search candidates are really encoded/decoded. Up to8 midpoint trials plus2 charged endpoints, choose bestobserved feasible bytes; no monotonicity/optimality or realtime claim.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
