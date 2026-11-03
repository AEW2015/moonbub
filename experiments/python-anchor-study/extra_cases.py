#!/usr/bin/env python3
"""Slower assumed decoder sensitivity using actual immutable-anchor packets."""
import hashlib
import json
from pathlib import Path
import sys

import timed
from timed import Config, run

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'python-coupled-study'))
from validation import summarize_presentation


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline = json.loads((HERE/'results.json').read_text())
    sources = [HERE/'extra_cases.py', HERE/'timed.py', HERE/'anchor_codec.py',
               HERE.parent/'python-coupled-study/validation.py', Path(timed.mt.__file__),
               Path(timed.mt.cc.__file__), Path(timed.mt.ft.__file__), Path(timed.corpus.__file__)]
    hashes = {str(p): digest(p) for p in sources}
    scenarios = []
    for scene in baseline['scenes'][:2]:
        manifest = scene['manifest']
        frames, current = timed.corpus.load_video(manifest['source'], max_frames=60,
                                                 start_seconds=manifest['start_seconds'])
        if current['frame_sha256'] != manifest['frame_sha256']:
            raise AssertionError('source changed')
        for decode in ((20,40) if '2600' in scene['name'] else (20,)):
            row = run(frames, current, Config(feedback_ms=10, decode_ms=decode))
            check = summarize_presentation([{'id':i, 'capture_ms':i*1000/30} for i in range(60)],
                                           row['presented'], 2000, (500,1500))
            if check['presented_count'] != row['presented_strict'] or check['steady_fps'] != row['steady_fps']:
                raise AssertionError('independent presentation metrics differ')
            scenarios.append({'name':scene['name'], 'manifest':current, 'decode_ms':decode,
                              'result':row, 'independent_metrics':check})
    if hashes != {str(p):digest(p) for p in sources}:
        raise RuntimeError('sources changed')
    report = {'evidence':'Actual anchor re-encoding with slower assumed virtual decode, not physical timing',
              'source_sha256':hashes, 'baseline_sha256':digest(HERE/'results.json'), 'scenarios':scenarios}
    (HERE/'extra-results.json').write_text(json.dumps(report,indent=2)+'\n')
    for x in scenarios:
        r=x['result']
        print(x['name'],x['decode_ms'],r['steady_fps'],r['presented_eventual'],r['steady_age_ms'],r['drops_by_reason'])


if __name__=='__main__':
    main()
