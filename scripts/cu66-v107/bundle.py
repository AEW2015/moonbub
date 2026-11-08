#!/usr/bin/env python3
"""Record or verify the exact V107 handoff files, leaving unrelated work alone."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/'experiments/python-gamebub-v107/bundle-manifest.json'
ROOTS=[
    'scripts/cu66-v107','docs/cu66-v107','experiments/python-gamebub-v107',
    *['fpga/experiments/cu66-v107-'+suffix for suffix in
      ('flow','threshold-runtime-flow','count-threshold-native','fanout-attribution','postroute-probe','rice','quant','value-check','elastic','header','scale','tables','payload-reset','idct-reset','guard-dsp','meta-flags','plan-prefix','count-threshold','cdc','cdc-flow','cdc-sync')],
]
PLANS=['docs/gamebub-v91-v110-development-plan.md',
       'docs/gamebub-application-specific-codec-plan.md',
       'docs/literature-review-2026-11-06/README.md']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def files():
    result=[]
    for name in ROOTS:
        base=ROOT/name
        assert base.is_dir(),name
        for p in base.rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.pyc','.dcp','.o','.a','.so') or p==MANIFEST:
                continue
            assert not p.is_symlink(),p
            assert p.stat().st_size<95*1024*1024,('GitHub-file-size',p)
            result.append(p)
    result += [ROOT/name for name in PLANS]
    assert len(result)==len(set(result))
    return sorted(result)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');ap.add_argument('--paths',action='store_true');args=ap.parse_args()
    current={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files()}
    if args.verify or args.paths:
        old=json.loads(MANIFEST.read_text())
        assert old['files']==current,'bundle file or hash drift'
    else:
        data=dict(schema='v107-portable-handoff-file-manifest-v1',
            base_revision='f228dc3adedae9a8ff44ca8d531c01aa5b94d970',
            branch='study/gamebub-v107-clock-timing-20261108',
            scope='Only V107 owned directories and three explicitly updated roadmap documents; earlier tracked dependencies remain in the base tree.',
            exclusions=['This self-describing manifest','Python caches','External checkpoints/build binaries','Unrelated marker-recovery work'],
            file_count=len(current),total_bytes=sum(x['bytes'] for x in current.values()),files=current)
        MANIFEST.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    if args.paths:
        print('\n'.join([*current,str(MANIFEST.relative_to(ROOT))]))
    else:print(json.dumps(dict(status='PASS_CURRENT_BUNDLE',files=len(current),bytes=sum(x['bytes'] for x in current.values()))))


if __name__=='__main__':main()
