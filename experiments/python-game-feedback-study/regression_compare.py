#!/usr/bin/env python3
"""Reproduce the frozen GF01 delivered-pin bug and verify GF02 retains it."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import transport

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'python-game-link-study/chunks.py'
spec=importlib.util.spec_from_file_location('v8_pin_regression_baseline',OLD)
old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def exercise(module):
    data=b'read-pinned payload, still owned by a decoder'
    r=module.Reassembler();wire=module.datagrams(data,1,0)
    done=r.feed(wire[0],0);assert done is not None
    fields=list(module.HEADER.unpack_from(wire[0]));fields[-1]^=1
    bad=module.HEADER.pack(*fields)+wire[0][module.HEADER.size:]
    try:r.feed(bad,1)
    except ValueError:pass
    else:raise AssertionError('expected inconsistent metadata rejection')
    retained=(0 in r.pending and r.pending[0].get('complete') is done)
    try:r.commit(done)
    except ValueError:commit_ok=False
    else:commit_ok=True
    return {'delivered_pin_retained_after_conflict':retained,'original_complete_can_commit':commit_ok,
            'pending_payload_bytes_after':r.payload_bytes()}


def main():
    paths=[HERE/'regression_compare.py',HERE/'transport.py',OLD]
    hashes={str(p):sha(p) for p in paths}
    before,after=exercise(old),exercise(transport)
    assert not before['delivered_pin_retained_after_conflict'] and not before['original_complete_can_commit']
    assert after['delivered_pin_retained_after_conflict'] and after['original_complete_can_commit']
    assert hashes=={str(p):sha(p) for p in paths}
    result={'evidence':'In-process ownership regression on conflicting metadata while a completed frame is held by a decoder',
            'source_sha256':hashes,'v8_gf01':before,'v9_gf02':after,
            'scope':'Old immutable bytes still exist in Python; the defect is premature logical slot/ownership release. No physical decoder was run.'}
    (HERE/'regression.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['v8_gf01']),json.dumps(result['v9_gf02']))


if __name__=='__main__':main()
