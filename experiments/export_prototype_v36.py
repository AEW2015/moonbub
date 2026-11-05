#!/usr/bin/env python3
"""Freeze canonical-reference and fixed-geometry component evidence."""
import hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
FOLDERS=('canonical','maskplan','comparison')
PREFIX='experiments/python-game-'
MUTABLE=('README.md','docs/gamebub-application-specific-codec-plan.md')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    old=json.loads((ROOT/'docs/prototype-v35-provenance.json').read_text())
    frozen={p:h for p,h in old['file_sha256'].items() if p not in MUTABLE}
    for path,tag in frozen.items():assert sha(ROOT/path)==tag,('frozen v35',path)
    paths={ROOT/p for p in old['file_sha256']}
    paths|={ROOT/p for p in ('docs/prototype-v35-provenance.json',
             'docs/custom-codec-prototype-v36-2026-11-04.md',
             'docs/v36-application-codec-acceptance-checklist.md',
             'experiments/export_prototype_v36.py','experiments/verify_prototype_v36.py')}
    runs=[];tests={}
    for name in FOLDERS:
        folder=ROOT/(PREFIX+name+'-v36-study')
        paths|={p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        artifact=folder/'results.json';runs.append(artifact.relative_to(ROOT).as_posix())
        for raw,tag in json.loads(artifact.read_text())['source_sha256'].items():
            q=Path(raw);assert not q.is_absolute() and '..' not in q.parts
            assert sha(ROOT/q)==tag,('producer',name,raw);paths.add(ROOT/q)
        logs=('tests.log','tests_verify.log') if name=='canonical' else (() if name=='comparison' else ('tests.log',))
        for logfile in logs:
            log=folder/logfile;content=log.read_text()
            match=re.search(r'^Ran (\d+) tests? in ',content,re.M)
            assert match and content.rstrip().endswith('OK'),str(log)
            tests[log.relative_to(ROOT).as_posix()]=int(match[1])
    manifest=dict(schema='gamebub-v36-provenance',parent_commit='4b9b6bc0862e70141a7df69b0bc1731cadcdfd25',
                  file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},
                  frozen_v35_sha256=frozen,passing_test_logs=tests,run_artifacts=runs,
                  stored_helpers=[PREFIX+n+'-v36-study/verify.py' for n in FOLDERS],
                  limitations=['Python-only, retained short reused gameplay.',
                               'CN36 is a new research profile. Full/skip same-profile equality is not unchanged quality versus old reference semantics.',
                               'Compiled masking is measured separately; no addition or multiplication of component speedups.',
                               'No native ESP32/FPGA endpoint, physical30fps, or HEVC/AV1 superiority proof.'])
    (ROOT/'docs/prototype-v36-provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v35_files=len(frozen),recorded_passing_tests=sum(tests.values()))))

if __name__=='__main__':main()
