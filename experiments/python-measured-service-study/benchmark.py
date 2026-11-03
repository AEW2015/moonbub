#!/usr/bin/env python3
"""Per-selected-call Python service durations drive a finite actual-codec model."""
import hashlib
import json
import os
from pathlib import Path
import platform
import time

import av
import numpy as np
import PIL

import model
from model import Config,run

HERE=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    paths=[HERE/'benchmark.py',HERE/'model.py',HERE/'test_model.py',
           HERE.parent/'python-anchor-study/anchor_codec.py',HERE.parent/'python-fast-entropy-study/fast_anchor.py',
           HERE.parent/'python-fast-entropy-study/fast_coeff.py',HERE.parent/'python-key-prepare-study/key_encoder.py',
           HERE.parent/'python-motion-study/motion_codec.py',HERE.parent/'python-transform-study/fixed_codec.py',
           HERE.parent/'python-coefficient-study/coeff_codec.py',HERE.parent/'python-codec-study/corpus.py',
           HERE.parent/'python-coupled-study/validation.py']
    hashes={str(p):digest(p) for p in paths}
    cases=[]
    started=time.perf_counter()
    for index,clip in enumerate(('mass-effect-combat','mass-effect-2600')):
        frames,manifest=model.corpus.load_video(media/f'{clip}.mp4',max_frames=60,start_seconds=1)
        profiles=('baseline','fast_p','fast_key') if index==0 else ('fast_key','fast_p','baseline')
        for decoder in ('assumed','python_wall'):
            for profile in profiles:
                row=run(frames,manifest,Config(encoder_profile=profile,decoder_service=decoder,motion_mode='zero'))
                assert all(slot is None for slot in row['unresolved_slots'])
                assert not row['unresolved_pending'] and not row['pending_ids']
                cases.append({'name':clip,'manifest':manifest,'result':row})
                print(clip,profile,decoder,'strict/eventual',row['presented_strict'],row['presented_eventual'],
                      'diagnostic',row['metrics']['steady_fps'],'encode key/P',row['service_summary']['key_encode_ms'],
                      row['service_summary']['p_encode_ms'],flush=True)
    if hashes!={str(p):digest(p) for p in paths}:raise RuntimeError('executed source changed')
    result={'evidence':'Actual Python per-selected-packet prepare/receive duration replay into a finite stage model; offline calls, not concurrent wall throughput/native/FPGA timing',
            'source_sha256':hashes,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'pyav':av.__version__},
            'case_count':len(cases),'motion':'zero for every profile; earlier baseline timed models defaulted to global and are not directly comparable',
            'encode_scope':'Each prepare wall duration measured before expected_hash; lazy host RGB oracle/metrics/source capture/scale excluded. Baseline eager RGB oracle remains part of baseline prepare.',
            'decoder_scope':'Each receive call measured at admission with output held until virtual decode completion. No virtual publication before completion. Assumed mode uses8ms while recording actual receive separately; python_wall mode charges that packet receive time.',
            'load_scope':'Sequential cases, uncontrolled concurrent external host load, no CPU isolation/affinity or warmup. Timings and selected IDs can vary on rerun. Case order reversed across sources, not randomized paired timing.',
            'service_scope':'8Mb/s ideal forward network with68bytes/1024payload IP-UDP accounting,160Mb/s QSPI,10ms feedback,60Hz vblank remain assumptions; memory/RF/feedback overhead and true concurrent host/network/ESP32/FPGA execution not modeled.',
            'cases':cases,'python_total_wall_seconds':time.perf_counter()-started}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
