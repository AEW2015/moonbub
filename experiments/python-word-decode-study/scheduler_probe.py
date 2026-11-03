"""Four measured-service replays with token encoder and word MA01 receiver."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

from word_receiver import AnchorReceiver,anchor

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-token-entropy-study'))
from token_key_encoder import Encoder
SCHED=HERE.parent/'python-measured-service-study'
spec=importlib.util.spec_from_file_location('word_scheduler_model',SCHED/'model.py')
model=importlib.util.module_from_spec(spec);sys.modules[spec.name]=model;spec.loader.exec_module(model)


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    paths=[HERE/'scheduler_probe.py',HERE/'word_coeff.py',HERE/'word_receiver.py',SCHED/'model.py',
           HERE.parent/'python-token-entropy-study/token_key_encoder.py',HERE.parent/'python-token-entropy-study/token_coeff.py',
           HERE.parent/'python-fast-entropy-study/fast_anchor.py',HERE.parent/'python-fast-entropy-study/fast_coeff.py',
           Path(anchor.__file__),Path(anchor.mt.__file__),Path(anchor.mt.ft.__file__),Path(anchor.mt.cc.__file__),
           Path(model.corpus.__file__),HERE.parent/'python-coupled-study/validation.py']
    hashes={str(p):digest(p) for p in paths};cases=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=model.corpus.load_video(media/f'{clip}.mp4',max_frames=60,start_seconds=1)
        for decoder in ('assumed','python_wall'):
            row=model.run(frames,manifest,model.Config(encoder_profile='fast_key',decoder_service=decoder,motion_mode='zero'),
                          encoder_factory=Encoder,receiver_factory=AnchorReceiver)
            assert all(s is None for s in row['unresolved_slots']) and not row['unresolved_pending'] and not row['pending_ids']
            assert row['waiting_at_end'] is None
            cases.append(dict(name=clip,manifest=manifest,result=row,actual_encoder='token_key_encoder.Encoder',actual_receiver='word_receiver.AnchorReceiver'))
            print(clip,decoder,row['presented_strict'],row['presented_eventual'],row['metrics']['steady_fps'],flush=True)
    assert hashes=={str(p):digest(p) for p in paths},'source changed'
    result={'evidence':'Actual selected-packet Python services replayed offline in finite stage model; not concurrent/native/FPGA FPS',
            'source_sha256':hashes,'case_count':len(cases),'cases':cases,
            'configuration_note':'Config fast_key compatibility API; actual encoder_factory token and receiver_factory word explicitly supplied.',
            'scope':'Assumed decoder8ms versus actual per-call receive. Network8Mb/s,QSPI160Mb/s,feedback10ms,vblank60Hz remain assumptions. No capture/scale/oracle/RF/physicalmemory cost. Originalsource25/29.88fps scheduled30captureIDs/s.',
            'comparison_limit':'These are sequential endogenous service samples; prior receiver scheduler result is not a paired identical-service or same-ID speed experiment.'}
    (HERE/'scheduler-results.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
