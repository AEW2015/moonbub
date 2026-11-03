"""Source-bound AA01 versus drained MA01 cohorts; actual bytes, virtual clocks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import timed
from timed import Config,run

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'python-anchor-study'


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psnr(mse):return None if mse==0 else float(10*np.log10(65025/mse))


def comparison(actual,baseline):
    ours={r['id']:r['active_mse'] for r in actual['commits']}
    theirs={r['id']:r['active_rgb565_mse'] for r in baseline['commits']}
    common=sorted(set(r['id'] for r in actual['presented'])&set(r['id'] for r in baseline['presented']))
    return dict(common_presented_ids=common,
                async_psnr_common_ids=psnr(np.mean([ours[i] for i in common])) if common else None,
                baseline_psnr_common_ids=psnr(np.mean([theirs[i] for i in common])) if common else None,
                baseline=dict(presented_strict=baseline['presented_strict'],presented_eventual=baseline['presented_eventual'],
                              steady_fps=baseline['steady_fps'],age_ms=baseline['age_ms'],
                              wire_bytes=baseline['transmitted_wire_bytes'],drops=baseline['drops_by_reason']),
                quality_scope='same source IDs, different reconstructions; PSNR is not visual acceptance')


def old_module():
    sys.path.insert(0,str(OLD))
    spec=importlib.util.spec_from_file_location('prior_anchor_timed',OLD/'timed.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def main():
    baseline=json.loads((OLD/'results.json').read_text())
    paths=[HERE/'benchmark.py',HERE/'async_codec.py',HERE/'timed.py',HERE/'test_async_codec.py',HERE/'test_timed.py',
           OLD/'anchor_codec.py',OLD/'timed.py',Path(timed.mt.__file__),Path(timed.mt.cc.__file__),
           Path(timed.mt.ft.__file__),Path(timed.corpus.__file__),HERE.parent/'python-coupled-study/validation.py']
    hashes={str(p):digest(p) for p in paths};cases=[]
    old=old_module()
    for scene in baseline['scenes']:
        manifest=scene['manifest']
        primary=manifest['start_seconds']==1
        if not primary and 'combat' not in scene['name']:continue
        frames,current=timed.corpus.load_video(manifest['source'],max_frames=60,start_seconds=manifest['start_seconds'])
        if current['frame_sha256']!=manifest['frame_sha256']:raise AssertionError('changed cohort')
        delays=(10,20) if primary else (10,)
        for delay in delays:
            actual=run(frames,current,Config(feedback_ms=delay))
            prior=next(r for r in scene['cases'] if r['label']==f'feedback{delay}')
            row=dict(name=scene['name'],kind='baseline',manifest=current,result=actual,comparison=comparison(actual,prior))
            cases.append(row)
            print(row['name'],delay,'strict',actual['metrics']['presented_count'],'eventual',len(actual['presented']),
                  'steady',actual['metrics']['steady_fps'],'baseline',prior['steady_fps'],'drops',actual['drop_counts'],flush=True)
        if primary and '2600' in scene['name']:
            fault=run(frames,current,Config(feedback_ms=10,lost_key_ack_once=True,drop_first_display=True,duplicate_ack_ms=15))
            cases.append(dict(name=scene['name'],kind='fault_campaign',manifest=current,result=fault))
            print(scene['name'],'fault','eventual',len(fault['presented']),'drops',fault['drop_counts'],flush=True)
            longer,record=timed.corpus.load_video(manifest['source'],max_frames=90,start_seconds=1)
            if len(longer)!=90:raise AssertionError('incomplete longer cohort')
            actual=run(longer,record,Config(feedback_ms=20))
            prior=old.run(longer,record,old.Config(feedback_ms=20))
            cases.append(dict(name=scene['name']+'-90frames',kind='longer',manifest=record,result=actual,
                              comparison=comparison(actual,prior),baseline_actual=prior))
            print(scene['name'],'90frames','steady',actual['metrics']['steady_fps'],'baseline',prior['steady_fps'],flush=True)
    if hashes!={str(p):digest(p) for p in paths}:raise RuntimeError('source changed')
    result=dict(evidence='Actual AA01 background-key/display/retirement packets with assumed virtual timings; no physical FPS',
                source_sha256=hashes,baseline_sha256=digest(OLD/'results.json'),cases=cases,
                wire_scope='allKEY/P/RETIRE IP-UDP bytes counted; ACK/control-feedback RF/link overhead excluded')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
