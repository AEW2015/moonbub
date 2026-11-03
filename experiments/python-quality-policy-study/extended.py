#!/usr/bin/env python3
"""Exploratory longer held-out recovery window; no main-policy retuning."""
import hashlib
import importlib.util
import json
from pathlib import Path

import model
from model import Config,run
from policy import PolicyConfig

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('quality_report_helpers',HERE/'benchmark.py')
helpers=importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    main_path=HERE/'results.json'
    main_report=json.loads(main_path.read_text())
    prior=next(s for s in main_report['scenes'] if s['name']=='mass-effect-combat-start4')
    frames,manifest=model.corpus.load_video(prior['manifest']['source'],max_frames=90,start_seconds=4)
    if len(frames)!=90 or manifest['frame_sha256'][:60]!=prior['manifest']['frame_sha256']:
        raise AssertionError('extended source mismatch')
    paths=[HERE/'extended.py',HERE/'benchmark.py',HERE/'policy.py',HERE/'model.py',
           HERE.parent/'python-anchor-study/anchor_codec.py',Path(model.mt.__file__),
           Path(model.mt.cc.__file__),Path(model.mt.ft.__file__),Path(model.corpus.__file__)]
    hashes={str(p):digest(p) for p in paths}
    rows=[]
    for mode in ('backoff','restore'):
        row=run(frames,manifest,Config(policy=PolicyConfig(mode=mode)))
        row['presented_quality']=helpers.quality_for_ids(row,{x['id'] for x in row['presented']},manifest)
        rows.append(row)
        print(mode,row['steady_fps'],row['presented_eventual'],row['drops_by_reason'],
              row['final_quant_scale'],row['policy_events'],flush=True)
    if hashes!={str(p):digest(p) for p in paths}:raise RuntimeError('sourceschanged')
    result={'evidence':'Exploratory90frameheldout extension after shortwindow showed latebackoff; no nativeFPS/hardwareclaim',
            'source_sha256':hashes,'main_result_sha256':digest(main_path),'manifest':manifest,'cases':rows,
            'comparison':helpers.compare(rows[0],rows[1],manifest),
            'scope':'Sameunchangedpolicyparameters; sourceextends heldoutwindow, notindependentofmain60framecase; noparentprimary90windowcomparison'}
    (HERE/'extended-results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
