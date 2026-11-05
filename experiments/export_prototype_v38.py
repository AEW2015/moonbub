#!/usr/bin/env python3
"""Freeze v38 exact integration, arithmetic and spatial Python evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
FOLDERS=('integrated','binary','spatial');PREFIX='experiments/python-game-'
MUTABLE=('README.md','docs/gamebub-application-specific-codec-plan.md')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    old=json.loads((ROOT/'docs/prototype-v37-provenance.json').read_text())
    frozen={p:h for p,h in old['file_sha256'].items() if p not in MUTABLE}
    for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen v37',p)
    paths={ROOT/p for p in old['file_sha256']}
    paths|={ROOT/p for p in ('docs/prototype-v37-provenance.json','docs/custom-codec-prototype-v38-2026-11-05.md',
                           'docs/v38-prediction-inventory.md','docs/prototype-v38-comparison.json',
                           'experiments/compare_prototype_v38.py','experiments/export_prototype_v38.py','experiments/verify_prototype_v38.py')}
    runs=[];tests={}
    for name in FOLDERS:
        folder=ROOT/(PREFIX+name+'-v38-study')
        paths|={p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        runs.append((folder/'results.json').relative_to(ROOT).as_posix())
        for filename in ('tests.log','tests_verify.log'):
            log=folder/filename;content=log.read_text();match=re.search(r'^Ran (\d+) tests? in ',content,re.M)
            assert match and content.rstrip().endswith('OK'),str(log)
            tests[log.relative_to(ROOT).as_posix()]=int(match[1])
    runs.append('docs/prototype-v38-comparison.json')
    for name in runs:
        for raw,tag in json.loads((ROOT/name).read_text())['source_sha256'].items():
            path=Path(raw);assert not path.is_absolute() and '..' not in path.parts
            assert sha(ROOT/path)==tag,('source snapshot',name,raw);paths.add(ROOT/path)
    result=dict(schema='gamebub-v38-provenance',parent_commit='8ed136c631bcf15221b98bd0fec48fbffc4b38f1',
                file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v37_sha256=frozen,
                passing_test_logs=tests,run_artifacts=runs,stored_helpers=[PREFIX+n+'-v38-study/verify.py' for n in FOLDERS],
                limitations=['Sixhour research checkpoint, not completion of sixhour objective.',
                             'Exact directCS37 integratedsender and separate coefficientarithmetic/spatial pilots on reused short content.',
                             'AB38frame proofadapter stagesarrays and reencodesfrozenentropy; no native streamingreceiver or arithmeticFPGA service proof.',
                             'Spatial modeproxy pilot is a compressionregression despite lowerMSE; independentmode0control differsfrom oldRDO policy.',
                             '48retainednativeAUs freshlydecoded, zero newnativeencodes; no matchedqualityBDrate or HEVC/AV1 superiority.',
                             'No nativeESP32/FPGA endpoint or physical30fps proof.'])
    (ROOT/'docs/prototype-v38-provenance.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v37_files=len(frozen),recorded_passing_tests=sum(tests.values()))))

if __name__=='__main__':main()
