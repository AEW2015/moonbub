#!/usr/bin/env python3
"""Retain each strict finite-memory packed-scratch RTL simulation attempt."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91d'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vectors', type=Path, default=ROOT / 'experiments/python-gamebub-v91d/vectors/coefficients.jsonl.gz')
    args = parser.parse_args()
    args.vectors = args.vectors.resolve()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    name = stamp + '-' + uuid.uuid4().hex[:8]
    out = AREA / 'scratch-attempts' / name
    out.mkdir(parents=True)
    build = '/build/v91d-scratch-' + name
    sources = [Path(__file__).resolve(), AREA / 'packed_scratch.sv', AREA / 'tb_scratch.cpp']
    report = dict(schema='cu66-v91d-scratch-rtl-v1', status='FAIL', build_directory=build,
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  vectors=str(args.vectors.relative_to(ROOT)), vectors_sha256=sha(args.vectors), commands=[],
                  scope='Functional sequential packed scratch RTL with finite-latency acknowledged 128-bit memory; independent image/dense goldens; no hardware, synthesis/fit, frequency, IDCT or full-frame deadline proof.',
                  reset_contract='FPGA power-on initialized state/outstanding/epoch-seen; external bus empty at cold construction. Warm reset cancels owner and drains accepted old transaction before begin_ready.',
                  full_30fps_proven=False, complete_under10ms_proven=False)
    for path in sources:
        snapshot = out / 'sources' / path.relative_to(ROOT)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, snapshot)
    shutil.copyfile(args.vectors, out / 'cases.jsonl.gz')
    index = args.vectors.with_name('index.json')
    if index.exists():
        shutil.copyfile(index, out / 'index.json')
        report['vector_index_sha256'] = sha(index)
    started = time.monotonic()

    def command(argv, log, timeout):
        row = dict(argv=argv, log=log, exit_code=None)
        report['commands'].append(row)
        with (out / log).open('w') as stream:
            result = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        row['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Command failed ({result.returncode}): {out / log}')

    try:
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        count = outputs = 0
        text_vectors = out / 'vectors.txt'
        with gzip.open(out / 'cases.jsonl.gz', 'rt') as source, text_vectors.open('w') as target:
            for line in source:
                case = json.loads(line)
                sparse = case['sparse']
                target.write(' '.join(map(str, [case['id'], case['blocks'], int(case['raw']), *case['counts'],
                                               case['used_bytes'], len(sparse), case['dense_hex'], case['packed_hex']])) + '\n')
                for event in sparse:
                    target.write(' '.join(map(str, event)) + '\n')
                count += 1
                outputs += case['blocks'] * 64
        report.update(vector_cases=count, outputs_per_configuration=outputs, text_vectors_sha256=sha(text_vectors))
        command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2', '--assert', '-Wall',
                 '--top-module', 'packed_scratch', '--Mdir', build, '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
                 str(out / 'sources' / (AREA / 'packed_scratch.sv').relative_to(ROOT)),
                 str(out / 'sources' / (AREA / 'tb_scratch.cpp').relative_to(ROOT))], 'compile.log', 300)
        command(['docker', 'exec', CONTAINER, build + '/Vpacked_scratch', str(text_vectors)], 'simulation.jsonl', 300)
        rows = [json.loads(line) for line in (out / 'simulation.jsonl').read_text().splitlines()]
        verdict = [row for row in rows if row['type'] == 'verdict']
        assert len(verdict) == 1 and verdict[0]['status'] == 'TEST_PASS'
        assert verdict[0]['cases'] == count and verdict[0]['configurations'] == 4
        case_rows = [row for row in rows if row['type'] == 'case']
        assert len(case_rows) == count * 4
        for stalls in (0, 1):
            for serial in (0, 1):
                assert sum(row['outputs'] for row in case_rows if row['stalls'] == stalls and row['serial_clear'] == serial) == outputs
        assert report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sources}
        assert sha(args.vectors) == report['vectors_sha256'] == sha(out / 'cases.jsonl.gz')
        text_vectors.unlink()
        report.update(status='PASS_SCRATCH_RTL_FINITE_MEMORY', verdict=verdict[0])
    except BaseException as error:
        report.update(error_class=type(error).__name__, error=str(error))
        raise
    finally:
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(path.relative_to(out)): sha(path) for path in out.rglob('*') if path.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        selected = dict(report, selected_report=str((out / 'results.json').relative_to(ROOT)))
        (AREA / 'scratch-results.json').write_text(json.dumps(selected, indent=2) + '\n')
        print('V91D_SCRATCH_RTL', report['status'], out / 'results.json', flush=True)


if __name__ == '__main__':
    main()
