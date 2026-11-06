#!/usr/bin/env python3
"""Freeze independently audited row-to-word controller simulation and its limits."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91l-sdram'
FPGA = ROOT / 'fpga/experiments/cu66-v91l-sdram'
BASELINE = '67744b3340e92ab2b188143fe3727107a7647d69'
SHARED = ['docs/gamebub-application-specific-codec-plan.md',
          'docs/gamebub-v91-v110-development-plan.md',
          'docs/literature-review-2026-11-06/README.md']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def pins(path, report):
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASELINE, report['source_revision']], cwd=ROOT, check=True)
    for name, h in report['source_sha256'].items():
        assert sha(ROOT / name) == h, name
        assert sha(path.parent / 'sources' / name) == h, name
    assert all(sha(path.parent / name) == h for name, h in report['artifacts_sha256'].items())
    assert all(command['exit_code'] == 0 for command in report['commands'])


def layout_address(name, logical):
    if name == 'raster':
        return logical
    if logical >= 518400:
        return (522240 if name == 'micro16x8' else 518400) + logical - 518400
    plane = 0 if logical < 345600 else 1 if logical < 432000 else 2
    base = (0, 345600, 432000)[plane]
    width = (720, 360, 360)[plane]
    y, x = divmod(logical - base, width)
    if name == 'tile8x8':
        return base + ((y // 8) * (width // 8) + x // 8) * 64 + (y % 8) * 8 + x % 8
    assert name == 'micro16x8'
    return (0, 345600, 433920)[plane] + ((y // 8) * ((width + 15) // 16) + x // 16) * 128 + (y % 8) * 16 + x % 16


def main():
    audit = read(AREA / 'audit.json')
    assert audit['status'] == 'PASS_TWO_SEED_REAL_CONTROLLER_ROW_PIN_AUDIT'
    assert audit['verifier_sha256'] == sha(AREA / 'verify_results.py')
    assert len(audit['checker_negative_controls']) == 6
    assert all(c['rejected'] for c in audit['checker_negative_controls'])
    flags = audit['assertions']
    assert flags['native_candidate_traffic_replay_qualified'] and flags['strict_assert_and_warning_flags']
    for key in ('byte_rmw_implemented', 'byte_rmw_qualified', 'shared_service_complete',
                'current_live_codec_controller_join_qualified', 'physical_byte_vs_row_comparison_qualified',
                'hardware_or_frequency_qualified'):
        assert flags[key] is False
    model = read(AREA / 'model-results.json')
    assert model['status'] == 'PASS'
    original = ROOT / model['source']['path']
    assert sha(original) == model['source']['sha256'] == audit['frozen_controller_sha256']
    assert hashlib.sha256(subprocess.check_output(['git', 'show', BASELINE + ':' + str(original.relative_to(ROOT))], cwd=ROOT)).hexdigest() == sha(original)
    derivation = read(FPGA / 'controller-derivation.json')
    assert len(derivation['changes']) == 4
    text = original.read_text()
    for change in derivation['changes']:
        assert text.count(change['before']) == 1
        text = text.replace(change['before'], change['after'])
    assert text.encode() == (ROOT / derivation['derived']).read_bytes()
    assert sha(ROOT / derivation['derived']) == derivation['derived_sha256']
    traffic = read(AREA / 'traffic-results.json')
    assert traffic['status'] == 'PASS_SOURCE_BACKED_NATIVE_TRAFFIC'
    assert traffic['generator_sha256'] == sha(AREA / 'traffic.py')
    assert traffic['source_report_sha256'] == sha(ROOT / traffic['source_report'])
    assert traffic['fixture']['gzip_sha256'] == sha(ROOT / traffic['fixture']['path'])
    assert traffic['fixture']['rows'] == 140160
    expected_frames = {r['id']: r for r in traffic['frames']}
    assert set(expected_frames) == {'c0_f0', 'c0_f1'}
    runs, fences = [], []
    totals = dict(native_frame_replays=0, native_rows=0, native_pin_word_writes=0,
                  native_bytes=0, all_pin_word_writes=0, checked_read_words=0, check_entries=0)
    assert {r['seed'] for r in audit['attempts']} == {912301, 912302}
    for checked in audit['attempts']:
        path = ROOT / checked['selected_report']
        assert sha(path) == checked['report_sha256']
        report = read(path)
        pins(path, report)
        assert report['status'] == 'PASS_REAL_CONTROLLER_ROW_WRITES_AND_READ_PROBES'
        assert report['native_replay'] is True
        for flag in ('byte_rmw_supported', 'physical_hardware_tested', 'full_live_codec_join',
                     'hardware_distinct_30fps_proven', 'full_frame_decode_under10ms_proven'):
            assert report[flag] is False
        for name, value in report['inputs_sha256'].items():
            assert sha(ROOT / name) == value
            assert sha(path.parent / 'inputs' / Path(name).name) == value
        builds = [c['argv'] for c in report['commands'] if '--binary' in c['argv']]
        assert len(builds) == 2
        for argv in builds:
            assert all(flag in argv for flag in ('--timing', '--assert', '-Wall', '-DSIMULATION'))
            assert argv[argv.index('-j') + 1] == '2'
            assert '-std=c++20' in argv[argv.index('-CFLAGS') + 1]
            assert '-Wall -Wextra -Werror' in argv[argv.index('-CFLAGS') + 1]
        assert '5.020' in (path.parent / 'tool-version.log').read_text()
        assert '13.3.0' in (path.parent / 'compiler-version.log').read_text()
        modes = {int(m['t_ac_ns']): m for m in checked['modes']}
        assert set(modes) == {2, 7}
        for tac, mode in modes.items():
            verdict = mode['verdict']
            native_rows = 140160 if tac == 2 else 0
            assert mode['native_rows'] == verdict['native_rows'] == native_rows
            assert verdict['status'] == 'TEST_PASS' and verdict['seed'] == report['seed']
            assert verdict['checks'] == (21 if tac == 2 else 20)
            assert verdict['rows'] == verdict['logical_responses'] == native_rows + 89
            assert verdict['word_writes'] == native_rows * 4 + 352
            assert verdict['read_words'] == 32
            assert verdict['controller_accepts'] == verdict['controller_retires'] == verdict['word_writes'] + 4
            totals['all_pin_word_writes'] += verdict['word_writes']
            totals['checked_read_words'] += verdict['read_words']
            totals['check_entries'] += verdict['checks']
            assert len(mode['native_frames']) == (2 if tac == 2 else 0)
            for frame in mode['native_frames']:
                expected = expected_frames[frame['id']]
                assert frame['sha256'] == frame['expected_sha256'] == expected['accepted_bank_sha256']
                assert frame['complete_bank_matches_accepted_golden']
                assert frame['rows'] == 70080 and frame['physical_writes'] == 280320 and frame['bytes'] == 560640
                assert frame['bank'] == expected['bank'] and frame['epoch'] == expected['epoch']
                cycles = frame['last_matching_response_cycle'] - frame['first_accepted_row_cycle']
                ps = frame['last_matching_response_time_ps'] - frame['first_accepted_row_time_ps']
                assert ps == cycles * 10000
                fences.append(dict(seed=report['seed'], id=frame['id'], bank=frame['bank'],
                                   first_accepted_cycle=frame['first_accepted_row_cycle'],
                                   last_matching_response_cycle=frame['last_matching_response_cycle'],
                                   request_to_response_cycles=cycles, simulated_elapsed_ps=ps,
                                   simulated_elapsed_ms=ps / 1_000_000_000,
                                   bank_sha256=frame['sha256']))
                totals['native_frame_replays'] += 1
                totals['native_rows'] += frame['rows']
                totals['native_pin_word_writes'] += frame['physical_writes']
                totals['native_bytes'] += frame['bytes']
        runs.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), seed=report['seed']))
    assert totals['native_frame_replays'] == 4 and totals['native_rows'] == 280320
    assert totals['native_pin_word_writes'] == 1121280 and totals['native_bytes'] == 2242560
    eq_path = FPGA / 'equivalence-results.json'
    eq_alias = read(eq_path)
    # The helper's latest alias does not carry a selected_report; find the exact
    # successful, current-source retained report instead.
    equivalences = []
    for path in sorted((FPGA / 'equivalence-attempts').glob('*/results.json')):
        report = read(path)
        if report['status'] == 'PASS_ORIGINAL_STRICT_OBSERVABLE_TRACE_IDENTITY' and all(sha(ROOT / n) == h for n, h in report['source_sha256'].items()):
            equivalences.append((path, report))
    assert equivalences and eq_alias['status'] == 'PASS_ORIGINAL_STRICT_OBSERVABLE_TRACE_IDENTITY'
    eq_path, eq = equivalences[-1]
    pins(eq_path, eq)
    original_trace = [json.loads(line) for line in (eq_path.parent / 'simulation-original.jsonl').read_text().splitlines() if line.startswith('{')]
    strict_trace = [json.loads(line) for line in (eq_path.parent / 'simulation-strict.jsonl').read_text().splitlines() if line.startswith('{')]
    assert original_trace == strict_trace and len(original_trace) == eq['event_count']
    assert eq['verdict']['checks'] == 20 and eq['verdict']['native_rows'] == 0
    result = dict(schema='cu66-v91l-real-controller-qualified-v1', status='PASS_ROW_CONTROLLER_PIN_REPLAY',
                  baseline_revision=BASELINE, runs=runs, totals=totals, native_fences=fences,
                  unit_t_ac_ns=[2, 7], native_replay_t_ac_ns=[2], nominal_clock_period_ns=10,
                  native_source_frames=2, native_validated_commits_in_this_gate=0,
                  complete_v91l_full_rtl_proven=False, byte_rmw_supported=False,
                  current_live_codec_controller_join=False, shared_service_complete=False,
                  physical_hardware_tested=False, hardware_distinct_30fps_proven=False,
                  full_frame_decode_under10ms_proven=False, physical_byte_vs_row_comparison=False,
                  bank_mapping='word=(candidate_bank<<22)|(byte_offset>>1)|word_index; bank0..2; byteoffset<560640',
                  candidate_data_bytes=1681920, reserved_aperture_bytes=25165824,
                  original_controller_sha256=sha(original), strict_controller_sha256=derivation['derived_sha256'],
                  bounded_equivalence=dict(path=str(eq_path.relative_to(ROOT)), sha256=sha(eq_path), events=eq['event_count']),
                  integrity={name: sha(AREA / name) for name in ('audit.json', 'verify_results.py', 'model.py', 'model-results.json', 'traffic.py', 'traffic-results.json')},
                  timing_scope='Actual controller+bridge with timed functional SDRAM pins and source-backed write traffic replay. First accepted row to last matching response; includes bridge/client scheduling, row commands and refresh. Excludes live codec/hash/publication, CPU HUD, source transport, scratch/reference/conversion/display traffic and physical board/PVT validation.',
                  next='Model physical layout together with read/display traffic; qualify faster legal word-write or burst scheduling. Then join live codec and all clients on one shared finite controller; byte RMW and hardware timing remain open.')
    layout_path = AREA / 'layout-results.json'
    if layout_path.exists():
        layout = read(layout_path)
        assert layout['status'] == 'PASS_BOUNDED_LAYOUT_BIJECTION_AND_LOCALITY'
        assert layout['inputs']['fixture_sha256'] == traffic['fixture']['gzip_sha256']
        native_raw = gzip.decompress((ROOT / traffic['fixture']['path']).read_bytes())
        assert hashlib.sha256(native_raw).hexdigest() == traffic['fixture']['raw_sha256']
        native_rows = native_raw.splitlines()
        assert len(native_rows) == 140160
        locality = {}
        for name, item in layout['layouts'].items():
            activations = 0
            for frame in item['per_frame']:
                expected = expected_frames[frame['frame_id']]
                assert frame['source_frame_sha256'] == frame['inverse_reconstruction_sha256'] == expected['accepted_bank_sha256']
                assert frame['reconstruction_exact'] and frame['all_logical_bytes_injective']
                receipt = frame['word_address_trace']
                packed = ROOT / receipt['path']
                assert sha(packed) == receipt['gzip_sha256']
                raw = gzip.decompress(packed.read_bytes())
                assert hashlib.sha256(raw).hexdigest() == receipt['raw_sha256']
                records = raw.splitlines()
                assert len(records) == receipt['rows'] == 70080
                seen = set()
                previous_row = None
                count = 0
                for index, record in enumerate(records):
                    assert len(record) == 34
                    logical, physical = int(record[:5], 16), int(record[5:10], 16)
                    words = [int(record[10 + i * 6:16 + i * 6], 16) for i in range(4)]
                    native = int(native_rows[expected['first_row'] + index], 16)
                    assert logical == ((native >> 64) & 0xfffff)
                    assert ((native >> 84) & 3) == expected['bank']
                    assert physical == layout_address(name, logical) and physical % 8 == 0
                    assert physical + 8 <= frame['allocated_physical_extent_bytes']
                    assert physical not in seen
                    seen.add(physical)
                    assert words == [(expected['bank'] << 22) | (physical >> 1) | i for i in range(4)]
                    row = words[0] >> 9
                    assert all((w >> 9) == row for w in words)
                    if row != previous_row:
                        count += 1
                        previous_row = row
                assert len(seen) == 70080 and count == frame['ideal_activate_count_closed_first_row']
                assert frame['padding_bytes'] == (3840 if name == 'micro16x8' else 0)
                activations += count
            assert activations == item['two_frame_ideal_activates']
            locality[name] = dict(ideal_row_activations=activations,
                                  allocated_bank_bytes=item['per_frame'][0]['allocated_physical_extent_bytes'],
                                  padding_bytes=item['per_frame'][0]['padding_bytes'])
        assert {name: r['ideal_row_activations'] for name, r in locality.items()} == {'raster': 82478, 'tile8x8': 1096, 'micro16x8': 1104}
        result['layout_proposal_sha256'] = sha(layout_path)
        result['layout_study_source_sha256'] = sha(AREA / 'layout_study.py')
        result['layout_proposal_implemented_in_rtl'] = False
        result['layout_proposal_root_checked_requests'] = 420480
        result['write_only_ideal_layout_locality'] = locality
    (AREA / 'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    manifest_path = AREA / 'bundle-manifest.json'
    paths = [ROOT / name for name in SHARED]
    for directory in ('docs/cu66-v91l-sdram', 'scripts/cu66-v91l-sdram', 'fpga/experiments/cu66-v91l-sdram', 'experiments/python-gamebub-v91l-sdram'):
        paths.extend(p for p in (ROOT / directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p != manifest_path)
    manifest_path.write_text(json.dumps(dict(schema='cu66-v91l-sdram-bundle-v1', baseline_revision=BASELINE,
                                            files_sha256={str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))}), indent=2)+'\n')
    print('SDRAM_PIN_SUMMARY_PASS', totals, ';', len(set(paths)), 'artifact hashes')


if __name__ == '__main__':
    main()
