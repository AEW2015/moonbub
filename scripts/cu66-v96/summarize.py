#!/usr/bin/env python3
"""Bind V96 software/standalone-RTL evidence without claiming full-path closure."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v96'
HISTORICAL_PLAN = 'docs/gamebub-v91-v110-development-plan.md'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    pins, requirements = {}, []
    def read(path):
        path = ROOT / path
        pins[str(path.relative_to(ROOT))] = sha(path)
        return json.loads(path.read_text())
    def qualify(pointer_path):
        pointer = read(pointer_path)
        selected = pointer.get('selected_report', pointer_path)
        report = read(selected)
        if 'report_sha256' in pointer:
            assert sha(ROOT / selected) == pointer['report_sha256']
        assert report['status'].startswith('PASS'), (selected, report['status'])
        for key in ('source_sha256', 'input_sha256', 'inputs_sha256'):
            for name, expected in report.get(key, {}).items():
                if name == HISTORICAL_PLAN:
                    snapshot = (ROOT / selected).parent / 'sources' / name
                    assert sha(snapshot) == expected, ('historical requirement snapshot', name)
                    requirements.append(dict(path=name, snapshot=str(snapshot.relative_to(ROOT)),
                                             sha256=expected, current_plan_status_may_be_updated=True))
                else:
                    assert sha(ROOT / name) == expected, ('stale source/input', selected, name)
        for key in ('artifact_sha256', 'artifacts_sha256'):
            for name, expected in report.get(key, {}).items():
                assert sha((ROOT / selected).parent / name) == expected, ('changed artifact', selected, name)
        return report, (ROOT / selected).parent
    inventory, inv_attempt = qualify('experiments/python-gamebub-v96/inventory/index.json')
    audit, _ = qualify('experiments/python-gamebub-v96/inventory-audit/results.json')
    model, _ = qualify('experiments/python-gamebub-v96/service-model/results.json')
    rtl, rtl_attempt = qualify('fpga/experiments/cu66-v96-materialize/results.json')
    assert inventory['frames'] == audit['frames'] == model['frames'] == 457
    assert audit['streams'] == 1371 and audit['independently_checked_tiles'] == 11105100
    assert len(rtl['modes']) == 3 and not rtl['full_path_integrated']
    assert model['lifecycle_check_count'] == 34
    for profile, total in inventory['totals'].items():
        independent = audit['totals'][profile]
        for key in ('stream_bytes', 'header_bytes', 'descriptor_bytes', 'fallback_bytes', 'FALLBACK', 'COPY_REF', 'CONST128', 'CROSSCOPY'):
            assert total[key] == independent.get(key, 0), (profile, key)
        assert total['materialization_destination_write_bytes'] == 457 * 518400
        assert total['retained_predictor_read_bytes'] == 218318208
    max_frame = {p: 0 for p in inventory['profiles']}
    profile_frames = {p: 0 for p in inventory['profiles']}
    with gzip.open(inv_attempt / 'frames.jsonl.gz', 'rt') as stream:
        rows = 0
        for line in stream:
            row = json.loads(line)
            rows += 1
            for profile, stats in row['profiles'].items():
                max_frame[profile] = max(max_frame[profile], stats['stream_bytes'])
                profile_frames[profile] += int(stats['ops']['CROSSCOPY'] > 0)
    assert rows == 457
    mode_results = []
    for mode in rtl['modes']:
        assert mode['status'] == 'PASS' and mode['verdict']['status'] == 'TEST_PASS'
        with gzip.open(rtl_attempt / mode['event_log'], 'rt') as stream:
            events = [json.loads(line) for line in stream if line.startswith('{')]
        checks = [event for event in events if event.get('type') == 'check']
        verdicts = [event for event in events if event.get('type') == 'verdict']
        assert len(verdicts) == 1 and verdicts[0] == mode['verdict']
        assert len(checks) == mode['verdict']['checks'] and all(event['status'] == 'PASS' for event in checks)
        assert mode['verdict']['pin_reads'] == mode['verdict']['read_lines'] * 8
        assert mode['verdict']['pin_writes'] == mode['verdict']['write_rows'] * 4 + 192
        for metric in mode['metrics']:
            assert metric['descriptors'] == 1 and metric['descriptor_interface_bits'] == 204
            assert metric['write_rows'] == 8
            if metric['name'] == 'copy':
                assert metric['read_lines'] == 4 and metric['generator_cycles'] == 0
            elif metric['name'] == 'const128':
                assert metric['read_lines'] == 0 and metric['generator_cycles'] == 64 // mode['generator_lanes']
            else:
                assert metric['name'] == 'literal' and metric['literal_samples'] == 64 and metric['read_lines'] == 0
        mode_results.append(dict(mode=mode['mode'], t_ac_ns=mode['t_ac_ns'],
                                 generator_lanes=mode['generator_lanes'],
                                 verdict=mode['verdict'], metrics=mode['metrics']))
    profile_results = []
    for profile, total in inventory['totals'].items():
        cross = total['CROSSCOPY']
        profile_results.append(dict(profile=profile, crosscopies=cross,
                                    original_active_residual_blocks=1350695,
                                    bypassed_residual_fraction_percent=100 * cross / 1350695,
                                    frames_using_crosscopy=profile_frames[profile],
                                    materialization_source_read_bytes=total['materialization_source_read_bytes'],
                                    materialization_destination_write_bytes=total['materialization_destination_write_bytes'],
                                    retained_predictor_read_bytes=total['retained_predictor_read_bytes'],
                                    research_stream_bytes=total['stream_bytes'], research_max_frame_bytes=max_frame[profile],
                                    descriptor_bytes=total['descriptor_bytes'], header_bytes=total['header_bytes'],
                                    fallback_bytes=total['fallback_bytes']))
    pins[str(Path(__file__).resolve().relative_to(ROOT))] = sha(Path(__file__).resolve())
    result = dict(schema='cu66-v96-qualified-summary-v1', status='PASS', input_sha256=pins,
                  historical_requirement_snapshots=requirements, profiles=profile_results,
                  frames=457, independent_streams=1371, independent_tiles=11105100,
                  hidden_tiles_per_frame=294, sameposition_copy_tiles=2216647,
                  nonCOPY_exact_sameposition_tiles=38099, unbounded_cross_opportunities_not_implemented=101936,
                  service_model=dict(lifecycle_checks=model['lifecycle_check_count'],
                                     baseline_display_bl8_commands=32400, candidate_display_bl8_commands=31224,
                                     potential_read_reduction_percent=100 * 1176 / 32400,
                                     generator_clocks_per_frame={str(width): next(row['generator_clocks'] for row in model['rows'] if row['generator_bytes_per_clock'] == width) for width in (1,4,16)},
                                     model_only=True, physical_storage_proven=False),
                  rtl_modes=mode_results,
                  rtl_check_count=sum(mode['verdict']['checks'] for mode in rtl['modes']),
                  decision='Retain control; integrate bounded materialization and price constant consumers before any memory/latency promotion.',
                  checkpoint='V96a inventory qualified; V96b standalone component implemented; V96c component tests only; V96d complete-path integration open.',
                  full_path_integrated=False, physical_hardware_tested=False,
                  hardware_30fps_proven=False, complete_under10ms_proven=False,
                  limitations=['Research literal stream is not deployed residual syntax or a packet-cap/compression result.',
                               'Crosscopy changes predictor address and bypasses a residual-work proxy; no measured full-path memory reduction.',
                               'Standalone timed pin model is not achieved frequency, routing, CDC or hardware validation.',
                               'Constant display producer is a Python tile-order model, not an RTL raster/controller join.',
                               'V96 does not newly reconstruct/validate full RTL HUD, roots/seals, RGB or continuous display.',
                               'Frozen canonical walkthrough-family/synthetic targets; no wider independent raw captures or live encoder test.'])
    (AREA / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS_V96_SUMMARY', result['independent_streams'], 'streams;', result['rtl_check_count'], 'RTL checks')
    for row in profile_results:
        print(row['profile'], 'crosscopies', row['crosscopies'], 'residual work proxy %', round(row['bypassed_residual_fraction_percent'], 3))


if __name__ == '__main__':
    main()
