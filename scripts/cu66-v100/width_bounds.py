#!/usr/bin/env python3
"""Derive conservative V101 width hypotheses from the frozen IDCT constants.

This is a static integer bound, not an RTL implementation or performance test.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv'
constants = {}
for match in re.finditer(r"((?:5'd\d+\s*,?\s*)+):\s*basis=(-?)14'sd(\d+)", SOURCE.read_text()):
    for index in re.findall(r"5'd(\d+)", match[1]):
        constants[int(index)] = int(match[3]) * (-1 if match[2] else 1)
assert set(constants) == set(range(32)), 'basis parser requires all frozen entries'
column_sums = [sum(abs(constants[k * 4 + x]) for k in range(8)) for x in range(4)]
norm = max(column_sums)
first = (522240 * norm + 8192) // 16384
second = (first * norm + 8192) // 16384
assert (norm, first, second) == (43284, 1379678, 3644896)
assert first < 2**21 and first * norm + 8192 < 2**36
result = {
    'schema': 'v100-next-width-bounds-v1', 'status': 'PASS_STATIC_INTEGER_BOUNDS_ONLY',
    'source': str(SOURCE.relative_to(ROOT)),
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'basis_entries': len(constants), 'column_abs_sums': column_sums,
    'max_legal_abs_input': 522240, 'max_first_pass_abs': first,
    'max_second_pass_abs': second, 'max_first_unrounded_abs': 522240 * norm,
    'max_second_unrounded_abs': first * norm,
    'proposed_signed_intermediate_bits': 22, 'proposed_signed_product_bits': 36,
    'proposed_signed_accumulator_bits': 37,
    'limits': 'Static whole-column bound only. No RTL width change, cycle gain, inference or timing qualification.'}
output = ROOT / 'experiments/python-gamebub-v100/width-bounds.json'
output.write_text(json.dumps(result, indent=2) + '\n')
print(result['status'], 'first_pass_abs=', first, 'second_pass_abs=', second)
