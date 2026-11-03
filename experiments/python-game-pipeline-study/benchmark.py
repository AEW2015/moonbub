#!/usr/bin/env python3
"""Source-bound actual GM01/GF02/GA01 packets under finite offline scheduling."""
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

HERE=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def stress():
    rng=np.random.default_rng(909)
    frames=[rng.integers(0,256,(480,720,3),dtype=np.uint8) for _ in range(6)]
    frames.extend(np.full((480,720,3),75+i,np.uint8) for i in range(6))
    manifest={'source':'synthetic:seed909-six-noise-six-flat','synthetic':True,'frame_count':12,
              'frame_sha256':[hashlib.sha256(a.tobytes()).hexdigest() for a in frames],
              'active_rects':[(0,0,720,480)]*12,'native_fps':None,'generator_source':'benchmark.py'}
    return frames,manifest


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    paths=[HERE/'benchmark.py',HERE/'model.py',HERE/'test_model.py',Path(model.gc.__file__),
           Path(model.normal_controller.__file__),Path(model.cheap_gate.__file__),
           Path(model.cheap_gate.exact.__file__),Path(model.transport.__file__),
           Path(model.gc.roi.__file__),Path(model.gc.mt.__file__),Path(model.gc.ft.__file__),
           Path(model.gc.token_coeff.__file__),Path(model.gc.word_coeff.__file__),
           Path(model.gc.word_coeff.frozen_codec.__file__),Path(model.corpus.__file__),
           HERE.parent/'python-coupled-study/validation.py']
    hashes={str(p):digest(p) for p in paths};cases=[];started=time.perf_counter()
    for index,clip in enumerate(('mass-effect-combat','mass-effect-2600')):
        frames,manifest=model.corpus.load_video(media/f'{clip}.mp4',max_frames=60,start_seconds=1)
        controllers=('normal','gate') if index==0 else ('gate','normal')
        for decoder in ('assumed','python_wall'):
            for controller in controllers:
                cfg=model.Config(controller=controller,decoder_service=decoder)
                row=model.run(frames,manifest,cfg)
                cases.append(dict(name=clip,kind='baseline',manifest=manifest,result=row))
                print(clip,controller,decoder,'strict/eventual',row['presented_strict'],row['presented_eventual'],
                      'diagnostic',row['metrics']['steady_fps'],'drops',row['drops_by_reason'],flush=True)
                assert all(x is None for x in row['unresolved_sender_slots'])
                assert not row['unresolved_ingress_frames'] and not row['unresolved_credits'] and not row['pending_ids']
        if index==1:
            for label,cfg in (
                ('initial_key_chunk_loss',model.Config(controller='gate',decoder_service='python_wall',data_loss_ids=(0,),duplicate_chunk_ids=(12,))),
                ('initial_key_ack_loss',model.Config(controller='gate',decoder_service='python_wall',feedback_loss_ids=(0,),duplicate_feedback_ids=(12,)))):
                row=model.run(frames,manifest,cfg)
                cases.append(dict(name=clip,kind=label,manifest=manifest,result=row))
                print(clip,label,'strict/eventual',row['presented_strict'],row['presented_eventual'],
                      'diagnostic',row['metrics']['steady_fps'],'drops',row['drops_by_reason'],flush=True)
                assert all(x is None for x in row['unresolved_sender_slots'])
                assert not row['unresolved_ingress_frames'] and not row['unresolved_credits'] and not row['pending_ids']
    frames,manifest=stress()
    for controller in ('normal','gate'):
        row=model.run(frames,manifest,model.Config(controller=controller,decoder_service='python_wall'))
        cases.append(dict(name='seed909-noise-recovery',kind='stress',manifest=manifest,result=row))
        print('stress',controller,'prepared',row['prepared'],'eventual',row['presented_eventual'],'drops',row['drops_by_reason'],flush=True)
        assert all(x is None for x in row['unresolved_sender_slots'])
        assert not row['unresolved_ingress_frames'] and not row['unresolved_credits'] and not row['pending_ids']
    assert hashes=={str(p):digest(p) for p in paths},'executed source changed'
    result={'evidence':'Actual GM01/GF02/GA01 bytes, measured selected-frame preparation/optional receive costs in finite offline stage replay; no concurrent/native/hardware proof',
            'source_sha256':hashes,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'pyav':av.__version__},
            'case_count':len(cases),'cases':cases,'python_total_wall_seconds':time.perf_counter()-started,
            'service_scope':'8Mb/sforward and reverse links,160Mb/sGM01payloadQSPI,10msfeedbackpropagation,60Hzvblank declared. Predecodednative25/29.88fpsframes scheduled30captureIDs/s, acquisition_msdefault0 excludes actual capture/scale.',
            'cost_scope':'FullselectedController.prepare wall paid includingallfailedcandidates,keycommit/cleanup; optionalRGB/hashoracleanderror metrics excluded. Receiverbodyparse/reconstruct wall chargedonlyinpython_wallmode; otherwiseassumed8ms recordedbesideactual.',
            'wire_scope':'ActualGF02datagrams31Bheader+payload plus28IPv4/UDP; actualGA0124Bfeedbackplus28IPv4/UDP serializedbefore10mslatency. NoRF/lowerlayer/retry/framing costs. QSPIchargesGM01bytesonly.',
            'ownership_scope':'Twosenderpacket/transaction slots, twoGF02ingressslots throughdecode/readfinish,twologicalGM01credits,threeframebufferroles. Deadline/timeoutcannotrefundundrainedencode/network/QSPI/decodework. This is a softwareownershiporacle, not a physicalmemory/CDCmodel.',
            'fault_scope':'Faults name captureIDs and can be skipped byoverload; initialframe0 is alwaysprepared. Report actual timeout/feedback/drop records instead ofassuming everyconfiguredlaterIDwastransmitted.',
            'causality':{'future_frames_used':0,'oracle_used_for_selection':False,'quality_metrics_used_for_selection':False},
            'measurement_limit':'Sequentialcasesunderuncontrolledexternalhostload, noaffinity/isolatedwarmup. Per-call costs and selected IDs can vary on rerun; held source pairs are related compressed short clips.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
