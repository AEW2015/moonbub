#!/usr/bin/env python3
"""One declared synthetic control isolates current/previous-source cut requests."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import model
from model import Config,run
from policy import PolicyConfig

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-coupled-study'))
from stress_corpus import make_stress_frames
spec=importlib.util.spec_from_file_location('quality_cut_helpers',HERE/'benchmark.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    main_path=HERE/'results.json'
    baseline=json.loads(main_path.read_text())
    source=next(s for s in baseline['scenes'] if s['kind']=='synthetic')
    fixed_on=next(x for x in source['cases'] if x['config']['policy']['mode']=='fixed')
    frames,manifest=make_stress_frames()
    manifest['active_rects']=[r['active_rect'] for r in manifest['frames']]
    if manifest['frames']!=source['manifest']['frames']:raise AssertionError('stresscorpuschanged')
    paths=[HERE/'cut_ablation.py',HERE/'benchmark.py',HERE/'model.py',HERE/'policy.py',
           HERE.parent/'python-coupled-study/stress_corpus.py',HERE.parent/'python-anchor-study/anchor_codec.py',
           Path(model.mt.__file__),Path(model.mt.cc.__file__),Path(model.mt.ft.__file__)]
    hashes={str(p):digest(p) for p in paths}
    off=run(frames,manifest,Config(policy=PolicyConfig(mode='fixed',cut_threshold=0)))
    off['presented_quality']=helpers.quality_for_ids(off,{r['id'] for r in off['presented']},manifest)
    if hashes!={str(p):digest(p) for p in paths}:raise RuntimeError('sourceschanged')
    result={'evidence':'Single synthetic cutdetector-off actualcodec ablation; notrealgamecut coverage orhardware',
            'source_sha256':hashes,'baseline_sha256':digest(main_path),'case':off,
            'comparison_cut_off_to_on':helpers.compare(off,fixed_on,manifest)}
    (HERE/'cut-ablation-results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('cutoff',off['presented_eventual'],off['steady_fps'],off['drops_by_reason'],off['keyframes'])
    print('cuton',fixed_on['presented_eventual'],fixed_on['steady_fps'],fixed_on['drops_by_reason'],fixed_on['keyframes'])


if __name__=='__main__':main()
