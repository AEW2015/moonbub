"""Guard actual clock parsing/budgets; synthetic fixtures never qualify hardware."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('v112_native_guard', ROOT/'scripts/cu66-v112/native.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
OLD = ROOT/'experiments/python-gamebub-v110/count-domain-native/20261108T172431599061Z'

class NativeGuards(unittest.TestCase):
    def test_actual_control_reports(self):
        r = native.parse_reports(OLD/'reports', 10.0)
        old = json.loads((OLD/'receipt.json').read_text())
        self.assertEqual(r['timing'], old['result']['timing'])
        self.assertEqual(r['routing'], old['result']['routing'])
        self.assertTrue(r['clock_target_matches'])
        self.assertFalse(r['component_internal_target_pass'])

    def test_actual_100_reports_do_not_qualify_125(self):
        r = native.parse_reports(OLD/'reports', 8.0)
        self.assertFalse(r['clock_target_matches'])
        self.assertFalse(r['component_internal_target_pass'])

    def positive_fixture(self, folder):
        for n in ('route-timing-summary.rpt','route-check-timing.rpt','route-status.rpt','route-clocks.rpt','route-setup-paths.rpt'):
            shutil.copyfile(OLD/'reports'/n,folder/n)
        p=folder/'route-timing-summary.rpt';lines=p.read_text().splitlines()
        for i,line in enumerate(lines):
            vals=line.split()
            if len(vals)==12 and all(re.fullmatch(r'-?\d+(?:\.\d+)?',v) for v in vals):
                vals[:3]=['0.100','0.000','0'];lines[i]='    '+'    '.join(vals);break
        else:raise AssertionError('actual summary row missing')
        p.write_text('\n'.join(lines)+'\n')
        p=folder/'route-setup-paths.rpt';p.write_text(p.read_text().replace('Slack (VIOLATED) :        -1.022ns','Slack (MET) :        0.100ns',1))
        return folder

    def test_synthetic_positive_requires_matching_period(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.positive_fixture(Path(d))
            self.assertTrue(native.parse_reports(p,10.0)['component_internal_target_pass'])
            self.assertFalse(native.parse_reports(p,8.0)['component_internal_target_pass'])
            f=p/'route-clocks.rpt';text=f.read_text();text,n=re.subn(r'^component_clk\s+[\d.]+\s+\{[\d.]+\s+[\d.]+\}', 'component_clk 8.000 {0.000 4.000}',text,count=1,flags=re.M);self.assertEqual(n,1);f.write_text(text)
            self.assertTrue(native.parse_reports(p,8.0)['component_internal_target_pass'])
            self.assertFalse(native.parse_reports(p,10.0)['component_internal_target_pass'])

    def test_wrong_waveform_rejects_synthetic_positive(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.positive_fixture(Path(d));f=p/'route-clocks.rpt';text,n=re.subn(r'^component_clk\s+[\d.]+\s+\{[\d.]+\s+[\d.]+\}', 'component_clk 8.000 {0.000 5.000}',f.read_text(),count=1,flags=re.M);self.assertEqual(n,1);f.write_text(text)
            self.assertFalse(native.parse_reports(p,8.0)['component_internal_target_pass'])

    def test_external_positive_parent_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'receipt.json';p.write_text('{}')
            with self.assertRaises(AssertionError):native.positive_parent(p)

    def test_actual_local_control_qualification(self):
        policy=native.load(native.POLICY);q=native.qualify('control-125',policy)
        self.assertEqual(len(q['source_origins']),18)
        old=native.load(OLD/'receipt.json')['source_contract']['source_sha256']
        self.assertEqual({a for a in old if q['source_sha256'][a]!=old[a]},set(policy['candidate_aliases']))
        self.assertEqual(q['observability']['public_latency_delta_cycles'],0)

    def test_reject_unknown_trial(self):
        with self.assertRaises(AssertionError):native.qualify('control-150',native.load(native.POLICY))

if __name__=='__main__':unittest.main()
