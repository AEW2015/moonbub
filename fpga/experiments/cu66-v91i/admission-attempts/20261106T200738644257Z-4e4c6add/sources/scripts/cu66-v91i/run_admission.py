#!/usr/bin/env python3
"""Retain a strict seeded Verilator CS88 admission-only qualification attempt."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91i'
MODEL = ROOT / 'experiments/python-gamebub-v91i'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=911101)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'admission-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    sources = [AREA / 'cs88_admission_v91i1.sv', AREA / 'tb_admission.cpp',
               MODEL / 'admission-model.py', Path(__file__).resolve(),
               ROOT / 'docs/cu66-v91i/admission-contract.md']
    vectors = MODEL / 'vectors'
    vector_paths = sorted(p for p in vectors.rglob('*') if p.is_file())
    assert vector_paths and (vectors / 'vectors.txt').is_file()
    build = '/build/v91i-admission-' + out.name
    report = dict(schema='cu66-v91i1-outer-admission-rtl-v1', status='FAIL',
                  seed=args.seed, source_revision=subprocess.check_output(
                      ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  vectors_sha256={str(p.relative_to(vectors)): sha(p) for p in vector_paths},
                  commands=[], build_directory=build,
                  scope='Restricted native CS88 structural admission only. No entropy consumer dispatch, coefficient/pixel decode, accepted-reference commit, HUD/hash validation or publication.',
                  hardware_distinct_30fps_proven=False,
                  full_frame_decode_under10ms_proven=False,
                  full_frame_publication_timestamp=None)
    started = time.monotonic()

    def command(argv, name, timeout):
        entry = dict(argv=argv, log=name, exit_code=None)
        report['commands'].append(entry)
        with (out / name).open('w') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=timeout, cwd=ROOT)
        entry['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Command exit {result.returncode}: {out / name}')

    try:
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        shutil.copytree(vectors, out / 'vectors')
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build',
                 '-j', '2', '--assert', '-Wall', '--top-module', 'cs88_admission_v91i1',
                 '--Mdir', build, '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
                 *[str(out / 'sources' / p.relative_to(ROOT)) for p in sources[:2]]],
                'compile.log', 300)
        command(['docker', 'exec', CONTAINER, build + '/Vcs88_admission_v91i1',
                 str(out / 'vectors/vectors.txt'), str(args.seed)], 'simulation.jsonl', 600)
        rows = [json.loads(line) for line in (out / 'simulation.jsonl').read_text().splitlines()]
        cases = [r for r in rows if r['type'] == 'case']
        verdicts = [r for r in rows if r['type'] == 'verdict']
        assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
        assert verdicts[0]['seed'] == args.seed and verdicts[0]['cases'] == len(cases)
        assert cases and len({r['id'] for r in cases}) == len(cases)
        assert all(r['status'] == 'PASS' and r['seed'] == args.seed for r in cases)
        assert report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sources}
        assert report['vectors_sha256'] == {str(p.relative_to(vectors)): sha(p) for p in vector_paths}
        report.update(status='PASS_RESTRICTED_CS88_STRUCTURAL_ADMISSION',
                      verdict=verdicts[0], case_rows=len(cases),
                      admitted_rows=sum(r['error'] == 0 for r in cases),
                      rejected_rows=sum(r['error'] != 0 for r in cases))
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p)
                                     for p in sorted(out.rglob('*')) if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'admission-results.json').write_text(json.dumps(
            dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V91I1_ADMISSION', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
