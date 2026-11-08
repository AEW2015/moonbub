#!/usr/bin/env python3
"""Record/verify owned V109 handoff bytes without including unrelated work."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT/'experiments/python-gamebub-v109/bundle-manifest.json'
FINAL_AUDIT = ROOT/'experiments/python-gamebub-v109/audit/final-bundle-audit.json'
PLANS = ['docs/gamebub-v91-v110-development-plan.md',
         'docs/gamebub-application-specific-codec-plan.md',
         'docs/literature-review-2026-11-06/README.md']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--paths', action='store_true')
    ap.add_argument('--check-index', action='store_true')
    args = ap.parse_args()
    roots = [ROOT/n for n in ('scripts/cu66-v109','docs/cu66-v109','experiments/python-gamebub-v109')]
    roots += sorted((ROOT/'fpga/experiments').glob('cu66-v109-*'))
    assert {p.name for p in roots[3:]} >= {'cu66-v109-flow','cu66-v109-fault','cu66-v109-prefetch','cu66-v109-bank','cu66-v109-fetch'}
    files = []
    for base in roots:
        assert base.is_dir()
        for p in base.rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.pyc','.dcp','.o','.a','.so') or p in (MANIFEST,FINAL_AUDIT):
                continue
            assert not p.is_symlink(), p
            assert p.stat().st_size < 95*1024**2, ('GitHub file-size budget',p)
            files.append(p)
    files += [ROOT/n for n in PLANS]
    assert len(files) == len(set(files))
    current = {str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)}
    root_names = [str(p.relative_to(ROOT)) for p in roots]
    if args.verify or args.paths or args.check_index:
        old = json.loads(MANIFEST.read_text())
        assert old['files'] == current and old['roots'] == root_names, 'Owned handoff scope/hash drift'
    else:
        data = dict(schema='v109-portable-handoff-file-manifest-v1',
                    base_revision='388208dcb73800d93e8c26bfb0c678485a7de133',
                    branch='study/gamebub-v109-integrated-timing-20261108',roots=root_names,
                    scope='Owned V109 directories and three central plans; earlier tracked dependencies remain in the base tree.',
                    exclusions=['This manifest and its final binding audit','Python caches','External checkpoints/build binaries','Unrelated marker-recovery work'],
                    file_count=len(current),total_bytes=sum(x['bytes'] for x in current.values()),files=current)
        MANIFEST.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    if args.check_index:
        for name,meta in current.items():
            raw = subprocess.check_output(['git','show',':'+name],cwd=ROOT)
            assert len(raw) == meta['bytes'] and hashlib.sha256(raw).hexdigest() == meta['sha256'], name
        assert subprocess.check_output(['git','show',':'+str(MANIFEST.relative_to(ROOT))],cwd=ROOT) == MANIFEST.read_bytes()
    if args.paths:
        print('\n'.join([*current,str(MANIFEST.relative_to(ROOT))]))
    else:
        print(json.dumps(dict(status='PASS_CURRENT_V109_BUNDLE',files=len(current),bytes=sum(x['bytes'] for x in current.values()),index_verified=args.check_index)))


if __name__ == '__main__':
    main()
