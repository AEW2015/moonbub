#!/usr/bin/env python3
"""Causal restoration versus monotone backoff on actual MA01 packets."""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import model
from model import Config,run
from policy import PolicyConfig
sys.path.insert(0,str(HERE.parent/'python-coupled-study'))
from stress_corpus import make_stress_frames
import stress_corpus


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def quality_for_ids(result,ids,manifest):
    values={r['id']:r['active_rgb565_mse'] for r in result['commits']}
    sample_count=sse=0.
    for i in ids:
        rect=manifest['active_rects'][i]
        n=rect[2]*rect[3]*3
        sse+=values[i]*n;sample_count+=n
    mse=sse/sample_count if sample_count else None
    return {'count':len(ids),'ids':sorted(ids),'pooled_active_mse':mse,
            'psnr_db':None if mse is None or mse==0 else 10*math.log10(65025/mse),
            'exact':mse==0 if mse is not None else False}


def compare(reference,candidate,manifest):
    a={r['id'] for r in reference['presented']};b={r['id'] for r in candidate['presented']}
    common=a&b
    return {'reference_policy':reference['config']['policy']['mode'],
            'candidate_policy':candidate['config']['policy']['mode'],
            'reference_common':quality_for_ids(reference,common,manifest),
            'candidate_common':quality_for_ids(candidate,common,manifest),
            'new_candidate':quality_for_ids(candidate,b-a,manifest),
            'lost_candidate':quality_for_ids(reference,a-b,manifest),
            'scope':'common source IDs matched, output references/pixels may differ; not perceptual acceptance'}


def main():
    baseline_path=HERE.parent/'python-anchor-study/results.json'
    baseline=json.loads(baseline_path.read_text())
    paths=[HERE/'benchmark.py',HERE/'policy.py',HERE/'model.py',HERE/'test_policy.py',HERE/'test_model.py',
           Path(model.mt.__file__),Path(model.mt.cc.__file__),Path(model.mt.ft.__file__),Path(model.corpus.__file__),
           HERE.parent/'python-anchor-study/anchor_codec.py',HERE.parent/'python-coupled-study/validation.py',Path(stress_corpus.__file__)]
    hashes={str(p):digest(p) for p in paths}
    output=[]
    for source in baseline['scenes']:
        old=source['manifest']
        frames,manifest=model.corpus.load_video(old['source'],max_frames=60,start_seconds=old['start_seconds'])
        if manifest['frame_sha256']!=old['frame_sha256'] or manifest['selected_pts']!=old['selected_pts']:
            raise AssertionError('video corpus changed')
        cases=[]
        for mode in ('backoff','restore'):
            row=run(frames,manifest,Config(feedback_ms=10,policy=PolicyConfig(mode=mode)))
            row['presented_quality']=quality_for_ids(row,{r['id'] for r in row['presented']},manifest)
            cases.append(row)
            print(source['name'],mode,'steady',row['steady_fps'],'eventual',row['presented_eventual'],
                  'caps',row['drops_by_reason'].get('cap',0),'scale',row['final_quant_scale'],
                  'restore',sum(x['kind']=='restore' for x in row['policy_events']),flush=True)
        output.append({'name':source['name'],'kind':'native_video_window','manifest':manifest,'cases':cases,
                       'comparison':compare(cases[0],cases[1],manifest)})
    frames,manifest=make_stress_frames()
    manifest['active_rects']=[r['active_rect'] for r in manifest['frames']]
    cases=[]
    for mode in ('fixed','backoff','restore'):
        row=run(frames,manifest,Config(feedback_ms=10,policy=PolicyConfig(mode=mode)))
        row['presented_quality']=quality_for_ids(row,{r['id'] for r in row['presented']},manifest)
        cases.append(row)
        print('synthetic',mode,'steady',row['steady_fps'],'eventual',row['presented_eventual'],
              'caps',row['drops_by_reason'].get('cap',0),'scale',row['final_quant_scale'],
              'restore',sum(x['kind']=='restore' for x in row['policy_events']),flush=True)
    output.append({'name':'synthetic_cut_noise_recovery','kind':'synthetic','manifest':manifest,'cases':cases,
                   'comparisons':[compare(cases[0],cases[1],manifest),compare(cases[1],cases[2],manifest)]})
    if hashes!={str(p):digest(p) for p in paths}:raise RuntimeError('sources changed during benchmark')
    report={'evidence':'Actual encoded packet/reconstruction with causalpolicy and assumed stage times; no physicalFPS',
            'source_sha256':hashes,'baseline_sha256':digest(baseline_path),'case_count':sum(len(x['cases']) for x in output),
            'scenes':output,'windows':'strict[0,N/30), diagnostic[500,N/30-500)ms whenN>=60, separate1000msdrain',
            'quality_scope':'All-presented, common-presented and newlyadmitted IDs separate; sourceclips compressed25/29.88fps scheduled30IDs/s'}
    (HERE/'results.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
