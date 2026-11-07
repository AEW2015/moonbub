#!/usr/bin/env python3
"""Independently audit a Yosys 0.33 shift-parameter compatibility delta.

The complete RTLIL text must stay identical except B_SIGNED 1 -> 0 inside
$shl/$shr/$sshl/$sshr cells. Names, modules, other parameters, connections,
processes and provenance must match byte-for-byte. This is not an RTL rewrite.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

SHIFT = {'$shl', '$shr', '$sshl', '$sshr'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(before, after):
    left = before.read_text().splitlines(keepends=True)
    right = after.read_text().splitlines(keepends=True)
    if len(left) != len(right):
        raise ValueError('IR line count changed')
    module = None
    cell = None
    kind = None
    inventory = []
    changed = []
    for number, (old, new) in enumerate(zip(left, right), 1):
        if old.startswith('module '):
            module = old.split()[1]
        match = re.match(r'  cell (\S+) (\S+)\s*$', old)
        if match:
            kind, cell = match.groups()
        if old.startswith('  end'):
            kind = cell = None
        parameter = re.match(r'    parameter \\B_SIGNED ([01])\s*$', old)
        if parameter and kind in SHIFT:
            entry = dict(module=module, cell=cell, type=kind, before=int(parameter[1]), after=0, line=number)
            inventory.append(entry)
            expected = old.replace('\\B_SIGNED 1', '\\B_SIGNED 0')
            if new != expected:
                raise ValueError('shift B_SIGNED normalization mismatch at line ' + str(number))
        if old != new:
            if not parameter or kind not in SHIFT or parameter[1] != '1' or new != old.replace('\\B_SIGNED 1', '\\B_SIGNED 0'):
                raise ValueError('unauthorized IR change at line ' + str(number))
            changed.append(entry)
    return dict(schema='v100-yosys033-shift-ir-delta-audit-v1', status='PASS_ONLY_SHIFT_B_SIGNED_1_TO_0',
                before_sha256=sha(before), after_sha256=sha(after), auditor_sha256=sha(Path(__file__)),
                complete_text_line_count=len(left), shift_cells=inventory, changed_cells=changed,
                changed_count=len(changed), all_other_text_byte_identical=True,
                semantic_basis='Pinned installed simlib.v models for these four shift types ignore B_SIGNED; B port is unsigned. A_SIGNED and all bit connections are unchanged.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.before, args.after)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(status=result['status'], changed_cells=result['changed_count'])))


if __name__ == '__main__':
    main()
