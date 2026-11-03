"""Four measured-service cases using the local token-key encoder."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

from token_key_encoder import Encoder, frozen

HERE=Path(__file__).resolve().parent
SCHED=HERE.parent/'python-measured-service-study'
spec=importlib.util.spec_from_file_location('token_scheduler_model',SCHED/'model.py')
model=importlib.util.module_from_spec(spec);sys.modules[spec.name]=model;spec.loader.exec_module(model)


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    paths=[HERE/'scheduler_probe.py',HERE/'token_key_encoder.py',HERE/'token_coeff.py',SCHED/'model.py',
           HERE.parent/'python-fast-entropy-study/fast_anchor.py',HERE.parent/'python-fast-entropy-study/fast_coeff.py',
           Path(frozen.__file__),Path(frozen.mt.__file__),Path(frozen.mt.ft.__file__),Path(frozen.mt.cc.__file__),
           Path(model.corpus.__file__),HERE.parent/'python-coupled-study/validation.py']
    hashes={str(p):digest(p) for p in paths};cases=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=model.corpus.load_video(media/f'{clip}.mp4',max_frames=60,start_seconds=1)
        for decoder in ('assumed','python_wall'):
            row=model.run(frames,manifest,model.Config(encoder_profile='fast_key',decoder_service=decoder,motion_mode='zero'),encoder_factory=Encoder)
            assert all(s is None for s in row['unresolved_slots']) and not row['unresolved_pending'] and not row['pending_ids']
            cases.append(dict(name=clip,manifest=manifest,result=row,actual_encoder='local token_key_encoder.Encoder'))
            print(clip,decoder,row['presented_strict'],row['presented_eventual'],row['metrics']['steady_fps'],flush=True)
    assert hashes=={str(p):digest(p) for p in paths},'source changed'
    result={'evidence':'Actual per-selected-call Python preparation and optionally receive durations replayed into finite model; not native/concurrent/hardware FPS',
            'source_sha256':hashes,'case_count':len(cases),'cases':cases,
            'configuration_note':'Config encoder_profile fast_key identifies compatible MA01 API only; encoder_factory explicitly supplies token_key_encoder.Encoder.',
            'scope':'Assumed decoder uses8ms; python_wall charges actual packet receive. Network8Mb/s,QSPI160Mb/s,feedback10ms,vblank60Hz remain assumptions. Source capture/scale, lazy oracle and physical memory/RF service excluded. Short60frame clips at25/29.88nativefps scheduled30IDs/s.'}
    (HERE/'scheduler-results.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
