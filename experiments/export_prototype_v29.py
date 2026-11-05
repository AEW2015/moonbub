#!/usr/bin/env python3
"""Freeze v29 inputs, derived packets, source snapshots and verification logs."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
FOLDERS=('controller','adaptive','entropy','audit')
P='experiments/python-game-'
RUNS=[P+n+'-v29-study/results.json' for n in ('controller','adaptive','entropy')]
RUNS += [P+'audit-v29-study/audit.json']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    old=json.loads((ROOT/'docs/prototype-v28-provenance.json').read_text())
    frozen={p:h for p,h in old['file_sha256'].items() if p not in ('README.md','docs/gamebub-application-specific-codec-plan.md')}
    for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen v28',p)
    paths={ROOT/p for p in old['file_sha256']}
    paths|={ROOT/p for p in ('docs/prototype-v28-provenance.json','docs/custom-codec-prototype-v29-2026-11-04.md','experiments/export_prototype_v29.py','experiments/verify_prototype_v29.py')}
    for n in FOLDERS:
        paths|={p for p in (ROOT/(P+n+'-v29-study')).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    for name in RUNS:
        for p,h in json.loads((ROOT/name).read_text())['source_sha256'].items():
            q=Path(p);assert not q.is_absolute() and '..' not in q.parts
            assert sha(ROOT/q)==h,('source snapshot',name,p);paths.add(ROOT/q)
    tests={}
    for n in FOLDERS:
        folder=ROOT/(P+n+'-v29-study')
        logs=[folder/('all_tests.log' if (folder/'all_tests.log').exists() else 'tests.log')]
        for log in logs:
            content=log.read_text();m=re.search(r'^Ran (\d+) tests? in ',content,re.M)
            assert m and content.rstrip().endswith('OK'),str(log)
            tests[log.relative_to(ROOT).as_posix()]=int(m[1])
    manifest=dict(schema='gamebub-v29-provenance',parent_commit='6fabf8c35e4684dc266d0e2e4ae760f47db9bb55',
                  file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v28_sha256=frozen,
                  passing_test_logs=tests,run_artifacts=RUNS,
                  stored_helpers=[P+'controller-v29-study/verify.py',P+'adaptive-v29-study/verify.py',P+'entropy-v29-study/verify.py'],
                  limitations=['Python evidence only; 96 retained source frames reused across cohorts.',
                               'GM27 wire unchanged; quiet-block search and exact EC26 counter evaluated; whole-plane selector is a negative control.',
                               'No native ESP32/FPGA/RF, physical 30 fps, or HEVC/AV1 parity proof.'])
    (ROOT/'docs/prototype-v29-provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v28_files=len(frozen),recorded_passing_tests=sum(tests.values()))))


if __name__=='__main__':main()
