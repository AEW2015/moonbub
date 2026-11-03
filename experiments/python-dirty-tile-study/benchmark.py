#!/usr/bin/env python3
"""Content eligibility and byte/quality study, not a transport FPS benchmark."""
import hashlib
import json
import math
import platform
import importlib.metadata
import os
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image,ImageDraw
import tile_codec as dt

HERE=Path(__file__).resolve().parent
for name in ('python-codec-study','python-token-entropy-study'):
    sys.path.insert(0,str(HERE.parent/name))
import corpus
import token_key_encoder


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psnr(mse):return None if mse==0 else float(10*np.log10(65025/mse))
def wire_bytes(size):return size+68*math.ceil(size/1024)


def synthetic(scrolling=False):
    yy,xx=np.mgrid[:480,:720]
    frames=[]
    for i in range(12):
        if scrolling:
            value=((xx+i*5)//12*13+yy//12*7)%128
            rgb=np.stack((value+20,value//2+15,value//3+20),axis=2).astype(np.uint8)
        else:
            rgb=np.full((480,720,3),(18,25,32),np.uint8)
            rgb[::32]=42;rgb[:,::32]=42
        rgb[:64]=(20,20,24)
        image=Image.fromarray(rgb)
        draw=ImageDraw.Draw(image)
        draw.rectangle((12,12,212,24),fill=(190,35,35))
        draw.text((12,36),'HP 100 / 100    AMMO 30   MISSION 01',fill=(245,245,245))
        draw.rectangle((260+i*13,210,279+i*13,229),fill=(45,210,90))
        frames.append(np.array(image))
    manifest={'source':'synthetic-scrolling-hud' if scrolling else 'synthetic-static-hud',
              'frame_count':len(frames),'frame_sha256':[hashlib.sha256(a.tobytes()).hexdigest() for a in frames],
              'active_rects':[(0,0,720,480)]*len(frames),'generator':'benchmark.py fixed procedural12 frames; not actual HUD/game footage',
              'native_fps':None}
    return frames,manifest


def run_scene(frames,manifest):
    dirty=dt.Encoder();receiver=dt.Receiver();anchor=token_key_encoder.Encoder()
    anchor_rx=token_key_encoder.frozen.AnchorReceiver()
    records=[]
    for i,rgb in enumerate(frames):
        start=time.perf_counter()
        packet,info=dirty.prepare(rgb,i,quant_scale=8)
        actual,decoded=receiver.receive(packet)
        np.testing.assert_array_equal(actual,dirty.expected_rgb())
        dirty.ack(i,epoch=1)
        intra=dt.entropy.encode(rgb,8);intra_rgb=dt.cc.decode(intra)
        temporal=anchor.prepare(rgb,i,quant_scale=8,mode='zero')
        anchor_rgb,_=anchor_rx.receive(temporal)
        assert hashlib.sha256(anchor_rgb.tobytes()).hexdigest()==anchor.expected_hash(i)
        anchor.ack(i,epoch=1)
        rect=tuple(manifest['active_rects'][i])
        row={'id':i,'input_sha256':manifest['frame_sha256'][i],'dirty':dict(info,**{k:v for k,v in decoded.items() if k.startswith('logical_')}),
             'packets':{},'python_wall_seconds_all_profiles_and_oracles':time.perf_counter()-start}
        for name,data,image in (('dirty',packet,actual),('whole_intra',intra,intra_rgb),('immutable_anchor',temporal,anchor_rgb)):
            output=corpus.expand565(corpus.rgb565(image))
            row['packets'][name]={'bytes':len(data),'wire_bytes':wire_bytes(len(data)),
                                  'packet_sha256':hashlib.sha256(data).hexdigest(),
                                  'active_mse':corpus.metrics(rgb,output,rect)['active']['mse'],
                                  'over_48k_cap':len(data)>49152}
        records.append(row)
    summaries={}
    for name in ('dirty','whole_intra','immutable_anchor'):
        rows=[r['packets'][name] for r in records]
        tail=rows[1:]
        summaries[name]={'packet_mean_bytes':float(np.mean([r['bytes'] for r in rows])),
                         'tail_mean_bytes':float(np.mean([r['bytes'] for r in tail])),
                         'wire_mbps_if30captures_per_second':sum(r['wire_bytes'] for r in rows)/len(rows)*8*30/1e6,
                         'pooled_active_mse':float(np.mean([r['active_mse'] for r in rows])),
                         'pooled_active_psnr_db':psnr(np.mean([r['active_mse'] for r in rows])),
                         'over_48k_cap':sum(r['over_48k_cap'] for r in rows)}
    return {'manifest':manifest,'records':records,'summary':summaries,
            'skipped_tiles_total':sum(r['dirty']['skipped_tiles'] for r in records),
            'tile_opportunities':sum(r['dirty']['tiles'] for r in records),
            'fully_unchanged_source_frames':sum(r['dirty']['changed_tiles']==0 for r in records),
            'scope':'Immediate in-process ACK after exact decode. Byte demand/quality only, not a finite link schedule. All packets including overcap decoded for study; they are failures for a48KiB receiver.'}


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    sources=[HERE/'benchmark.py',HERE/'tile_codec.py',Path(dt.entropy.__file__),Path(dt.cc.__file__),Path(dt.ft.__file__),
             Path(corpus.__file__),Path(token_key_encoder.__file__),Path(token_key_encoder.fast_anchor.__file__),
             HERE.parent/'python-fast-entropy-study/fast_coeff.py',Path(token_key_encoder.frozen.__file__),Path(token_key_encoder.frozen.mt.__file__)]
    hashes={str(p):digest(p) for p in sources};scenes=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=12,start_seconds=4)
        scenes.append(run_scene(frames,manifest))
        print(clip,scenes[-1]['summary'],'skip',scenes[-1]['skipped_tiles_total'],'/',scenes[-1]['tile_opportunities'],flush=True)
    for scrolling in (False,True):
        frames,manifest=synthetic(scrolling);scenes.append(run_scene(frames,manifest))
        print(manifest['source'],scenes[-1]['summary'],'skip',scenes[-1]['skipped_tiles_total'],'/',scenes[-1]['tile_opportunities'],flush=True)
    assert hashes=={str(p):digest(p) for p in sources},'source changed'
    result={'evidence':'Actual DT01 tiled packets+reconstruction with immediateACK; no transport/performance/hardware proof',
            'source_sha256':hashes,'scenes':scenes,'versions':{'python':platform.python_version(),**{name:importlib.metadata.version(name) for name in ('numpy','Pillow','av')}},
            'codec':'32x32 RGB source-equality dirty map; independent FT02 quant8 tiles, nested and full CRC; distinct DT01 profile',
            'comparison':'Same source captures, different reconstructed pixels and chroma/tile edges; no equal-quality claim',
            'memory':'Host retains ACKed original and reconstructed uint8 RGB plus pending copies; receiver retains RGB. LogicalRGB565copy accounting is not physicalSDRAMbandwidth.',
            'policy':'No change detector threshold, future oracle, adaptive cap search or partial-send fallback. Only ACKed source byte equality authorizes SKIP.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
