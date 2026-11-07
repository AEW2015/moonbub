#!/usr/bin/env python3
"""Finite approximate Rice-rate search for actual N2S10 EC94OPT streams.
All legal k histograms are scored, chosen streams actually encoded, and the
frozen byte anchor retained whenever it is smaller. All three packets undergo
native and independent Python validation on the full frozen 457-frame corpus.
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
AREA = ROOT / 'experiments/python-gamebub-v94/native/optimized'
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
             ROOT / 'experiments/python-gamebub-v94/native/codec.hpp',
             ROOT / 'experiments/python-gamebub-v94/native/data.py',
             ROOT / 'experiments/python-gamebub-v94/native/index.json',
             ROOT / 'experiments/python-gamebub-v92/native/codec.hpp',
             ROOT / 'experiments/python-gamebub-v85/residual/encode.hpp',
             ROOT / 'experiments/python-gamebub-v88/entropy/codec.hpp',
             ROOT / 'experiments/python-gamebub-v88/entropy/data.py',
             ROOT / 'experiments/python-gamebub-v88/entropy/index.json',
             ROOT / 'experiments/python-gamebub-v85/residual/data.py',
             ROOT / 'experiments/python-gamebub-v85/residual/index.json']
    paths += sorted((ROOT / 'experiments/cu66-native-v69').glob('*.hpp'))
    for area in ('experiments/python-gamebub-v88/entropy', 'experiments/python-gamebub-v85/residual', 'experiments/python-gamebub-v94/native'):
        frozen_index = json.loads((ROOT / area / 'index.json').read_text())
        archive_path = ROOT / area / frozen_index['data']['path']
        assert sha(archive_path) == frozen_index['data']['gzip_sha256'], 'frozen input archive pin'
        paths.append(archive_path)
    pins = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    for path in paths:
        target = out / 'sources' / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    report = dict(schema='cu66-v94-rice-rate-search-v1', status='FAIL', source_sha256=pins, commands=[],
                  physical_timing_proven=False, partial_v94=True, approximate_search=True,
                  search_rule='For each DC/run/level model evaluate every legal k (14/20/12 choices); score literal_bits + sum(count_q * log2(1024 / normalized_frequency_q)); lower k wins an exact score tie. Actual encoded stream retained only if smaller than frozen N2S10 anchor. No globally optimal bitstream promise.',
                  candidates=['frozen_ANS2S10', 'rate_optimized_ANS2S10_with_actual_anchor_guard', 'local_AB_BR_rate_optimized_ANS2S10'],
                  qualification='Software coefficient and component framing only; no FPGA/ESP32 timing or frame publication claim.',
                  collector_bound=dict(blocks=5400, coefficient_bytes=691200, candidates=3, candidate_bytes_upper_bound=2073744),
                  timing_scope='generation_ns = frozen source decode + frozen AB/BR encode (including AB internal parity and explicit BR decode validation) + frozen N2S10 anchor encode + all 110 legal-k histogram/normalization/rate evaluations + actual chosen-k encode including discarded proposals + all three assemblies and hashes. search_ns is a subtotal of prepare_ns. Separate validate_ns covers all three native decodes. Python wall includes independent all-three validation and I/O.')
    process = None
    stderr = None
    started = time.monotonic()
    previous = signal.getsignal(signal.SIGALRM)
    def expired(_signum, _frame):
        raise TimeoutError('finite EC94OPT campaign watchdog')
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
        binary = '/build/v94opt-contexts-' + stamp
        test_binary = binary + '-test'
        common = ['docker', 'exec', CONTAINER, 'g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror']
        command(common + [str(source / 'collect.cpp'), '-o', binary], 'compile.log')
        command(common + [str(source / 'test_codec.cpp'), '-o', test_binary], 'compile-tests.log')
        command(['docker', 'exec', CONTAINER, test_binary], 'native-tests.json')
        command(['docker', 'cp', CONTAINER + ':' + binary, str(out / 'collector.bin')], 'copy-binary.log')
        codec = load('ec94_independent_python', ROOT / 'experiments/python-gamebub-v94/python/codec.py')
        old = load('ec94_opt_frozen_inputs', ROOT / 'experiments/python-gamebub-v94/native/data.py')
        stderr = (out / 'collector.stderr').open('wb')
        argv = ['docker', 'exec', '-i', CONTAINER, 'timeout', str(args.timeout), binary]
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
        report['commands'].append(dict(argv=argv))
        def take(length):
            value = process.stdout.read(length)
            assert len(value) == length, ('native helper truncation', process.poll())
            return value
        metric_keys = ('ab_decisions', 'ab_renorm', 'literal_bits', 'ans_symbols', 'ans_renorm_bytes', 'model_tables', 'model_entries', 'ans_lanes')
        candidate_keys = ('anchor_bytes', 'rate_bytes', 'min_bytes')
        totals = dict.fromkeys(('old_bytes', 'old_ab_bytes', 'old_br_bytes', 'raw_fallback_chunks', 'search_ns', 'searched_ks', 'guarded_contexts', 'changed_k_contexts', 'source_decode_ns', 'prepare_ns', 'assemble_ns', 'hash_ns', 'generation_ns', 'validate_ns') + metric_keys + candidate_keys, 0)
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
                        assert line and len(line) <= 131072, 'EC94OPT helper stats bound'
                        stats = json.loads(line)
                        assert stats['blocks'] == chunk['blocks'] and stats['old_bytes'] == len(chunk['data'])
                        candidates = []
                        for mask in range(3):
                            length, = struct.unpack('<I', take(4))
                            assert 48 <= length <= 48 + 128 * chunk['blocks']
                            packet = take(length)
                            observation = stats['masks'][mask]
                            assert observation['requested_selector'] == (170 if mask < 2 else stats['masks'][2]['requested_selector']) and observation['bytes'] == length
                            assert hashlib.sha256(packet).hexdigest() == observation['sha256']
                            candidates.append(packet)
                        assert candidates[0] == chunk['ec94'][4], 'exact frozen N2S10 anchor'
                        assert stats['old_ab_bytes'] == len(chunk['data'])
                        assert stats['old_br_bytes'] == len(chunk['br88'])
                        for packet in candidates:
                            values = codec.decode(packet, chunk['blocks'])
                            packed = struct.pack('<' + 'h' * len(values), *values)
                            assert hashlib.sha256(packed).hexdigest() == stats['coefficient_sha256'], 'independent coefficient mismatch'
                        endpoints = [codec.parse_header(packet, chunk['blocks']) for packet in candidates]
                        if not endpoints[0][0]:
                            assert all(len(endpoints[1][2][c]) <= len(endpoints[0][2][c]) for c in range(4)), 'context anchor guard'
                            ab_br = [codec.parse_header(packet, chunk['blocks']) for packet in chunk['ec94'][:2]]
                            for context, method in enumerate(stats['masks'][2]['methods']):
                                expected = ab_br[method][2][context] if method < 2 else endpoints[1][2][context]
                                assert endpoints[2][2][context] == expected, 'local exact stream composition'
                        assert len(candidates[2]) <= len(candidates[1]) <= len(candidates[0]), 'actual packet no regression'
                        totals['old_ab_bytes'] += stats['old_ab_bytes']
                        totals['old_br_bytes'] += stats['old_br_bytes']
                        totals['searched_ks'] += sum(item['tried'] for context in stats['searches'] for item in context)
                        totals['guarded_contexts'] += sum(stats['anchor_used'])
                        totals['changed_k_contexts'] += sum((stats['rate_k0'][c], stats['rate_k1'][c]) != (stats['anchor_k0'][c], stats['anchor_k1'][c]) for c in range(4))
                        best = stats['masks'][2]['requested_selector']
                        hist[best] += 1
                        totals['old_bytes'] += len(chunk['data'])
                        for i, key in enumerate(candidate_keys):
                            totals[key] += len(candidates[i])
                        totals['raw_fallback_chunks'] += stats['source_raw_fallback']
                        for key in metric_keys:
                            totals[key] += sum(stats['masks'][2][key])
                        for key in ('search_ns', 'source_decode_ns', 'prepare_ns', 'assemble_ns', 'hash_ns', 'generation_ns', 'validate_ns'):
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
                    print('EC94OPT_PROGRESS', len(frames), chunks, 'elapsed', round(time.monotonic() - started, 1), flush=True)
        process.stdin.close()
        code = process.wait(timeout=30)
        stderr.close()
        report['native_exit_code'] = code
        assert code == 0
        assert len(frames) == 457 and chunks == 1371
        assert pins == {name: sha(ROOT / name) for name in pins}, 'executed source freshness'
        memory_lines = (out / 'collector.stderr').read_text().splitlines()
        peak = next((int(line.split()[-1]) for line in memory_lines if line.startswith('EC94OPT_NATIVE_PEAK_RSS_KIB ')), None)
        assert peak is not None, 'native peak RSS unavailable'
        report.update(status='PASS_NATIVE_ALL_3_INDEPENDENT_PYTHON_ALL_3', native_sources=457, chunks=chunks,
                      actual_candidates=chunks * 3, coefficient_values=coefficients, totals=totals, min_selector_histogram=hist,
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
        print('EC94OPT_REPORT', out / 'results.json', report['status'], flush=True)
    (AREA / 'index.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')


if __name__ == '__main__':
    main()
