#!/usr/bin/env python3
"""Actual codecs with a slower preparation scenario informed by host timing.

32ms is a declared scalar sensitivity, not measured per-packet AA01/MA01
service. The paired fast-entropy timings concern MT02 and have variable tails.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import timed as asynchronous

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'python-anchor-study'
sys.path.insert(0,str(OLD))
spec=importlib.util.spec_from_file_location('ma01_service_sensitivity',OLD/'timed.py')
serial=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=serial
spec.loader.exec_module(serial)


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    paths=[HERE/'service_sensitivity.py',HERE/'timed.py',HERE/'async_codec.py',OLD/'timed.py',OLD/'anchor_codec.py',
           Path(asynchronous.mt.__file__),Path(asynchronous.mt.cc.__file__),Path(asynchronous.mt.ft.__file__),
           Path(asynchronous.corpus.__file__)]
    hashes={str(p):digest(p) for p in paths}
    baseline=json.loads((HERE/'results.json').read_text())
    manifests={}
    # The async benchmark records cohort manifests in its per-case rows.
    for scene in baseline['cases'] if 'cases' in baseline else baseline.get('scenes',[]):
        manifest=scene.get('manifest')
        if manifest is not None:manifests[manifest['source']]=manifest
    if not manifests:
        # Use the source-bound prior MA01 manifest for the same primary windows.
        old=json.loads((OLD/'results.json').read_text())
        manifests={s['manifest']['source']:s['manifest'] for s in old['scenes'][:2]}
    cases=[]
    for source,manifest in manifests.items():
        frames,current=asynchronous.corpus.load_video(source,max_frames=60,start_seconds=1)
        for label,module in (('MA01-drained',serial),('AA01-async',asynchronous)):
            cfg=module.Config(encode_ms=32,decode_ms=8,feedback_ms=10)
            row=module.run(frames,current,cfg)
            cases.append({'source':source,'manifest':current,'label':label,'result':row})
    if hashes!={str(p):digest(p) for p in paths}:raise RuntimeError('sources changed')
    result={'evidence':'Actual re-encoding at declared32ms virtual host service; not a real-time/native or hardware measurement',
            'source_sha256':hashes,'timing_evidence_sha256':digest(HERE.parent/'python-fast-entropy-study/results.json'),
            'cases':cases}
    (HERE/'service-results.json').write_text(json.dumps(result,indent=2)+'\n')
    for case in cases:
        row=case['result']
        steady=row['metrics']['steady_fps'] if 'metrics' in row else row['steady_fps']
        eventual=len(row['presented']) if 'presented' in row else row['presented_eventual']
        print(Path(case['source']).name,case['label'],steady,eventual)


if __name__=='__main__':main()
