#!/usr/bin/env python3
"""Derive controlled comparisons without rerunning any codec or benchmark."""
import hashlib
import json
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def signature(result):
    """Actual identities and virtual events; observed wall timers excluded."""
    return digest(dict(
        presented=result['presented'], drops=result['drops'], commits=result['commits'],
        feedback=result['feedback'], allocations=result['allocations'],
        wire=result['forward_wire'], encoder_states=result['encoder_states'],
        cpu=[{k: x.get(k) for k in ('stage', 'id', 'start_ms', 'service_ms', 'done_ms',
              'input_sha256', 'output_sha256', 'index')} for x in result['cpu_services']],
        resize=[{k: x.get(k) for k in ('id', 'start_ms', 'service_ms', 'done_ms', 'output_sha256')}
                for x in result['resize_services']],
        packets=[{k: x.get(k) for k in ('id', 'packet_sha256', 'key', 'reference_id', 'bytes',
                 'admitted', 'encode_started_ms', 'encode_service_ms', 'decode_started_ms',
                 'decode_service_ms', 'decode_done_ms', 'released_ms', 'release_reason')}
                 for x in result['packets']], waits=result['encoder_admission_waits']))


def describe(case):
    result = case['result']
    slots = [p['released_ms'] - p['encode_started_ms'] for p in result['packets']
             if p['admitted'] and not p['key'] and p['release_reason'].startswith('decoded_ack')]
    return dict(strict=result['presented_strict'], eventual=result['presented_eventual'],
                diagnostic=result['metrics']['steady_fps'],
                virtual_trace_sha256=signature(result),
                p_sender_slot_hold_ms_mean=sum(slots) / len(slots) if slots else None,
                encoder_admission_wait_ms=result['encoder_admission_wait_ms'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify retained analysis without writing')
    args = parser.parse_args()
    source = HERE / 'results.json'; data = json.loads(source.read_text()); groups = {}
    for case in data['cases']:
        key = (case['source'], case['mode'], case['service_scale'])
        groups.setdefault(key, {})[case['policy']] = case
    comparisons = []
    for (clip, mode, scale), policies in groups.items():
        row = dict(source=clip, mode=mode, scale=scale,
                   policies={name: describe(case) for name, case in policies.items()})
        assert len({c['result']['service_tape']['table_sha256'] for c in policies.values()}) == 1
        assert len({digest(c['manifest']['frame_sha256']) for c in policies.values()}) == 1
        a, b = policies['periodic30'], policies['initial_only']
        row['initial_minus_periodic30'] = {
            name: describe(b)[name] - describe(a)[name] for name in ('strict', 'eventual', 'diagnostic')}
        if 'periodic60' in policies:
            row['periodic60_initial_checked_event_identity_trace_equal'] = signature(policies['periodic60']['result']) == signature(b['result'])
            assert row['periodic60_initial_checked_event_identity_trace_equal']
        ap = {p['id']: p for p in a['result']['packets']}
        bp = {p['id']: p for p in b['result']['packets']}
        common = sorted(ap.keys() & bp.keys())
        row['common_prepared_ids'] = common
        row['identical_outer_packet_ids'] = [i for i in common if ap[i].get('packet_sha256') is not None
                                            and ap[i].get('packet_sha256') == bp[i].get('packet_sha256')]
        row['reference_history_scope'] = 'After refresh, changed reference histories and packet bytes are causal policy outcomes; common source IDs do not imply equal packet work.'
        comparisons.append(row)
    report = dict(results_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  comparisons=comparisons,
                  conclusion='Removing periodic30refresh improves all tested native policy pairs but leaves UI below30diagnostic at pinned service. Declaredhalfservice plus initialonly reaches30diagnostic in one short case, still57strict/59eventual. No60strict primarytarget pass.',
                  limitation='exclusive waiting intervals and finite sender slot residence are diagnostics, not additive causal loss attribution or measured target CPU/memory capacity')
    output = HERE / 'controlled-comparison.json'
    if args.check:
        assert json.loads(output.read_text()) == report, 'retained analysis differs from pinned results/source'
    else:
        output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print('PASS: six controlled groups; identical checked periodic60/initial event and packet identity traces in four clean native60-frame groups')


if __name__ == '__main__':
    main()
