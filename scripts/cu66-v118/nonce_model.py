#!/usr/bin/env python3
"""Exact arithmetic prototype for the actual32-bit producer nonce budget.

Preparation is read-only. Root dispatches --run inside its bounded job cgroup.
This models arithmetic and entropy error priority, not RTL timing or owner life.
"""
import argparse
import datetime
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'fpga/experiments/cu66-v110-ready/cs88_coefficients_v91k.sv'
SOURCE_SHA = 'b5f9dce886ce9d6d1460ac6d8579512750bc66504e306ecabf8bdd7f11bb40fd'
AREA = ROOT/'experiments/python-gamebub-v118/nonce-model'
MASK32 = (1 << 32)-1
MASK64 = (1 << 64)-1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def source_contract():
    assert sha(SOURCE) == SOURCE_SHA
    text = SOURCE.read_text()
    assert 'logic [31:0] last_frame_epoch=0, child_nonce=0;' in text
    first = text.index('                    CHECK_ENTROPY:begin')
    last = text.index('                    PREP_PLANE:begin', first)
    branch = text[first:last]
    assert "{32'd0,child_nonce}+64'(fork_blocks[0]!=0)+64'(fork_blocks[1]!=0)+64'(fork_blocks[2]!=0)>64'hffffffff" in branch
    assert branch.index('error<=64') < branch.index('error<=66')
    assert '(fork_blocks[0]!=0&&fork_entropy[0]!=2)||(fork_blocks[1]!=0&&fork_entropy[1]!=2)||(fork_blocks[2]!=0&&fork_entropy[2]!=2)' in branch
    return dict(path=str(SOURCE.relative_to(ROOT)), sha256=SOURCE_SHA,
                first_line=text[:first].count('\n')+1, branch=branch,
                input_domain=dict(child_nonce_bits=32, arithmetic_extension_bits=64,
                                  planes=3, nonzero_plane_count_min=0, nonzero_plane_count_max=3,
                                  block_count_bits=32, entropy_bits=2))


def source_overflow32(nonce, blocks):
    """Literal widened source expression; all inputs retain their full width."""
    assert 0 <= nonce <= MASK32 and len(blocks) == 3
    assert all(0 <= value <= MASK32 for value in blocks)
    widened = (nonce + int(blocks[0] != 0) + int(blocks[1] != 0) + int(blocks[2] != 0)) & MASK64
    return widened > MASK32


def candidate_overflow(nonce, count, width=32):
    """Upper(width-2) equality and one three-bit low/count addition."""
    assert 2 <= width <= 32 and 0 <= nonce < (1 << width) and 0 <= count <= 3
    return (nonce >> 2) == ((1 << (width-2))-1) and ((nonce & 3)+count) > 3


def source_error(nonce, blocks, entropy):
    if ((blocks[0] != 0 and entropy[0] != 2) or
            (blocks[1] != 0 and entropy[1] != 2) or
            (blocks[2] != 0 and entropy[2] != 2)):
        return 64
    if source_overflow32(nonce, blocks):
        return 66
    return 0


