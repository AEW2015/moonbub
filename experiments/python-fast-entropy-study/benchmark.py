#!/usr/bin/env python3
"""Paired reference/optimized MT02 measurements; same bytes, uncontrolled load."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np

import fast_coeff
from fast_motion import Encoder, frozen

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def stats(values):
    return {name:float(value) for name,value in zip(('mean','p50','p95','max'),
            (np.mean(values),*np.percentile(values,[50,95]),max(values)))}


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    sources=[HERE/'benchmark.py',HERE/'fast_coeff.py',HERE/'fast_motion.py',HERE/'test_fast_coeff.py',
             Path(frozen.__file__),Path(fast_coeff.frozen.__file__),Path(frozen.ft.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in sources}
    scenes=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=12,start_seconds=4)
        records=[]
        for repeat in range(3):
            old,new,rx=frozen.Encoder(),Encoder(),frozen.Receiver()
            for i,rgb in enumerate(frames):
                packets={};times={}
                order=(('old',old),('fast',new)) if (i+repeat)%2==0 else (('fast',new),('old',old))
                for label,enc in order:
                    began=time.perf_counter_ns()
                    packets[label]=enc.prepare(rgb,i,quant_scale=8,mode='zero')
                    times[label]=(time.perf_counter_ns()-began)/1e6
                if packets['old']!=packets['fast']:
                    raise AssertionError('wire output changed')
                begin_decode=time.perf_counter_ns()
                actual,info=rx.receive(packets['fast'])
                decoded_ms=(time.perf_counter_ns()-begin_decode)/1e6
                if not np.array_equal(actual,new.prepared_rgb()):
                    raise AssertionError('reference drift')
                old.ack(i,epoch=info['epoch']);new.ack(i,epoch=info['epoch'])
                records.append({'repeat':repeat,'frame':i,'input_sha256':manifest['frame_sha256'][i],
                                'packet_sha256':hashlib.sha256(packets['fast']).hexdigest(),'bytes':len(packets['fast']),
                                'old_encode_ms':times['old'],'fast_encode_ms':times['fast'],'frozen_decode_ms':decoded_ms})
        old_ms=stats([x['old_encode_ms'] for x in records]);fast_ms=stats([x['fast_encode_ms'] for x in records])
        scenes.append({'name':clip,'manifest':manifest,'old_encode_ms':old_ms,'fast_encode_ms':fast_ms,
                       'mean_speedup':old_ms['mean']/fast_ms['mean'],'paired_checks':len(records),'records':records})
    if hashes!={str(p):digest(p) for p in sources}:raise RuntimeError('sources changed')
    result={'evidence':'Paired actual Python wall timings under uncontrolled concurrent host load, not native/FPGA timing',
            'profile':'MT02 quant8 zero motion; frozen arithmetic/decoder; byte-identical CP02/MT02 packets',
            'python':platform.python_version(),'numpy':np.__version__,'source_sha256':hashes,
            'timing_scope':'encode includes reconstructed YUV ref; excludes source decode/scale, host RGB oracle, network, QSPI, vblank',
            'warmup_scope':'No isolated warmup/CPU affinity; alternating measurement order and 3 repetitions, including independent first frames',
            'scenes':scenes}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    for s in scenes:
        print(s['name'],'old',s['old_encode_ms'],'fast',s['fast_encode_ms'],'mean speedup',s['mean_speedup'])


if __name__=='__main__':main()
