#!/usr/bin/env python3
"""Finite independent algebra checks for the V129 Rice response candidates."""
import argparse
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
MASK32 = (1 << 32) - 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    rng = random.Random(12901)
    # The high field is a 27-bit partition. If nonzero, unsigned remaining is
    # at least 32 while any 5-bit suffix is at most 31, so both predicates are
    # false for *all* 2**27-1 nonzero high values. Enumerate every low-field
    # value and suffix in the zero-high partition; sample explicit high-bit
    # boundaries and random full-width values as regression witnesses.
    values = list(range(32)) + [32, 33, 63, 64, 0x7fffffff, 0x80000000,
                                 0xffffffe0, 0xfffffff0, 0xffffffff]
    values += [rng.getrandbits(32) for _ in range(32768)]
    comparisons = 0
    for remaining in values:
        for suffix in range(32):
            old = remaining < suffix
            decomposed = (remaining >> 5) == 0 and (remaining & 31) < suffix
            assert old == decomposed, (remaining, suffix)
            comparisons += 1
    prefix_cases = suffix_cases = wraps = 0
    for serial in (0, 1):
        for found in (0, 1):
            for window in range(64):
                for rank in range(16):
                    old_take = 1 if serial else ((rank + 1) if found else window)
                    new_take = 1 if serial else ((rank + 1) if found else window)
                    assert old_take == new_take and 0 <= new_take < 64
                    for consumed in (0,1,31,0xffffffc0,0xfffffff0,0xffffffff,rng.getrandbits(32)):
                        old = (consumed + old_take) & MASK32
                        new = (consumed + new_take) & MASK32
                        assert old == new
                        wraps += consumed + old_take > MASK32
                        prefix_cases += 1
        for suffix in range(32):
            old_take = 1 if serial and suffix != 0 else suffix
            new_take = 1 if serial and suffix != 0 else suffix
            for consumed in (0,1,31,0xffffffc0,0xfffffff0,0xffffffff,rng.getrandbits(32)):
                assert ((consumed + old_take) & MASK32) == ((consumed + new_take) & MASK32)
                suffix_cases += 1
    obj = dict(schema='v129-parser-response-algebra-v1',status='PASS_MODEL_ONLY',seed=12901,
               suffix_predicate_comparisons=comparisons,zero_high_exhaustive_pairs=32*32,
               nonzero_high_partition_argument='remaining >= 32 > suffix for all nonzero high fields',
               random_fullwidth_values=32768,prefix_response_addition_cases=prefix_cases,
               suffix_response_addition_cases=suffix_cases,wrapping_prefix_additions=wraps,
               mismatches=0,actual_RTL_run=False,sequential_behavior_modeled=False,
               physical_timing_measured=False,exhaustive_full32_simulation=False,
               candidate_sha256=hashlib.sha256((HERE/'br88_rice_elastic.sv').read_bytes()).hexdigest())
    if a.output:
        assert not a.output.exists()
        a.output.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    print(json.dumps(obj,sort_keys=True))


if __name__ == '__main__':
    main()