def candidate_error(nonce, blocks, entropy):
    nonzero = (int(blocks[0] != 0) | (int(blocks[1] != 0) << 1) |
               (int(blocks[2] != 0) << 2))
    entropy_bad_mask = (int(entropy[0] != 2) | (int(entropy[1] != 2) << 1) |
                        (int(entropy[2] != 2) << 2))
    if nonzero & entropy_bad_mask:
        return 64
    if candidate_overflow(nonce, nonzero.bit_count()):
        return 66
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--root-grant')
    ap.add_argument('--random-cases-per-seed', type=int, default=250000)
    args = ap.parse_args()
    contract = source_contract()
    assert args.random_cases_per_seed >= 10000
    if not args.run:
        print('V118_NONCE_ARITHMETIC_PREPARED_NOT_RUN', SOURCE_SHA)
        return
    assert args.root_grant, 'Root bounded-job grant required'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/stamp
    out.mkdir(parents=True)
    report = dict(schema='v118-source32-nonce-budget-arithmetic-prototype-v1', status='RUNNING',
                  actual_Python_model_run=False, actual_RTL_run=False,
                  root_grant=args.root_grant, source_contract=contract,
                  source_sha256={str(SOURCE.relative_to(ROOT)): sha(SOURCE),
                                 str(Path(__file__).resolve().relative_to(ROOT)): sha(Path(__file__))},
                  analytic_argument=[
                      'The source has exactly three Boolean nonzero-plane terms, so count is in0..3 regardless of the full32-bit block count magnitudes.',
                      'For any32-bit x, write x=4h+l with l in0..3 and h in0..2^30-1.',
                      'If h<2^30-1 then x<=2^32-5, hence x+count<=2^32-2 and no overflow can occur.',
                      'If h=2^30-1 then x=2^32-4+l, so x+count>2^32-1 exactly when l+count>3.',
                      'The widened source sum is at most2^32+2, below2^64; its64-bit arithmetic cannot itself wrap in this domain.'
                  ],
                  assumptions=['Unsigned32-bit child nonce and three full32-bit block count inputs.',
                               'Entropy values are two-bit inputs; a nonzero plane requires entropy2.',
                               'Combinational arithmetic model only; no receipt-stage ownership or temporal state modeled.'],
                  scope_limits=['No RTL edit, FPGA synthesis, placement, route, frequency or timing-improvement claim.',
                                'Does not map the observed eight CARRY4 cells to this source branch.',
                                'Does not validate nonce anti-replay lifetime, warm-reset behavior, child allocation or physical drain.',
                                'Does not prove arbitrary private state reachability or host/ESP32/FPGA throughput.'],
                  checks={}, witnesses=[], failures=[])
    write(out/'receipt.json', report)
    start = time.monotonic()
    try:
        report['actual_Python_model_run'] = True
        write(out/'receipt.json', report)
        def check_nonce(nonce, count, label):
            blocks = (1 if count >= 1 else 0, MASK32 if count >= 2 else 0,
                      0x80000000 if count >= 3 else 0)
            expected = source_overflow32(nonce, blocks)
            actual = candidate_overflow(nonce, count)
            assert expected == actual, (label, nonce, count, expected, actual)
            return int(expected)
        # All low/count combinations for representative upper classes. The
        # analytic argument above covers every unenumerated upper value.
        upper_classes = (0, 1, (1 << 29)-1, (1 << 30)-2, (1 << 30)-1)
        abstract_cases = abstract_overflows = 0
        for high, low, count in itertools.product(upper_classes, range(4), range(4)):
            abstract_overflows += check_nonce((high << 2) | low, count, 'upperclass')
            abstract_cases += 1
        report['checks']['upper_classes'] = dict(cases=abstract_cases, overflow_cases=abstract_overflows,
                                                upper_values=list(upper_classes), low_values=4, counts=4)
        # Exhaustive reduced-width analogues retain the exact carry structure.
        bounded = []
        for width in range(2, 17):
            cases = overflows = 0
            limit = (1 << width)-1
            for nonce in range(1 << width):
                for count in range(4):
                    widened = nonce+count > limit
                    actual = candidate_overflow(nonce, count, width)
                    assert widened == actual, ('bounded', width, nonce, count)
                    cases += 1
                    overflows += int(widened)
            bounded.append(dict(width=width, cases=cases, overflow_cases=overflows))
        report['checks']['bounded_widths'] = bounded
        endpoints = sorted(set(range(8)) | set(range(MASK32-7, MASK32+1)) |
                           {0x7ffffffe, 0x7fffffff, 0x80000000, 0x80000001})
        overflow_count = 0
        for nonce, count in itertools.product(endpoints, range(4)):
            overflow_count += check_nonce(nonce, count, 'endpoint')
        report['checks']['full32_endpoints'] = dict(cases=len(endpoints)*4,
                                                  overflow_cases=overflow_count, nonces=endpoints)
        for nonce in range(MASK32-3, MASK32+1):
            for count in range(4):
                report['witnesses'].append(dict(nonce=nonce, count=count,
                                                overflow=bool(check_nonce(nonce, count, 'witness'))))
        random_rows = []
        for seed in (118661, 118662):
            rng = random.Random(seed)
            overflow_count = 0
            for i in range(args.random_cases_per_seed):
                nonce = MASK32-rng.randrange(8) if i % 16 == 0 else rng.getrandbits(32)
                overflow_count += check_nonce(nonce, rng.randrange(4), 'random')
            random_rows.append(dict(seed=seed, cases=args.random_cases_per_seed,
                                    endpoint_bias_every=16, overflow_cases=overflow_count))
        report['checks']['seeded_full32'] = random_rows
        # Complete mask/entropy matrix, with four distinct full-width nonzero
        # values and both safe and overflowing nonce neighborhoods.
        priority_counts = dict(cases=0, entropy_reject64=0, nonce_reject66=0, accept0=0,
                               entropy_and_nonce_bad_priority64=0, zero_plane_bad_entropy_ignored=0)
        nonce_boundary = tuple(range(MASK32-3, MASK32+1))+(0, 1)
        for mask, nonzero_value, entropy, nonce in itertools.product(
                range(8), (1, MASK32, 0x80000000, 0x01234567),
                itertools.product(range(4), repeat=3), nonce_boundary):
            blocks = tuple(nonzero_value if mask & (1 << i) else 0 for i in range(3))
            old, new = source_error(nonce, blocks, entropy), candidate_error(nonce, blocks, entropy)
            assert old == new, ('priority', nonce, blocks, entropy, old, new)
            priority_counts['cases'] += 1
            priority_counts[{0:'accept0', 64:'entropy_reject64', 66:'nonce_reject66'}[old]] += 1
            bad_entropy = any(blocks[i] != 0 and entropy[i] != 2 for i in range(3))
            if bad_entropy and source_overflow32(nonce, blocks):
                assert new == 64
                priority_counts['entropy_and_nonce_bad_priority64'] += 1
            if any(blocks[i] == 0 and entropy[i] != 2 for i in range(3)) and not bad_entropy:
                assert new in (0, 66)
                priority_counts['zero_plane_bad_entropy_ignored'] += 1
        assert priority_counts['entropy_and_nonce_bad_priority64'] > 0
        assert priority_counts['zero_plane_bad_entropy_ignored'] > 0
        report['checks']['entropy_nonce_priority'] = priority_counts
        assert report['source_sha256'] == {name:sha(ROOT/name) for name in report['source_sha256']}
        report['status'] = 'PASS_PYTHON_ARITHMETIC_ONLY'
    except BaseException as error:
        report['status'] = 'FAIL'
        report['failures'].append(repr(error))
        raise
    finally:
        report['wall_seconds'] = time.monotonic()-start
        write(out/'receipt.json', report)
        write(AREA/'results.json', dict(status=report['status'], actual_Python_model_run=report['actual_Python_model_run'],
                                       actual_RTL_run=False, path=str((out/'receipt.json').relative_to(ROOT)),
                                       sha256=sha(out/'receipt.json')))
        print('V118_NONCE_ARITHMETIC', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
