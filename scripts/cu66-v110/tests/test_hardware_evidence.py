#!/usr/bin/env python3
"""Synthetic offline self-tests; fixtures stay in an external temporary tree."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys
import tempfile
import time
import unittest

CHECKER = Path(__file__).resolve().parents[1] / 'hardware_evidence.py'
SPEC = importlib.util.spec_from_file_location('hardware_evidence', CHECKER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def digest(path):
    return MODULE.sha256(path)


class HardwareEvidenceTests(unittest.TestCase):
    hashes = {}
    findings = []

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='v110-hardware-evidence-', dir='/tmp')
        cls.work = Path(cls.temporary.name)
        cls.calibration = dict(kind='synthetic_fixture', clock_id='fixture_clock',
                               tick_rate_numerator=1000000, tick_rate_denominator=1,
                               method='Deterministic fixture clock; no device measurement.')
        (cls.work / 'calibration.json').write_text(json.dumps(cls.calibration))
        (cls.work / 'fixture-provenance.txt').write_text('Synthetic test fixture only. No hardware contacted.\n')
        cls.base = dict(schema=MODULE.SCHEMA, evidence_kind='synthetic',
                        coded_width=720, coded_height=480, profile_id='synthetic_fixture_profile',
                        calibration={key: value for key, value in cls.calibration.items() if key != 'method'},
                        counter=dict(width_bits=16, clock_id='fixture_clock', reset_epoch='fixture_epoch',
                                     reset_policy='single_epoch', wrap_policy='explicit_wrap_count'),
                        source_release_schedule='floor_30hz_from_window_start', queue_capacity=4,
                        windows=[dict(id='60s', start=cls.stamp(1000000), end=cls.stamp(61000000)),
                                 dict(id='600s', start=cls.stamp(61000000), end=cls.stamp(661000000))])
        for window in cls.base['windows']:
            window['health'] = dict({key: 0 for key in MODULE.HEALTH_COUNTERS},
                                    queue_bounded=True, max_queue_depth=1)
        cls.base['calibration']['artifact'] = cls.pin('calibration.json')
        cls.base['provenance'] = [cls.pin('fixture-provenance.txt')]
        trace = cls.work / 'base.jsonl'
        with trace.open('w') as output:
            # Independent integer construction: exactly 1800/18000 distinct
            # releases and 5ms latency, with explicit 16-bit counter wraps.
            for name, count, origin in (('60s', 1800, 1000000), ('600s', 18000, 61000000)):
                for index in range(count):
                    identity = name + '-source-' + str(index)
                    release = origin + (index * 100000) // 3
                    row = dict(window_id=name, frame_id=identity, source_frame_id=identity,
                               published_frame_id=identity, displayed_frame_id=identity,
                               source_release=cls.stamp(release), packet_complete=cls.stamp(release + 1000),
                               validated_publication=cls.stamp(release + 6000),
                               displayed_at=cls.stamp(release + 7000),
                               flags={name: True for name in MODULE.FLAGS},
                               hash=hashlib.sha256(identity.encode()).hexdigest(),
                               expected_hash=hashlib.sha256(identity.encode()).hexdigest(),
                               queue_depth=1, queue_bounded=True, underruns=0)
                    output.write(json.dumps(row, separators=(',', ':')) + '\n')
        cls.base['trace'] = cls.pin('base.jsonl')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @staticmethod
    def stamp(ticks):
        return dict(tick=ticks % 65536, wrap_count=ticks // 65536, reset_epoch='fixture_epoch')

    @classmethod
    def pin(cls, name):
        value = digest(cls.work / name)
        cls.hashes[name] = value
        return dict(path=name, sha256=value)

    def evaluate(self, name, change=None, rows=None, expected=False, kind='synthetic'):
        manifest = copy.deepcopy(self.base)
        if rows is not None:
            with (self.work / (name + '.jsonl')).open('w') as output:
                for line_number, line in enumerate((self.work / 'base.jsonl').open()):
                    frame = json.loads(line)
                    replacement = rows(frame, line_number)
                    if replacement is not None:
                        output.write(json.dumps(replacement, separators=(',', ':')) + '\n')
            manifest['trace'] = self.pin(name + '.jsonl')
        if change:
            change(manifest)
        path = self.work / (name + '.manifest.json')
        path.write_text(json.dumps(manifest))
        self.pin(path.name)
        result = MODULE.check_manifest(path)
        self.findings.append(dict(test=name, **result))
        self.assertEqual(result['numerical_gates_pass'], expected, result['errors'])
        self.assertEqual(result['evidence_kind'], kind)
        self.assertIs(result['hardware_execution_verified'], False)
        self.assertIs(result['hardware_acceptance'], False)
        self.assertEqual(result['hardware_acceptance_status'], 'NOT_ATTESTED_OFFLINE')
        return result

    def test_synthetic_60_and_600_seconds_pass_only_numbers(self):
        result = self.evaluate('positive', expected=True)
        self.assertEqual([w['distinct_frames'] for w in result['windows']], [1800, 18000])
        for window in result['windows']:
            self.assertEqual(window['fps'], 30)
            self.assertEqual(window['latency_ms'], dict(min=5, median=5, p95=5, p99=5, max=5))
            self.assertTrue(window['every_latency_strictly_below_10ms'])

    def test_duplicate_source_frame_rejected(self):
        def rows(frame, number):
            if number == 50:
                for key in ('frame_id', 'source_frame_id', 'published_frame_id', 'displayed_frame_id'):
                    frame[key] = '60s-source-0'
            return frame
        self.evaluate('duplicate', rows=rows)

    def test_repeated_publication_identity_rejected(self):
        def rows(frame, number):
            if number == 5:
                frame['published_frame_id'] = '60s-source-0'
            return frame
        self.evaluate('repeated-publication', rows=rows)

    def test_missing_calibration_and_missing_wrap_policy(self):
        self.evaluate('no-calibration', lambda manifest: manifest.pop('calibration'))
        self.evaluate('no-wrap-policy', lambda manifest: manifest['counter'].pop('wrap_policy'))

    def test_invalid_tick_and_reset_epoch_rejected(self):
        for field, value in (('tick', 65536), ('reset_epoch', 'different_epoch'), ('wrap_count', -1)):
            def rows(frame, number, key=field, replacement=value):
                if number == 4:
                    frame['packet_complete'][key] = replacement
                return frame
            self.evaluate('invalid-' + field, rows=rows)

    def test_one_exact_10ms_outlier_fails_despite_5ms_median(self):
        def rows(frame, number):
            if number == 17:
                packet = frame['packet_complete']['wrap_count'] * 65536 + frame['packet_complete']['tick']
                frame['validated_publication'] = self.stamp(packet + 10000)
                frame['displayed_at'] = self.stamp(packet + 11000)
            return frame
        result = self.evaluate('exact-10ms', rows=rows)
        self.assertEqual(result['windows'][0]['latency_ms']['median'], 5)
        self.assertEqual(result['windows'][0]['latency_ms']['max'], 10)
        self.assertFalse(result['windows'][0]['every_latency_strictly_below_10ms'])
        self.assertEqual(result['windows'][0]['worst_frame']['frame_id'], '60s-source-17')

    def test_hash_underrun_reference_and_hud_failure(self):
        for failure in ('hash', 'underruns', 'reference_valid', 'hud_valid'):
            def rows(frame, number, fault=failure):
                if number == 7:
                    if fault == 'hash':
                        frame['hash'] = '0' * 64
                    elif fault == 'underruns':
                        frame['underruns'] = 1
                    else:
                        frame['flags'][fault] = False
                return frame
            self.evaluate('failed-' + failure, rows=rows)

    def test_insufficient_duration_and_dropped_frame(self):
        self.evaluate('short-window', lambda manifest: manifest['windows'][0].update(end=self.stamp(60000000)))
        self.evaluate('missing-frame', rows=lambda frame, number: None if number == 1799 else frame)

    def test_release_stall_and_unbounded_queue(self):
        def stalled(frame, number):
            if number == 8:
                frame['source_release']['tick'] += 1
            return frame
        self.evaluate('release-stall', rows=stalled)
        def overflowing(frame, number):
            if number == 8:
                frame['queue_depth'] = 5
            return frame
        self.evaluate('queue-overflow', rows=overflowing)

    def test_claimed_provenance_must_exist_and_hash_match(self):
        self.evaluate('missing-provenance', lambda manifest: manifest['provenance'][0].update(path='absent'))
        self.evaluate('bad-provenance-hash', lambda manifest: manifest['provenance'][0].update(sha256='0' * 64))

    def test_whole_window_health_and_resolution(self):
        self.evaluate('window-underrun', lambda manifest: manifest['windows'][1]['health'].update(underruns=1))
        self.evaluate('window-unbounded-queue', lambda manifest: manifest['windows'][0]['health'].update(queue_bounded=False))
        self.evaluate('wrong-resolution', lambda manifest: manifest.update(coded_width=640))

    def test_hardware_capture_label_still_cannot_attest_execution(self):
        calibration = dict(self.calibration, kind='measured', method='Synthetic adversarial claim; no measurement.')
        (self.work / 'claimed-calibration.json').write_text(json.dumps(calibration))
        def claim(manifest):
            manifest['evidence_kind'] = 'hardware_capture'
            manifest['calibration']['kind'] = 'measured'
            manifest['calibration']['artifact'] = self.pin('claimed-calibration.json')
        self.evaluate('hardware-label-only', claim, expected=True, kind='hardware_capture')


if __name__ == '__main__':
    started = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(HardwareEvidenceTests)
    verdict = unittest.TextTestRunner(verbosity=2).run(suite)
    destination = os.environ.get('V110_HARDWARE_EVIDENCE_RECEIPT_DIR')
    if destination:
        receipt = dict(status='PASS_SYNTHETIC_SELFTEST_ONLY' if verdict.wasSuccessful() else 'FAIL',
                       hardware_execution_verified=False, hardware_acceptance=False,
                       tests_run=verdict.testsRun, failures=len(verdict.failures), errors=len(verdict.errors),
                       wall_seconds=time.monotonic() - started,
                       maximum_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                       cpu_user_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime,
                       cpu_system_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                       address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],
                       cpu_limit_seconds=resource.getrlimit(resource.RLIMIT_CPU)[0],
                       source_sha256={str(path): digest(path) for path in (CHECKER, Path(__file__).resolve())},
                       ephemeral_synthetic_input_sha256=HardwareEvidenceTests.hashes,
                       findings=HardwareEvidenceTests.findings,
                       limitations='All inputs generated in deleted external /tmp directory; hashes/results retained only. No device evidence or hardware execution verified, including hardware-labelled adversarial fixture.')
        Path(destination).mkdir(parents=True, exist_ok=True)
        (Path(destination) / 'selftest.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    raise SystemExit(0 if verdict.wasSuccessful() else 1)
