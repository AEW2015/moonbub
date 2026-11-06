#!/usr/bin/env python3
"""Retain a finite-memory packet/scratch/dense-coefficient RTL simulation."""
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
VECTOR = ROOT / 'experiments/python-gamebub-v91d/vectors/coefficients.jsonl.gz'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=910432)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'pipeline-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    build = '/build/v91d-pipeline-' + out.name
    paths = [ROOT / 'fpga/experiments/cu66-v91/br88_rice_elastic.sv',
             ROOT / 'fpga/experiments/cu66-v91b/br88_context.sv',
             AREA / 'br88_packet_ingress.sv', AREA / 'packed_scratch.sv', AREA / 'br88_pipeline.sv',
             AREA / 'tb_pipeline.cpp', Path(__file__).resolve()]
    report = dict(schema='cu66-v91d-integrated-pipeline-v1', status='FAIL', seed=args.seed,
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(path.relative_to(ROOT)): sha(path) for path in paths},
                  vectors_sha256=sha(VECTOR), vector_index_sha256=sha(VECTOR.with_name('index.json')),
                  build_directory=build, commands=[],
                  fence='Start edge excluded; every later edge through sticky integrated done, after dense final delivery, included.',
                  memory_model='One outstanding 16B transaction; FAST ack1cycle, SLOW write16/read18 plus0..3 deterministic jitter; ready/output stalls. Writes commit on delayed ACK. Cold memory bus empty, warm reset/abort retain pending requests.',
                  scope='Packet and packed scratch through dense coefficients only. Finite external memory model, not physical SDRAM calibration; packet staging still combinational multiport. No pixel/HUD/reference/display/full-frame or hardware proof.')
    started = time.monotonic()

    def command(argv, name, timeout):
        record = dict(argv=argv, log=name, exit_code=None)
        report['commands'].append(record)
        with (out / name).open('w') as target:
            result = subprocess.run(argv, stdout=target, stderr=subprocess.STDOUT, timeout=timeout)
        record['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Command exit {result.returncode}; see {out / name}')

    try:
        for path in paths:
            target = out / 'sources' / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        shutil.copyfile(VECTOR, out / 'vectors.jsonl.gz')
        shutil.copyfile(VECTOR.with_name('index.json'), out / 'index.json')
        text_path = out / 'vectors.txt'
        cases = [json.loads(line) for line in gzip.open(VECTOR, 'rt')]
        with text_path.open('w') as target:
            for case in cases:
                target.write(' '.join(map(str, (case['id'], case['blocks'], case['packet_hex'],
                    case['dense_hex'], case['packed_hex']))) + '\n')
        report['text_vectors_sha256'] = sha(text_path)
        report['vector_packets'] = len(cases)
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2',
            '--assert', '-Wall', '--top-module', 'br88_pipeline', '--Mdir', build,
            '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
            *[str(out / 'sources' / path.relative_to(ROOT)) for path in paths if path.suffix in ('.sv', '.cpp')]],
            'compile.log', 300)
        command(['docker', 'exec', CONTAINER, build + '/Vbr88_pipeline', str(text_path), str(args.seed)],
                'simulation.jsonl', 600)
        rows = [json.loads(line) for line in (out / 'simulation.jsonl').read_text().splitlines()]
        verdicts = [row for row in rows if row['type'] == 'verdict']
        assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
        records = [row for row in rows if row['type'] == 'case']
        assert len(records) == len(cases) * 4 == 68
        totals = {}
        for row in records:
            population = 'actual' if row['id'].startswith('actual:') else 'other'
            key = population, row['memory_profile'], row['serial_clear']
            aggregate = totals.setdefault(key, dict(population=population, memory_profile=key[1],
                serial_clear=key[2], packets=0, **{field: 0 for field in (
                    'cycles', 'input_bytes', 'dense_coefficients', 'read_requests', 'write_requests',
                    'output_stalls', 'metadata_wait', 'memory_pending_edges')}))
            aggregate['packets'] += 1
            for field in ('cycles', 'input_bytes', 'dense_coefficients', 'read_requests', 'write_requests',
                          'output_stalls', 'metadata_wait', 'memory_pending_edges'):
                aggregate[field] += row[field]
        comparisons = []
        for population in ('actual', 'other'):
            for profile in (0, 1):
                mask, serial = totals[(population, profile, 0)], totals[(population, profile, 1)]
                for field in ('dense_coefficients', 'read_requests', 'write_requests', 'input_bytes'):
                    assert mask[field] == serial[field]
                comparisons.append(dict(population=population, memory_profile=profile,
                    mask_cycles=mask['cycles'], serial_cycles=serial['cycles'],
                    serial_over_mask=serial['cycles'] / mask['cycles'],
                    cycle_reduction_percent=100 * (1 - mask['cycles'] / serial['cycles'])))
        assert report['source_sha256'] == {str(path.relative_to(ROOT)): sha(path) for path in paths}
        assert sha(VECTOR) == report['vectors_sha256']
        assert sha(VECTOR.with_name('index.json')) == report['vector_index_sha256']
        report.update(status='PASS_INTEGRATED_FINITE_MEMORY_COEFFICIENT_PIPELINE',
                      verdict=verdicts[0], totals=list(totals.values()), comparisons=comparisons)
        text_path.unlink()
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(path.relative_to(out)): sha(path) for path in out.rglob('*') if path.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'pipeline-results.json').write_text(json.dumps(dict(report,
            selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V91D_PIPELINE', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
