#!/usr/bin/env python3
"""Freeze the v25 study inventory after all campaigns and checks finish."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = ('base-motion','hud-motion','base-probe','native-motion','fine-key','capped-key','combined-motion','audit')
PREFIX = 'experiments/python-game-'
TESTS = {'base-motion':15,'hud-motion':13,'fine-key':3,'capped-key':2,'combined-motion':10,'audit':8}
RUNS = [PREFIX+name+'-v25-study/results.json' for name in FOLDERS if name not in ('base-motion','audit')]
RUNS += [PREFIX+'audit-v25-study/audit.json']


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    old = json.loads((ROOT/'docs/prototype-v24-provenance.json').read_text())
    indexes = {'README.md','docs/gamebub-application-specific-codec-plan.md'}
    frozen = {p:expected for p,expected in old['file_sha256'].items() if p not in indexes}
    for p,expected in frozen.items(): assert sha(ROOT/p) == expected, ('frozen v24 changed',p)
    paths = {ROOT/p for p in old['file_sha256']}
    paths |= {ROOT/p for p in ('docs/prototype-v24-provenance.json','docs/custom-codec-prototype-v25-2026-11-04.md',
                               'experiments/export_prototype_v25.py','experiments/verify_prototype_v25.py')}
    for folder in FOLDERS:
        paths |= {p for p in (ROOT/(PREFIX+folder+'-v25-study')).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    for artifact in RUNS:
        data = json.loads((ROOT/artifact).read_text())
        for p,expected in data['source_sha256'].items():
            relative = Path(p); assert not relative.is_absolute() and '..' not in relative.parts
            assert sha(ROOT/relative) == expected, ('source snapshot changed',artifact,p)
            paths.add(ROOT/relative)
    manifest = dict(schema='gamebub-v25-provenance', parent_commit='4025d35593e8b71b9d9f5e4fb68d1e7a9ed29189',
                    file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},
                    frozen_v24_sha256=frozen, test_counts={PREFIX+k+'-v25-study':v for k,v in TESTS.items()},
                    run_artifacts=RUNS, stored_helpers=[PREFIX+k+'-v25-study' for k in ('hud-motion','fine-key','capped-key','combined-motion')],
                    scope=['All inherited v24 codec/results frozen; only README/plan indexes advance.',
                           'Retained offline compression evidence, not native/RTL/RF/physical30fps or HEVC/AV1 parity proof.'])
    (ROOT/'docs/prototype-v25-provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v24_files=len(frozen),recorded_tests=sum(TESTS.values()))))


if __name__ == '__main__': main()
