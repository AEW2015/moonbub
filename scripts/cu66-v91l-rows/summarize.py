#!/usr/bin/env python3
"""Freeze audited candidate-write row comparison and explicit physical limits."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91l-rows'
BASELINE = '2c1562f100a3c47f2096314eb9125144ddad12b5'
SHARED = ['docs/gamebub-application-specific-codec-plan.md',
          'docs/gamebub-v91-v110-development-plan.md',
          'docs/literature-review-2026-11-06/README.md']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def pin_report(path, report):
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASELINE, report['source_revision']], cwd=ROOT, check=True)
    assert all(sha(ROOT / name) == h for name, h in report['source_sha256'].items())
    assert all(sha(path.parent / 'sources' / name) == h for name, h in report['source_sha256'].items())
    assert all(sha(path.parent / name) == h for name, h in report['artifacts_sha256'].items())
    assert all(cmd['exit_code'] == 0 for cmd in report['commands'])
    for build in (cmd['argv'] for cmd in report['commands'] if '--build' in cmd['argv']):
        assert '--assert' in build and '-Wall' in build and build[build.index('-j') + 1] == '2'
        assert '-Wall -Wextra -Werror' in build[build.index('-CFLAGS') + 1]


def main():
    audit = read(AREA / 'audit.json')
    assert audit['status'] == 'PASS_BOTH_SEEDS'
    assert audit['verifier_sha256'] == sha(AREA / 'verify_results.py')
    standalone = read(AREA / 'row-audit.json')
    assert standalone['status'] == 'PASS' and set(standalone['audited_seeds']) == {912101, 912102}
    for item in standalone['attempts']:
        path = ROOT / item['selected_report']
        report = read(path)
        pin_report(path, report)
        assert report['status'] == 'PASS_ROW_ACK_BEFORE_ORDERED_HASH'
        assert report['verdict']['exact_bytes'] == 4096 and report['verdict']['directed_checks'] == 32
        assert item['trace_samples'] == 4096 and item['directed_checks'] == 32
    model = read(AREA / 'model-results.json')
    assert model['status'] == 'PASS' and model['address_bijection']['full_address_bijection']
    assert model['stream_counts']['total_row_requests'] == 70080
    controller = read(AREA / 'controller-cost-results.json')
    assert controller['status'] == 'PASS'
    controller_source = ROOT / controller['source']['path']
    assert sha(controller_source) == controller['source']['sha256']
    assert controller['fsm_probes']['three_open_row_word_writes']['acceptance_spacing'] == [6, 6]
    generated = read(AREA / 'generator-reproduction.json')
    assert generated['status'] == 'PASS_BYTE_IDENTICAL'
    assert all(sha(ROOT / name) == value for group in ('sources_sha256', 'outputs_sha256') for name, value in generated[group].items())
    totals = {name: dict(validated_commits=0, canonical_bytes=0, hud_bytes=0, write_requests=0,
                        write_acks=0, physical_write_bytes=0, hash_deliveries=0, hash_jobs=0,
                        x16_data_beats=0) for name in ('control', 'rows')}
    runs, comparisons, frozen = [], [], {}
    assert {r['seed'] for r in audit['results']} == {912101, 912102}
    for checked in audit['results']:
        path = ROOT / checked['selected_report']
        assert sha(path) == checked['selected_report_sha256']
        report = read(path)
        pin_report(path, report)
        assert report['status'] == 'PASS_EXACT_X16_PRICED_TILE_ROW_WRITES'
        assert report['live_canonical_producer'] is True
        for flag in ('full_rtl_hud_decoder', 'full_rtl_hud_overlay', 'physical_memory_controller',
                     'hardware_distinct_30fps_proven', 'full_frame_decode_under10ms_proven'):
            assert report[flag] is False
        for name, h in report['source_sha256'].items():
            if not name.startswith(('fpga/experiments/cu66-v91l-rows/', 'scripts/cu66-v91l-rows/')):
                assert hashlib.sha256(subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)).hexdigest() == h
                frozen[name] = h
        for name, h in report['inputs_sha256'].items():
            assert sha(ROOT / name) == h and sha(path.parent / 'inputs' / Path(name).name) == h
        builds = [c['argv'] for c in report['commands'] if '--build' in c['argv']]
        assert len(builds) == 2
        assert {a for build in builds for a in build if a.startswith('-GROW_WRITES=')} == {"-GROW_WRITES=1'b0", "-GROW_WRITES=1'b1"}
        assert '5.020' in (path.parent / 'tool-version.log').read_text()
        assert '13.3.0' in (path.parent / 'compiler-version.log').read_text()
        modes = {mode['name']: mode for mode in report['modes']}
        assert set(modes) == {'control', 'rows'}
        pairs = {}
        for name, mode in modes.items():
            width = 1 if name == 'control' else 8
            assert mode['status'] == 'PASS_EXACT_LIVE_PATH' and mode['write_batch_bytes'] == width
            assert mode['verdict']['cases'] == 4 and mode['verdict']['directed_checks'] == 39
            assert checked['mode_results'][name]['rtl_sha_jobs_independently_verified'] == 4100
            assert {(r['id'], r['profile']) for r in mode['live_rows']} == {(f, p) for f in ('c0_f0', 'c0_f1') for p in (0, 1)}
            for row in mode['live_rows']:
                assert row['status'] == 'PASS'
                assert row['canonical_bytes'] == 518400 and row['hud_bytes'] == 42240
                assert row['hash_jobs'] == 1025 and row['hash_message_bytes'] == 628815 and row['hash_blocks'] == 10298
                assert row['physical_write_bytes'] == row['hash_deliveries'] == 560640
                assert row['write_requests'] == row['write_acks'] == 560640 // width
                assert row['x16_data_beats'] == (560640 if width == 1 else 280320)
                overhead = row['candidate_response_overhead_cycles']
                requests = row['write_requests']
                if row['profile'] == 0:
                    assert overhead == requests
                else:
                    assert 2 * requests <= overhead <= 7 * requests
                assert row['start_to_commit_cycles'] == row['commit_cycle'] - row['start_cycle']
                assert row['first_outer_to_commit_cycles'] == row['commit_cycle'] - row['first_outer_cycle']
                assert row['last_outer_to_commit_cycles'] == row['commit_cycle'] - row['last_outer_cycle']
                totals[name]['validated_commits'] += 1
                for key in totals[name]:
                    if key != 'validated_commits':
                        totals[name][key] += row[key]
                pairs.setdefault((row['id'], row['profile']), {})[name] = row
        for (fid, profile), pair in sorted(pairs.items()):
            control, rows = pair['control'], pair['rows']
            assert control['root'] == rows['root'] and control['hud_sha256'] == rows['hud_sha256'] and control['seal'] == rows['seal']
            old, new = control['start_to_commit_cycles'], rows['start_to_commit_cycles']
            assert new < old, 'Do not promote a performance regression'
            comparisons.append(dict(seed=report['seed'], id=fid, profile=profile,
                                    control_cycles=old, row_cycles=new, fewer_cycles_percent=(old-new)*100/old,
                                    control_last_outer_to_commit=control['last_outer_to_commit_cycles'],
                                    rows_last_outer_to_commit=rows['last_outer_to_commit_cycles'],
                                    separately_charged_qcache_preload_cycles=rows['qcache_preload_cycles']))
        runs.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), seed=report['seed']))
    assert all(v['validated_commits'] == 8 and v['hash_jobs'] == 8200 for v in totals.values())
    reduction = {str(p): dict(min=min(c['fewer_cycles_percent'] for c in comparisons if c['profile'] == p),
                             max=max(c['fewer_cycles_percent'] for c in comparisons if c['profile'] == p)) for p in (0, 1)}
    result = dict(schema='cu66-v91l-tile-row-qualified-v1', status='PASS_EXACT_DECLARED_SERVICE_ROW_COMPARISON',
                  baseline_revision=BASELINE, runs=runs, totals_by_mode=totals, comparisons=comparisons,
                  fewer_cycles_percent_by_profile=reduction, source_frames=['c0_f0', 'c0_f1'],
                  prior_sources_unchanged=frozen, payload_bytes_control=1, payload_bytes_rows=8, extra_payload_bytes=7,
                  logical_row_requests_per_frame=70080, logical_byte_requests_per_frame=560640,
                  request_reduction_percent=87.5, candidate_payload_beat_reduction_percent=50,
                  complete_v91l_full_rtl_proven=False, physical_memory_controller=False,
                  hardware_distinct_30fps_proven=False, full_frame_decode_under10ms_proven=False,
                  candidate_x16_pricing_only=True, shared_physical_memory_service_proven=False,
                  timing_scope='Live supported BR88 reconstruction plus candidate x16 payload/response pricing and real RTL C2/HUD/seal/publication. Scratch/reference retain separate frozen logical service; no shared bandwidth. C++ HUD/header work precedes start, preload is separate, RGB/overlay/display/ESP32/physical clock are excluded.',
                  controller_scope='Existing16-bit controller performs single-word writes. Row-to-word bridge, per-command waits, refresh/row misses, byte baseline mask/RMW policy, and shared arbitration are not implemented here. Controller-cost Python model is service-work arithmetic only, not integrated RTL latency.',
                  integrity={name: sha(AREA / name) for name in ('audit.json', 'verify_results.py', 'row-audit.json',
                             'verify_rows.py', 'model.py', 'model-results.json', 'controller_cost_model.py', 'controller-cost-results.json', 'generator-reproduction.json')},
                  next='Implement and test row-to-word bridge against actual controller, price all x16 actors and shared service; then evaluate bounded two-row overlap and complete HUD/overlay/transport integration before V91m and physical V100–V110 goals.')
    (AREA / 'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    manifest_path = AREA / 'bundle-manifest.json'
    paths = [ROOT / name for name in SHARED]
    for directory in ('docs/cu66-v91l-rows', 'scripts/cu66-v91l-rows', 'fpga/experiments/cu66-v91l-rows', 'experiments/python-gamebub-v91l-rows'):
        paths.extend(p for p in (ROOT / directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p != manifest_path)
    manifest = dict(schema='cu66-v91l-rows-bundle-v1', baseline_revision=BASELINE,
                    files_sha256={str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))})
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    print('ROW_COMPARISON_SUMMARY_PASS', reduction, ';', len(manifest['files_sha256']), 'artifact hashes')


if __name__ == '__main__':
    main()
