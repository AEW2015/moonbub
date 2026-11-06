#!/usr/bin/env python3
"""Analyze monitored finite-history results; distinguish service, output and model limits."""
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v79'


def stats(values):
    values = sorted(values)
    return dict(min=values[0], median=statistics.median(values), max=values[-1])


def main():
    reports, failures, pins = [], [], {}
    all_validated, all_delta_validated = [], []
    for path in sorted((AREA/'system').glob('cohort*/results.json')):
        data = json.loads(path.read_text())
        pins[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        if data['status'] != 'PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY':
            failures.append(dict(path=str(path.relative_to(ROOT)), failure=data.get('failure')))
            continue
        ts, frames, summary = data['timings'], data['frames'], data['summary']
        n = len(ts)
        starts = [t['first_complete_raster_start_ps'] for t in ts]
        validated = [t['validated_decode_model_cycles']*1e-5 for t in ts]
        delta = [v for f,v in zip(frames,validated) if not f['key']]
        ingress_full = [(t['first_complete_raster_end_ps']-t['packet_complete_cycle']*10000)/1e9 for t in ts]
        stage5 = [f['stage5_cycles']/f['cycles'] for f in frames]
        # Disjoint tick samples, not subtraction of overlapping port service counters.
        base_tile_busy = [(f['base1_tile1_aux0_cycles']+f['base1_tile1_aux1_cycles'])/f['cycles'] for f in frames]
        for f in frames:
            assert sum(f[f'base{b}_tile{t}_aux{a}_cycles'] for b in range(2) for t in range(2) for a in range(2)) == f['cycles']
            assert sum(f[f'stage{i}_cycles'] for i in range(16)) == f['cycles']
        reports.append(dict(run=path.parent.name, cohort=data['cohort'], sources=n,
            functional='PASS', validated_ms=stats(validated),
            transaction_service_ms=stats([f['cycles']*1e-5 for f in frames]),
            admission_to_validated_ms=stats([(t['validated_ready_cycle']-t['admission_cycle'])*1e-5 for t in ts]),
            ingress_to_commit_ack_ms=stats([(t['commit_ack_cycle']-t['packet_complete_cycle'])*1e-5 for t in ts]),
            delta_validated_ms=stats(delta),
            ingress_to_first_full_raster_end_ms=stats(ingress_full),
            first_full_raster_start_gap_ms=stats([(b-a)/1e9 for a,b in zip(starts,starts[1:])]),
            finite_first_to_last_source_cadence_fps=(n-1)*1e12/(starts[-1]-starts[0]),
            serial_ack_33ms_passes=sum(t['met_serial_30fps_budget'] for t in ts),
            strict_validated_under10ms_passes=sum(t['met_validated_under10ms'] for t in ts),
            max_release_to_admission_ms=max(t['queue_cycles'] for t in ts)*1e-5,
            max_waiting=summary['max_waiting_released_unadmitted'],
            max_in_service=summary['max_in_service'],
            max_total_released_unacked=summary['max_total_released_unacked'],
            base_run_fraction=stats(stage5),base_run_tile_busy_fraction=stats(base_tile_busy),
            native_pixels_checked=summary['observed_pixels'],
            wall_seconds=data['wall_seconds']))
        if n == data['cohort_available_frames']:
            all_validated.extend(validated)
            all_delta_validated.extend(delta)
    full = [r for r in reports if r['sources'] in (119,100)]
    report = dict(schema='cu79-finite-history-analysis-v1', source_sha256=pins,
        runs=reports, failures=failures,
        full_history_sources=sum(r['sources'] for r in full),
        full_history_validated_ms=stats(all_validated) if all_validated else None,
        full_history_delta_validated_ms=stats(all_delta_validated) if all_delta_validated else None,
        limitations=['Source identity is(cohort,generation,frameID); independent histories reset once each.',
          'Finite first-to-last cadence excludes startup/final drain and is not the1800-source/60s sustained gate.',
          'Disjoint stage/tile-busy bins measure occupancy, not critical-path attribution or a speedup bound.',
          'Native CPU HUD cost is zero-simtime; no liveESP32, routed Fmax/fit/CDC or physical performance proof.'])
    (AREA/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    for r in reports:
        print(r['run'],json.dumps({k:r[k] for k in ('sources','validated_ms','finite_first_to_last_source_cadence_fps','max_waiting','base_run_tile_busy_fraction')}))
    print('full_history_sources',report['full_history_sources'],'retained_failures',len(failures))


if __name__ == '__main__':
    main()
