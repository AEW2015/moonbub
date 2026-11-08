#!/usr/bin/env python3
"""Check proposed V110 trace numbers offline; never attest device execution."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

SCHEMA = 'v110-hardware-evidence-proposed-v1'
FLAGS = ('validated', 'pixels_valid', 'reference_valid', 'hud_valid',
         'hash_valid', 'ownership_valid', 'displayed')
HEALTH_COUNTERS = ('underruns', 'hash_failures', 'reference_failures',
                   'hud_failures', 'pixel_failures', 'queue_overflows')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, name, minimum=0):
    require(type(value) is int and value >= minimum, name + ': invalid integer')
    return value


def identifier(value, name):
    require(isinstance(value, str) and bool(value), name + ': missing identity')
    return value


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def check_manifest(manifest_path):
    """Return numeric findings, with hardware verification/acceptance always false."""
    result = dict(schema=SCHEMA, evidence_kind='unknown', numerical_gates_pass=False,
                  hardware_execution_verified=False, hardware_acceptance=False,
                  hardware_acceptance_status='NOT_ATTESTED_OFFLINE',
                  errors=[], windows=[], verified_artifacts=[])
    try:
        manifest_path = Path(manifest_path).resolve()
        result['manifest_sha256'] = sha256(manifest_path)
        manifest = json.loads(manifest_path.read_text())
        require(manifest.get('schema') == SCHEMA, 'unsupported proposed trace schema')
        kind = manifest.get('evidence_kind')
        require(kind in ('synthetic', 'hardware_capture'), 'invalid evidence_kind')
        result['evidence_kind'] = kind
        require(manifest.get('coded_width') == 720 and manifest.get('coded_height') == 480,
                'coded resolution must be 720x480')
        identifier(manifest.get('profile_id'), 'profile_id')

        def pin(spec, role):
            require(isinstance(spec, dict), role + ': missing artifact pin')
            name = identifier(spec.get('path'), role + '.path')
            expected = spec.get('sha256')
            require(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected),
                    role + ': missing SHA-256')
            path = (manifest_path.parent / name).resolve()
            require(path.is_file(), role + ': artifact missing')
            actual = sha256(path)
            require(actual == expected, role + ': artifact hash mismatch')
            result['verified_artifacts'].append(dict(role=role, path=str(path), sha256=actual))
            return path

        calibration = manifest.get('calibration')
        require(isinstance(calibration, dict), 'missing calibration')
        require(calibration.get('kind') == ('synthetic_fixture' if kind == 'synthetic' else 'measured'),
                'calibration kind does not match evidence kind')
        rate_num = integer(calibration.get('tick_rate_numerator'), 'tick rate numerator', 1)
        rate_den = integer(calibration.get('tick_rate_denominator'), 'tick rate denominator', 1)
        calibration_path = pin(calibration.get('artifact'), 'calibration')
        provenance = manifest.get('provenance')
        require(isinstance(provenance, list) and bool(provenance), 'missing provenance artifacts')
        for artifact in provenance:
            pin(artifact, 'provenance')
        counter = manifest.get('counter')
        require(isinstance(counter, dict), 'missing counter contract')
        width = integer(counter.get('width_bits'), 'counter width', 1)
        require(width <= 64, 'counter width exceeds 64')
        require(counter.get('wrap_policy') == 'explicit_wrap_count', 'explicit wrap counts required')
        require(counter.get('reset_policy') == 'single_epoch', 'single reset epoch required')
        epoch = identifier(counter.get('reset_epoch'), 'counter.reset_epoch')
        clock_id = identifier(counter.get('clock_id'), 'counter.clock_id')
        require(calibration.get('clock_id') == clock_id, 'calibration clock identity mismatch')
        calibration_data = json.loads(calibration_path.read_text())
        for field in ('kind', 'clock_id', 'tick_rate_numerator', 'tick_rate_denominator'):
            require(calibration_data.get(field) == calibration[field], 'calibration artifact value mismatch')
        identifier(calibration_data.get('method'), 'calibration.method')
        modulus = 1 << width

        def timestamp(value, name):
            require(isinstance(value, dict), name + ': missing timestamp')
            require(value.get('reset_epoch') == epoch, name + ': reset epoch mismatch')
            raw = integer(value.get('tick'), name + '.tick')
            wraps = integer(value.get('wrap_count'), name + '.wrap_count')
            require(raw < modulus, name + ': raw tick exceeds counter width')
            return wraps * modulus + raw

        require(manifest.get('source_release_schedule') == 'floor_30hz_from_window_start',
                'explicit fixed 30-Hz source schedule required')
        capacity = integer(manifest.get('queue_capacity'), 'queue_capacity', 1)
        declared = manifest.get('windows')
        require(isinstance(declared, list) and len(declared) == 2, 'need ordered 60s then 600s windows')
        windows = {}
        previous_end = None
        for spec, seconds in zip(declared, (60, 600)):
            name = identifier(spec.get('id'), 'window.id')
            require(name not in windows, 'duplicate window identity')
            start = timestamp(spec.get('start'), name + '.start')
            end = timestamp(spec.get('end'), name + '.end')
            require(end > start and (end - start) * rate_den == seconds * rate_num,
                    name + ': insufficient or incorrect window duration')
            require(previous_end is None or start >= previous_end, 'windows overlap or are out of order')
            previous_end = end
            health = spec.get('health')
            require(isinstance(health, dict), name + ': missing full-window health totals')
            for field in HEALTH_COUNTERS:
                require(integer(health.get(field), name + '.' + field) == 0,
                        name + ': window health failure ' + field)
            require(health.get('queue_bounded') is True, name + ': unbounded window queue')
            peak = integer(health.get('max_queue_depth'), name + '.max_queue_depth')
            require(peak <= capacity, name + ': window queue overflow')
            windows[name] = dict(id=name, start=start, end=end, seconds=seconds,
                                 count=0, latencies=[], worst=None, max_queue_depth=0,
                                 declared_max_queue_depth=peak, last_display=None)
        trace_spec = manifest.get('trace')
        trace = pin(trace_spec, 'trace')
        seen = set()
        current_window = 0
        names = list(windows)
        with trace.open('rb') as source:
            digest = hashlib.sha256()
            for line_number, line in enumerate(source, 1):
                digest.update(line)
                require(bool(line.strip()), 'blank trace record')
                frame = json.loads(line)
                name = frame.get('window_id')
                require(name in windows, 'unknown frame window')
                index = names.index(name)
                require(index >= current_window, 'trace window order regressed')
                current_window = index
                window = windows[name]
                frame_id = identifier(frame.get('frame_id'), 'frame_id')
                require(frame_id not in seen, 'duplicate/repeated frame identity')
                seen.add(frame_id)
                for field in ('source_frame_id', 'published_frame_id', 'displayed_frame_id'):
                    require(frame.get(field) == frame_id, field + ': intended frame identity mismatch')
                release = timestamp(frame.get('source_release'), 'source_release')
                packet = timestamp(frame.get('packet_complete'), 'packet_complete')
                publication = timestamp(frame.get('validated_publication'), 'validated_publication')
                displayed = timestamp(frame.get('displayed_at'), 'displayed_at')
                require(window['start'] <= release <= packet <= publication <= displayed < window['end'],
                        'invalid event ordering or frame outside window')
                expected_release = window['start'] + window['count'] * rate_num // (30 * rate_den)
                require(release == expected_release, 'source release cadence/stall mismatch')
                require(window['last_display'] is None or displayed > window['last_display'],
                        'display timestamps must strictly increase')
                window['last_display'] = displayed
                flags = frame.get('flags', {})
                require(all(flags.get(flag) is True for flag in FLAGS), 'frame validation/integrity flag failed')
                actual_hash = frame.get('hash')
                require(isinstance(actual_hash, str) and re.fullmatch('[0-9a-f]{64}', actual_hash)
                        and actual_hash == frame.get('expected_hash'), 'frame hash mismatch')
                require(integer(frame.get('underruns'), 'underruns') == 0, 'scanout underrun')
                depth = integer(frame.get('queue_depth'), 'queue_depth')
                require(frame.get('queue_bounded') is True and depth <= capacity, 'unbounded/overflowing queue')
                window['max_queue_depth'] = max(window['max_queue_depth'], depth)
                latency = publication - packet
                window['latencies'].append(latency)
                if window['worst'] is None or latency > window['worst']['latency_ticks']:
                    window['worst'] = dict(frame_id=frame_id, latency_ticks=latency,
                                           trace_line=line_number)
                window['count'] += 1
        require(digest.hexdigest() == trace_spec['sha256'], 'trace changed while being read')
        all_pass = True
        for window in windows.values():
            values = sorted(window['latencies'])
            count = len(values)
            throughput_pass = count >= 30 * window['seconds']
            latency_pass = bool(values) and all(100 * value * rate_den < rate_num for value in values)
            require(window['max_queue_depth'] <= window['declared_max_queue_depth'],
                    window['id'] + ': health queue peak contradicts trace')
            all_pass = all_pass and throughput_pass and latency_pass

            def milliseconds(value):
                return float(Fraction(value * rate_den * 1000, rate_num))

            stats = None
            if values:
                middle = Fraction(values[count // 2]) if count % 2 else Fraction(values[count // 2 - 1] + values[count // 2], 2)
                stats = dict(min=milliseconds(values[0]), median=milliseconds(middle),
                             p95=milliseconds(values[(95 * count + 99) // 100 - 1]),
                             p99=milliseconds(values[(99 * count + 99) // 100 - 1]),
                             max=milliseconds(values[-1]))
            result['windows'].append(dict(id=window['id'], duration_seconds=window['seconds'],
                                          distinct_frames=count, fps=count / window['seconds'],
                                          throughput_gate_pass=throughput_pass,
                                          every_latency_strictly_below_10ms=latency_pass,
                                          latency_ms=stats, worst_frame=window['worst'],
                                          max_queue_depth=window['declared_max_queue_depth']))
        if not all_pass:
            result['errors'].append('distinct-frame throughput or strict every-sample latency gate failed')
        result['numerical_gates_pass'] = all_pass
        result['tick_rate_hz'] = dict(numerator=rate_num, denominator=rate_den)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        result['errors'].append(str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = check_manifest(args.manifest)
    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(text)
    print(text, end='')
    return 0 if result['numerical_gates_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
