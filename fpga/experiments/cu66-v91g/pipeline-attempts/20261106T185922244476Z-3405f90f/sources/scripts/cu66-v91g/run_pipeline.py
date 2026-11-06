#!/usr/bin/env python3
"""Retain bounded read prefetch with exact V91f overlap-enabled control."""
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

import telemetry

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91g'
VECTORS = ROOT / 'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compress_trace(out, report):
    raw_path = out / 'tile-events.jsonl'
    if not raw_path.is_file():
        return
    path = out / 'tile-events.jsonl.gz'
    with raw_path.open('rb') as source, path.open('wb') as target:
        with gzip.GzipFile(filename='', mode='wb', fileobj=target, mtime=0, compresslevel=9) as encoded:
            shutil.copyfileobj(source, encoded)
    raw_digest = sha(raw_path)
    digest = hashlib.sha256()
    records = 0
    with gzip.open(path, 'rb') as source:
        for line in source:
            digest.update(line)
            records += 1
    assert digest.hexdigest() == raw_digest
    report['tile_trace'] = dict(path=path.name, gzip_sha256=sha(path), jsonl_sha256=raw_digest, records=records,
                                scope='Accepted first/last dense scalars per block/config; external harness trace, not an RTL trace buffer.')
    raw_path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=910432)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'pipeline-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    build = '/build/v91g-pipeline-' + out.name
    paths = [ROOT / 'fpga/experiments/cu66-v91/br88_rice_elastic.sv',
             ROOT / 'fpga/experiments/cu66-v91b/br88_context.sv',
             ROOT / 'fpga/experiments/cu66-v91d/br88_packet_ingress.sv',
             AREA / 'packed_scratch_v91g.sv', AREA / 'br88_pipeline_v91g.sv', AREA / 'tb_pipeline.cpp', AREA / 'tb_scratch_hazards.cpp',
             Path(__file__).resolve(), Path(__file__).with_name('telemetry.py'), telemetry.CONTRACT_PATH]
    report = dict(schema='cu66-v91g-observed-coefficient-pipeline-v1', status='FAIL', seed=args.seed,
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(path.relative_to(ROOT)): sha(path) for path in paths},
                  vectors_sha256=sha(VECTORS), vector_index_sha256=sha(VECTORS.with_name('index.json')),
                  build_directory=build, commands=[],
                  fence='Start edge excluded; rising edges1..integrated_done through dense coefficient completion. Last-input byte, last-dense acceptance and observed done are distinct.',
                  scope='Bounded needed-line read prefetch functional simulation. Full next-tile merge is not integrated. No full-frame validated publication, achieved clock, physical controller or hardware fps/decode result.',
                  full_frame_publication_timestamp=None, full_frame_decode_under10ms_proven=False,
                  hardware_distinct_30fps_proven=False)
    started = time.monotonic()

    def command(argv, name, timeout):
        entry = dict(argv=argv, log=name, exit_code=None)
        report['commands'].append(entry)
        with (out / name).open('w') as target:
            result = subprocess.run(argv, stdout=target, stderr=subprocess.STDOUT, timeout=timeout)
        entry['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Command exit {result.returncode}: {out / name}')

    try:
        for path in paths:
            target = out / 'sources' / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        shutil.copyfile(VECTORS, out / 'vectors.jsonl.gz')
        shutil.copyfile(VECTORS.with_name('index.json'), out / 'index.json')
        cases = telemetry.cases()
        text_path = out / 'vectors.txt'
        with text_path.open('w') as target:
            for case in cases:
                target.write(' '.join(map(str, (case['id'], case['blocks'], case['packet_hex'],
                                                case['dense_hex'], case['packed_hex']))) + '\n')
        report['text_vectors_sha256'] = sha(text_path)
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2',
                 '--assert', '-Wall', '--top-module', 'br88_pipeline_v91g', '--Mdir', build,
                 '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
                 *[str(out / 'sources' / path.relative_to(ROOT)) for path in paths if path.suffix in ('.sv', '.cpp') and path.name != 'tb_scratch_hazards.cpp']],
                'compile.log', 300)
        hazard_build = build + '-hazards'
        command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2',
                 '--assert', '-Wall', '--top-module', 'packed_scratch_v91g', '--Mdir', hazard_build,
                 '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
                 str(out / 'sources' / (AREA / 'packed_scratch_v91g.sv').relative_to(ROOT)),
                 str(out / 'sources' / (AREA / 'tb_scratch_hazards.cpp').relative_to(ROOT))],
                'hazard-compile.log', 300)
        command(['docker', 'exec', CONTAINER, hazard_build + '/Vpacked_scratch_v91g'], 'hazards.jsonl', 60)
        hazards = [json.loads(line) for line in (out / 'hazards.jsonl').read_text().splitlines()]
        assert len(hazards) == 1 and hazards[0]['status'] == 'TEST_PASS'
        report['scratch_hazards'] = hazards[0]
        command(['docker', 'exec', CONTAINER, build + '/Vbr88_pipeline_v91g', str(text_path),
                 str(args.seed), str(out / 'tile-events.jsonl')], 'simulation.jsonl', 600)
        compress_trace(out, report)
        rows = [json.loads(line) for line in (out / 'simulation.jsonl').read_text().splitlines()]
        verdicts = [row for row in rows if row['type'] == 'verdict']
        assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
        assert verdicts[0]['packets'] == len(cases) == 20
        assert verdicts[0]['configurations'] == 4 and verdicts[0]['case_rows'] == 80
        assert verdicts[0]['dense_comparisons'] == sum(case['blocks'] * 64 for case in cases) * 4
        assert verdicts[0]['directed_checks'] == 36
        records = telemetry.validate_rows(rows, cases)
        baseline = telemetry.compare_v91f(records, args.seed)
        tile_summary = telemetry.validate_tiles(out / report['tile_trace']['path'], records, cases)
        assert report['tile_trace']['records'] == sum(case['blocks'] for case in cases) * 4
        (out / 'tile-summary.json').write_text(json.dumps(tile_summary, indent=2) + '\n')
        report.update(verdict=verdicts[0], baseline_v91f=baseline,
                      population_totals=telemetry.aggregate(records),
                      telemetry_reconciliation='PASS_EACH_CYCLE_PARTITION_AND_EVENT_FENCE',
                      tile_summary_sha256=sha(out / 'tile-summary.json'))
        assert report['source_sha256'] == {str(path.relative_to(ROOT)): sha(path) for path in paths}
        assert sha(VECTORS) == report['vectors_sha256']
        assert sha(VECTORS.with_name('index.json')) == report['vector_index_sha256']
        report['status'] = 'PASS_BOUNDED_READ_PREFETCH_WITH_FROZEN_V91F_CONTROL'
        text_path.unlink()
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        compress_trace(out, report)
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(path.relative_to(out)): sha(path) for path in out.rglob('*') if path.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'pipeline-results.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V91G_PIPELINE', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
