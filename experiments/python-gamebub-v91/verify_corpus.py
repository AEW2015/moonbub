#!/usr/bin/env python3
"""Independent read-only audit of the saved V91 corpus attempt."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91'
SELECTED = {(0, 0), (0, 1), (0, 3), (3, 50)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def distribution(values):
    ordered = sorted(values)
    return dict(count=len(ordered), min=min(ordered), median=statistics.median(ordered),
                p95=ordered[min(len(ordered)-1, int(.95*len(ordered)))],
                p99=ordered[min(len(ordered)-1, int(.99*len(ordered)))],
                max=max(ordered), total=sum(ordered))


def audit():
    public = json.loads((AREA / 'corpus-results.json').read_text())
    result_path = ROOT / public['selected_report']
    result = json.loads(result_path.read_text())
    attempt = result_path.parent
    assert result['status'] == public['status'] == 'PASS'
    assert {key: value for key, value in public.items() if key != 'selected_report'} == result

    # Source pins and attempt snapshots are checked independently.
    for relative, digest in result['source_sha256'].items():
        assert sha(ROOT / relative) == digest, relative
    assert sha(attempt / 'parser.py') == result['source_sha256']['experiments/python-gamebub-v91/parser.py']
    assert sha(attempt / 'run_corpus.py') == result['source_sha256']['scripts/cu66-v91/run_corpus.py']
    for name, digest in result['artifacts_sha256'].items():
        assert sha(attempt / name) == digest, name

    old_area = ROOT / 'experiments/python-gamebub-v88/entropy'
    old = load('v91_audit_frozen_data', old_area / 'data.py')
    native = load('v91_audit_frozen_tiles', ROOT / 'experiments/python-gamebub-v82/native/data.py')
    with gzip.open(attempt / 'frames.jsonl.gz', 'rt') as stream:
        rows = [json.loads(line) for line in stream]
    assert len(rows) == 457

    identities, selected = set(), []
    chunks = coefficient_values = chunk_bytes = canonical_matches = 0
    counters = {key: 0 for key in result['counters'] if key != 'max_reservoir_bits'}
    max_reservoir = 0
    for frame, original, row in zip(old.iter_frames(), native.iter_frames(), rows, strict=True):
        identity = (frame['cohort'], frame['fid'])
        assert identity not in identities
        identities.add(identity)
        for key in ('cohort', 'fid', 'ordinal', 'key', 'canonical_sha256', 'hud_sha256', 'display_sha256'):
            assert frame[key] == original[key], (identity, key)
        assert frame['zero_mask'] == ''.join(str(value) for value in original['zero_coeff_mask'])
        assert (row['cohort'], row['fid']) == identity
        assert row['canonical_coefficients_sha256'] == frame['canonical_coefficients_sha256']
        canonical_matches += 1

        all_source_chunks = sum((list(plane) for plane in frame['variants']['65536']), [])
        assert len(row['chunks']) == len(all_source_chunks)
        row_offset = 0
        for axis, plane in enumerate(frame['variants']['65536']):
            for index, source in enumerate(plane):
                observed = row['chunks'][row_offset]
                row_offset += 1
                assert observed['axis'] == axis and observed['chunk'] == index
                assert observed['blocks'] == source['blocks']
                assert observed['bytes'] == len(source['br88'])
                assert observed['packet_sha256'] == source['br88_sha256']
                assert sha_bytes(source['br88']) == source['br88_sha256']
                assert observed['coefficient_sha256'] == source['coefficient_sha256']
                chunks += 1
                coefficient_values += source['blocks'] * 64
                chunk_bytes += len(source['br88'])
                for name, value in observed['counters'].items():
                    if name == 'max_reservoir_bits':
                        max_reservoir = max(max_reservoir, value)
                    else:
                        counters[name] += value
                if identity in SELECTED:
                    selected.append(f'c{identity[0]}-f{identity[1]}-p{axis}-{index}')

    assert len(identities) == canonical_matches == 457
    assert (chunks, coefficient_values, chunk_bytes) == (1371, 86444480, 4805106)
    assert counters == {key: value for key, value in result['counters'].items() if key != 'max_reservoir_bits'}
    assert max_reservoir == result['counters']['max_reservoir_bits']
    assert counters['logical_bits'] == 37656819 and counters['symbols'] == 11435381

    # Replay the fixed shuffle and alternation schedule, validate each paired
    # record, and reconstruct reported per-repeat host-time distributions.
    timings = json.loads((attempt / 'timings.json').read_text())
    assert len(selected) == len(set(selected)) == 12 and len(timings) == 168
    rng, cursor = random.Random(910091), 0
    sums = {'bit': [], 'word32': []}
    for repeat in range(7):
        order = selected[:]
        rng.shuffle(order)
        repeat_sums = {'bit': 0, 'word32': 0}
        for index, chunk_id in enumerate(order):
            variants = ['bit', 'word32']
            if (repeat + index) % 2:
                variants.reverse()
            for variant in variants:
                sample = timings[cursor]
                cursor += 1
                assert (sample['repeat'], sample['chunk'], sample['variant']) == (repeat, chunk_id, variant)
                assert sample['ns'] > 0
                repeat_sums[variant] += sample['ns']
        for variant in sums:
            sums[variant].append(repeat_sums[variant])
    assert cursor == len(timings)
    computed = {name: distribution(values) for name, values in sums.items()}
    benchmark = result['cpu_benchmark']
    assert computed == benchmark['total_ns_per_repeat']
    ratio = statistics.median(sums['bit']) / statistics.median(sums['word32'])
    assert ratio == benchmark['median_bit_over_word32']
    assert benchmark['chunks'] == 12 and benchmark['repetitions'] == 7
    assert benchmark['samples'] == 168 and benchmark['seed'] == 910091
    assert result['physical_30fps_proven'] is False
    assert result['complete_under10ms_proven'] is False
    assert result['fpga_cycles_measured_by_this_script'] is False

    return dict(schema='cu66-v91-independent-corpus-audit-v1', status='PASS',
                selected_report=str(result_path.relative_to(ROOT)),
                source_pins_checked=len(result['source_sha256']),
                attempt_snapshots_checked=2,
                attempt_artifacts_checked=len(result['artifacts_sha256']),
                frames=len(identities), chunks=chunks, coefficient_values=coefficient_values,
                chunk_bytes=chunk_bytes, canonical_hash_matches=canonical_matches,
                counters={**counters, 'max_reservoir_bits': max_reservoir},
                benchmark=dict(rows=len(timings), selected_chunks=len(selected), repetitions=7,
                               schedule='fixed-seed shuffle and alternating decoder order verified',
                               total_ns_per_repeat=computed, median_bit_over_word32=ratio),
                claim_scope='Exact coefficient/hash qualification and host Python timing records only; no pixel, native, hardware, or frame-rate claim.')


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


if __name__ == '__main__':
    report = audit()
    (AREA / 'corpus-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS', report['frames'], report['chunks'], report['benchmark']['rows'])
