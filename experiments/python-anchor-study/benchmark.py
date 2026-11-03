"""Actual MA01 packet/capture/ACK benchmark with finite resources and assumed clocks."""
import dataclasses
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

import numpy as np

from timed import Config, run
import anchor_codec as ac

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    media=HERE.parents[3]/'media'
    paths=[HERE/'anchor_codec.py',HERE/'timed.py',HERE/'benchmark.py',HERE/'test_anchor_codec.py',HERE/'test_timed.py',
           Path(ac.mt.__file__),Path(ac.mt.ft.__file__),Path(ac.mt.cc.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in paths}
    output=[]
    for scene_index,(clip,start) in enumerate((('mass-effect-combat',1),('mass-effect-2600',1),('mass-effect-combat',4),('mass-effect-2600',4))):
        frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=60,start_seconds=start)
        if len(frames)!=60:raise ValueError('expected60nativeframes')
        cases=[]
        configs=[(f'feedback{delay}',Config(feedback_ms=delay)) for delay in (0,10,20)]
        if start==1:configs.append(('faults',Config(feedback_ms=10,data_loss_ids=(7,),ack_loss_ids=(25,),corruption_ids=(45,))))
        if start==4 and clip=='mass-effect-combat':
            configs.extend((f'adaptive_cap_feedback{delay}',Config(feedback_ms=delay,cap_backoff_max=32)) for delay in (0,10))
        for label,cfg in configs:
            row=run(frames,manifest,cfg)
            byid={r['id']:r for r in row['commits']}
            mses=[byid[r['id']]['active_rgb565_mse'] for r in row['presented']]
            mse=float(np.mean(mses)) if mses else None
            row['active_psnr_db_presented_ids']=None if not mse else float(10*np.log10(65025/mse))
            row['label']=label
            cases.append(row)
            print(clip,start,label,'prepared',row['prepared'],'strict',row['presented_strict'],'drain',row['presented_eventual'],
                  'steady',row['steady_fps'],'age',row['steady_age_ms'],'wire',row['transmitted_mbps_over_capture_window'],
                  'drops',row['drops_by_reason'],flush=True)
        output.append(dict(name=f'{clip}-start{start}',manifest=manifest,cases=cases))
    if hashes!={str(p):digest(p) for p in paths}:raise RuntimeError('source changed during actual-packet benchmark')
    result=dict(evidence='Actual MA01 packets/re-encoding/reference checks in finite virtual stages; no real-time/hardware FPS',
                source_sha256=hashes,source_hashes_unchanged=True,python=platform.python_version(),numpy=np.__version__,
                timing_scope='Nativeimagewindows replayedat30captureIDs/s; actualPythonwallcost separate from assumed encode2/decode8ms',
                ACK_scope='One ACKed key anchor; bounded2 Pcredits; P ACKs release credit only; periodic key requires old credits drained',
                wire_scope='40 application+28IPv4UDPbytesper1024payload; ACK/link/RF/audio/inputbytes excluded',scenes=output)
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
