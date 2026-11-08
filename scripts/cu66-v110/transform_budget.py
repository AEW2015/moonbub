#!/usr/bin/env python3
"""Join retained transform events by full identity; no pure-math timing claim."""
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v110'
IDENTITY = ('id', 'memory_profile', 'frame_epoch', 'child_epoch', 'token',
            'plane', 'block', 'tile', 'qcell', 'qscale')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def summarize(values):
    if not values:
        return None
    ordered = sorted(value for value, identity in values)
    worst = max(values, key=lambda pair: pair[0])
    return dict(n=len(values), min=ordered[0], p50=statistics.median(ordered),
                p95=ordered[math.ceil(.95 * len(ordered)) - 1],
                p99=ordered[math.ceil(.99 * len(ordered)) - 1], max=ordered[-1],
                negative_count=sum(value < 0 for value in ordered),
                worst_identity=dict(zip(IDENTITY, worst[1])))


def main():
    summary_path = AREA / 'canonical-ready-rice/combined/results.json'
    summary = json.loads(summary_path.read_text())
    assert summary['status'] == 'PASS_EXACT_V110_CANONICAL' and summary['actual_RTL_run']
    receipt_path = ROOT / summary['selected_receipt']
    receipt = json.loads(receipt_path.read_text())
    assert receipt['runs'] == summary['runs']
    pins = {str(path.relative_to(ROOT)): sha(path) for path in (summary_path, receipt_path)}
    sources = {}
    for name, expected in receipt['source_sha256'].items():
        if name.endswith(('.sv', '.svh', '/bench.cpp')):
            assert sha(ROOT / name) == sha(receipt_path.parent / 'sources' / name) == expected
            sources[name] = expected
    rows = []
    per_seed = {}
    for run in summary['runs']:
        seed = run['seed']
        transcript = receipt_path.parent / f'candidate-{seed}-simulation.jsonl'
        events = receipt_path.parent / f'candidate-{seed}-events.jsonl.gz'
        for path in (transcript, events):
            assert sha(path) == receipt['artifact_sha256'][path.name]
            pins[str(path.relative_to(ROOT))] = sha(path)
        cases = {}
        for line in transcript.read_text().splitlines():
            case = json.loads(line)
            if case['type'] == 'case':
                assert case['status'] == 'PASS' and case['seed'] == seed
                cases[case['id'], case['memory_profile']] = case
        pending = {}
        seen = set()
        tiles = {key: [] for key in cases}
        counts = {key: Counter() for key in cases}
        peak_pending = 0
        with gzip.open(events, 'rt') as source:
            for line in source:
                event = json.loads(line)
                if event['type'] != 'transform':
                    continue
                key = tuple(event[field] for field in IDENTITY)
                case_key = key[0], key[1]
                assert case_key in cases and event['token'] > 0
                assert event['frame_epoch'] == cases[case_key]['frame_epoch']
                assert event['child_epoch'] in cases[case_key]['child_epochs']
                stage = event['stage']
                counts[case_key][stage] += 1
                counts[case_key][stage + '_samples'] += event['samples']
                if stage == 'assemble':
                    assert key not in seen and key not in pending
                    assert event['samples'] == 64 and event['complete']
                    assert event['first_cycle'] == event['last_cycle']
                    seen.add(key)
                    pending[key] = dict(assemble=event['first_cycle'])
                elif stage == 'dequant':
                    assert key in pending and 'dequant' not in pending[key]
                    assert event['samples'] == 64 and event['complete']
                    assert event['first_cycle'] == event['last_cycle']
                    pending[key]['dequant'] = event['first_cycle']
                else:
                    assert stage == 'residual' and key in pending and 'dequant' in pending[key]
                    item = pending.pop(key)
                    assert item['assemble'] <= item['dequant'] <= event['first_cycle'] <= event['last_cycle']
                    assert 0 < event['samples'] <= 64
                    assert event['complete'] == (event['samples'] == 64)
                    tiles[case_key].append((item['assemble'], item['dequant'], event['first_cycle'],
                                            event['last_cycle'], key, event['complete']))
                peak_pending = max(peak_pending, len(pending))
        unmatched = Counter((key[0], key[1]) for key in pending)
        for case_key, case in cases.items():
            observed = counts[case_key]
            assert observed['assemble'] == case['inverse']['assembled_tiles']
            assert observed['dequant'] == case['inverse']['dq_tiles']
            assert observed['residual_samples'] == case['inverse']['residual_samples']
            complete = sorted((item for item in tiles[case_key] if item[5]), key=lambda item: item[0])
            incomplete = sum(not item[5] for item in tiles[case_key])
            assert len(complete) == case['inverse']['residual_tiles']
            if case['error'] == 0:
                assert unmatched[case_key] == incomplete == 0
                assert len(complete) == observed['assemble'] == observed['dequant']
                assert 64 * len(complete) == case['coefficients']
            metrics = {name: [] for name in ('assemble_to_dequant', 'dequant_to_first_residual',
                                             'residual_span', 'assemble_to_last_residual',
                                             'successive_assembly_spacing', 'successive_residual_start_spacing',
                                             'successive_residual_finish_spacing',
                                             'previous_residual_finish_to_next_assembly_signed',
                                             'same_child_assembly_spacing', 'cross_child_assembly_spacing')}
            for index, (assembly, dequant, first, last, identity, full) in enumerate(complete):
                for name, value in (('assemble_to_dequant', dequant - assembly),
                                    ('dequant_to_first_residual', first - dequant),
                                    ('residual_span', last - first),
                                    ('assemble_to_last_residual', last - assembly)):
                    metrics[name].append((value, identity))
                if index:
                    previous = complete[index - 1]
                    assert first > previous[2] and last > previous[3]
                    for name, value in (('successive_assembly_spacing', assembly - previous[0]),
                                        ('successive_residual_start_spacing', first - previous[2]),
                                        ('successive_residual_finish_spacing', last - previous[3]),
                                        ('previous_residual_finish_to_next_assembly_signed', assembly - previous[3])):
                        metrics[name].append((value, identity))
                    same_child = identity[3] == previous[4][3] and identity[5] == previous[4][5]
                    metrics['same_child_assembly_spacing' if same_child else 'cross_child_assembly_spacing'].append((assembly - previous[0], identity))
            rows.append(dict(seed=seed, id=case['id'], memory_profile=case['memory_profile'],
                             expected_error=case['error'], successful=case['error'] == 0,
                             complete_matched_tiles=len(complete), incomplete_residual_records=incomplete,
                             unmatched_assembled_owners_at_trace_end=unmatched[case_key],
                             observed_counts=dict(observed),
                             metrics_cycles={name: summarize(values) for name, values in metrics.items()},
                             assemble_to_dequant_histogram=dict(sorted(Counter(value for value, identity in metrics['assemble_to_dequant']).items())),
                             first_complete_tile=None if not complete else
                             dict(identity=dict(zip(IDENTITY, complete[0][4])), assemble=complete[0][0],
                                  dequant=complete[0][1], residual_first=complete[0][2], residual_last=complete[0][3]),
                             assembly_during_math_input_handshakes=case['inverse']['assembly_during_math_inputs']))
        per_seed[str(seed)] = dict(unique_full_identities=len(seen), peak_pending_launched_transform_identities=peak_pending,
                                   unmatched_owners_at_trace_end=len(pending))
    output = dict(schema='v110-retained-transform-event-budget-v1',
                  status='READ_ONLY_QUALIFIED_RTL_EVENT_RESPONSE_AND_SPACING_DIAGNOSTIC',
                  script_sha256=sha(Path(__file__)), input_sha256=pins, current_source_sha256=sources,
                  identity_fields=list(IDENTITY), per_seed=per_seed, rows=rows,
                  definitions=['All durations use endpoint differences without +1. Residual span63 means64 accepted samples at consecutive clocks.',
                               'Assemble event is the complete-tile dequant launch/handshake, not the first coefficient-fill cycle.',
                               'Peak pending identities counts launched transform events not yet matched to residual completion, not all physical coefficient banks or private owners.',
                               'Response/service envelopes include FSM waits, fast paths and downstream readiness; they are not exclusive arithmetic occupancy.',
                               'Successive spacing includes source/chunk gaps and output backpressure. Same-child spacing still need not be pure math initiation interval.',
                               'Signed previous-residual-finish to next-assembly gap records overlap when negative, without summing overlapping stage envelopes.',
                               'Expected-error cases and incomplete/unretired owners are separate; no rejected work is promoted to validated output.'],
                  no_new_RTL_simulation_synthesis_implementation_or_hardware=True,
                  achieved_clock_or_decoder_only_math_service_proven=False,
                  calibrated_hardware_latency=False, validated_decode_under10ms=False)
    path = AREA / 'transform-budget.json'
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print('TRANSFORM_BUDGET', sha(path), per_seed)


if __name__ == '__main__':
    main()
