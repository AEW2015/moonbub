#!/usr/bin/env python3
"""Actual exact GE26/CP26 entropy repacking of ACKed v25 source histories."""
from pathlib import Path
import hashlib
import json
import math
import platform
import sys
import time
import zlib
import numpy as np
import model as e
import protocol as p

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=HERE.parent/'python-game-capped-key-v25-study'
V24=HERE.parent/'python-game-standard-v24-study'
n=e.load_module('entropy26_native_helpers',HERE.parent/'python-game-native-motion-v25-study/benchmark.py')
joint=e.load_module('entropy26_frozen_joint',HERE.parent/'python-game-combined-motion-v25-study/model.py')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def raw(desc,directory=HERE):return n.raw(desc,directory)


def blob(data):
    stored=zlib.compress(data,9);path='objects/'+hashlib.sha256(stored).hexdigest()+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(stored)
    return dict(path=path,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(stored).hexdigest())


def pins():
    old=load(OLD/'results.json');paths={ROOT/s for s in old['source_sha256']}
    paths|={OLD/'results.json',V24/'results.json'}
    paths|=set(HERE.glob('*.py'))|{HERE/'README.md',HERE/'SCHEMA.md'}
    for c in old['cases']:
        if c['profile']!='capped_key_zero_rdo1':continue
        for r in c['rows']:
            paths|={OLD/r[k]['path'] for k in ('base_packet','hud_packet','packet','ack')}
    for inp in load(V24/'results.json')['inputs']:
        for r in inp['rows']:paths.add(V24/r['original_rgb565']['path'])
    return {q.relative_to(ROOT).as_posix():sha(q) for q in sorted(paths)}


def summary(rows):
    total=sum(r['complete_bytes'] for r in rows);prior=sum(r['old_complete_bytes'] for r in rows)
    sse=sum(r['hybrid']['active_squared_error'] for r in rows);samples=sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=len(rows),complete_bytes=total,old_complete_bytes=prior,coded_body_Mbps_at30=total*5/1e6,
                old_body_Mbps_at30=prior*5/1e6,body_saving_fraction=1-total/prior,
                base_bytes=sum(r['base_bytes'] for r in rows),old_base_bytes=sum(r['old_base_bytes'] for r in rows),
                hud_bytes=sum(r['hud_bytes'] for r in rows),binding_bytes=60*len(rows),
                maximum_complete_bytes=max(r['complete_bytes'] for r in rows),cap_fit_frames=sum(r['complete_bytes']<=49152 for r in rows),
                exact_hud_words=21120*len(rows),hud_word_errors=sum(r['hybrid']['hud_word_errors'] for r in rows),
                active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples,
                active_psnr_db=10*math.log10(65025/(sse/samples)),
                mean_incremental_repack_ms=sum(r['work']['repack_ms'] for r in rows)/len(rows),
                mean_joint_receive_ms=sum(r['receive_ms'] for r in rows)/len(rows),
                entropy_planes_selected=sum(w['selected_mode']=='EC26' for r in rows for w in r['work']['planes']),
                selected_layouts={str(k):sum(w['selected_mode']=='EC26' and w['selected_layout']==k for r in rows for w in r['work']['planes']) for k in (0,1)})


def run(case,policy,source):
    rx=p.Receiver(epoch=25);oldrx=joint.Receiver(epoch=25);rows=[]
    layouts=(0,) if policy=='block_major' else (0,1)
    for oldrow,original in zip(case['rows'],source['rows']):
        fid=oldrow['id'];bp=raw(oldrow['base_packet'],OLD);hud=raw(oldrow['hud_packet'],OLD)
        baseline,oldhud,oldack=oldrx.receive(raw(oldrow['packet'],OLD))
        assert oldack==raw(oldrow['ack'],OLD)
        newer,work=e.repack(bp,layouts=layouts)
        pair=p.encode_pair(newer,hud,epoch=25,frame_id=fid,source_slot=oldrow['source_slot'],destination_slot=oldrow['destination_slot'],publish=True,key=oldrow['key'])
        began=time.perf_counter_ns();decoded,patches,ack=rx.receive(pair);receive_ms=(time.perf_counter_ns()-began)/1e6
        p.validate_ack(ack,pair)
        for a,b in zip(baseline,decoded):np.testing.assert_array_equal(a,b)
        meta=e.parse(newer);oldmeta=e.old.parse(bp)
        for a,b in zip(meta['coefficients'],oldmeta['coefficients']):np.testing.assert_array_equal(a,b)
        orig=n.original(original);bare=e.C.corpus.rgb565(e.ft.planes_to_rgb(decoded));hybrid=n.overlay(bare,tuple(v['words'] for v in patches))
        assert n.digest(bare)==oldrow['bare_rgb565_sha256'] and n.digest(hybrid)==oldrow['hybrid_rgb565_sha256']
        metric=n.metric(orig,hybrid);assert metric==oldrow['hybrid'] and metric['hud_word_errors']==0
        assert len(pair)<=oldrow['body_bytes']<=49152
        rows.append(dict(id=fid,key=oldrow['key'],reference_id=oldrow['reference_id'],source_slot=oldrow['source_slot'],destination_slot=oldrow['destination_slot'],
                         source_common_yuv_sha256=oldrow['source_common_yuv_sha256'],
                         base_packet=blob(newer),hud_packet=blob(hud),packet=blob(pair),ack=blob(ack),work=work,receive_ms=receive_ms,
                         base_bytes=len(newer),old_base_bytes=len(bp),hud_bytes=len(hud),binding_bytes=60,complete_bytes=len(pair),old_complete_bytes=oldrow['body_bytes'],
                         bare_rgb565_sha256=n.digest(bare),hybrid_rgb565_sha256=n.digest(hybrid),reconstructed_yuv_tag=meta['reconstructed_tag'].hex(),
                         hybrid=metric,baseline_case_profile=case['profile']))
    out=dict(scene=case['scene'],policy=policy,rows=rows,summary=summary(rows))
    print(json.dumps(dict(scene=out['scene'],policy=policy,summary=out['summary'])),flush=True);return out


def main():
    before=pins();old=load(OLD/'results.json');v24=load(V24/'results.json');cases=[]
    for case in old['cases']:
        if case['profile']!='capped_key_zero_rdo1':continue
        source=next(x for x in v24['inputs'] if x['scene']==case['scene'])
        for policy in ('block_major','best_layout'):cases.append(run(case,policy,source))
    assert before==pins(),'source changed'
    data=dict(schema='gamebub-entropy-v26',source_sha256=before,cases=cases,
              counts=dict(unique_source_frames=96,accepted_pairs=192,exact_hud_words=192*21120),
              versions=dict(python=platform.python_version(),numpy=np.__version__),
              scope=['Actual lossless coefficient repacking of frozen v25 source/reference histories; decoded pixels/tags/MSE exactly unchanged.',
                     'CP26/GE26/EC26 are laboratory wire formats, actualHU25 retained andrealJA26ACK65bytes. Complete49,152Bcap includes60binding.',
                     'Ratesproject nominal30IDs/sec on two reused29.88fpswindows; notlivecapture/native/RF/ESP32/FPGAfit/physical30fps.',
                     'Incrementalrepacktime includesfrozenGM25parse,twoEC26candidateencodes(bestlayout),newframing; previousv25encoderworknotretimed.',
                     'Blockmajorhas4logicalstreamcursors and128Bcoefficientblockpotential; frequencymajororacleusesfullplanecoefficientarray, requiresdifferentmemoryarchitecture. NoRTLstreamingproof.'])
    (HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')


if __name__=='__main__':main()
