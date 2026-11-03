"""Byte-identical token-list entropy and actual whole-key preparation pairs."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
from token_key_encoder import Encoder, fast_anchor, frozen
import token_coeff

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'python-key-prepare-study'
spec=importlib.util.spec_from_file_location('v6_key_original',OLD/'key_encoder.py')
previous=importlib.util.module_from_spec(spec);sys.modules[spec.name]=previous;spec.loader.exec_module(previous)
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(a):return dict(zip(('mean','p50','p95','max'),map(float,(np.mean(a),*np.percentile(a,[50,95]),max(a)))))


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    paths=[HERE/'benchmark.py',HERE/'token_coeff.py',HERE/'token_key_encoder.py',HERE/'test_token_coeff.py',
           OLD/'key_encoder.py',Path(previous.fast_coeff.__file__),Path(fast_anchor.__file__),Path(frozen.__file__),
           Path(frozen.mt.__file__),Path(frozen.mt.ft.__file__),Path(frozen.mt.cc.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in paths};cases=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        for start in (1,4):
            frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=12,start_seconds=start)
            records=[]
            for index,i in enumerate(range(0,12,2)):
                rgb=frames[i];row={'input_index':i,'input_sha256':manifest['frame_sha256'][i]}
                source=frozen.mt.ft.rgb_to_planes(rgb)
                prediction=[np.full_like(a,128) for a in source]
                coeff=frozen.mt.residual_coefficients(source,prediction,8)
                entropy=[]
                for plane,(a,src) in enumerate(zip(coeff,source)):
                    packets={};elapsed={}
                    order=(('previous',previous.fast_coeff),('token',token_coeff))
                    if (index+plane)%2:order=order[::-1]
                    for label,codec in order:
                        began=time.perf_counter_ns();packets[label]=codec.encode_coefficients(a,(src.shape[1]+7)//8)
                        elapsed[label]=(time.perf_counter_ns()-began)/1e6
                    assert packets['previous']==packets['token']
                    entropy.append({'plane':plane,'blocks':len(a),'bytes':len(packets['token']),
                                    'packet_sha256':hashlib.sha256(packets['token']).hexdigest(),**elapsed})
                encoders={'previous':previous.Encoder(),'token':Encoder()};packets={};elapsed={}
                order=('previous','token') if index%2==0 else ('token','previous')
                for label in order:
                    began=time.perf_counter_ns();packets[label]=encoders[label].prepare(rgb,0,quant_scale=8,mode='zero')
                    elapsed[label]=(time.perf_counter_ns()-began)/1e6
                assert packets['previous']==packets['token']
                pixels,_=frozen.AnchorReceiver().receive(packets['token'])
                expected=hashlib.sha256(pixels.tobytes()).hexdigest()
                assert all(enc.expected_hash(0)==expected for enc in encoders.values())
                row.update(bytes=len(packets['token']),packet_sha256=hashlib.sha256(packets['token']).hexdigest(),
                           rgb_sha256=expected,prepare_ms=elapsed,entropy_planes=entropy,
                           new_key_stages_ms=encoders['token'].last_prepare_stages_ms)
                records.append(row)
            cases.append(dict(name=f'{clip}-start{start}',manifest=manifest,records=records))
    assert hashes=={str(p):digest(p) for p in paths},'source changed'
    rows=[r for c in cases for r in c['records']]
    entropy=[p for r in rows for p in r['entropy_planes']]
    summary={scope:{label:stats([r[label] for r in samples]) for label in ('previous','token')}
             for scope,samples in [('entropy_plane_ms',entropy),('whole_key_ms',[r['prepare_ms'] for r in rows])]}
    summary['whole_key_over_33_333_ms']={label:sum(r['prepare_ms'][label]>1000/30 for r in rows) for label in ('previous','token')}
    result={'evidence':'Actual paired Python wall time; no hardware/native or sustained FPS qualification',
            'profile':'24 independent keys from same v6 source indices; quant8 zero motion; optional RGB oracle excluded',
            'measurement':'Alternating old/new order; source capture/scale and coefficient preparation excluded from isolated entropy; no affinity or isolated warmup, uncontrolled host load',
            'python':platform.python_version(),'numpy':np.__version__,'source_sha256':hashes,
            'cases':cases,'summary':summary,'byte_checked_key_pairs':len(rows),'byte_checked_plane_pairs':len(entropy),
            'host_memory_caveat':'Python-int lists add transient host allocations proportional to nonzero coefficients; no target SRAM/DSP memory saving.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
