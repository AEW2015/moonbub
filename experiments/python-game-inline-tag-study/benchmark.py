#!/usr/bin/env python3
"""Exact canonical streaming tag experiment with actual retained reconstructions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np
import inline_tag
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'python-game-unified-codec-study'))
import unified_codec as codec

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

# Golden verifier has uniquely named imports; do not import a generic verify.
sys.path.insert(0,str(HERE.parent/'python-game-golden-vectors-study'))
golden=module('inline_golden_verify',HERE.parent/'python-game-golden-vectors-study/verify.py')
budget=module('inline_frozen_budget',HERE.parent/'python-game-decoder-budget-study/budget.py')

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def cases():
    d=golden.load()
    for c in d['cohorts']:
        for row in c['rows']:
            yield c['spec']['name']+'-'+str(row['request']['id']),tuple(golden.read_array(p) for p in row['decoded_yuv']),'retained synthetic golden decode'
    d=json.loads((HERE.parent/'python-game-decoder-budget-study/results.json').read_text())
    for mode in ('gm','exact'):
        rx=codec.Receiver()
        for t in d['traces']:
            if t['label'].startswith('720x480_native_'+mode+'_'):
                task=rx.begin(bytes.fromhex(t['packet_hex']));planes=task.planes
                rx.complete(task)
                yield t['label'],planes,'retained native-derived actual AR02 decode; three related source IDs per mode'
    for w,h,seed in ((2,2,1601),(34,18,1602),(66,50,1603),(720,480,1604)):
        rng=np.random.default_rng(seed)
        planes=tuple(rng.integers(0,256,shape,dtype=np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))
        yield f'random-{w}x{h}-seed{seed}',planes,'deterministic synthetic canonical YUV, not encoded gameplay'

def pins():
    paths={HERE/n for n in ('inline_tag.py','benchmark.py','verify.py','test_inline.py')}
    paths|={Path(codec.__file__),Path(codec.old.__file__),HERE.parent/'python-game-golden-vectors-study/verify.py',
            HERE.parent/'python-game-golden-vectors-study/fixtures.py',HERE.parent/'python-game-golden-vectors-study/results.json',
            HERE.parent/'python-game-decoder-budget-study/budget.py',HERE.parent/'python-game-decoder-budget-study/results.json'}
    # All frozen codec dependencies are conservatively pinned as a source superset.
    golden_data=golden.load()
    paths|={ROOT/p for p in golden_data['source_sha256']}
    d=json.loads((HERE.parent/'python-game-unified-codec-study/results.json').read_text())
    paths|={ROOT/p.split('/moonbub-30fps-study/',1)[1] for p in d['source_sha256']}
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)}

def build():
    before=pins();rows=[];start=time.perf_counter()
    for name,planes,scope in cases():
        tag,info=inline_tag.compute(planes);expected=codec.reference_tag(planes);assert tag==expected
        h,w=planes[0].shape;logical=sum(p.size for p in planes)
        assert info['stripe_storage_bytes']==min(8,h)*w*2
        assert info['canonical_bytes_hashed']==4+2*logical
        rows.append(dict(name=name,width=w,height=h,scope=scope,canonical_planes_sha256=[hashlib.sha256(np.asarray(p,dtype='<i2').tobytes()).hexdigest() for p in planes],
                         tag=tag.hex(),reference_tag=expected.hex(),**info,
                         conditional_eliminable_packed8_publication_reread_bytes=logical))
    d=json.loads((HERE.parent/'python-game-decoder-budget-study/results.json').read_text())
    trace=next(t for t in d['traces'] if t['label']=='720x480_native_gm_1')
    counterfactual=[]
    for arch in budget.scenarios():
        e=budget.estimate(trace,arch);cycles=e['burst_counts']['publication_yuv_tag_read']*arch.read_burst_cycles
        available=e['background_available_cycles_per_second']
        changed=None if available<=0 else e['compute_serialized_ms']+1000*(e['background_memory_cycles']-cycles)/available
        counterfactual.append(dict(scenario=arch.name,trace=trace['label'],baseline_planning_ms=e['serialized_planning_frame_ms'],
                                  conditional_planning_ms=changed,eliminated_packed8_reread_bytes=518400,
                                  sha_stage_cycles_unchanged=e['stage_cycles']['sha_tag'],canonical_sha_input_bytes_unchanged=1036804,
                                  removed_read_bursts=e['burst_counts']['publication_yuv_tag_read'],
                                  scope='Counterfactual removes only separate tag memory read; assumes decoder producer can feed canonical stripe SHA without extra stalls. No fused decoder/RTL/hardware bandwidth result.'))
    assert before==pins()
    return dict(evidence='Exact bounded-stripe canonical publication SHA from simulated ordered reconstructed tiles',
                source_sha256=before,case_count=len(rows),cases=rows,counterfactual=counterfactual,
                elapsed_python_seconds=time.perf_counter()-start,
                limits='Producer reads already decoded whole planes; this proves tag-order/stripe-buffer logic only. Stripe allocation bound excludes SHA state/control and producer storage. Canonical SHAbytes unchanged; no actual decoderfusion, full-frame memory reread saved, sourcequality/FPS/hardware fit or bandwidthproof.')

if __name__=='__main__':
    d=build();(HERE/'results.json').write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps(dict(cases=d['case_count'],max_stripe_bytes=max(c['stripe_storage_bytes'] for c in d['cases']),counterfactual=d['counterfactual']),indent=2))
