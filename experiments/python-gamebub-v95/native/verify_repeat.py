#!/usr/bin/env python3
"""Compare two immutable native campaigns' actual planes, excluding timings."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time
AREA = Path(__file__).resolve().parent
ROOT = AREA.parents[2]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('first', type=Path)
    parser.add_argument('second', type=Path)
    args = parser.parse_args()
    first, second = (json.loads(path.read_text()) for path in (args.first,args.second))
    assert first['status'] == second['status'] == 'PASS_NATIVE_AND_INDEPENDENT_PYTHON_ALL_RECORDS'
    assert first['source_sha256'] == second['source_sha256']
    spec = importlib.util.spec_from_file_location('pa95_repeat_data',AREA/'data.py')
    data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data)
    digest = hashlib.sha256()
    frames = planes = 0
    started = time.monotonic()
    for a,b in zip(data.iter_frames(index_path=args.first),data.iter_frames(index_path=args.second),strict=True):
        assert a['fid'] == b['fid'] and a['cohort'] == b['cohort']
        for axis in range(3):
            for profile in range(6):
                x,y = a['plane_variants'][axis][profile], b['plane_variants'][axis][profile]
                assert x == y, ('repeat bytes',frames,axis,profile)
                digest.update(x)
                sx,sy = a['palette_stats'][axis][profile],b['palette_stats'][axis][profile]
                assert {k:v for k,v in sx.items() if not k.endswith('_ns')} == {k:v for k,v in sy.items() if not k.endswith('_ns')}
                planes += 1
        frames += 1
    assert frames == 457 and planes == 8226
    result = dict(status='PASS_BYTE_IDENTICAL_REPEAT',frames=frames,variants=planes,all_variant_bytes_sha256=digest.hexdigest(),first=str(args.first.relative_to(ROOT)),second=str(args.second.relative_to(ROOT)),wall_seconds=time.monotonic()-started,physical_timing_proven=False)
    (AREA/'repeat-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':
    main()
