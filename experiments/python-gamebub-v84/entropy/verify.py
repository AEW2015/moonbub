#!/usr/bin/env python3
"""Independent retained-data/source checks, without compiling or rerunning C++."""
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys

AREA = Path(__file__).resolve().parent
ROOT = AREA.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    index = json.loads((AREA/'index.json').read_text())
    for name, digest in index['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest
    data = load('cu84_verify_entropy_data', AREA/'data.py')
    native = load('cu84_verify_native', ROOT/'experiments/python-gamebub-v82/native/data.py')
    totals = dict.fromkeys(data.FIELDS, 0)
    native_frames = iter(native.iter_frames())
    count = 0
    copy_totals = dict.fromkeys(data.FIELDS, 0)
    copy_count = 0
    for frame in data.iter_frames():
        original = next(native_frames)
        meta = index['frames'][count]
        for name in ('cohort','ordinal','fid','key','packet_sha256','canonical_sha256','hud_sha256','display_sha256'):
            assert frame[name] == original[name] == meta[name]
        assert frame['zero_mask'] == ''.join(str(x) for x in original['zero_coeff_mask'])
        raw = [[w[name] for name in data.FIELDS] for w in frame['tile_work']]
        assert hashlib.sha256(json.dumps(raw,separators=(',',':')).encode()).hexdigest() == meta['work_sha256']
        stats = {name:sum(w[name] for w in frame['tile_work']) for name in data.FIELDS}
        assert stats == meta['totals']
        assert stats['emits'] == 8100
        assert all(w['emits']==1 for w in frame['tile_work'])
        assert stats['raw_bytes']==0, 'This corpus is compressed-only; raw path is not claimed tested.'
        assert stats['raw_bits'] == stats['renorm'] + 3*72
        assert stats['header_bytes'] == 3*28
        assert stats['prob_init'] == 3*352
        assert stats['crc_bytes'] == sum(frame['plane_bytes'])
        encoded = sum(n-(sum(original['hidden_mask'][start:start+n]) if dispatch==6 else 0)
                      for n,start,dispatch in zip((5400,1350,1350),(0,5400,6750),frame['dispatches']))
        assert stats['rice_values'] == encoded + 2*stats['events']
        assert (stats['raw_bits']+7)//8 <= stats['stream_bytes'] <= (stats['raw_bits']+7)//8 + 11
        for mask,w in zip(original['copy_ref_mask'],frame['tile_work']):
            if mask:
                copy_count += 1
                for name in data.FIELDS:
                    copy_totals[name] += w[name]
        for name in data.FIELDS:
            totals[name] += stats[name]
        count += 1
    assert count == index['record_count'] == 457
    try:
        next(native_frames)
    except StopIteration:
        pass
    else:
        raise AssertionError('native frame coverage mismatch')
    assert totals == index['totals']
    assert copy_count == 2216647
    result = dict(schema='cu66-v84-entropy-verification-v1',status='PASS',records=count,
                  native_coefficient_plane_checks=1371,totals=totals,
                  copy_tiles=copy_count,copy_attributed_totals=copy_totals,
                  index_sha256=hashlib.sha256((AREA/'index.json').read_bytes()).hexdigest(),
                  verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope='Every retained native mask, digest and work row checked; native coefficient equality is the collector oracle, primitive clocks are not measured.',
                  untested='Raw coefficient fallback is implemented but absent from all457 native inputs; no raw-path correctness claim.')
    (AREA/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('V84_ENTROPY_DATA_PASS records=457 planes=1371 copy_tiles=2216647')


if __name__=='__main__':
    main()
