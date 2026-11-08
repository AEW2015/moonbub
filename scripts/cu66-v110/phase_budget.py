#!/usr/bin/env python3
"""Attribute existing qualified RTL fence intervals; no state-occupancy/time claim."""
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v110'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def stats(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return None
    return dict(n=len(values), min=values[0], median=statistics.median(values),
                p95=values[math.ceil(.95 * len(values)) - 1], max=values[-1],
                negative_intervals=sum(value < 0 for value in values))


def main():
    summary_path = AREA / 'canonical-ready-rice/combined/results.json'
    summary = json.loads(summary_path.read_text())
    assert summary['status'] == 'PASS_EXACT_V110_CANONICAL' and summary['actual_RTL_run']
    receipt_path = ROOT / summary['selected_receipt']
    receipt = json.loads(receipt_path.read_text())
    assert receipt['runs'] == summary['runs'] and receipt['source_sha256'] == summary['source_sha256']
    inputs = {str(summary_path.relative_to(ROOT)): sha(summary_path),
              str(receipt_path.relative_to(ROOT)): sha(receipt_path)}
    current_sources = {}
    for name, expected in receipt['source_sha256'].items():
        if name.endswith(('.sv', '.svh', '/bench.cpp')):
            assert sha(ROOT / name) == sha(receipt_path.parent / 'sources' / name) == expected
            current_sources[name] = expected
    case_input = summary['inputs']['cases.tsv']
    case_path = ROOT / case_input['source']
    assert sha(case_path) == case_input['sha256']
    inputs[str(case_path.relative_to(ROOT))] = sha(case_path)
    packet_bytes = {parts[0]: len(parts[2]) // 2 if parts[2] != '-' else 0
                    for line in case_path.read_text().splitlines() if (parts := line.split())}
    rows = []
    event_type_counts = {}
    for run in summary['runs']:
        seed = run['seed']
        assert run['exact_stdout_events_cycles_and_canonical']
        transcript = receipt_path.parent / f'candidate-{seed}-simulation.jsonl'
        events = receipt_path.parent / f'candidate-{seed}-events.jsonl.gz'
        canonical = receipt_path.parent / f'candidate-{seed}-canonical.tsv.gz'
        for path in (transcript, events, canonical):
            assert sha(path) == receipt['artifact_sha256'][path.name]
            inputs[str(path.relative_to(ROOT))] = sha(path)
        aggregates = {}
        kinds = Counter()
        with gzip.open(events, 'rt') as source:
            for line in source:
                event = json.loads(line)
                kinds[event['type']] += 1
                key = event['id'], event['memory_profile']
                stage = event.get('stage', event['type'])
                first = event.get('first_cycle', event.get('cycle'))
                last = event.get('last_cycle', event.get('cycle'))
                item = aggregates.setdefault(key, {}).setdefault(stage, dict(records=0, samples=0,
                                                                            first=first, last=last,
                                                                            incomplete_records=0))
                item['records'] += 1
                item['samples'] += event.get('samples', 0)
                item['first'] = min(item['first'], first)
                item['last'] = max(item['last'], last)
                item['incomplete_records'] += event.get('complete') is False
        event_type_counts[str(seed)] = dict(kinds)
        for line in transcript.read_text().splitlines():
            case = json.loads(line)
            if case['type'] != 'case':
                continue
            assert case['status'] == 'PASS' and case['seed'] == seed and not case['full_frame_publication']
            stages = aggregates.get((case['id'], case['memory_profile']), {})
            for stage, field in (('assemble', 'assembled_tiles'), ('dequant', 'dq_tiles')):
                assert stages.get(stage, {}).get('records', 0) == case['inverse'][field]
            assert stages.get('residual', {}).get('samples', 0) == case['inverse']['residual_samples']
            assert stages.get('canonical', {}).get('samples', 0) == case['canonical']['samples']
            if 'residual' in stages:
                assert stages['residual']['last'] == case['last_residual']
            if 'canonical' in stages:
                assert stages['canonical']['last'] == case['canonical']['last_pixel_cycle']
            assert stages.get('reference_request', {}).get('records', 0) == case['canonical']['reference_requests']
            fences = {name: case[name] or None for name in ('first_input', 'last_input', 'first_coef',
                                                           'last_coef', 'coefficient_done_cycle',
                                                           'last_residual', 'done_cycle')}
            fences['last_pixel'] = case['canonical']['last_pixel_cycle'] or None
            fences['first_pixel'] = stages.get('canonical', {}).get('first')

            def interval(start, end):
                return None if fences[start] is None or fences[end] is None else fences[end] - fences[start]

            durations = dict(first_input_to_last_input=interval('first_input', 'last_input'),
                             last_input_to_first_coef_signed=interval('last_input', 'first_coef'),
                             first_coef_to_first_pixel_signed=interval('first_coef', 'first_pixel'),
                             coefficient_emit_span=interval('first_coef', 'last_coef'),
                             last_coef_to_coefficient_done=interval('last_coef', 'coefficient_done_cycle'),
                             coefficient_done_to_last_residual_signed=interval('coefficient_done_cycle', 'last_residual'),
                             coefficient_done_to_component_done=interval('coefficient_done_cycle', 'done_cycle'),
                             last_residual_to_last_pixel_signed=interval('last_residual', 'last_pixel'),
                             last_pixel_to_component_done=interval('last_pixel', 'done_cycle'),
                             canonical_pixel_span=interval('first_pixel', 'last_pixel'),
                             first_input_to_component_done=interval('first_input', 'done_cycle'),
                             last_input_to_component_done=interval('last_input', 'done_cycle'))
            overlap = None
            if all(fences[name] is not None for name in ('first_coef', 'last_coef', 'first_pixel', 'last_pixel')):
                overlap = max(0, min(fences['last_coef'], fences['last_pixel']) -
                              max(fences['first_coef'], fences['first_pixel']))
            rows.append(dict(seed=seed, id=case['id'], memory_profile=case['memory_profile'],
                             expected_error=case['error'], successful=case['error'] == 0,
                             case_cycles_including_finish_settle=case['cycles'],
                             cache_preload_cycles_excluded=case['cache_cycles'],
                             packet_vector_bytes=packet_bytes[case['id']], actual_inner_refill_bytes=case['refill_bytes'],
                             coefficients=case['coefficients'], coefficient_payload_bytes=2 * case['coefficients'],
                             inverse=case['inverse'], canonical=case['canonical'],
                             scratch_requests=case['requests'], scratch_acks=case['acks'],
                             refill_queue=case['refill_queue'], elastic=case['elastic'],
                             fences=fences, intervals_cycles=durations, event_fences=stages,
                             coefficient_canonical_envelope_overlap_cycles=overlap,
                             last_input_precedes_first_coef=None if fences['first_coef'] is None else fences['last_input'] <= fences['first_coef'],
                             final_physical_owner_settle_span=None,
                             missing_fence_policy='Zero transcript timestamps mean absent; never subtract absent fences. Final bench settle duration is not separately timestamped.',
                             conditional_post_last_input_below_1M=None if durations['last_input_to_component_done'] is None else durations['last_input_to_component_done'] < 1000000))
    assert len(rows) == 44
    groups = {}
    for profile in (0, 1):
        selected = [row for row in rows if row['memory_profile'] == profile and row['successful']]
        groups[str(profile)] = dict(successful_case_profiles=len(selected),
                                   case_cycles=stats(row['case_cycles_including_finish_settle'] for row in selected),
                                   intervals={field: stats(row['intervals_cycles'][field] for row in selected)
                                              for field in selected[0]['intervals_cycles']},
                                   conditional_case_cycles_below_1M=sum(row['case_cycles_including_finish_settle'] < 1000000 for row in selected),
                                   conditional_post_last_input_below_1M=sum(row['conditional_post_last_input_below_1M'] for row in selected))
    output = dict(schema='v110-actual-RTL-fence-phase-budget-v1',
                  status='READ_ONLY_EXISTING_QUALIFIED_RTL_COUNTER_DIAGNOSTIC',
                  script_sha256=sha(Path(__file__)), inputs=inputs, current_source_hashes=current_sources,
                  event_type_counts=event_type_counts, rows=rows, groups=groups,
                  error_case_profiles=sum(not row['successful'] for row in rows),
                  budget=dict(assumed_clock_Hz=100000000, strict_cycle_limit=1000000,
                              measured_hardware_time=False, achieved_clock_qualification=False,
                              validated_publication_fence_present=False),
                  definitions=['Intervals are endpoint differences without +1; spans include stalls and idle holes, not internal occupancy.',
                               'All interval signs are retained. Overlapping coefficient/canonical envelopes must not be summed as serial phases.',
                               'case_cycles starts at start assertion, excludes cache preload, and includes finish/settle; global event stamps use the bench clock.',
                               'coefficient_done is the raw producer done fence; component done also waits for arithmetic/reconstruction. Neither is production validated framebuffer publication.',
                               'Byte counts distinguish frozen packet-vector length from observed inner refill counter and emitted signed16 coefficient payload.',
                               'Profile1 intentionally applies approximately1/3 final output readiness and longer memory/reference service; these conditions can dominate elapsed cycles without IDCT work.'],
                  proposed_next_diagnostic='Measure per-cause producer DISPATCH/child-valid/inverse-ready/reconstruction-output stalls before changing arithmetic lanes. Existing envelopes cannot isolate producer compute from downstream backpressure.',
                  source_candidate_scope='A producer mapping lookahead around MAP_REQ/MAP_WAIT/DISPATCH is a concrete source investigation only; live mapped tile/cell/scale and child/epoch ownership must remain exact. No safe cycle-exact latency reduction or measured gain is established by these counters.',
                  no_RTL_simulation_synthesis_implementation_or_hardware_executed=True)
    path = AREA / 'phase-budget.json'
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps(groups, sort_keys=True))
    print('PHASE_BUDGET', sha(path))


if __name__ == '__main__':
    main()
