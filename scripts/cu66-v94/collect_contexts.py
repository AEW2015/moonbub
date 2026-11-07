#!/usr/bin/env python3
"""Finite actual EC94 inline-model byte-rANS campaign on frozen V88 inputs.
Runs eight whole-plane alternatives and all nine packets, including discarded
alternatives. Independent Python decodes all eight and validates composition.
"""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import resource
from pathlib import Path
import signal
import statistics
import struct
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v94/native'
CONTAINER = 'gamebub-cu66-v69-build'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=int, default=1800)
    args = parser.parse_args()
    assert 60 <= args.timeout <= 7200
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    paths = [Path(__file__).resolve(), AREA / 'codec.hpp', AREA / 'collect.cpp', AREA / 'data.py', AREA / 'test_codec.cpp',
             ROOT / 'experiments/python-gamebub-v94/python/codec.py',
             ROOT / 'experiments/python-gamebub-v92/native/codec.hpp',
             ROOT / 'experiments/python-gamebub-v85/residual/encode.hpp',
             ROOT / 'experiments/python-gamebub-v88/entropy/codec.hpp',
             ROOT / 'experiments/python-gamebub-v88/entropy/data.py',
             ROOT / 'experiments/python-gamebub-v88/entropy/index.json',
             ROOT / 'experiments/python-gamebub-v85/residual/data.py',
             ROOT / 'experiments/python-gamebub-v85/residual/index.json']
    paths += sorted((ROOT / 'experiments/cu66-native-v69').glob('*.hpp'))
    for area in ('experiments/python-gamebub-v88/entropy', 'experiments/python-gamebub-v85/residual'):
        frozen_index = json.loads((ROOT / area / 'index.json').read_text())
        archive_path = ROOT / area / frozen_index['data']['path']
        assert sha(archive_path) == frozen_index['data']['gzip_sha256'], 'frozen input archive pin'
        paths.append(archive_path)
    pins = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    for path in paths:
        target = out / 'sources' / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    report = dict(schema='cu66-v94-context-components-v1', status='FAIL', source_sha256=pins, commands=[],
                  physical_timing_proven=False, partial_v94=True,
                  implemented='Bounded byte-rANS, inline observed tables, 2/4 lanes, scales 8/9/10; frozen AB/BR.',
                  deferred_gates=['tANS', 'fixed trained model', 'cached model references'],
                  qualification='Software coefficient and component framing only; no FPGA/ESP32 timing or frame publication claim.',
                  collector_bound=dict(blocks=5400, coefficient_bytes=691200, candidates=9, candidate_bytes_upper_bound=6221232),
                  timing_scope='generation_ns = frozen source decode + one AB and BR whole-plane prepare + six rANS whole-plane alternatives + nine assemblies + all nine SHA256 hashes; includes discarded alternatives/candidates and AB internal parity validation. Native all-nine validation separate. Python wall includes I/O, archive, JSON and independent validation.')
    process = None
    stderr = None
    started = time.monotonic()
    previous = signal.getsignal(signal.SIGALRM)
    def expired(_signum, _frame):
        raise TimeoutError('finite EC94 campaign watchdog')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, args.timeout)
    try:
        def command(argv, name, timeout=120):
            result = subprocess.run(argv, capture_output=True, timeout=timeout)
            (out / name).write_bytes(result.stdout + result.stderr)
            report['commands'].append(dict(argv=argv, exit_code=result.returncode))
            assert result.returncode == 0, name
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler.log', 30)
        source = out / 'sources' / AREA.relative_to(ROOT)
        binary = '/build/v94-contexts-' + stamp
        test_binary = binary + '-test'
        common = ['docker', 'exec', CONTAINER, 'g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror']
        command(common + [str(source / 'collect.cpp'), '-o', binary], 'compile.log')
        command(common + [str(source / 'test_codec.cpp'), '-o', test_binary], 'compile-tests.log')
        command(['docker', 'exec', CONTAINER, test_binary, str(out / 'fixtures')], 'native-tests.json')
        command(['docker', 'cp', CONTAINER + ':' + binary, str(out / 'collector.bin')], 'copy-binary.log')
        codec = load('ec94_independent_python', ROOT / 'experiments/python-gamebub-v94/python/codec.py')
        old = load('ec94_frozen_inputs', ROOT / 'experiments/python-gamebub-v88/entropy/data.py')
        stderr = (out / 'collector.stderr').open('wb')
        argv = ['docker', 'exec', '-i', CONTAINER, 'timeout', str(args.timeout), binary]
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
        report['commands'].append(dict(argv=argv))
        def take(length):
            value = process.stdout.read(length)
            assert len(value) == length, ('native helper truncation', process.poll())
            return value
        metric_keys = ('ab_decisions', 'ab_renorm', 'literal_bits', 'ans_symbols', 'ans_renorm_bytes', 'model_tables', 'model_entries', 'ans_lanes')
        candidate_keys = ('ab_bytes', 'br_bytes', 'ans2s8_bytes', 'ans2s9_bytes', 'ans2s10_bytes', 'ans4s8_bytes', 'ans4s9_bytes', 'ans4s10_bytes', 'min_bytes')
        totals = dict.fromkeys(('old_bytes', 'raw_fallback_chunks', 'source_decode_ns', 'prepare_ns', 'assemble_ns', 'hash_ns', 'generation_ns', 'validate_ns') + metric_keys + candidate_keys, 0)
        raw_sha = hashlib.sha256()
        frames = []
        chunks = 0
        coefficients = 0
        generations = []
        frame_generations = []
        hist = [0] * 256
        with gzip.open(out / 'data.bin.gz', 'wb', compresslevel=6) as archive:
            def write(data):
                raw_sha.update(data)
                archive.write(data)
            for frame in old.iter_frames():
                meta = {key: frame[key] for key in ('cohort', 'fid', 'ordinal', 'key', 'canonical_coefficients_sha256')}
                meta['planes'] = []
                payloads = []
                frame_generation = 0
                for axis, plane in enumerate(frame['variants']['65536']):
                    observations = []
                    for chunk in plane:
                        process.stdin.write(struct.pack('<II', chunk['blocks'], len(chunk['data'])) + chunk['data'])
                        process.stdin.flush()
                        line = process.stdout.readline()
                        assert line and len(line) <= 131072, 'EC94 helper stats bound'
                        stats = json.loads(line)
                        assert stats['blocks'] == chunk['blocks'] and stats['old_bytes'] == len(chunk['data'])
                        candidates = []
                        for mask in range(9):
                            length, = struct.unpack('<I', take(4))
                            assert 48 <= length <= 48 + 128 * chunk['blocks']
                            packet = take(length)
                            observation = stats['masks'][mask]
                            assert observation['requested_selector'] == ([0, 85, 170, 170, 170, 255, 255, 255][mask] if mask < 8 else stats['masks'][8]['requested_selector']) and observation['bytes'] == length
                            assert hashlib.sha256(packet).hexdigest() == observation['sha256']
                            candidates.append(packet)
                        # Decode every distinct alternative independently. The local
                        # packet must be an exact context composition of these bytes.
                        endpoints = [codec.parse_header(packet, chunk['blocks']) for packet in candidates[:8]]
                        for packet in candidates[:8]:
                            values = codec.decode(packet, chunk['blocks'])
                            packed = struct.pack('<' + 'h' * len(values), *values)
                            assert hashlib.sha256(packed).hexdigest() == stats['coefficient_sha256'], 'independent coefficient mismatch'
                        parsed = codec.parse_header(candidates[8], chunk['blocks'])
                        if parsed[0]:
                            assert codec.decode(candidates[8], chunk['blocks']) == values
                        else:
                            selector = stats['masks'][8]['requested_selector']
                            assert parsed[1] == selector
                            assert all(parsed[3] == endpoint[3] for endpoint in endpoints)
                            methods = stats['masks'][8]['methods']
                            for context in range(4):
                                assert parsed[2][context] == endpoints[methods[context]][2][context]
                                assert len(parsed[2][context]) == min(len(endpoint[2][context]) for endpoint in endpoints)
                        if not stats['source_raw_fallback']:
                            assert stats['masks'][0]['bytes'] == len(chunk['data']) + 2
                            assert stats['masks'][1]['bytes'] == len(chunk['br88']) + 2
                        assert len(candidates[8]) <= min(map(len, candidates[:8]))
                        best = stats['masks'][8]['requested_selector']
                        hist[best] += 1
                        totals['old_bytes'] += len(chunk['data'])
                        for i, key in enumerate(candidate_keys):
                            totals[key] += len(candidates[i])
                        totals['raw_fallback_chunks'] += stats['source_raw_fallback']
                        for key in metric_keys:
                            totals[key] += sum(stats['masks'][8][key])
                        for key in ('source_decode_ns', 'prepare_ns', 'assemble_ns', 'hash_ns', 'generation_ns', 'validate_ns'):
                            totals[key] += stats[key]
                        generations.append(stats['generation_ns'])
                        frame_generation += stats['generation_ns']
                        observations.append(stats)
                        payloads.extend(candidates)
                        chunks += 1
                        coefficients += chunk['blocks'] * 64
                    meta['planes'].append(observations)
                encoded = json.dumps(meta, separators=(',', ':')).encode()
                assert len(encoded) <= 131072
                write(struct.pack('<I', len(encoded)) + encoded)
                for packet in payloads:
                    write(struct.pack('<I', len(packet)) + packet)
                frames.append({key: meta[key] for key in ('cohort', 'fid', 'ordinal', 'key', 'canonical_coefficients_sha256')})
                frame_generations.append(frame_generation)
                if len(frames) == 1 or len(frames) % 25 == 0:
                    print('EC94_PROGRESS', len(frames), chunks, 'elapsed', round(time.monotonic() - started, 1), flush=True)
        process.stdin.close()
        code = process.wait(timeout=30)
        stderr.close()
        report['native_exit_code'] = code
        assert code == 0
        assert len(frames) == 457 and chunks == 1371
        assert pins == {name: sha(ROOT / name) for name in pins}, 'executed source freshness'
        memory_lines = (out / 'collector.stderr').read_text().splitlines()
        peak = next((int(line.split()[-1]) for line in memory_lines if line.startswith('EC94_NATIVE_PEAK_RSS_KIB ')), None)
        assert peak is not None, 'native peak RSS unavailable'
        report.update(status='PASS_NATIVE_ALL_9_INDEPENDENT_PYTHON_ALL_8_COMPOSITION_LOCAL', native_sources=457, chunks=chunks,
                      actual_candidates=chunks * 9, coefficient_values=coefficients, totals=totals, min_selector_histogram=hist,
                      native_peak_rss_kib=peak, frame_generation_ns=dict(min=min(frame_generations), median=statistics.median(frame_generations),
                      p95=sorted(frame_generations)[int(.95 * (len(frame_generations) - 1))], max=max(frame_generations)),
                      data=dict(path=str((out / 'data.bin.gz').relative_to(AREA)), gzip_sha256=sha(out / 'data.bin.gz'), raw_sha256=raw_sha.hexdigest()), frames=frames)
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if stderr is not None and not stderr.closed:
            stderr.close()
        if process is not None and process.poll() is not None and report['status'] == 'FAIL':
            (out / 'helper-stdout-tail.bin').write_bytes(process.stdout.read(1048576))
        report['wall_seconds'] = time.monotonic() - started
        report['python_peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        report['local_children_peak_rss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        report['artifacts_sha256'] = {str(path.relative_to(out)): sha(path) for path in out.rglob('*') if path.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print('EC94_REPORT', out / 'results.json', report['status'], flush=True)
    (AREA / 'index.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')


if __name__ == '__main__':
    main()
