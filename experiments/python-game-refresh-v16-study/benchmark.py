#!/usr/bin/env python3
"""GM full-UI periodic-refresh study; new costs for each actual run."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import time
import numpy as np
import PIL
import av
import model
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('unified_benchmark_deps',HERE.parent/'python-game-unified-stream-study/benchmark.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dependencies():
    paths=set(base.dependencies())
    paths.update(HERE/name for name in ('model.py','benchmark.py','verify.py','test_refresh.py','test_inherited.py','test_ingress_feedback.py'))
    paths.add(HERE.parent/'python-game-unified-stream-study/model.py')
    paths.add(Path(base.__file__))
    return sorted(paths)
def summarize(c):
    r=c['result'];packets=r['packets'];refresh=[p for p in packets if p['admitted'] and p['refresh_key']]
    commits=r['commits'];w=r['steady_window_ms'];ids=[p['id'] for p in r['presented'] if w[0]<=p['at_ms']<w[1]]
    decoded={p['id']:p for p in commits}
    return dict(profile=c['profile'],strict=r['presented_strict'],eventual=r['presented_eventual'],
        diagnostic_ids_per_second=r['diagnostic_ids_per_second'],steady_ids=ids,
        distinct_steady_input_hashes=len({c['manifest']['frame_sha256'][i] for i in ids}),
        distinct_steady_decoded_hashes=len({decoded[i]['rgb_sha256'] for i in ids}),
        refresh_ids=[p['id'] for p in refresh],refresh_bytes=[p['bytes'] for p in refresh],
        mean_refresh_bytes=None if not refresh else float(np.mean([p['bytes'] for p in refresh])),
        mean_prepare_ms=float(np.mean([p['encode_service_ms'] for p in packets])),
        mean_rgb565_mse=float(np.mean([p['active_rgb565_mse'] for p in commits])),
        mean_body_bytes=float(np.mean([p['bytes'] for p in packets if p['admitted']])),
        wire_bytes=r['forward_ipv4_udp_bytes'],drops=r['drops_by_reason'],
        selected_words_per_decoded=sorted({p['selected_exact_pixels'] for p in commits}),
        selected_word_errors=sum(p['selected_ui_mismatches'] for p in commits))
def main():
    paths=dependencies();pins={str(p):sha(p) for p in paths}
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    frames,manifest=base.source.native(media/'mass-effect-2600.mp4',n=180,start=4)
    assert len(frames)==manifest['unique_frame_count']==180
    cases=[];start=time.perf_counter()
    configs=[('gm_refresh30',30,16),('gm_refresh30_coarse',30,32),('gm_initial_only',0,16),
             ('gm_refresh60_coarse',60,32),('gm_refresh90_coarse',90,32),('gm_refresh30_repeat',30,16)]
    for name,period,scale in configs:
        cfg=model.Config(codec_mode='gm',exact_ui=True,refresh_period=period,refresh_key_background_scale=scale)
        r=model.run(frames,manifest,cfg)
        c=dict(source='mass-effect-2600-heldout180',profile=name,manifest=manifest,result=r)
        cases.append(c);print(json.dumps(summarize(c)),flush=True)
    assert pins=={str(p):sha(p) for p in paths},'executed sources changed'
    out=dict(evidence='Full-resolution all-UI GM refresh control and explicit coarser refresh-key background; finite measured-host model only',
        source_sha256=pins,cases=cases,case_count=len(cases),summary=[summarize(c) for c in cases],
        total_python_wall_seconds=time.perf_counter()-start,
        versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
        scope='Independent serializedvirtualservers; actualBOX/map/GM/UI/transport/decode/AFmutation paid;8Mb/sforward/reverse,160Mb/sQSPI,10msfeedback,60Hzvblank assumed. No capture/native/sharedCPU/targetmemory/hardwareproof.',
        quality_scope='Coarser background only on refresh keys, priorityscale8+selectedoriginalRGB565UI preserved. Keys change future predictionhistory; sourceMSE and matchedIDs required, not same-output/lossless claim.',
        policy_scope='Full refresh still drains all; coarser background does not change AR02 syntax/ownership. Longer intervals trade recovery/referenceage, not free cadence. Repeatregularrefresh30 exposes hosttiming variation; no causal ranking from tiny deltas.')
    (HERE/'results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
