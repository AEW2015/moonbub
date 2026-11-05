#!/usr/bin/env python3
"""Freeze v32 Python codec studies and their retained verification evidence."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
FOLDERS=('controller','shrink','hud','wide-motion','wide-escape','schedule','audit')
P='experiments/python-game-'
RUNS=[P+n+'-v32-study/results.json' for n in FOLDERS if n!='audit']
RUNS += [P+'audit-v32-study/audit.json']
MUTABLE=('README.md','docs/gamebub-application-specific-codec-plan.md')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    old=json.loads((ROOT/'docs/prototype-v31-provenance.json').read_text())
    frozen={p:h for p,h in old['file_sha256'].items() if p not in MUTABLE}
    for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen v31',p)
    paths={ROOT/p for p in old['file_sha256']}
    paths|={ROOT/p for p in ('docs/prototype-v31-provenance.json','docs/custom-codec-prototype-v32-2026-11-04.md','experiments/export_prototype_v32.py','experiments/verify_prototype_v32.py')}
    for n in FOLDERS:
        paths|={p for p in (ROOT/(P+n+'-v32-study')).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    for name in RUNS:
        for p,h in json.loads((ROOT/name).read_text())['source_sha256'].items():
            q=Path(p);assert not q.is_absolute() and '..' not in q.parts
            assert sha(ROOT/q)==h,('source snapshot',name,p);paths.add(ROOT/q)
    tests={}
    for n in FOLDERS:
        folder=ROOT/(P+n+'-v32-study')
        log=folder/'tests.log';content=log.read_text()
        m=re.search(r'^Ran (\d+) tests? in ',content,re.M)
        assert m and content.rstrip().endswith('OK'),str(log)
        tests[log.relative_to(ROOT).as_posix()]=int(m[1])
    manifest=dict(schema='gamebub-v32-provenance',parent_commit='582e306bfec30f064f0929b933e4a5a4812911c2',
                  file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v31_sha256=frozen,
                  passing_test_logs=tests,run_artifacts=RUNS,
                  stored_helpers=[P+n+'-v32-study/verify.py' for n in FOLDERS if n!='audit'],
                  limitations=['Python evidence only; short retained gameplay windows reused.',
                               'Actual causal CP27 packets preserve old HU25; HX32/HS32 and WV32 components require new full profiles.',
                               'Two/three-bank scheduling is a dependency model, not new RTL or routed timing.',
                               'No native ESP32/FPGA/RF endpoint, physical 30 fps, or HEVC/AV1 parity proof.'])
    (ROOT/'docs/prototype-v32-provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v31_files=len(frozen),recorded_passing_tests=sum(tests.values()))))


if __name__=='__main__':main()
