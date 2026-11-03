#!/usr/bin/env python3
"""Correlate normalized per-frame telemetry without conflating clock domains."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

STAGES = ('capture', 'encode', 'send', 'ingress', 'decoded', 'presented')
PAIRS = (
    ('capture', 'encode'), ('encode', 'send'), ('capture', 'send'),
    ('ingress', 'decoded'), ('decoded', 'presented'), ('ingress', 'presented'),
    ('capture', 'ingress'), ('send', 'ingress'),
    ('capture', 'presented'), ('send', 'presented'),
)
HOST_CLOCK = 'host_monotonic'
RECEIVER_CLOCK = 'receiver'


def read_jsonl(paths):
    events = []
    for path in paths:
        with Path(path).open(encoding='utf-8') as stream:
            for line_no, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f'{path}:{line_no}: invalid JSON: {exc.msg}') from exc
                try:
                    validate_event(event)
                except ValueError as exc:
                    raise ValueError(f'{path}:{line_no}: {exc}') from exc
                events.append(event)
    return events


def validate_event(event):
    if not isinstance(event, dict):
        raise ValueError('event must be a JSON object')
    required = ('session_id', 'frame_seq', 'frame_id', 'stage', 'clock_domain', 'timestamp_ns', 'evidence_kind')
    if any(key not in event for key in required):
        raise ValueError('event missing required normalized telemetry fields')
    if type(event['session_id']) is not str or not event['session_id']:
        raise ValueError('session_id must be a nonempty string')
    if type(event['frame_seq']) is not int or event['frame_seq'] < 0:
        raise ValueError('frame_seq must be a nonnegative integer')
    if type(event['frame_id']) is not int or event['frame_id'] < 0:
        raise ValueError('frame_id must be a nonnegative integer')
    if event['stage'] not in STAGES:
        raise ValueError(f"stage must be one of: {', '.join(STAGES)}")
    if type(event['clock_domain']) is not str or not event['clock_domain']:
        raise ValueError('clock_domain must be a nonempty string')
    if type(event['timestamp_ns']) is not int or event['timestamp_ns'] < 0:
        raise ValueError('timestamp_ns must be a nonnegative integer')
    if event['evidence_kind'] not in ('hardware', 'simulated'):
        raise ValueError("evidence_kind must be 'hardware' or 'simulated'")


def _ranges(values):
    """Compress sorted integer values into inclusive contiguous ranges."""
    values = sorted(set(values))
    if not values:
        return []
    output = []
    start = previous = values[0]
    for value in values[1:]:
        if value != previous + 1:
            output.append({'start': start, 'end': previous})
            start = value
        previous = value
    output.append({'start': start, 'end': previous})
    return output


def _missing_sequence_ranges(ordered_values):
    ranges = []
    missing_count = 0
    for left, right in zip(ordered_values, ordered_values[1:]):
        if right > left + 1:
            ranges.append({'start': left + 1, 'end': right - 1})
            missing_count += right - left - 1
    return ranges, missing_count


def _latency(start, end, calibration):
    start_domain, end_domain = start['clock_domain'], end['clock_domain']
    if start_domain == end_domain:
        estimate = end['timestamp_ns'] - start['timestamp_ns']
        result = {'status': 'computed_same_clock', 'estimate_ns': estimate,
                  'uncertainty_ns': 0, 'lower_bound_ns': estimate, 'upper_bound_ns': estimate,
                  'clock_domain': start_domain}
        if estimate < 0:
            result['ordering_warning'] = 'end timestamp precedes start timestamp on the same clock'
        return result
    if start_domain == HOST_CLOCK and end_domain == RECEIVER_CLOCK:
        if calibration is None:
            return {'status': 'not_computed', 'reason': 'explicit clock offset and uncertainty required'}
        offset = calibration['receiver_minus_host_ns']
        uncertainty = calibration['uncertainty_ns']
        estimate = end['timestamp_ns'] - offset - start['timestamp_ns']
        result = {'status': 'computed_with_calibration', 'estimate_ns': estimate,
                  'uncertainty_ns': uncertainty, 'lower_bound_ns': estimate - uncertainty,
                  'upper_bound_ns': estimate + uncertainty,
                  'calibration': {'receiver_minus_host_ns': offset, 'uncertainty_ns': uncertainty}}
        if estimate < 0:
            result['ordering_warning'] = 'negative cross-clock latency estimate; inspect calibration and event ordering'
        elif estimate - uncertainty < 0:
            result['ordering_warning'] = 'uncertainty interval crosses zero; event order is unresolved'
        return result
    return {'status': 'not_computed',
            'reason': f'no supported explicit mapping from {end_domain!r} to {start_domain!r}'}


def _summary(values):
    if not values:
        return {'count': 0, 'min_ns': None, 'median_ns': None, 'p95_ns': None, 'max_ns': None}
    ordered = sorted(values)
    def percentile(p):
        pos = (len(ordered) - 1) * p
        lo, hi = math.floor(pos), math.ceil(pos)
        if lo == hi:
            return ordered[lo]
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)
    return {'count': len(values), 'min_ns': min(values), 'median_ns': percentile(.5),
            'p95_ns': percentile(.95), 'max_ns': max(values)}


def analyze(events, calibrations=None, frame_id_bits=32):
    if type(frame_id_bits) is not int or not 1 <= frame_id_bits <= 64:
        raise ValueError('frame_id_bits must be in 1..64')
    for event in events:
        validate_event(event)
        if event['frame_id'] >= (1 << frame_id_bits):
            raise ValueError(f"frame_id does not fit configured {frame_id_bits}-bit field")
    calibrations = {} if calibrations is None else calibrations
    if not isinstance(calibrations, dict):
        raise ValueError('calibrations must be an object keyed by session_id')
    groups = defaultdict(list)
    for event in events:
        groups[(event['session_id'], event['evidence_kind'])].append(event)

    output_groups = []
    for (session, evidence), group_events in sorted(groups.items()):
        session_calibrations = calibrations.get(session, {})
        if not isinstance(session_calibrations, dict):
            raise ValueError(f'invalid clock calibration mapping for session {session}')
        calibration = session_calibrations.get(evidence)
        if calibration is not None:
            if (not isinstance(calibration, dict) or
                    type(calibration.get('receiver_minus_host_ns')) is not int or
                    type(calibration.get('uncertainty_ns')) is not int or
                    calibration['uncertainty_ns'] < 0):
                raise ValueError(f'invalid explicit clock calibration for {session}/{evidence}')
        frames = defaultdict(list)
        by_raw_id = defaultdict(set)
        clocks = set()
        for event in group_events:
            frames[event['frame_seq']].append(event)
            by_raw_id[event['frame_id']].add(event['frame_seq'])
            clocks.add(event['clock_domain'])

        stage_map = {}
        duplicate_rows = []
        mismatch_rows = []
        for seq, rows in frames.items():
            stage_events = defaultdict(list)
            for row in rows:
                stage_events[row['stage']].append(row)
            stage_map[seq] = stage_events
            raw_ids = sorted({row['frame_id'] for row in rows})
            if len(raw_ids) > 1:
                mismatch_rows.append({'frame_seq': seq, 'frame_ids': raw_ids})
            for stage, items in stage_events.items():
                if len(items) > 1:
                    duplicate_rows.append({'frame_seq': seq, 'frame_id': items[0]['frame_id'],
                                           'stage': stage, 'records': len(items),
                                           'extra_records': len(items) - 1})

        captured = sorted(seq for seq, stages in stage_map.items() if 'capture' in stages)
        missing_capture_ranges, missing_capture_count = _missing_sequence_ranges(captured)
        captured_set = set(captured)
        stage_coverage = {}
        for stage in STAGES[1:]:
            observed = {seq for seq, stages in stage_map.items() if stage in stages}
            stage_coverage[stage] = {
                'observed_frame_count': len(observed),
                'missing_for_captured_frame_count': len(captured_set - observed),
                'missing_for_captured_frame_seq_ranges': _ranges(captured_set - observed),
                'events_without_capture_count': len(observed - captured_set),
                'events_without_capture_frame_seq_ranges': _ranges(observed - captured_set),
            }

        modulus = 1 << frame_id_bits
        capture_rows = []
        for seq in captured:
            items = stage_map[seq]['capture']
            if len(items) == 1:
                capture_rows.append(items[0])
        wraps, regressions, step_mismatches = [], [], []
        for previous, current in zip(capture_rows, capture_rows[1:]):
            prev_id, cur_id = previous['frame_id'], current['frame_id']
            seq_delta = current['frame_seq'] - previous['frame_seq']
            expected = (prev_id + seq_delta) % modulus
            if cur_id != expected:
                step_mismatches.append({'from_frame_seq': previous['frame_seq'], 'to_frame_seq': current['frame_seq'],
                                        'expected_frame_id': expected, 'actual_frame_id': cur_id})
            if cur_id < prev_id:
                row = {'from_frame_seq': previous['frame_seq'], 'to_frame_seq': current['frame_seq'],
                       'from_frame_id': prev_id, 'to_frame_id': cur_id}
                if prev_id >= (modulus * 3) // 4 and cur_id < modulus // 4 and cur_id == expected:
                    wraps.append(row)
                else:
                    regressions.append(row)

        frame_rows = []
        same_clock_values = defaultdict(list)
        calibrated_values = defaultdict(list)
        for seq in sorted(stage_map):
            stages = stage_map[seq]
            unique = {stage: items[0] for stage, items in stages.items() if len(items) == 1}
            latency_rows = {}
            for start_stage, end_stage in PAIRS:
                key = f'{start_stage}_to_{end_stage}'
                if start_stage not in unique or end_stage not in unique:
                    continue
                value = _latency(unique[start_stage], unique[end_stage], calibration)
                latency_rows[key] = value
                if value['status'] == 'computed_same_clock':
                    same_clock_values[key].append(value['estimate_ns'])
                elif value['status'] == 'computed_with_calibration':
                    calibrated_values[key].append(value['estimate_ns'])
            frame_rows.append({
                'frame_seq': seq,
                'frame_ids': sorted({row['frame_id'] for row in stages_to_events(stages)}),
                'stage_records': {stage: len(items) for stage, items in sorted(stages.items())},
                'timestamps': {stage: [{'clock_domain': item['clock_domain'], 'timestamp_ns': item['timestamp_ns']}
                                       for item in items] for stage, items in sorted(stages.items())},
                'latencies': latency_rows,
            })
        reused_ids = []
        for frame_id, seqs in sorted(by_raw_id.items()):
            ordered_seqs = sorted(seqs)
            if len(ordered_seqs) > 1:
                deltas = [b - a for a, b in zip(ordered_seqs, ordered_seqs[1:])]
                reused_ids.append({'frame_id': frame_id, 'frame_seqs': ordered_seqs,
                                   'reuse_after_full_wrap': all(delta % modulus == 0 for delta in deltas)})

        output_groups.append({
            'session_id': session,
            'evidence_kind': evidence,
            'event_count': len(group_events),
            'clock_domains_seen': sorted(clocks),
            'frame_id_bits': frame_id_bits,
            'explicit_clock_calibration': calibration,
            'calibration_assumption': ('offset is constant over this session; uncertainty must include clock drift for the full run. A calibration from another time, session, or boot is invalid.' if calibration else None),
            'cross_clock_latency_policy': ('computed with supplied offset and uncertainty' if calibration else
                                           'not computed; provide per-session/evidence receiver_minus_host_ns and uncertainty_ns'),
            'captured_frame_count': len(captured),
            'capture_frame_seq_range': [min(captured), max(captured)] if captured else None,
            'missing_capture_frame_seq_count': missing_capture_count,
            'missing_capture_frame_seq_ranges': missing_capture_ranges,
            'frame_id_wrap_count': len(wraps),
            'frame_id_wraps': wraps,
            'frame_id_regressions': regressions,
            'frame_id_step_mismatches': step_mismatches,
            'reused_raw_frame_ids': reused_ids,
            'duplicate_stage_events': duplicate_rows,
            'frame_id_mismatches_within_frame_seq': mismatch_rows,
            'stage_coverage': stage_coverage,
            'same_clock_latency_summary_ns': {key: _summary(values) for key, values in sorted(same_clock_values.items())},
            'calibrated_cross_clock_latency_summary_ns': {key: _summary(values) for key, values in sorted(calibrated_values.items())},
            'frames': frame_rows,
        })
    return {'schema_version': 1, 'input_event_count': len(events), 'groups': output_groups}


def stages_to_events(stages):
    return [event for items in stages.values() for event in items]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('events', nargs='+', type=Path, help='normalized JSONL event logs to join')
    parser.add_argument('--calibration', type=Path, help='JSON mapping session/evidence to explicit clock offset and uncertainty')
    parser.add_argument('--frame-id-bits', type=int, default=32)
    parser.add_argument('--output', type=Path, help='write full JSON report; stdout if omitted')
    args = parser.parse_args()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
    calibration = json.loads(args.calibration.read_text()) if args.calibration else {}
    result = analyze(read_jsonl(args.events), calibration, args.frame_id_bits)
    encoded = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end='')


if __name__ == '__main__':
    main()
