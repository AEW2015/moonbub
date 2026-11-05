#!/usr/bin/env python3
"""Freeze v39 rank/signal pilots and full arithmetic qualification."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
FOLDERS=('mode-rank','signal','binary-full');PREFIX='experiments/python-game-'
MUTABLE=('README.md','docs/gamebub-application-specific-codec-plan.md')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def passing(path):
    content=path.read_text();found=re.search(r'^Ran (\d+) tests? in ',content,re.M)
    assert found and content.rstrip().endswith('OK'),str(path);return int(found[1])
def main():
    old=json.loads((ROOT/'docs/prototype-v38-provenance.json').read_text());frozen={p:h for p,h in old['file_sha256'].items() if p not in MUTABLE}
    for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen v38',p)
    paths={ROOT/p for p in old['file_sha256']}
    paths|={ROOT/p for p in ('docs/prototype-v38-provenance.json','docs/custom-codec-prototype-v39-2026-11-05.md','docs/v39-source-qualification-notes.md',
                           'docs/prototype-v39-comparison.json','experiments/compare_prototype_v39.py','experiments/export_prototype_v39.py','experiments/verify_prototype_v39.py')}
    tests={};runs=[]
    for name in FOLDERS:
        folder=ROOT/(PREFIX+name+'-v39-study');paths|={p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        runs.append((folder/'results.json').relative_to(ROOT).as_posix())
        if name!='binary-full':
            for logfile in ('tests.log','tests_verify.log'):
                path=folder/logfile;tests[path.relative_to(ROOT).as_posix()]=passing(path)
    inherited={PREFIX+'binary-v38-study/'+name:passing(ROOT/(PREFIX+'binary-v38-study/'+name)) for name in ('tests.log','tests_verify.log')}
    runs.append('docs/prototype-v39-comparison.json')
    for name in runs:
        for raw,tag in json.loads((ROOT/name).read_text())['source_sha256'].items():
            p=Path(raw);assert not p.is_absolute() and '..' not in p.parts
            assert sha(ROOT/p)==tag,('source snapshot',name,raw);paths.add(ROOT/p)
    data=dict(schema='gamebub-v39-provenance',parent_commit='082bc8f761c261ead2f41bf92f664f1b8e3d6efa',
              file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v38_sha256=frozen,
              passing_test_logs=tests,inherited_codec_test_logs=inherited,run_artifacts=runs,
              stored_helpers=[PREFIX+name+'-v39-study/verify.py' for name in FOLDERS],
              limitations=['Sixhourrun stillactive; intermediatecheckpoint.',
                           'Rank lossless vsSP38; signalpolicy changescoefficientchoices/history and retains actualtradeoffs/negativefixtures.',
                           'AB38full48qualification usesfrozencodec andinheritedtests, notnewindependentcontent.',
                           'No freshnativeencode/decode; frozenfull48/prefix12original-inputanchors usedforappropriatecohorts.',
                           'No hardwarefit,physical30fps or HEVC/AV1 superiority proof.'])
    (ROOT/'docs/prototype-v39-provenance.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v38_files=len(frozen),new_passing_tests=sum(tests.values()),inherited_codec_tests=sum(inherited.values()))))
if __name__=='__main__':main()
