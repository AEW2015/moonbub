#!/usr/bin/env python3
"""Paired CP02/MA01 decode wall costs with exact frozen packets and pixels."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
import word_coeff as wc
from word_receiver import AnchorReceiver, anchor

HERE=Path(__file__).resolve().parent
for directory in ('python-codec-study','python-token-entropy-study'):
    sys.path.insert(0,str(HERE.parent/directory))
import corpus
from token_key_encoder import Encoder


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    return {k:float(v) for k,v in zip(('mean','p50','p95','max'),(np.mean(values),*np.percentile(values,[50,95]),max(values)))}


def planes(raw):
    pos=anchor.mt.HEADER.size
    fields=anchor.mt.HEADER.unpack_from(raw);w,h=fields[6:8]
    result=[]
    for hh,ww in ((h,w),(h//2,w//2),(h//2,w//2)):
        size=anchor.mt.LENGTH.unpack_from(raw,pos)[0];pos+=4
        result.append((raw[pos:pos+size],((hh+7)//8)*((ww+7)//8),(ww+7)//8));pos+=size
    assert pos==len(raw)-4
    return result


def main():
    paths=[HERE/'benchmark.py',HERE/'word_coeff.py',HERE/'word_receiver.py',HERE/'test_word_decode.py',
           Path(wc.frozen_codec.__file__),Path(wc.frozen.__file__),Path(anchor.__file__),Path(anchor.mt.__file__),
           HERE.parent/'python-token-entropy-study/token_key_encoder.py',HERE.parent/'python-token-entropy-study/token_coeff.py',
           HERE.parent/'python-fast-entropy-study/fast_anchor.py',HERE.parent/'python-fast-entropy-study/fast_coeff.py',Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in paths}
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    scenes=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=12,start_seconds=4)
        records=[]
        for repeat in range(3):
            enc=Encoder();receivers={'old':anchor.AnchorReceiver(),'word':AnchorReceiver()}
            for i,rgb in enumerate(frames):
                raw=enc.prepare(rgb,i,quant_scale=8,mode='zero')
                samples=[]
                for plane,(payload,n,bw) in enumerate(planes(raw)):
                    durations={};decoded={}
                    order=(('old',wc.frozen_codec.decode_coefficients),('word',wc.decode_coefficients))
                    if (i+plane+repeat)%2:order=order[::-1]
                    for label,decode in order:
                        start=time.perf_counter_ns();decoded[label]=decode(payload,n,bw)
                        durations[label]=(time.perf_counter_ns()-start)/1e6
                    np.testing.assert_array_equal(decoded['old'],decoded['word'])
                    samples.append({'plane':plane,'bytes':len(payload),'old_ms':durations['old'],'word_ms':durations['word']})
                values={};times={}
                order=('old','word') if (i+repeat)%2==0 else ('word','old')
                for label in order:
                    start=time.perf_counter_ns();values[label]=receivers[label].receive(raw)
                    times[label]=(time.perf_counter_ns()-start)/1e6
                np.testing.assert_array_equal(values['old'][0],values['word'][0])
                assert values['old'][1]==values['word'][1]
                sha=hashlib.sha256(values['word'][0].tobytes()).hexdigest()
                assert sha==enc.expected_hash(i)
                enc.ack(i,epoch=1)
                records.append({'repeat':repeat,'frame':i,'kind':'KEY' if i==0 else 'P',
                                'input_sha256':manifest['frame_sha256'][i],'packet_sha256':hashlib.sha256(raw).hexdigest(),
                                'rgb_sha256':sha,'bytes':len(raw),'old_receive_ms':times['old'],'word_receive_ms':times['word'],
                                'word_stages_ms':receivers['word'].last_stages_ms,'planes':samples})
        summaries={}
        for kind in ('all','KEY','P'):
            rows=[r for r in records if kind=='all' or r['kind']==kind]
            summaries[kind]={label:stats([r[label+'_receive_ms'] for r in rows]) for label in ('old','word')}
        summary_planes={label:stats([sum(p[label+'_ms'] for p in r['planes']) for r in records]) for label in ('old','word')}
        scenes.append({'name':clip,'manifest':manifest,'paired_packets':len(records),'summary_receive_ms':summaries,
                       'summary_three_plane_coeff_ms':summary_planes,'records':records})
    assert hashes=={str(p):digest(p) for p in paths},'source changed'
    result={'evidence':'Actual paired Python CP02 and MA01 receiver timing; not native/FPGA/concurrent realtime service',
            'source_sha256':hashes,'python':platform.python_version(),'numpy':np.__version__,'scenes':scenes,
            'paired_packets':sum(s['paired_packets'] for s in scenes),'paired_planes':sum(len(r['planes']) for s in scenes for r in s['records']),
            'scope':'Exact frozen MA01 packets, reconstructed RGB/info; only CP02 bit parsing changed. Same Q14 reconstruction/color, reference lifetime, CRC/padding/range semantics.',
            'timing':'12nativeframes perclip at4s,3independentrepetitions,alternating old/new ordering. Uncontrolled concurrent host load; excludes source/prepare/network/oracles/metrics/presentation; fullreceive includes required reconstruction/color/snapshot.',
            'sample_limit':'24 source capture IDs repeatedly used; native25/29.88fps and duplicated content, not72independentimages or native30fps.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    for s in scenes:print(s['name'],'receive',s['summary_receive_ms'],'coeff',s['summary_three_plane_coeff_ms'])


if __name__=='__main__':main()
