#!/usr/bin/env python3
"""Measured-host AR03 bank-local refresh versus frozen AR02 global refresh."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import time
import numpy as np
import PIL,av
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('frozen_stream_benchmark_deps',HERE.parent/'python-game-unified-stream-study/benchmark.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def paths():
    data=json.loads((HERE.parent/'python-game-unified-codec-study/results.json').read_text())
    names={ROOT/p.split('/moonbub-30fps-study/',1)[1] for p in data['source_sha256']}
    names|=set(base.dependencies())
    names|={HERE/n for n in ('local_codec.py','model.py','benchmark.py','verify.py','test_local_codec.py','test_local_model.py','test_inherited.py','test_ingress_feedback.py')}
    names|={Path(base.__file__),HERE.parent/'python-game-unified-codec-study/unified_codec.py',HERE.parent/'python-game-unified-stream-study/model.py',HERE.parent/'python-game-refresh-v16-study/model.py'}
    return sorted(names)
def summary(c):
    r=c['result'];w=r['steady_window_ms'];packets=r['packets'];commits=r['commits'];decoded={p['id']:p for p in commits}
    ids=[] if w is None else [p['id'] for p in r['presented'] if w[0]<=p['at_ms']<w[1]]
    return dict(profile=c['profile'],strict=r['presented_strict'],eventual=r['presented_eventual'],
        diagnostic_ids_per_second=r['diagnostic_ids_per_second'],steady_ids=ids,
        distinct_steady_input_hashes=len({c['manifest']['frame_sha256'][i] for i in ids}),
        distinct_steady_decoded_hashes=len({decoded[i]['rgb_sha256'] for i in ids}),
        key_ids=[p['id'] for p in packets if p['admitted'] and p['key']],
        deferred_refresh_Ps=sum(p['refresh_deferred'] for p in packets),
        mean_preparation_ms=float(np.mean([p['encode_service_ms'] for p in packets])),
        mean_source_rgb565_mse=float(np.mean([p['active_rgb565_mse'] for p in commits])),
        mean_complete_body_bytes=float(np.mean([p['bytes'] for p in packets if p['admitted']])),
        wire_bytes=r['forward_ipv4_udp_bytes'],selected_ui_word_errors=sum(p['selected_ui_mismatches'] for p in commits),
        drops=r['drops_by_reason'])
def main():
    dependencies=paths();pins={p.relative_to(ROOT).as_posix():sha(p) for p in dependencies}
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    frames,manifest=base.source.native(media/'mass-effect-2600.mp4',n=180,start=4)
    assert len(frames)==manifest['unique_frame_count']==180
    cases=[];started=time.perf_counter()
    for label,policy,period in [('global_refresh30','global',30),('local_refresh30','local',30),('local_initial_only','local',0),('local_refresh30_repeat','local',30)]:
        cfg=model.Config(codec_mode='gm',refresh_policy=policy,refresh_period=period)
        c=dict(source='native-regression180',profile=label,manifest=manifest,result=model.run(frames,manifest,cfg));cases.append(c)
        print(json.dumps(summary(c)),flush=True)
    images=[np.full((16,32,3),40+i,np.uint8) for i in range(64)]
    manifest=dict(source='synthetic:flat64',synthetic=True,frame_count=64,frame_sha256=[model.digest(f) for f in images])
    for label,fault in [('local_lost_refresh_ack',dict(drop_first_refresh_ack=True)),('local_lost_refresh_chunk',dict(drop_first_refresh_chunk=True))]:
        cfg=model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),refresh_period=8,promotion_period=4,**fault)
        c=dict(source='synthetic-fault64',profile=label,manifest=manifest,result=model.run(images,manifest,cfg));cases.append(c)
        print(json.dumps(summary(c)),flush=True)
    assert pins=={p.relative_to(ROOT).as_posix():sha(p) for p in dependencies},'sources changed'
    out=dict(evidence='Versioned AR03/AF03 bank-local key refresh; actual GM/UI codec with bounded finite ownership versus AR02 global control',source_sha256=pins,cases=cases,case_count=len(cases),summary=[summary(c) for c in cases],
        total_python_wall_seconds=time.perf_counter()-started,versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
        protocol_scope='AR03/AF03v3changeskeytooverwritebank0only. ActualGM/SRinnerunchanged. Geometryfixedperadmitted/publishedepoch. NewestACKedreferencechosen;bank1continuitywhilebank0writerpending. LostkeyACKinvalidatesonly0,notconfirmed1. OldAR02peersreject.',
        timing_scope='New actualPythonBOX/map/GM/UI/packet/feed/decode/feedback/expirycostpaid;independentserializedvirtualservers. Assumed8Mb/slinks160Mb/sQSPI10msfeedback60Hzvblank. NoESP32/nativeCPU/FPGA/RF/memoryservicejointproof.',
        source_scope='Reusedv15/v16native180IDsat4seconds,precompressed29.88fps RGBloadedoffline,schedule30IDs/s;noindependentnewvalidation. Faultframesaresynthetic.',
        comparison_scope='Admission/promotion/referencehistoriesdiffer. SameinputsourceIDsandexactUIcoveragepreserved,sourcequalityreported;notlosslesscomparisonornetbytesgainattributedsolelytodrainpolicy.')
    (HERE/'results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
