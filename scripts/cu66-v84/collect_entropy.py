#!/usr/bin/env python3
"""Compile and retain native entropy primitive traces with independent oracles."""
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v84/entropy'
FIELDS = ('decisions', 'renorm', 'stream_bytes', 'rice_values', 'events',
          'raw_bytes', 'header_bytes', 'crc_bytes', 'emits', 'raw_bits', 'prob_init')
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (AREA / 'index.json').exists():
        raise FileExistsError('Refusing to overwrite retained entropy index')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    attempt = AREA / 'attempts' / stamp
    attempt.mkdir(parents=True)
    binary = '/build/v84-entropy-' + stamp
    sources = [Path(__file__).resolve(), AREA / 'trace.hpp', AREA / 'collect.cpp', AREA / 'data.py']
    sources += sorted((ROOT / 'experiments/cu66-native-v69').glob('*.hpp'))
    sources += [ROOT / 'experiments/cu66-native-v69/index.tsv',
                ROOT / 'experiments/python-gamebub-v82/native/index.json',
                ROOT / 'experiments/python-gamebub-v82/native/data.py',
                ROOT / 'fpga/experiments/cu66-v69/entropy/cu66_ab38_decoder.sv']
    pins = {str(p.relative_to(ROOT)):sha(p) for p in sources}
    with tarfile.open(attempt / 'sources.tar.gz', 'w:gz') as tar:
        for path in sources:
            tar.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    commands = []
    started = time.monotonic()
    report = dict(schema='cu66-v84-entropy-collection-v1', status='FAIL', source_sha256=pins)
    def run(command, log):
        commands.append(command)
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        log.write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f'{command[:3]} exit {result.returncode}; {log}')
        return result
    process = None
    try:
        run(['docker', 'exec', CONTAINER, 'g++', '--version'], attempt / 'compiler.txt')
        run(['docker', 'exec', CONTAINER, 'g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
             str(AREA / 'collect.cpp'), '-o', binary], attempt / 'compile.log')
        run(['docker', 'cp', f'{CONTAINER}:{binary}', str(attempt / 'collector.bin')], attempt / 'copy.log')
        spec = importlib.util.spec_from_file_location('cu84_entropy_native', ROOT / 'experiments/python-gamebub-v82/native/data.py')
        native = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(native)
        expected = iter(native.iter_frames())
        command = ['docker', 'exec', CONTAINER, binary, str(ROOT / 'experiments/cu66-native-v69/index.tsv')]
        commands.append(command)
        raw_hash = hashlib.sha256()
        rows = []
        totals = {name:0 for name in FIELDS}
        history = [0, 0, 0, 0]
        with (attempt / 'native.log').open('wb') as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=log)
            with gzip.open(attempt / 'data.jsonl.gz', 'wb') as output:
                for line in process.stdout:
                    record = json.loads(line)
                    original = next(expected)
                    for name in ('cohort', 'ordinal', 'fid', 'key', 'packet_sha256', 'canonical_sha256', 'hud_sha256', 'display_sha256'):
                        assert record[name] == original[name], ('native identity/digest', name)
                    assert record['zero_mask'] == ''.join(str(x) for x in original['zero_coeff_mask'])
                    assert len(record['work']) == 8100
                    frame_totals = {name:sum(row[i] for row in record['work']) for i,name in enumerate(FIELDS)}
                    assert frame_totals['emits'] == 8100
                    assert frame_totals['crc_bytes'] == sum(record['plane_bytes'])
                    assert all(row[8] == 1 for row in record['work'])
                    for name in FIELDS:
                        totals[name] += frame_totals[name]
                    history[record['cohort']] += 1
                    output.write(line);raw_hash.update(line)
                    meta = {k:v for k,v in record.items() if k not in ('work','zero_mask')}
                    meta['totals'] = frame_totals
                    meta['work_sha256'] = hashlib.sha256(json.dumps(record['work'], separators=(',',':')).encode()).hexdigest()
                    rows.append(meta)
                    if len(rows) % 25 == 0:
                        print('V84_ENTROPY_PROGRESS',len(rows),flush=True)
            code = process.wait()
            assert code == 0, ('native exit',code)
        assert len(rows) == 457 and history == [119,119,119,100]
        try:
            next(expected)
        except StopIteration:
            pass
        else:
            raise AssertionError('native trailing input')
        assert pins == {name:sha(ROOT / name) for name in pins}, 'sources changed during run'
        data = attempt / 'data.jsonl.gz'
        index = dict(schema='cu66-v84-native-entropy-v1', record_count=457, cohort_counts=history,
                     fields=FIELDS, data=dict(path=str(data.relative_to(AREA)), gzip_sha256=sha(data),
                                             raw_sha256=raw_hash.hexdigest()),
                     source_sha256=pins, frames=rows, totals=totals,
                     semantics='Per-tile primitive work in interleaved four-context event-lookahead order; not elapsed clocks.',
                     validation='Every plane coefficient equals frozen bulk decoder; every packet/canonical/HUD/display digest and every zero-mask bit equals V82 native oracle.')
        (AREA / 'index.json').write_text(json.dumps(index, indent=2)+'\n')
        report.update(status='PASS', records=457, planes=1371, cohort_counts=history, totals=totals,
                      gzip_sha256=sha(data), index_sha256=sha(AREA / 'index.json'), source_archive_sha256=sha(attempt / 'sources.tar.gz'))
    except BaseException as exc:
        report['failure'] = repr(exc)
        if process is not None and process.poll() is None:
            process.terminate();process.wait()
        raise
    finally:
        report['wall_seconds'] = time.monotonic()-started
        (attempt / 'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        (attempt / 'results.json').write_text(json.dumps(report, indent=2)+'\n')
        print('V84_ENTROPY_REPORT', attempt / 'results.json', report['status'], flush=True)


if __name__ == '__main__':
    main()
