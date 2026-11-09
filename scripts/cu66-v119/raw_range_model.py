#!/usr/bin/env python3
"""Exhaustive mathematical candidate proof; does not compile or simulate RTL."""
import hashlib
import json
import platform
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'fpga/experiments/cu66-v117-ingress-bytecount/br88_packet_ingress_sync_v91h.sv'
OUTPUT = ROOT / 'experiments/python-gamebub-v119/prototypes/raw-range.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed16(word):
    assert 0 <= word <= 0xffff
    return word if word < 0x8000 else word - 0x10000


def original(word):
    value = signed16(word)
    return -2048 <= value <= 2048


def prefix(word):
    upper = word >> 11
    return upper == 0 or upper == 31 or word == 0x0800


def main():
    began = time.perf_counter()
    text = SOURCE.read_text()
    signed_declaration = 'logic signed [15:0] ctx_coefficient, raw_coefficient;'
    acceptance = 'raw_coefficient>=-2048 && raw_coefficient<=2048'
    rejection = 'raw_coefficient < -2048 || raw_coefficient > 2048'
    assert signed_declaration in text and acceptance in text and rejection in text
    old = bytearray()
    candidate = bytearray()
    branch_counts = dict(zero_upper=0, one_upper=0, positive_2048=0)
    for word in range(0x10000):
        expected, actual = original(word), prefix(word)
        assert actual == expected, (hex(word), signed16(word), expected, actual)
        assert actual == (not (signed16(word) < -2048 or signed16(word) > 2048))
        old.append(expected)
        candidate.append(actual)
        branch_counts['zero_upper'] += word >> 11 == 0
        branch_counts['one_upper'] += word >> 11 == 31
        branch_counts['positive_2048'] += word == 0x0800
    endpoints = []
    for name, value, expected in (
        ('signed_minimum', -32768, False),
        ('below_negative_bound', -2049, False),
        ('negative_bound', -2048, True),
        ('negative_one', -1, True),
        ('zero', 0, True),
        ('below_positive_bound', 2047, True),
        ('positive_bound', 2048, True),
        ('above_positive_bound', 2049, False),
        ('signed_maximum', 32767, False),
    ):
        word = value & 0xffff
        assert signed16(word) == value and original(word) is expected and prefix(word) is expected
        endpoints.append(dict(name=name, signed_value=value, word_hex=f'0x{word:04x}',
                              original_accept=expected, candidate_accept=expected))
    accepted = sum(old)
    assert accepted == 4097 and sum(branch_counts.values()) == accepted
    assert old == candidate
    result = dict(
        schema='v119-exhaustive-signed16-raw-range-python-candidate-v1',
        status='PASS_PYTHON_EXHAUSTIVE_EQUIVALENCE',
        script=dict(path=str(Path(__file__).resolve().relative_to(ROOT)), sha256=sha(Path(__file__))),
        production_source=dict(path=str(SOURCE.relative_to(ROOT)), sha256=sha(SOURCE),
                               signed_declaration=signed_declaration,
                               acceptance_expression=acceptance, rejection_expression=rejection),
        candidate_expression="(word[15:11] == 5'b00000) or (word[15:11] == 5'b11111) or (word == 16'h0800)",
        domain=dict(bits=16, signed_minimum=-32768, signed_maximum=32767,
                    all_bit_patterns=65536, enumeration_order='unsigned word 0x0000 through 0xffff'),
        measured=dict(patterns_checked=len(old), mismatches=0, accepted=accepted,
                      rejected=len(old)-accepted, disjoint_acceptance_branch_counts=branch_counts,
                      original_truth_table_sha256=hashlib.sha256(old).hexdigest(),
                      candidate_truth_table_sha256=hashlib.sha256(candidate).hexdigest(),
                      elapsed_seconds=time.perf_counter()-began, python=platform.python_version()),
        named_endpoints=endpoints,
        actual_RTL_run=False, production_RTL_modified=False, physical_mapping_claim=False,
        timing_improvement_claim=False, hardware_contact=False,
        scope='Mathematical equivalence of the complete signed16 raw range acceptance and rejection predicates only.',
        limits=[
            'No production RTL candidate, Verilator model, synthesized netlist, or routed implementation was built.',
            'The observed two CARRY4s are consistent with this range check; their actual operands still need native netlist tracing.',
            'Output mode, cancellation, owner, ready/stall, packet rejection reason and cycle chronology are not modeled here.',
            'The next RTL experiment must retain those qualifiers and independently test every 16-bit pattern and real boundary packets.',
            'This prototype establishes no frame-rate, latency, resource, or physical timing improvement.',
        ],
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(status=result['status'], patterns=65536, accepted=accepted,
                          mismatches=0, output=str(OUTPUT.relative_to(ROOT)), sha256=sha(OUTPUT))))


if __name__ == '__main__':
    main()
