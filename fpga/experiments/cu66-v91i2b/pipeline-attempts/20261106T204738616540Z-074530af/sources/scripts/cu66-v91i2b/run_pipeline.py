#!/usr/bin/env python3
"""Qualify bounded refill overlap against a frozen exact V91i2a control."""
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
AREA = ROOT / 'fpga/experiments/cu66-v91i2b'
MODEL = ROOT / 'experiments/python-gamebub-v91i2b'
VECTORS = ROOT / 'experiments/python-gamebub-v91i2/vectors'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compress_trace(path):
    if not path.exists():
        return None
    target = path.with_suffix(path.suffix + '.gz')
    with path.open('rb') as src, target.open('wb') as dest:
        with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=9) as zipped:
            shutil.copyfileobj(src, zipped)
    raw = gzip.decompress(target.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == sha(path)
    result = dict(path=target.name, gzip_sha256=sha(target), jsonl_sha256=sha(path), records=len(raw.splitlines()))
    path.unlink()
    return result


def control_parity(out, seed):
    old_summary = json.loads((ROOT / 'experiments/python-gamebub-v91i2/summary.json').read_text())
    baseline = next(row for row in old_summary['retained_rtl_attempts'] if row['seed'] == seed)
    base_path = ROOT / baseline['path']
    assert sha(base_path) == baseline['sha256']
    old_report = json.loads(base_path.read_text())
    old_cases = [json.loads(line) for line in (base_path.parent / 'simulation.jsonl').read_text().splitlines()
                 if json.loads(line)['type'] == 'case']
    new_cases = [json.loads(line) for line in (out / 'simulation-serial.jsonl').read_text().splitlines()
                 if json.loads(line)['type'] == 'case']
    assert len(old_cases) == len(new_cases) == 22
    for old, new in zip(old_cases, new_cases, strict=True):
        assert all(new[key] == value for key, value in old.items()), (old['id'], old['memory_profile'])
    def trace(path):
        return [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
    old_tiles = trace(base_path.parent / old_report['tile_trace']['path'])
    new_tiles = trace(out / 'tile-events-serial.jsonl.gz')
    assert len(old_tiles) == len(new_tiles) == 63412
    assert all(all(new[key] == value for key, value in old.items())
               for old, new in zip(old_tiles, new_tiles, strict=True))
    return dict(status='PASS_EXACT_FROZEN_CONTROL', baseline_report=str(base_path.relative_to(ROOT)),
                baseline_report_sha256=sha(base_path), case_rows=len(old_cases),
                exact_legacy_case_fields=sum(len(row) for row in old_cases),
                exact_ordered_tile_rows=len(old_tiles))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, choices=(911201, 911202), default=911201)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'pipeline-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    old_sv = [ROOT / ('fpga/experiments/' + name) for name in (
        'cu66-v91/br88_rice_elastic.sv', 'cu66-v91b/br88_context.sv',
        'cu66-v91d/br88_packet_ingress.sv', 'cu66-v91g2/packed_scratch_v91g2.sv',
        'cu66-v91h/br88_packet_ingress_v91h.sv', 'cu66-v91h/br88_packet_ingress_sync_v91h.sv',
        'cu66-v91h/br88_pipeline_v91h.sv', 'cu66-v91i2/cs88_admission_v91i2a.sv')]
    helper = AREA / 'byte_refill_queue_v91i2b.sv'
    wrapper = AREA / 'cs88_pipeline_v91i2b.sv'
    cpp = AREA / 'tb_pipeline.cpp'
    standalone = AREA / 'tb_refill_queue.cpp'
    sources = [*old_sv, helper, wrapper, cpp, standalone, MODEL / 'queue_model.py',
               ROOT / 'docs/cu66-v91i2b/queue-contract.md', Path(__file__).resolve()]
    vector_paths = sorted(path for path in VECTORS.rglob('*') if path.is_file())
    assert vector_paths and (VECTORS / 'cases.tsv').exists()
    build = '/build/v91i2b-' + out.name
    report = dict(schema='cu66-v91i2b-refill-overlap-rtl-v1', status='FAIL', seed=args.seed,
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(path.relative_to(ROOT)): sha(path) for path in sources},
                  vectors_sha256={str(path.relative_to(VECTORS)): sha(path) for path in vector_paths},
                  commands=[], build_directory=build,
                  scope='Two-owner registered-byte refill queue; exact disabled V91i2a control and coefficient/tuple endpoint only.',
                  hardware_distinct_30fps_proven=False, full_frame_decode_under10ms_proven=False,
                  full_frame_publication_timestamp=None)
    began = time.monotonic()

    def command(argv, name, timeout):
        entry = dict(argv=argv, log=name, exit_code=None)
        report['commands'].append(entry)
        with (out / name).open('w') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, cwd=ROOT)
        entry['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Command exit {result.returncode}: {out / name}')

    try:
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        shutil.copytree(VECTORS, out / 'vectors')
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        snapshot = lambda path: str(out / 'sources' / path.relative_to(ROOT))
        base = ['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2', '--assert', '-Wall']
        traces = {}
        verdicts = []
        for mode, label in ((0, 'serial'), (1, 'overlap')):
            mode_build = build + '-' + label
            command(base + ['--top-module', 'cs88_pipeline_v91i2b', '--Mdir', mode_build,
                            f'-GREFILL_OVERLAP={mode}', '-CFLAGS',
                            f'-std=c++17 -O2 -Wall -Wextra -Werror -DREFILL_OVERLAP={mode}',
                            *[snapshot(path) for path in old_sv + [helper, wrapper, cpp]]],
                    f'compile-{label}.log', 300)
            command(['docker', 'exec', CONTAINER, mode_build + '/Vcs88_pipeline_v91i2b',
                     str(out / 'vectors/cases.tsv'), str(args.seed), str(out / f'tile-events-{label}.jsonl')],
                    f'simulation-{label}.jsonl', 600)
            traces[label] = compress_trace(out / f'tile-events-{label}.jsonl')
            rows = [json.loads(line) for line in (out / f'simulation-{label}.jsonl').read_text().splitlines()]
            verdict = [row for row in rows if row['type'] == 'verdict']
            assert len(verdict) == 1 and verdict[0]['status'] == 'TEST_PASS'
            assert verdict[0]['seed'] == args.seed and verdict[0]['refill_overlap'] == mode
            assert verdict[0]['cases'] == 22 and verdict[0]['configurations'] == 2
            assert verdict[0]['dense_comparisons'] == 4058368 and traces[label]['records'] == 63412
            verdicts.append(verdict[0])
        queue_build = build + '-queue'
        command(base + ['--top-module', 'byte_refill_queue_v91i2b', '--Mdir', queue_build,
                        '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
                        snapshot(helper), snapshot(standalone)], 'compile-queue.log', 300)
        command(['docker', 'exec', CONTAINER, queue_build + '/Vbyte_refill_queue_v91i2b', str(args.seed)],
                'queue.jsonl', 60)
        queue_rows = [json.loads(line) for line in (out / 'queue.jsonl').read_text().splitlines()]
        queue_verdict = [row for row in queue_rows if row['type'] == 'verdict']
        assert len(queue_verdict) == 1 and queue_verdict[0]['status'] == 'TEST_PASS'
        assert queue_verdict[0]['seed'] == args.seed and queue_verdict[0]['owner_bound'] == 2
        report['baseline_control'] = control_parity(out, args.seed)
        assert report['source_sha256'] == {str(path.relative_to(ROOT)): sha(path) for path in sources}
        assert report['vectors_sha256'] == {str(path.relative_to(VECTORS)): sha(path) for path in vector_paths}
        report.update(status='PASS_BOUNDED_REFILL_OVERLAP_WITH_EXACT_CONTROL', verdicts=verdicts,
                      tile_traces=traces, standalone_verdict=queue_verdict[0], case_rows=44)
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        partial = []
        for path in sorted(out.glob('tile-events-*.jsonl')):
            receipt = compress_trace(path)
            if receipt:
                partial.append(receipt)
        if partial:
            report['partial_tile_traces'] = partial
        report['wall_seconds'] = time.monotonic() - began
        report['artifacts_sha256'] = {str(path.relative_to(out)): sha(path)
                                     for path in sorted(out.rglob('*')) if path.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'pipeline-results.json').write_text(json.dumps(
            dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V91I2B_PIPELINE', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
