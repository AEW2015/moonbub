"""Coupled actual codec/ACK experiments on60 native frames per source window."""
import dataclasses
import hashlib
import json
from pathlib import Path
import sys

from model import Config,run
import model

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    baseline_path=HERE.parent/'python-motion-study/jpeg-reference.json'
    baseline=json.loads(baseline_path.read_text())
    paths=[HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',HERE/'validation.py',Path(model.mc.__file__),
           Path(model.mc.cc.__file__),Path(model.mc.ft.__file__),Path(corpus.__file__),Path(model.pacing.__file__)]
    hashes={str(p):digest(p) for p in paths}
    cases=[];manifests={}
    for si,source in enumerate(baseline['scenes']):
        old=source['manifest']
        frames,manifest=corpus.load_video(old['source'],max_frames=60,start_seconds=old['start_seconds'])
        manifests[source['name']]=manifest
        for delay in (0,10,20):
            cfg=Config(feedback_ms=delay)
            result=run(frames,manifest,cfg)
            result.update(scene=source['name'],role=source['role'],case='feedback')
            cases.append(result)
            print(source['name'],delay,result['attempted'],result['committed'],result['presented_strict'],
                  result['steady_fps'],result['age_ms'],result['drop_counts'],flush=True)
        if source['role']=='primary':
            cfg=Config(feedback_ms=10,loss_ids=(7,),ack_loss_ids=(25,),corrupt_ids=(45,),duplicate_ack_ms=15)
            result=run(frames,manifest,cfg)
            result.update(scene=source['name'],role=source['role'],case='fault_campaign')
            cases.append(result)
            print(source['name'],'fault',result['committed'],result['drop_counts'],flush=True)
        if source['role']=='heldout' and 'combat' in source['name']:
            for delay in (0,10):
                cfg=Config(feedback_ms=delay,cap_backoff_scales=(8,16,32))
                result=run(frames,manifest,cfg)
                result.update(scene=source['name'],role=source['role'],case='adaptive_cap_backoff')
                cases.append(result)
                print(source['name'],'adaptive',delay,result['committed'],result['steady_fps'],
                      result['drop_counts'],result['presented_scale_histogram'],result['pooled_presented_active_psnr_db'],flush=True)
    if hashes!={str(p):digest(p) for p in paths}:raise RuntimeError('source changed during run')
    report={'evidence':'Actual MT02 re-encoding, packets and reconstruction in assumed-time event simulation; no physical FPS',
            'source_sha256':hashes,'baseline_sha256':digest(baseline_path),'scenarios':cases,'manifests':manifests,
            'scenario_count':len(cases),'capture_scope':'native25/29.88fps frames scheduled at hypothetical30fps; nointerpolation; short1secondsteadywindow'}
    (HERE/'results.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
