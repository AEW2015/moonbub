#!/usr/bin/env python3
"""Independently audit retained V91l write-ACK/hash-join runs."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91l-live'
OUT = Path(__file__).with_name('write-join-audit.json')
SEEDS = (912001, 912002)
SOURCES = (
    'fpga/experiments/cu66-v91l-live/cu66_write_hash_join_v91l.sv',
    'fpga/experiments/cu66-v91l-live/tb_write_join.cpp',
    'scripts/cu66-v91l-live/run_write_join.py',
)
DIRECTED = {
    'fast_exact_ack_before_hash_and_held_payload',
    'slow_exact_ack_before_hash_and_held_payload',
    'cancel_unaccepted_offer', 'cancel_pending_ack_drain',
    'cancel_matching_ack_same_edge', 'cancel_held_hash_output',
    'reset_unaccepted_offer', 'reset_pending_ack_drain',
    'reset_matching_ack_same_edge', 'reset_held_hash_output',
    'wrong_epoch_ack_retains_lease', 'wrong_token_ack_retains_lease',
    'wrong_bank_ack_retains_lease', 'wrong_addr_ack_retains_lease',
    'matching_error_ack_retires_without_hash', 'clean_retry_after_fault',
}


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(path.read_bytes())


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_source_contract(source_path):
    src = source_path.read_text()
    # Source-level safety assertions establish ACK-before-output and owner hold.
    required = (
        'Payload delivered()const', 'd.out_epoch', 'd.out_data', 'd.out_hud',
        'd.out_fid', 'd.out_plane', 'd.out_tile', 'd.out_index', 'd.out_last',
        'payload()==expected', 'delivered()==p',
        'response(p);need(d.out_valid', 'd.count_outputs==0',
        'count_wrong_acks==1', 'd.physical_pending',
    )
    missing = [needle for needle in required if needle not in src]
    require(not missing, f'TB source misses required output/ACK assertions: {missing}')
    return {"required_source_checks": list(required), "missing": []}


def expected_sample(profile, ordinal):
    return {
        'type': 'sample', 'profile': profile, 'ordinal': ordinal,
        'epoch': profile + 2, 'token': profile * 1000 + ordinal + 1,
        'bank': 2, 'addr': ordinal * 7, 'data': (ordinal * 73 + 19) & 255,
        'hud': ordinal & 1, 'fid': 31, 'plane': ordinal % 3,
        'tile': ordinal % 1350, 'index': ordinal % 64,
        'last': int(ordinal == 999),
    }


def audit_attempt(report_path):
    result = json.loads(report_path.read_text())
    seed = result.get('seed')
    require(seed in SEEDS, f'unexpected seed in {report_path}: {seed}')
    require(result.get('schema') == 'cu66-v91l-live-write-join-v1', 'wrong report schema')
    require(result.get('status') == 'PASS_WRITE_ACK_BEFORE_HASH', f'seed {seed} failed')
    require(result.get('full_frame_integration_proven') is False, 'scope overstated full integration')
    require(result.get('hardware_distinct_30fps_proven') is False, 'scope overstated 30 fps')
    require(result.get('full_frame_decode_under10ms_proven') is False, 'scope overstated latency')
    attempt = report_path.parent

    snapshots = {}
    for rel in SOURCES:
        snap = attempt / 'sources' / rel
        require(snap.is_file(), f'missing pinned source snapshot: {rel}')
        digest = sha_file(snap)
        require(result.get('source_sha256', {}).get(rel) == digest,
                f'report source pin mismatch for {rel}')
        snapshots[rel] = digest
    tb_path = attempt / 'sources' / SOURCES[1]
    source_checks = check_source_contract(tb_path)

    commands = result.get('commands', [])
    require(commands and all(c.get('exit_code') == 0 for c in commands), 'failed command')
    joined = [str(x) for c in commands for x in c.get('argv', [])]
    require('--assert' in joined and '-Wall' in joined, 'missing strict Verilator flags')
    cflags = next((joined[i + 1] for i, x in enumerate(joined[:-1]) if x == '-CFLAGS'), '')
    for flag in ('-std=c++17', '-Wall', '-Wextra', '-Werror'):
        require(flag in cflags, f'missing strict C++ flag {flag}')
    require('verilator' in joined and '--cc' in joined and '--exe' in joined, 'wrong build command')

    verdict = result.get('verdict', {})
    require(verdict.get('status') == 'TEST_PASS' and verdict.get('seed') == seed,
            f'seed {seed} lacks passing verdict')
    require(verdict.get('directed_checks') == 16 and verdict.get('exact_bytes') == 2000,
            f'seed {seed} wrong directed or exact-byte count')
    trace_meta = result.get('simulation_trace', {})
    trace_path = attempt / trace_meta.get('path', '')
    require(trace_path.is_file(), 'missing retained simulation trace')
    packed = trace_path.read_bytes()
    raw = gzip.decompress(packed)
    require(sha_bytes(packed) == trace_meta.get('gzip_sha256'), 'compressed trace hash mismatch')
    require(sha_bytes(raw) == trace_meta.get('raw_sha256'), 'raw trace hash mismatch')
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    require(len(rows) == trace_meta.get('rows'), 'trace row count mismatch')
    samples = [r for r in rows if r.get('type') == 'sample']
    require(len(samples) == 2000, f'seed {seed} must record 2000 samples')
    for profile in (0, 1):
        cohort = [r for r in samples if r.get('profile') == profile]
        require(len(cohort) == 1000, f'seed {seed} profile {profile} not 1000 bytes')
        for ordinal, actual in enumerate(cohort):
            require(actual == expected_sample(profile, ordinal),
                    f'seed {seed} sample mismatch profile={profile} ordinal={ordinal}: {actual}')
    directed = [r.get('name') for r in rows if r.get('type') == 'directed' and r.get('status') == 'PASS']
    require(len(directed) == 16 and set(directed) == DIRECTED,
            f'seed {seed} directed case set mismatch: {directed}')
    cases = [r for r in rows if r.get('type') == 'case']
    require(len(cases) == 2 and all(c.get('bytes') == 1000 and c.get('status') == 'PASS' for c in cases),
            f'seed {seed} fast/slow cases malformed')
    require(result.get('artifacts_sha256'), 'missing artifact hash inventory')
    for rel, digest in result['artifacts_sha256'].items():
        artifact = attempt / rel
        require(artifact.is_file() and sha_file(artifact) == digest,
                f'artifact hash mismatch: {rel}')
    return {
        'seed': seed,
        'attempt': str(report_path.relative_to(ROOT)),
        'report_sha256': sha_file(report_path),
        'source_sha256': snapshots,
        'trace_sha256': {'gzip': sha_bytes(packed), 'raw': sha_bytes(raw)},
        'exact_generated_bytes': len(samples),
        'profiles': [{'profile': p, 'bytes': 1000} for p in (0, 1)],
        'directed_checks': directed,
        'strict_flags': ['--assert', '-Wall', '-std=c++17', '-Wextra', '-Werror'],
        'source_checks': source_checks,
        'limitations': result['scope'],
    }


def main():
    reports = sorted((AREA / 'write-attempts').glob('*/results.json'))
    require(reports, 'no retained write-join attempts')
    latest = {}
    for path in reports:
        try:
            row = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if row.get('seed') in SEEDS:
            latest[row['seed']] = path
    require(set(latest) == set(SEEDS), f'missing required seeds; found {sorted(latest)}')
    # Latest chronological report per required seed must pass; stale passes do not mask failures.
    audit = [audit_attempt(latest[seed]) for seed in SEEDS]
    same_sources = all(audit[0]['source_sha256'][p] == audit[1]['source_sha256'][p] for p in SOURCES)
    require(same_sources, 'the two seeds did not use byte-identical source snapshots')
    local_sources = {rel: sha_file(ROOT / rel) for rel in SOURCES}
    require(local_sources == audit[0]['source_sha256'], 'current sources differ from audited snapshots')
    output = {
        'schema': 'cu66-v91l-live-write-join-independent-audit-v1',
        'status': 'PASS_TWO_SEED_WRITE_ACK_PROTOCOL_AUDIT',
        'seeds': audit,
        'source_pins': local_sources,
        'assertions': {
            'seeds': list(SEEDS), 'directed_checks_per_seed': 16,
            'exact_generated_bytes_per_seed': 2000,
            'samples_independently_regenerated': True,
            'samples_are_actual_hash_outputs_after_good_ack': True,
            'no_output_without_good_ack_source_checked': True,
            'same_source_bytes_for_both_seeds': same_sources,
        },
        'scope': 'Standalone adapter simulation and independent trace/source audit; no full-frame RTL integration, physical SDRAM qualification, FPS, or latency claim.',
    }
    OUT.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({'status': output['status'], 'seeds': [x['seed'] for x in audit],
                      'audit': str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == '__main__':
    main()
