#!/usr/bin/env python3
"""Paired actual arithmetic timings, exact frozen key bytes and inverse output."""
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import sys
import time
import zlib

import numpy as np
import bounded_math as bm

HERE=Path(__file__).resolve().parent
for directory in ('python-codec-study','python-key-prepare-study'):
    sys.path.insert(0,str(HERE.parent/directory))
import corpus
import key_encoder
mt=key_encoder.frozen.mt
fc=key_encoder.fast_coeff


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def summary(values):
    return {name:float(value) for name,value in zip(('mean','p50','p95','max'),
            (np.mean(values),*np.percentile(values,[50,95]),max(values)))}


def packet_from(coefficients, source, frame, scale):
    payload=b''.join(mt.LENGTH.pack(len(p))+p for p in
                    (fc.encode_coefficients(c,(s.shape[1]+7)//8) for c,s in zip(coefficients,source)))
    h,w=source[0].shape
    body=mt.HEADER.pack(b'MA01',1,1,frame,mt.NO_REF,scale,w,h,0,0,len(payload))+payload
    return body+struct.pack('<I',zlib.crc32(body))


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    sources=[HERE/'benchmark.py',HERE/'bounded_math.py',Path(mt.__file__),Path(bm.frozen.__file__),
             Path(fc.__file__),Path(fc.frozen.__file__),Path(key_encoder.__file__),
             Path(key_encoder.fast_anchor.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in sources}
    scenes=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=12,start_seconds=4)
        records=[]
        for repeat in range(3):
            for frame in (0,3,6,9):
                rgb=frames[frame];source=bm.frozen.rgb_to_planes(rgb)
                prediction=[np.full_like(p,128) for p in source]
                for scale in (8,32):
                    results={};timings={}
                    order=(('wide',mt),('bounded',bm)) if (frame+repeat+scale)%2==0 else (('bounded',bm),('wide',mt))
                    for label,module in order:
                        began=time.perf_counter_ns()
                        coefficients=module.residual_coefficients(source,prediction,scale)
                        transform_ms=(time.perf_counter_ns()-began)/1e6
                        began=time.perf_counter_ns()
                        rebuilt=module.reconstruct(coefficients,prediction,scale)
                        inverse_ms=(time.perf_counter_ns()-began)/1e6
                        results[label]=(coefficients,rebuilt)
                        timings[label]={'transform_ms':transform_ms,'reconstruct_ms':inverse_ms,
                                        'combined_ms':transform_ms+inverse_ms}
                    for a,b in zip(results['wide'][0]+results['wide'][1],results['bounded'][0]+results['bounded'][1]):
                        np.testing.assert_array_equal(a,b)
                    packet=packet_from(results['bounded'][0],source,frame,scale)
                    reference=key_encoder.Encoder()
                    assert reference.prepare(rgb,frame,quant_scale=scale,mode='zero')==packet
                    actual,_=key_encoder.frozen.AnchorReceiver().receive(packet)
                    rebuilt_rgb=bm.frozen.planes_to_rgb(results['bounded'][1])
                    np.testing.assert_array_equal(actual,rebuilt_rgb)
                    maxima=[int(np.abs(c.astype(np.int64)*bm.frozen.qtable(scale,i!=0)).max())
                            for i,c in enumerate(results['bounded'][0])]
                    records.append({'repeat':repeat,'frame':frame,'scale':scale,'input_sha256':manifest['frame_sha256'][frame],
                                    'packet_sha256':hashlib.sha256(packet).hexdigest(),'bytes':len(packet),
                                    'dequant_max_per_plane':maxima,
                                    'inverse_paths':['int32' if bm.stage_bounds(m,'inverse')['int32_safe'] else 'int64' for m in maxima],
                                    'timings':timings})
        stats={label:{stage:summary([r['timings'][label][stage] for r in records])
                       for stage in ('transform_ms','reconstruct_ms','combined_ms')} for label in ('wide','bounded')}
        scenes.append({'name':clip,'manifest':manifest,'paired_checks':len(records),'stats':stats,'records':records})
    assert hashes=={str(p):digest(p) for p in sources},'sources changed'
    result={'evidence':'Analytical intermediate bounds plus actual paired Python arithmetic; not a DSP schedule or hardware FPS proof',
            'source_sha256':hashes,'python':platform.python_version(),'numpy':np.__version__,
            'domain_bounds':bm.domain_report(),'scenes':scenes,
            'timing_scope':'Only residual transform/quantization and key inverse/clip; RGB/color, entropy, snapshots, packet, network, oracle, decode and presentation excluded.',
            'concurrency':'Uncontrolled background host load, paired alternating order, 3 repetitions; prior codec benchmark finished first.',
            'sample_scope':'4 selected native frames per clip repeated at2 scales and3 repetitions:8 source capture IDs,48 checks total; source images may repeat.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    for scene in scenes:print(scene['name'],scene['stats'])
    print('max_dequant',max(m for s in scenes for r in s['records'] for m in r['dequant_max_per_plane']))


if __name__=='__main__':main()
