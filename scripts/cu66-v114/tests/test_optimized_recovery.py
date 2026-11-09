"""Exercise actual recovery qualification and reject altered provenance in memory."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('v114_optimized_guard',ROOT/'scripts/cu66-v114/native_optimized.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
SUMMARY=ROOT/'experiments/python-gamebub-v114/optimized/spatial/results.json'

class OptimizedRecoveryGuards(unittest.TestCase):
    def altered(self,mutate):
        original=native.load
        q=copy.deepcopy(original(SUMMARY));assert q['canonical_reused_actual_RTL']
        receipt=ROOT/q['selected_receipt'];mutate(q)
        def read(path):
            if Path(path)==SUMMARY:return copy.deepcopy(q)
            if Path(path)==receipt:return {k:copy.deepcopy(v) for k,v in q.items() if k!='selected_receipt'}
            return original(path)
        with patch.object(native,'load',side_effect=read):
            with self.assertRaises(AssertionError):native.spatial(SUMMARY)

    def test_actual_completed_recovery(self):
        q=native.spatial(SUMMARY)
        self.assertEqual(q['newly_executed_candidate_case_profiles'],0)
        self.assertEqual(q['transport_qualified_case_profiles'],24)

    def test_reject_overcounted_new_canonical(self):
        self.altered(lambda q:q.update(newly_executed_candidate_case_profiles=44))

    def test_reject_counting_partial_transport_seed(self):
        self.altered(lambda q:q.update(transport_reused_seeds=[107601,107602]))

    def test_reject_missing_new_execution(self):
        self.altered(lambda q:q.update(commands=[]))

    def test_reject_changed_binary(self):
        self.altered(lambda q:q['recovery_assets']['custom_transport'].update(sha256='0'*64))

    def test_reject_extra_container_swap(self):
        def mutate(q):
            argv=q['commands'][0]['argv'];argv[argv.index('--memory-swap')+1]='16g'
        self.altered(mutate)

    def test_reject_unbound_parent(self):
        self.altered(lambda q:q['canonical_parent_receipt'].update(sha256='0'*64))

if __name__=='__main__':unittest.main()
