#!/usr/bin/env python3
"""Summarize audited live canonical/write ownership, preserving evidence scope."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91l-live'
BASELINE = '0bfc018f06f1ac20342041eb8b948b6a33f83a6c'
SHARED = [
    'docs/gamebub-application-specific-codec-plan.md',
    'docs/gamebub-v91-v110-development-plan.md',
    'docs/literature-review-2026-11-06/README.md',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def freeze_manifest():
    path = AREA / 'bundle-manifest.json'
    files = [ROOT / name for name in SHARED]
    for directory in ('docs/cu66-v91l-live', 'scripts/cu66-v91l-live',
                      'fpga/experiments/cu66-v91l-live',
                      'experiments/python-gamebub-v91l-live'):
        files.extend(p for p in (ROOT / directory).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts and p != path)
    report = dict(schema='cu66-v91l-live-bundle-v1', baseline_revision=BASELINE,
                  files_sha256={str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))},
                  prior_shared_plan_sha256={name: hashlib.sha256(subprocess.check_output(
                      ['git', 'show', BASELINE + ':' + name], cwd=ROOT)).hexdigest()
                      for name in SHARED})
    path.write_text(json.dumps(report, indent=2) + '\n')
    return len(report['files_sha256'])


def main():
    audit = read(AREA / 'audit.json')
    assert audit['status'] == 'PASS_TWO_SEED_LIVE_CANONICAL_ACK_HASH_PUBLICATION_AUDIT'
    assert all(sha(ROOT / name) == value for name, value in audit['source_pins'].items())
    assert all(sha(ROOT / name) == value for name, value in audit['model_pins'].items())
    audited_reports = {item['attempt']: item for item in audit['selected_attempts']}
    assert {item['seed'] for item in audited_reports.values()} == {911901, 911902}
    write_audit = read(AREA / 'write-join-audit.json')
    assert write_audit['status'] == 'PASS_TWO_SEED_WRITE_ACK_PROTOCOL_AUDIT'
    assert all(sha(ROOT / name) == value for name, value in write_audit['source_pins'].items())
    model = read(AREA / 'model-results.json')
    assert model['status'] == 'PASS_PROTOCOL_MODEL_ONLY' and model['check_count'] == 9
    selected = {}
    for path in sorted((ROOT / 'fpga/experiments/cu66-v91l-live/integration-attempts').glob('*/results.json')):
        report = read(path)
        if report['status'] != 'PASS_LIVE_CANONICAL_ACK_HASH_PUBLICATION_WITH_SOFTWARE_HUD':
            continue
        if not all(sha(ROOT / name) == value for name, value in report['source_sha256'].items()):
            continue
        selected[report['seed']] = (path, report)
    assert set(selected) == {911901, 911902}
    fences = []
    runs = []
    totals = dict(validated_commits=0, canonical_bytes=0, hud_bytes=0, write_requests=0,
                  write_acks=0, hash_deliveries=0, hash_jobs=0)
    frozen = {}
    for seed, (path, report) in sorted(selected.items()):
        audited = audited_reports[str(path.relative_to(ROOT))]
        assert sha(path) == audited['attempt_sha256'] and audited['seed'] == seed
        assert audited['independently_checked_rtl_hash_jobs'] == 4100
        assert audited['actual_registered_qcache_bytes_captured'] == 5400
        subprocess.run(['git', 'merge-base', '--is-ancestor', BASELINE, report['source_revision']],
                       cwd=ROOT, check=True)
        assert report['live_canonical_producer'] is True
        assert report['full_rtl_hud_decoder'] is False and report['full_rtl_hud_overlay'] is False
        assert report['physical_memory_controller'] is False
        assert report['hardware_distinct_30fps_proven'] is False
        assert report['full_frame_decode_under10ms_proven'] is False
        for name, value in report['source_sha256'].items():
            assert sha(path.parent / 'sources' / name) == value
            if not name.startswith(('fpga/experiments/cu66-v91l-live/', 'scripts/cu66-v91l-live/')):
                assert hashlib.sha256(subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)).hexdigest() == value
                frozen[name] = value
        for name, value in report['inputs_sha256'].items():
            assert sha(ROOT / name) == value
            assert sha(path.parent / 'inputs' / Path(name).name) == value
        assert all(sha(path.parent / name) == value for name, value in report['artifacts_sha256'].items())
        assert all(c['exit_code'] == 0 for c in report['commands'])
        builds = [c['argv'] for c in report['commands'] if '--build' in c['argv']]
        assert len(builds) == 1
        build = builds[0]
        assert '--assert' in build and '-Wall' in build and build[build.index('-j') + 1] == '2'
        assert '-Wall -Wextra -Werror' in build[build.index('-CFLAGS') + 1]
        assert report['verdict']['cases'] == 4 and report['verdict']['source_frames'] == 2
        assert report['verdict']['directed_checks'] == 37
        assert len(report['live_rows']) == 4
        assert {(r['id'], r['profile']) for r in report['live_rows']} == {(i, p) for i in ('c0_f0', 'c0_f1') for p in (0, 1)}
        for row in report['live_rows']:
            assert row['status'] == 'PASS' and row['canonical_bytes'] == 518400 and row['hud_bytes'] == 42240
            assert row['write_requests'] == row['write_acks'] == row['hash_deliveries'] == 560640
            assert row['hash_jobs'] == 1025 and row['hash_message_bytes'] == 628815 and row['hash_blocks'] == 10298
            assert row['start_cycle'] < row['first_outer_cycle'] <= row['last_outer_cycle'] < row['commit_cycle']
            assert row['start_to_commit_cycles'] == row['commit_cycle'] - row['start_cycle']
            assert row['first_outer_to_commit_cycles'] == row['commit_cycle'] - row['first_outer_cycle']
            assert row['last_outer_to_commit_cycles'] == row['commit_cycle'] - row['last_outer_cycle']
            service_cycles = row['start_to_commit_cycles'] + row['qcache_preload_cycles']
            fences.append(dict(seed=seed, id=row['id'], profile=row['profile'],
                               start_to_commit_cycles=row['start_to_commit_cycles'],
                               first_outer_to_commit_cycles=row['first_outer_to_commit_cycles'],
                               last_outer_to_commit_cycles=row['last_outer_to_commit_cycles'],
                               qcache_preload_cycles=row['qcache_preload_cycles'],
                               standalone_serial_service_cycles=service_cycles,
                               required_clock_mhz_for_30hz_serial_service=service_cycles * 30 / 1_000_000,
                               strict_under10ms_start_fence_requires_clock_mhz_greater_than=row['start_to_commit_cycles'] / 10000))
            totals['validated_commits'] += 1
            for key in totals:
                if key != 'validated_commits':
                    totals[key] += row[key]
        runs.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), seed=seed,
                         verdict=report['verdict']))
    assert totals['validated_commits'] == 8 and totals['hash_jobs'] == 8200
    summary = dict(schema='cu66-v91l-live-qualified-v1', status='PASS_LIVE_CANONICAL_HETEROGENEOUS_PARTITION',
                   baseline_revision=BASELINE, runs=runs, totals=totals, service_fences=fences,
                   distinct_source_frames=2, native_chain=['c0/f0 key', 'c0/f1 delta'],
                   standalone_write_audit_sha256=sha(AREA / 'write-join-audit.json'),
                   independent_integration_audit_sha256=sha(AREA / 'audit.json'),
                   independent_integration_verifier_sha256=sha(AREA / 'verify_results.py'),
                   independent_write_verifier_sha256=sha(AREA / 'verify_write_join.py'),
                   python_model_sha256=sha(AREA / 'model.py'), python_model_results_sha256=sha(AREA / 'model-results.json'),
                   prior_sources_unchanged=frozen, canonical_bank_bytes=518400,
                   canonical_and_hud_bank_bytes=560640, three_bank_bytes=1681920,
                   complete_v91l_full_rtl_proven=False, full_rtl_hud_decoder=False, full_rtl_hud_overlay=False,
                   hardware_distinct_30fps_proven=False, full_frame_decode_under10ms_proven=False,
                   physical_bank_fit_proven=False, physical_memory_controller=False,
                   timing_scope='Live supported BR88 parser/entropy/inverse/reconstruction, finite independent scratch/reference/candidate services, actual candidate write ACKs, RTL C2/HUD/seal hashing and validated commit. Native C++ HUD decode, start-header preparation and fixture I/O occur before timed start. Quantizer preload is separately reported. RGB conversion, HUD overlay, shared memory arbitration, display, ESP32 transport and achieved clock are excluded.',
                   frequency_scope='Necessary clock arithmetic for the measured standalone serial service, not a routed-clock, sustained 30-Hz workload or full-frame hardware latency result. Under-10-ms frequency uses the timed start fence and excludes the separately reported preload and software work.',
                   next='Integrate/prioritize actual HUD semantic decode/overlay and shared finite memory/RGB/display/ESP32 service. Compare bounded acknowledged write coalescing against this frozen byte control before claiming performance improvement; V91m and V100–V110 physical gates remain open.')
    (AREA / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    count = freeze_manifest()
    print('V91L_LIVE_SUMMARY_PASS', totals, ';', count, 'artifact hashes')


if __name__ == '__main__':
    main()
