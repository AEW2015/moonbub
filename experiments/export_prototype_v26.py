#!/usr/bin/env python3
"""Freeze v26 inputs, derived packets, source snapshots and verification logs."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
FOLDERS=('rdo-counter','prediction','entropy','audit')
P='experiments/python-game-'
RUNS=[P+n+'-v26-study/results.json' for n in ('rdo-counter','prediction','entropy')]
RUNS += [P+'prediction-v26-study/full_results.json',P+'audit-v26-study/audit.json']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    old=json.loads((ROOT/'docs/prototype-v25-provenance.json').read_text())
    frozen={p:h for p,h in old['file_sha256'].items() if p not in ('README.md','docs/gamebub-application-specific-codec-plan.md')}
    for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen v25',p)
    paths={ROOT/p for p in old['file_sha256']}
    paths|={ROOT/p for p in ('docs/prototype-v25-provenance.json','docs/custom-codec-prototype-v26-2026-11-04.md','experiments/export_prototype_v26.py','experiments/verify_prototype_v26.py')}
    for n in FOLDERS:
        paths|={p for p in (ROOT/(P+n+'-v26-study')).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    for name in RUNS:
        for p,h in json.loads((ROOT/name).read_text())['source_sha256'].items():
            q=Path(p);assert not q.is_absolute() and '..' not in q.parts
            assert sha(ROOT/q)==h,('source snapshot',name,p);paths.add(ROOT/q)
    tests={}
    for n in FOLDERS:
        folder=ROOT/(P+n+'-v26-study')
        logs=[folder/('all_tests.log' if (folder/'all_tests.log').exists() else 'tests.log')]
        for log in logs:
            content=log.read_text();m=re.search(r'^Ran (\d+) tests? in ',content,re.M)
            assert m and content.rstrip().endswith('OK'),str(log)
            tests[log.relative_to(ROOT).as_posix()]=int(m[1])
    manifest=dict(schema='gamebub-v26-provenance',parent_commit='3d881382f022e95808f72cea2f2842a73343544f',
                  file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v25_sha256=frozen,
                  passing_test_logs=tests,run_artifacts=RUNS,
                  stored_helpers=[P+'rdo-counter-v26-study/verify.py',P+'prediction-v26-study/verify.py',P+'prediction-v26-study/full_verify.py',P+'entropy-v26-study/verify.py'],
                  limitations=['Python reference/prototype evidence only; retained96sourceframes reusedacrosscohorts.',
                               'Independententropyandfractionalformatshavenotbeenmerged. No nativeESP32/FPGA/RF/physical30fpsorHEVC/AV1parityproof.'])
    (ROOT/'docs/prototype-v26-provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v25_files=len(frozen),recorded_passing_tests=sum(tests.values()))))


if __name__=='__main__':main()
