#!/usr/bin/env python3
"""Paired exact size-admission versus full-serialization GM01 admission."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
import numpy as np
import cheap_gate as s

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def stats(values):
    return {k:float(v) for k,v in zip(('mean','p50','p95','max'),(np.mean(values),*np.percentile(values,[50,95]),max(values)))}


def compare(rgb,cap,index,kind,source_hash):
    config=s.rate.Config(frame_cap=cap)
    old,new=s.rate.Controller(config=config),s.Controller(config=config)
    controls={'full':old,'gate':new};decisions={};wall={}
    order=('full','gate') if index%2==0 else ('gate','full')
    for label in order:
        began=time.perf_counter_ns();decisions[label]=controls[label].prepare(rgb,0)
        wall[label]=(time.perf_counter_ns()-began)/1e6
    a,b=decisions['full'],decisions['gate']
    assert a.selected==b.selected and a.packet==b.packet
    for old_attempt,new_attempt in zip(a.attempts,b.attempts):
        assert old_attempt['label']==new_attempt['label'] and old_attempt['fits']==new_attempt['fits']
        assert new_attempt['lower_bytes']<=old_attempt['bytes']
        if new_attempt['bytes'] is not None:assert new_attempt['bytes']==old_attempt['bytes']
    if b.accepted:
        actual,_=s.gc.Receiver().receive(b.packet)
        expected=hashlib.sha256(actual.tobytes()).hexdigest()
        assert expected==old.encoder.expected_hash(0)==new.encoder.expected_hash(0)
    else:assert not old.encoder.pending and not new.encoder.pending
    return {'kind':kind,'input_sha256':source_hash,'cap':cap,'accepted':b.accepted,'selected':b.selected,
            'packet_sha256':None if b.packet is None else hashlib.sha256(b.packet).hexdigest(),
            'attempts_full':list(a.attempts),'attempts_gate':list(b.attempts),
            'full_ms':wall['full'],'gate_ms':wall['gate'],
            'analysis_calls':b.analyze_calls,'forward_calls':b.forward_calls}


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    sources=[HERE/'gate_benchmark.py',HERE/'cheap_gate.py',HERE/'preflight.py',HERE/'test_cheap_gate.py',Path(s.gc.__file__),Path(s.rate.__file__),
             Path(s.gc.roi.__file__),Path(s.gc.ft.__file__),Path(s.gc.mt.__file__),Path(s.gc.token_coeff.__file__),
             Path(s.cc.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in sources};rows=[];manifests=[]
    rng=np.random.default_rng(8803)
    for i in range(8):
        rgb=rng.integers(0,256,(480,720,3),dtype=np.uint8)
        rows.append(compare(rgb,49152,i,'seeded_noise_reject',hashlib.sha256(rgb.tobytes()).hexdigest()))
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=12,start_seconds=4);manifests.append(manifest)
        for i in range(0,12,2):
            for cap,kind in ((28672,'real_pressure'),(49152,'real_normal')):
                row=compare(frames[i],cap,len(rows),kind,manifest['frame_sha256'][i])
                row.update(source=manifest['source'],source_index=i);rows.append(row)
    assert hashes=={str(p):digest(p) for p in sources},'source changed'
    groups={}
    for kind in ('seeded_noise_reject','real_pressure','real_normal'):
        selected=[r for r in rows if r['kind']==kind]
        groups[kind]={'count':len(selected),'accepted':sum(r['accepted'] for r in selected),
                      'two_attempts':sum(len(r['attempts_full'])==2 for r in selected),
                      'full_ms':stats([r['full_ms'] for r in selected]),'gate_ms':stats([r['gate_ms'] for r in selected]),
                      'serialized_gate_candidates':sum(a['serialized'] for r in selected for a in r['attempts_gate'])}
    result={'evidence':'Conservative CP02 minimum-size gate with paired actual Python admission services, not hardware/real-time proof',
            'source_sha256':hashes,'versions':{'python':platform.python_version(),**{name:importlib.metadata.version(name) for name in ('numpy','Pillow','av')}},
            'manifests':manifests,'rows':rows,'groups':groups,'paired_calls':len(rows),
            'policy':'OneROI8/background16 andatmostoneROI8/background32, actual49152orpredeclared28672bytecap. Noqualityfloorrelaxation, futureorqualityoracle.',
            'timing_scope':'Fullcallincludesmaps,oneRGB/predict/rawDCTanalysis,alllowerboundgatess,candidatesactuallyserialized,andselectedkeycommit. VerificationRGB/oracle/sourceacquisition/network/displayexcluded. Alternatingorder, uncontrolledload.',
            'memory_scope':'Sizerretainsquantizedcoefficientarrays/mapsthenemitsfitpacket; rejectedfullentropybitstringsavoided, butrawanalysis/quantization/vectorcostarraysremainhostwork.'}
    (HERE/'gate-results.json').write_text(json.dumps(result,indent=2)+'\n')
    for kind,g in groups.items():print(kind,g)


if __name__=='__main__':main()
