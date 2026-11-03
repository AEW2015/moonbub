#!/usr/bin/env python3
"""Actual same-source GM01/GH01 bytes and declared-region RGB565 fidelity."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
import PIL
import av
import hud_codec as hc

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('hud_v7_metrics',HERE.parent/'python-game-roi-study/benchmark.py')
metrics=importlib.util.module_from_spec(spec);sys.modules[spec.name]=metrics;spec.loader.exec_module(metrics)
RECTS=metrics.RECTS
INDICES=(0,2,4,6,8,10,12,14)
PROFILES=('uniform16','roi8bg16','uniform16_patch','roi8bg16_patch')


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psnr(mse):return None if mse==0 else float(10*np.log10(65025/mse))
def wire(size):return size+68*math.ceil(size/1024)


def summary(scenes):
    out={}
    for label,prefix in (('combat','mass-effect-combat'),('second_clip','mass-effect-2600'),('synthetic','seeded-HUD')):
        selected=[s for s in scenes if s['name'].startswith(prefix)]
        profiles={}
        for profile in PROFILES:
            rows=[s['profiles'][profile] for s in selected]
            regions={}
            for region in ('active','roi','background'):
                pixels=sum(r['metrics'][region]['pixels'] for r in rows)
                mse=sum(r['metrics'][region]['mse']*r['metrics'][region]['pixels'] for r in rows)/pixels
                regions[region]={'mse':mse,'psnr':psnr(mse),'pixels':pixels}
            profiles[profile]={'frames':len(rows),'packet_mean_bytes':float(np.mean([r['bytes'] for r in rows])),
                'min_bytes':min(r['bytes'] for r in rows),'max_bytes':max(r['bytes'] for r in rows),
                'over_48k_cap':sum(r['bytes']>49152 for r in rows),
                'regions':regions,'lossless_roi_rgb565_frames':sum(r['roi_rgb565_word_mismatches']==0 for r in rows),
                'wire_mbps_if30captures':sum(wire(r['bytes']) for r in rows)/len(rows)*8*30/1e6,
                'patch_mode_histogram':{str(mode):sum(p['mode']==mode for r in rows for p in r['patches']) for mode in (0,1,2,4,8)},
                'prepare_mean_ms':float(np.mean([r['prepare_ms'] for r in rows])),
                'receive_mean_ms':float(np.mean([r['receive_ms'] for r in rows])),
                'patch_encode_mean_ms':float(np.mean([r['wrapper_encode_stages_ms'].get('patch_encode_ms',0) for r in rows])),
                'overlay_mean_ms':float(np.mean([r['receive_stages_ms'].get('overlay_rgb565',0) for r in rows]))}
        out[label]=profiles
    return out


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    sources=[HERE/'benchmark.py',HERE/'hud_codec.py',HERE/'test_hud_codec.py',Path(hc.gm.__file__),
             Path(hc.gm.roi.__file__),Path(hc.gm.ft.__file__),Path(hc.gm.mt.__file__),
             Path(hc.gm.token_coeff.__file__),Path(hc.gm.word_coeff.__file__),Path(hc.gm.word_coeff.frozen_codec.__file__),
             Path(hc.corpus.__file__),HERE.parent/'python-game-roi-study/benchmark.py']
    hashes={str(p):digest(p) for p in sources};inputs=[];scenes=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=hc.corpus.load_video(media/f'{clip}.mp4',max_frames=16,start_seconds=4)
        for i in INDICES:inputs.append((f'{clip}-frame{i}',frames[i],manifest,i,tuple(manifest['active_rects'][i]),False))
    for name,rgb in metrics.synthetic_fixtures():
        manifest={'source':'synthetic:'+name,'seed':'0x707','frame_sha256':[hashlib.sha256(rgb.tobytes()).hexdigest()],
                  'frame_count':1,'synthetic':True,'active_rects':[(0,0,720,480)]}
        inputs.append((name,rgb,manifest,0,(0,0,720,480),True))
    for name,rgb,manifest,index,active,synthetic in inputs:
        h,w=rgb.shape[:2];mw,mh=hc.gm.roi.geometry(w,h);roi=metrics.roi_mask(w,h,RECTS)
        source_words=hc.corpus.rgb565(rgb);rows={}
        for label in PROFILES:
            mapped=np.full((mh,mw),16,np.uint8) if label.startswith('uniform16') else hc.gm.roi.declared_map(w,h,RECTS,8,16)
            enc=hc.gm.Encoder();started=time.perf_counter_ns()
            base=enc.prepare(rgb,0,scale_map=mapped)
            base_prepare_ms=(time.perf_counter_ns()-started)/1e6
            wrapper_stages={};packet=base
            if label.endswith('_patch'):
                packet,wrapper_stages=hc.encode_frame(base,rgb,RECTS,return_info=True)
            prepare_ms=base_prepare_ms+wrapper_stages.get('total_ms',0)
            rx=hc.Receiver() if label.endswith('_patch') else hc.gm.Receiver()
            started=time.perf_counter_ns();actual,info=rx.receive(packet);receive_ms=(time.perf_counter_ns()-started)/1e6
            expected=enc.expected_hash(0)
            if label.endswith('_patch'):
                assert info['base_rgb_sha256']==expected
                patches=info['patches'];receive_stages=info['stages_ms']
                assert len(packet)==hc.FRAME.size+4+len(base)+sum(4+p['bytes'] for p in patches)
            else:
                assert hashlib.sha256(actual.tobytes()).hexdigest()==expected
                patches=[];receive_stages={}
            enc.ack(0,epoch=1)
            words=hc.corpus.rgb565(actual);mismatches=int(np.count_nonzero(words[roi]!=source_words[roi]))
            if patches:assert mismatches==0
            row={'bytes':len(packet),'base_bytes':len(base),'patch_bytes':len(packet)-len(base),
                 'over_48k_cap':len(packet)>49152,'packet_sha256':hashlib.sha256(packet).hexdigest(),
                 'base_packet_sha256':hashlib.sha256(base).hexdigest(),'display_rgb565_sha256':hashlib.sha256(words.astype('<u2').tobytes()).hexdigest(),
                 'roi_rgb565_word_mismatches':mismatches,'patches':patches,'metrics':metrics.metric(rgb,actual,RECTS,active,synthetic),
                 'base_prepare_ms':base_prepare_ms,'wrapper_encode_stages_ms':wrapper_stages,'prepare_ms':prepare_ms,
                 'receive_ms':receive_ms,'receive_stages_ms':receive_stages,
                 'anchor_id':info['anchor_id'],'base_rgb_sha256':expected}
            rows[label]=row
        assert rows['roi8bg16']['base_packet_sha256']==rows['roi8bg16_patch']['base_packet_sha256']
        assert rows['uniform16']['base_packet_sha256']==rows['uniform16_patch']['base_packet_sha256']
        scenes.append({'name':name,'manifest':manifest,'source_index':index,'input_sha256':manifest['frame_sha256'][index],
                       'synthetic':synthetic,'rectangles':RECTS,'profiles':rows})
        print(name,{label:(r['bytes'],r['roi_rgb565_word_mismatches'],[p['mode'] for p in r['patches']]) for label,r in rows.items()},flush=True)
    assert hashes=={str(p):digest(p) for p in sources},'source changed'
    result={'evidence':'Actual GH01 display-only losslessRGB565 patches over GM01; independent keys, no temporal/transport/hardwareFPS proof',
            'source_sha256':hashes,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'pyav':av.__version__},
            'scenes':scenes,'summary':summary(scenes),'source_inputs':len(scenes),'records':sum(len(s['profiles']) for s in scenes),
            'format':{'wrapper_magic':'GH01','patch_magic':'HP01','wrapper_header_crc_bytes':hc.FRAME.size+4,
                      'patch_header_crc_bytes':hc.PATCH.size+4,'length_prefix_per_patch':4,'max_patches':hc.MAX_PATCHES,
                      'palette_modes':'1/2/4/8bit sortedRGB565 palette; RAW565 for >256colors'},
            'policy':{'rectangles':RECTS,'oracle_used_for_selection':False,'future_frames_used':0,'lookahead_frames':0,
                      'source_scope':'Fixed real rectangles are priorities, not verified/detected HUDs. SyntheticHUD fixtures are separately labeled.'},
            'timing_scope':'Python wall under uncontrolled load. Fullprepare chargesbaseGM plus wrapperbasevalidation+patchpalette/indexconstruction+assembly. Fullreceive includesduplicatebaseparse/CRC, statefulGMreceive, basehashverification andRGB565overlay. Optionalencoderoracle/sourcecapture/scaling/metrics/network/display excluded.',
            'quality_scope':'Lossless only versus originalRGB565 words in patches; sourceRGB888 quantization still loses precision. Patch neverchanges YUVprediction anchor. Allovercap packets decoded for algorithm study and counted failures.',
            'deployment_scope':'New GH01 wrapper not supported by existingGF01harness/MSV1/JPEG peers; requiresnegotiatedwrapperdecoder and realtargettests.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    for name,profiles in result['summary'].items():
        print(name,{p:{k:r[k] for k in ('packet_mean_bytes','over_48k_cap','lossless_roi_rgb565_frames','patch_mode_histogram')} for p,r in profiles.items()},flush=True)


if __name__=='__main__':main()
