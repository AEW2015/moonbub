#!/usr/bin/env python3
"""Freeze exact sender, analyzer and implicit-grammar Python evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PREFIX='experiments/python-game-'
FOLDERS=('direct','implicit','analysis')
MUTABLE=('README.md','docs/gamebub-application-specific-codec-plan.md')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    old=json.loads((ROOT/'docs/prototype-v36-provenance.json').read_text())
    frozen={p:h for p,h in old['file_sha256'].items() if p not in MUTABLE}
    for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen v36',p)
    paths={ROOT/p for p in old['file_sha256']}
    extra=('docs/prototype-v36-provenance.json','docs/custom-codec-prototype-v37-2026-11-04.md',
           'docs/v37-next-deployment-gates.md','docs/prototype-v37-comparison.json','docs/prototype-v37-sender-profile.json',
           'experiments/compare_prototype_v37.py','experiments/profile_sender_v37.py',
           'experiments/export_prototype_v37.py','experiments/verify_prototype_v37.py')
    paths|={ROOT/p for p in extra};tests={};runs=[]
    for name in FOLDERS:
        folder=ROOT/(PREFIX+name+'-v37-study')
        paths|={p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        runs.append((folder/'results.json').relative_to(ROOT).as_posix())
        for filename in ('tests.log','tests_verify.log'):
            log=folder/filename;content=log.read_text();match=re.search(r'^Ran (\d+) tests? in ',content,re.M)
            assert match and content.rstrip().endswith('OK'),str(log)
            tests[log.relative_to(ROOT).as_posix()]=int(match[1])
    runs+=['docs/prototype-v37-comparison.json','docs/prototype-v37-sender-profile.json']
    for name in runs:
        for raw,tag in json.loads((ROOT/name).read_text())['source_sha256'].items():
            p=Path(raw);assert not p.is_absolute() and '..' not in p.parts
            assert sha(ROOT/p)==tag,('source snapshot',name,raw);paths.add(ROOT/p)
    manifest=dict(schema='gamebub-v37-provenance',parent_commit='f433677b66c1b9b6a2a74bf21f95dc6ff042524c',
                  file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v36_sha256=frozen,
                  passing_test_logs=tests,run_artifacts=runs,stored_helpers=[PREFIX+n+'-v37-study/verify.py' for n in FOLDERS],
                  limitations=['Python-only studies on reused retained gameplay plus directed motion checks.',
                               'CN36 direct sender/analyzer preserve wire; CS37 implicit grammar needs new receiver and negotiation.',
                               'Implicit transcode is separate from timed directsender. No addition/multiplication of independent speedups.',
                               'Nativeanchors reused from v36; no new nativeencode/decode or matchedqualityBDrate.',
                               'No native ESP32/FPGA endpoint, physical30fps or HEVC/AV1 superiority proof.'])
    (ROOT/'docs/prototype-v37-provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v36_files=len(frozen),recorded_passing_tests=sum(tests.values()))))

if __name__=='__main__':main()
