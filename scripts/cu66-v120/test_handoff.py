#!/usr/bin/env python3
"""Bounded fail-closed tests for the V120 component handoff exporter.

This test never creates positive native receipts or edits project handoff data.
If no real qualified manifest exists, positive export coverage is reported as
PENDING_REAL_QUALIFIED_MANIFEST. All negative fixtures use temporary manifests
and immutable real native receipts.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPORTER = ROOT / 'scripts/cu66-v120/prepare_handoff.py'
HANDOFF = ROOT / 'experiments/python-gamebub-v120/handoff.json'
A100 = ROOT / 'experiments/python-gamebub-v120/integrated-study/native/20261109T200300378785Z/receipt.json'
A125 = ROOT / 'experiments/python-gamebub-v120/integrated-study/native/20261109T193132372767Z/receipt.json'
REPORT = ROOT / 'experiments/python-gamebub-v120/audit/handoff-export-qa.json'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def native_manifest(a100=A100, a125=A125):
    """Manifest shape with real receipt pins; intentionally cannot qualify."""
    return {
        'part': 'xc7a100tcsg324-1',
        'top': 'cs88_pipeline_v91k',
        'period_ns': 10.0,
        'qualified_internal_component_clock_MHz': 100.0,
        'parameter_overrides': [],
        'initial_receipt': {'path': str(Path(a100).resolve()), 'sha256': digest(a100)},
        # Distinct actual 125 MHz receipt keeps duplicate-path guard from
        # masking the real 100 MHz component_internal_target_pass=false check.
        'repeat_receipt': {'path': str(Path(a125).resolve()), 'sha256': digest(a125)},
        'image_id': 'unused-before-real-target-failure',
        'recipe_sha256': {},
        'source_origins': {},
        'source_order': {},
    }


class ExporterNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a100 = json.loads(A100.read_text())
        a125 = json.loads(A125.read_text())
        if not a100['result']['component_internal_target_pass']:
            pass
        else:
            raise RuntimeError('Pinned negative A100 receipt unexpectedly qualifies; update fail-closed fixture selection.')
        if A100.resolve() == A125.resolve():
            raise RuntimeError('Negative fixture receipts must be distinct real attempts.')
        if a100['clock_period_ns'] != 10.0 or a100['result']['target_frequency_MHz'] != 100.0:
            raise RuntimeError('Pinned negative receipt is not the real 100 MHz attempt.')
        if a125['clock_period_ns'] != 8.0:
            raise RuntimeError('Second negative receipt is not the distinct real 125 MHz attempt.')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='v120-handoff-negative-')
        self.tmp = Path(self.temp.name)
        self.root = self.tmp / 'repo'
        helper = self.root / 'scripts/cu66-v120/prepare_handoff.py'
        helper.parent.mkdir(parents=True)
        shutil.copyfile(EXPORTER, helper)
        self.helper = helper
        self.manifest = self.root / 'experiments/python-gamebub-v120/handoff.json'
        self.manifest.parent.mkdir(parents=True)
        self.output = self.tmp / 'new-export'
        self.write_manifest(native_manifest())

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self, value):
        self.manifest.write_text(json.dumps(value, indent=2) + '\n')

    def invoke(self):
        return subprocess.run(
            [sys.executable, str(self.helper), '--output', str(self.output)],
            cwd=self.root, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=15, check=False)

    def assert_rejected_before_output(self, needle=None):
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        if needle:
            self.assertIn(needle, result.stdout)
        self.assertFalse(self.output.exists(), result.stdout)
        return result

    def test_wrong_top_rejected(self):
        m = json.loads(self.manifest.read_text()); m['top'] = 'moonshine_top'; self.write_manifest(m)
        self.assert_rejected_before_output('Manifest part/top differs')

    def test_wrong_part_rejected(self):
        m = json.loads(self.manifest.read_text()); m['part'] = 'xc7a35tcpg236-1'; self.write_manifest(m)
        self.assert_rejected_before_output('Manifest part/top differs')

    def test_wrong_period_rejected(self):
        m = json.loads(self.manifest.read_text()); m['period_ns'] = 9.0; self.write_manifest(m)
        self.assert_rejected_before_output('Only the measured 8 ns and 10 ns clocks')

    def test_wrong_clock_identity_rejected(self):
        m = json.loads(self.manifest.read_text()); m['qualified_internal_component_clock_MHz'] = 125.0; self.write_manifest(m)
        self.assert_rejected_before_output('Manifest clock identity differs')

    def test_parameter_override_rejected(self):
        m = json.loads(self.manifest.read_text()); m['parameter_overrides'] = ['TEST_ONLY=1']; self.write_manifest(m)
        self.assert_rejected_before_output('Only the measured default parameters')

    def test_duplicate_receipt_rejected(self):
        m = json.loads(self.manifest.read_text()); m['repeat_receipt'] = dict(m['initial_receipt']); self.write_manifest(m)
        self.assert_rejected_before_output('Fresh repeat must have a distinct receipt')

    def test_real_A100_unqualified_receipt_rejected_before_output(self):
        # The real A100 receipt is hash-pinned, its real retained artifacts are
        # checked read-only, and a distinct actual A125 path avoids duplicate
        # receipt rejection. No temporary receipt is synthesized.
        result = self.assert_rejected_before_output('')
        self.assertIn('AssertionError', result.stdout)
        self.assertNotIn('Fresh repeat must have a distinct receipt', result.stdout)
        self.assertNotIn('Receipt part/top differs', result.stdout)


class QualifiedManifestTests(unittest.TestCase):
    @unittest.skipUnless(HANDOFF.is_file(), 'PENDING_REAL_QUALIFIED_MANIFEST')
    def test_real_manifest_positive_export_and_no_overwrite(self):
        # This path runs only on a published, genuine handoff manifest. The
        # production exporter writes to a fresh temporary directory, never the
        # repository or a fixed build path.
        with tempfile.TemporaryDirectory(prefix='v120-handoff-positive-') as temp:
            output = Path(temp) / 'export'
            result = subprocess.run([sys.executable, str(EXPORTER), '--output', str(output)],
                                    cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=20, check=False)
            self.assertEqual(result.returncode, 0, result.stdout)
            prep = json.loads((output / 'preparation.json').read_text())
            self.assertEqual(prep['status'], 'PREPARED_NOT_RUN')
            self.assertFalse(prep['hardware_contact'])
            self.assertFalse(prep['tool_invoked'])
            self.assertFalse(prep['physical_trial_consumed'])
            self.assertEqual(prep['source_count'], 18)
            copied = json.loads((output / 'handoff-manifest.json').read_text())
            self.assertEqual(copied, json.loads(HANDOFF.read_text()))
            for alias, meta in copied['source_origins'].items():
                target = output / 'snapshot' / alias
                self.assertTrue(target.is_file(), alias)
                self.assertEqual(digest(target), meta['sha256'], alias)
            second = subprocess.run([sys.executable, str(EXPORTER), '--output', str(output)],
                                     cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, timeout=15, check=False)
            self.assertNotEqual(second.returncode, 0, second.stdout)
            self.assertIn('Refusing to overwrite', second.stdout)

    @unittest.skipUnless(HANDOFF.is_file(), 'PENDING_REAL_QUALIFIED_MANIFEST')
    def test_deep_receipt_metadata_corruption_rejected_from_temp_copy(self):
        self._corruption_case('metadata')

    @unittest.skipUnless(HANDOFF.is_file(), 'PENDING_REAL_QUALIFIED_MANIFEST')
    def test_retained_report_corruption_rejected_from_temp_copy(self):
        self._corruption_case('artifact')

    def _corruption_case(self, kind):
        original = json.loads(HANDOFF.read_text())
        first_rel = Path(original['initial_receipt']['path'])
        real_receipt = ROOT / first_rel
        with tempfile.TemporaryDirectory(prefix='v120-handoff-corrupt-') as temp:
            temp_root = Path(temp) / 'repo'
            helper = temp_root / 'scripts/cu66-v120/prepare_handoff.py'
            helper.parent.mkdir(parents=True)
            shutil.copyfile(EXPORTER, helper)
            manifest = temp_root / 'experiments/python-gamebub-v120/handoff.json'
            manifest.parent.mkdir(parents=True)
            m = original
            receipt_path = temp_root / first_rel
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            copied_receipt = json.loads(real_receipt.read_text())
            if kind == 'metadata':
                copied_receipt['top'] = 'incorrect_top'
            receipt_path.write_text(json.dumps(copied_receipt, indent=2) + '\n')
            m['initial_receipt'] = {'path': str(first_rel), 'sha256': digest(receipt_path)}
            manifest.write_text(json.dumps(m, indent=2) + '\n')
            if kind == 'artifact':
                # Copy just the first real retained artifact into the temporary
                # receipt tree, then corrupt that copy. No repo file is edited.
                rel_artifact = next(iter(copied_receipt['retained_artifact_sha256']))
                source_artifact = real_receipt.parent / rel_artifact
                target_artifact = receipt_path.parent / rel_artifact
                target_artifact.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_artifact, target_artifact)
                data = target_artifact.read_bytes()
                target_artifact.write_bytes(data + b'corruption')
            output = Path(temp) / 'no-export'
            result = subprocess.run([sys.executable, str(helper), '--output', str(output)],
                                    cwd=temp_root, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=15, check=False)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertFalse(output.exists(), result.stdout)
            if kind == 'metadata':
                self.assertIn('Receipt part/top differs', result.stdout)
            else:
                self.assertIn('Retained evidence differs', result.stdout)


def main():
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = runner.run(suite)
    complete = result.wasSuccessful() and (not HANDOFF.is_file() or not result.skipped)
    positive = 'PASS_REAL_MANIFEST_EXPORT_TESTED' if HANDOFF.is_file() and complete else (
        'PENDING_REAL_QUALIFIED_MANIFEST' if not HANDOFF.is_file() else 'FAILED')
    report = {
        'schema': 'v120-handoff-export-qa-v1',
        'status': 'PASS_NEGATIVE_GATES_ONLY' if complete and not HANDOFF.is_file() else ('PASS' if complete else 'FAIL'),
        'positive_case': positive,
        'positive_checks_executed': HANDOFF.is_file() and complete,
        'test_source_sha256': digest(Path(__file__)),
        'exporter_source_sha256': digest(EXPORTER),
        'manifest': {'path': str(HANDOFF.relative_to(ROOT)), 'sha256': digest(HANDOFF)} if HANDOFF.is_file() else None,
        'real_manifest_present': HANDOFF.is_file(),
        'base_negative_receipts': {
            'initial_100MHz': str(A100.relative_to(ROOT)), 'initial_sha256': digest(A100),
            'target_pass': json.loads(A100.read_text())['result']['component_internal_target_pass'],
            'distinct_repeat_125MHz': str(A125.relative_to(ROOT)), 'repeat_sha256': digest(A125),
        },
        'tests_run': result.testsRun,
        'tests_failed': len(result.failures) + len(result.errors),
        'tests_skipped': len(result.skipped),
        'tests': [
            'wrong top/part/period/clock/parameters/duplicate receipts reject before output creation',
            'real unqualified A100 receipt is processed with distinct real A125 repeat and rejected before output',
            'real positive export/no-overwrite/deep metadata/report corruption are tested only when genuine handoff.json exists',
        ],
        'constraints': ['Standard library only. No tools, builds, simulations, Docker, Vivado, Git mutations, fake positive receipts, or project-source changes.'],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print('REPORT', REPORT)
    return 0 if complete else 1


if __name__ == '__main__':
    raise SystemExit(main())
