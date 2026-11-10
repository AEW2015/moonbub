#!/usr/bin/env python3
"""Independent boundary cases for the synthetic wait-trace schema only."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/cu66-v122/wait_trace.py'
spec = importlib.util.spec_from_file_location('v122_wait_trace', SOURCE)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def main():
    base = validator.make_trace()
    tests = []

    def check(name, mutate, should_pass):
        trace = copy.deepcopy(base)
        mutate(trace)
        try:
            summary = validator.validate_trace(trace)
        except validator.TraceError as error:
            assert not should_pass, (name, str(error))
            tests.append(dict(name=name, expected='reject', actual='reject',
                              diagnostic=str(error)))
        else:
            assert should_pass, name + ' accepted malformed trace'
            tests.append(dict(name=name, expected='accept', actual='accept',
                              decode_interval_cycles=summary['decode_interval_cycles']))

    def pre_input_debt(trace):
        # Acceptance101 precedes decode-start102; matching ACK103 pays it.
        next(f for f in trace['fences'] if f['name']=='decode_start')['cycle'] = 102
        counts = trace['header']['declared_totals']['decode_wait_owner_edges']
        counts['producer_full'] = 0
        # Cycles102..104 consist of one pending-service and two owner-none edges.
        assert counts['physical_service_pending']==1 and counts['none']==2

    check('acceptance_before_decode_start_is_retained', pre_input_debt, True)
    check('boolean_bank_cannot_alias_integer_zero',
          lambda t: t['edges'][1]['accepted_writes'][0].update(bank=False), False)
    check('ACK_cannot_pay_wrong_byte_count',
          lambda t: t['edges'][3]['acked_writes'][0].update(bytes=7), False)
    check('ACK_cannot_pay_unknown_token',
          lambda t: t['edges'][3]['acked_writes'][0].update(token='other'), False)
    check('publication_cannot_switch_bank',
          lambda t: t['publication'].update(bank=1), False)
    check('required_root_fence_cannot_be_omitted',
          lambda t: t['fences'].__setitem__(slice(None),
              [f for f in t['fences'] if f['name']!='root_validated']), False)

    def boolean_cycle(trace):
        trace['header']['trace_start_cycle'] = 0
        trace['header']['trace_end_cycle'] = 7
        for edge in trace['edges']:
            edge['cycle'] -= 100
        for fence in trace['fences']:
            fence['cycle'] -= 100
        trace['publication']['cycle'] -= 100
        trace['edges'][0]['cycle'] = False

    check('boolean_cycle_cannot_alias_integer_zero', boolean_cycle, False)
    result = dict(schema='v122-wait-trace-independent-boundaries-v1',
        status='PASS', classification='synthetic schema validation only',
        validator=dict(path=str(SOURCE.relative_to(ROOT)),
            sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest()),
        auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        tests=tests, test_count=len(tests), hardware_contact=False,
        actual_RTL_instrumentation=False, physical_memory_model=False)
    output = ROOT / 'experiments/python-gamebub-v122/memory-study/wait-trace-independent.json'
    output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('PASS independent synthetic wait-trace boundaries:', len(tests))


if __name__ == '__main__':
    main()
