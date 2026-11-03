#!/usr/bin/env python3
"""Actual combined GM01 packets and paired uniform MA01 control; immediate ACK."""
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
import game_codec as gc

HERE=Path(__file__).resolve().parent
for directory in ('python-codec-study','python-anchor-study'):
    sys.path.insert(0,str(HERE.parent/directory))
import corpus
import anchor_codec
spec=importlib.util.spec_from_file_location('v7_roi_metrics',HERE.parent/'python-game-roi-study/benchmark.py')
metrics=importlib.util.module_from_spec(spec);sys.modules[spec.name]=metrics;spec.loader.exec_module(metrics)
RECTS=((16,48,192,80),(160,352,400,80))


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psnr(mse):return None if mse==0 else float(10*np.log10(65025/mse))
def wire(size):return size+68*math.ceil(size/1024)


def summary(records):
    result={}
    for profile in ('uniform16','roi8bg16','roi8bg32'):
        rows=[r for r in records if r['profile']==profile]
        regions={}
        for region in ('active','roi','background'):
            pixels=sum(r['metrics'][region]['pixels'] for r in rows)
            mse=sum(r['metrics'][region]['mse']*r['metrics'][region]['pixels'] for r in rows)/pixels
            regions[region]={'mse':mse,'psnr':psnr(mse),'pixels':pixels}
        result[profile]={'packet_mean_bytes':float(np.mean([r['bytes'] for r in rows])),
                         'wire_mbps_if30captures':sum(wire(r['bytes']) for r in rows)/len(rows)*8*30/1e6,
                         'over_48k_cap':sum(r['bytes']>49152 for r in rows),'regions':regions,
                         'prepare_ms':{'mean':float(np.mean([r['prepare_ms'] for r in rows])),
                                       'p95':float(np.percentile([r['prepare_ms'] for r in rows],95))},
                         'receive_ms':{'mean':float(np.mean([r['receive_ms'] for r in rows])),
                                       'p95':float(np.percentile([r['receive_ms'] for r in rows],95))}}
    return result


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    sources=[HERE/'benchmark.py',HERE/'game_codec.py',HERE/'test_game_codec.py',Path(gc.roi.__file__),
             Path(gc.ft.__file__),Path(gc.mt.__file__),Path(gc.token_coeff.__file__),Path(gc.word_coeff.__file__),
             Path(gc.word_coeff.frozen_codec.__file__),Path(corpus.__file__),Path(anchor_codec.__file__),
             HERE.parent/'python-game-roi-study/benchmark.py']
    hashes={str(p):digest(p) for p in sources};scenes=[];uniform_pairs=0
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=12,start_seconds=4)
        h,w=frames[0].shape[:2];mw,mh=gc.roi.geometry(w,h)
        maps={'uniform16':np.full((mh,mw),16,np.uint8),
              'roi8bg16':gc.roi.declared_map(w,h,RECTS,8,16),
              'roi8bg32':gc.roi.declared_map(w,h,RECTS,8,32)}
        records=[]
        for label,m in maps.items():
            enc,rx=gc.Encoder(),gc.Receiver()
            old,oldrx=anchor_codec.AnchorEncoder(),anchor_codec.AnchorReceiver()
            for i,rgb in enumerate(frames):
                begin=time.perf_counter_ns();prepared=enc.analyze(rgb,i,force_key=i==6,mode='zero')
                candidate=enc.encode_candidate(prepared,m);packet=enc.commit(candidate)
                prepare_ms=(time.perf_counter_ns()-begin)/1e6
                begin=time.perf_counter_ns();actual,info=rx.receive(packet)
                receive_ms=(time.perf_counter_ns()-begin)/1e6
                expected=enc.expected_hash(i)
                assert hashlib.sha256(actual.tobytes()).hexdigest()==expected
                old_bytes=None
                if label=='uniform16':
                    control=old.prepare(rgb,i,quant_scale=16,force_key=i==6,mode='zero')
                    golden,_=oldrx.receive(control);np.testing.assert_array_equal(actual,golden)
                    old.ack(i,epoch=1);old_bytes=len(control);uniform_pairs+=1
                enc.ack(i,epoch=1)
                parsed=gc.parse(packet,1)
                record={'id':i,'profile':label,'input_sha256':manifest['frame_sha256'][i],
                        'packet_sha256':hashlib.sha256(packet).hexdigest(),'rgb_sha256':expected,
                        'bytes':len(packet),'map_bytes':parsed['map_bytes'],'outer_header_crc_bytes':gc.HEADER.size+4,
                        'uniform_ma01_bytes':old_bytes,'key':info['key'],'anchor_id':info['anchor_id'],
                        'analysis_count':enc.analysis_count,'forward_calls_total':enc.forward_calls,
                        'analyze_ms':prepared.analyze_ms,'candidate_ms':candidate.candidate_ms,
                        'prepare_ms':prepare_ms,'receive_ms':receive_ms,
                        'metrics':metrics.metric(rgb,actual,RECTS,tuple(manifest['active_rects'][i]),False)}
                records.append(record)
            assert enc.analysis_count==12 and enc.forward_calls==36 and not enc.pending
        scenes.append({'name':clip,'manifest':manifest,'records':records,'summary':summary(records)})
        print(clip,scenes[-1]['summary'],flush=True)
    assert hashes=={str(p):digest(p) for p in sources},'source changed'
    result={'evidence':'Actual combined GM01 temporalROI bytes, parsed reconstruction and same-source metrics; immediateACK, no finite transport or hardwareFPS proof',
            'source_sha256':hashes,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'pyav':av.__version__},
            'scenes':scenes,'combined_packet_count':sum(len(s['records']) for s in scenes),'uniform_ma01_pixel_pairs':uniform_pairs,
            'format':{'magic':'GM01','outer_header_crc_bytes':gc.HEADER.size+4,'map_bytes_720x480':338,
                      'uniform_gm01_minus_ma01_bytes_720x480':gc.HEADER.size+338-(gc.mt.HEADER.size+12)},
            'regions':{'rectangles':RECTS,'scope':'Fixed declared priorities, not verified/detected real-game HUDs.'},
            'policy':{'mode':'zero','key_refresh_ids':[0,6],'feedback':'Immediate in-process ACK after verification.',
                      'oracle_used_for_selection':False,'future_frames_used':False,'lookahead_frames':0},
            'timing_scope':'Actual Python prepare includes analysis, quantization, entropy, assembly and selected-key reconstruction. Oracle/metrics/source acquisition/network/display excluded; hostload/order uncontrolled. All3profiles actuallysent/decoded including anyovercap.',
            'memory_scope':'Ownedpreparedraw/prediction and candidatecoeff/maparrays coexist withpendingpackets/anchors; countersnotdeviceheap/physicalmemoryproof.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
