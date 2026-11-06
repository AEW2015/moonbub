#!/usr/bin/env python3
"""Summarize paired off/on RTL service, preserving every case and regression."""
import hashlib
import json
from pathlib import Path
import telemetry

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91f'
OUT = ROOT / 'experiments/python-gamebub-v91f/analysis.json'


def main():
    selected = {}
    for path in sorted((AREA / 'pipeline-attempts').glob('*/results.json')):
        result = telemetry.read(path)
        if result['status'].startswith('PASS_'):
            selected[result['seed']] = (path, result)
    assert set(selected) == {910432, 910433}
    campaigns = []
    for seed, (path, result) in sorted(selected.items()):
        rows = [json.loads(line) for line in path.with_name('simulation.jsonl').read_text().splitlines()]
        records = telemetry.validate_rows(rows, telemetry.cases())
        telemetry.compare_v91e(records, seed)
        keyed = {telemetry.config_key(row): row for row in records}
        comparisons = []
        for (identity, profile, overlap), off in keyed.items():
            if overlap:
                continue
            on = keyed[(identity, profile, 1)]
            comparisons.append(dict(id=identity, memory_profile=profile, off_cycles=off['cycles'],
                on_cycles=on['cycles'], saved_cycles=off['cycles'] - on['cycles'],
                reduction_percent=100 * (off['cycles'] - on['cycles']) / off['cycles'],
                counters=on['observability']['write_overlap_counters'],
                off_output_stalls=off['output_stalls'], on_output_stalls=on['output_stalls'],
                off_request_stalls=off['observability']['overlapping_edges']['memory_request_stall'],
                on_request_stalls=on['observability']['overlapping_edges']['memory_request_stall']))
        population = []
        for label, predicate in [('all_actual', lambda r: r['id'].startswith('actual:')),
                                  ('synthetic_and_boundary', lambda r: not r['id'].startswith('actual:'))]:
            for profile in (0, 1):
                group = [r for r in comparisons if r['memory_profile'] == profile and predicate(r)]
                a, b = sum(r['off_cycles'] for r in group), sum(r['on_cycles'] for r in group)
                population.append(dict(population=label, memory_profile=profile, packets=len(group), off_cycles=a,
                    on_cycles=b, saved_cycles=a-b, reduction_percent=100*(a-b)/a,
                    regressions=sum(r['saved_cycles'] < 0 for r in group),
                    output_stall_delta=sum(r['on_output_stalls']-r['off_output_stalls'] for r in group),
                    request_stall_delta=sum(r['on_request_stalls']-r['off_request_stalls'] for r in group),
                    packing_during_write_pending=sum(r['counters']['packing_during_write_pending'] for r in group)))
        source_services = []
        for source in sorted({':'.join(r['id'].split(':')[:3]) for r in comparisons if r['id'].startswith('actual:')}):
            for profile in (0, 1):
                group = [r for r in comparisons if ':'.join(r['id'].split(':')[:3]) == source and r['memory_profile'] == profile]
                assert len(group) == 3
                a, b = sum(r['off_cycles'] for r in group), sum(r['on_cycles'] for r in group)
                source_services.append(dict(source=source, memory_profile=profile, serialized_chunks=3,
                    off_cycles=a, on_cycles=b, saved_cycles=a-b, reduction_percent=100*(a-b)/a))
        campaigns.append(dict(seed=seed, report=str(path.relative_to(ROOT)), report_sha256=telemetry.sha(path),
            verdict=result['verdict'], baseline=result['baseline_v91e'], populations=population,
            source_services=source_services, comparisons=comparisons,
            highwaters={name:max(r['observability']['highwaters'][name] for r in records)
                        for name in records[0]['observability']['highwaters']}))
    output = dict(schema='cu66-v91f-paired-write-overlap-analysis-v1', status='PASS', campaigns=campaigns,
        vector_sha256=telemetry.sha(ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'),
        source_sha256={str(p.relative_to(ROOT)):telemetry.sha(p) for p in [Path(__file__).resolve(),Path(telemetry.__file__).resolve()]},
        endpoint='BR88 residual chunk to dense coefficient completion; source service sums three serial chunks, not full-frame decoding.',
        full_frame_validated_decode_under10ms_proven=False, hardware_distinct_30fps_proven=False,
        physical_clock_fit_or_memory_controller_calibration_proven=False)
    OUT.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps([dict(seed=c['seed'],populations=c['populations']) for c in campaigns],indent=2))


if __name__ == '__main__':
    main()
