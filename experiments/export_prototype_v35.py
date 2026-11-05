#!/usr/bin/env python3
"""Freeze v35 Python codec studies and their retained verification evidence."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
FOLDERS=('controller','aligned','reuse','audit')
P='experiments/python-game-'
RUNS=[P+n+'-v35-study/results.json' for n in FOLDERS if n!='audit']
RUNS += [P+'audit-v35-study/audit.json']
MUTABLE=('README.md','docs/gamebub-application-specific-codec-plan.md')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    old=json.loads((ROOT/'docs/prototype-v34-provenance.json').read_text())
    frozen={p:h for p,h in old['file_sha256'].items() if p not in MUTABLE}
    for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen v34',p)
    paths={ROOT/p for p in old['file_sha256']}
    paths|={ROOT/p for p in ('docs/prototype-v34-provenance.json','docs/custom-codec-prototype-v35-2026-11-04.md','experiments/export_prototype_v35.py','experiments/verify_prototype_v35.py')}
    for n in FOLDERS:
        paths|={p for p in (ROOT/(P+n+'-v35-study')).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    for name in RUNS:
        for p,h in json.loads((ROOT/name).read_text())['source_sha256'].items():
            q=Path(p);assert not q.is_absolute() and '..' not in q.parts
            assert sha(ROOT/q)==h,('source snapshot',name,p);paths.add(ROOT/q)
    tests={}
    for n in FOLDERS:
        folder=ROOT/(P+n+'-v35-study')
        log=folder/'tests.log';content=log.read_text()
        m=re.search(r'^Ran (\d+) tests? in ',content,re.M)
        assert m and content.rstrip().endswith('OK'),str(log)
        tests[log.relative_to(ROOT).as_posix()]=int(m[1])
    manifest=dict(schema='gamebub-v35-provenance',parent_commit='c50df93e313c9402c3741e5f6c921ee40e6f10a3',
                  file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v34_sha256=frozen,
                  passing_test_logs=tests,run_artifacts=RUNS,
                  stored_helpers=[P+n+'-v35-study/verify.py' for n in FOLDERS if n!='audit'],
                  limitations=['Python evidence only; short retained gameplay windows reused.',
                               'Existing GM27/HM34/CP34 syntax unchanged; exact encoder reuse and guarded/raw source formation are separate studies.',
                               'Reuse measures already-paid map reuse at component scope; no full-sender gain extrapolation. Raw/guarded source studies have separate histories and fresh same-input native comparisons.',
                               'No native ESP32/FPGA/RF endpoint, physical 30 fps, or HEVC/AV1 parity proof.'])
    (ROOT/'docs/prototype-v35-provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v34_files=len(frozen),recorded_passing_tests=sum(tests.values()))))


if __name__=='__main__':main()
