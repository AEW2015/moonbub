#!/usr/bin/env python3
"""Project the suffix temporary to its consumed24 bits without a lint waiver."""
import argparse
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[2]
FPGA = ROOT / 'fpga/experiments/cu66-v106-suffix24'
AREA = ROOT / 'experiments/python-gamebub-v106/suffix24'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    FPGA.mkdir(exist_ok=True)
    AREA.mkdir(exist_ok=True)
    old = ROOT / 'fpga/experiments/cu66-v106-suffix/br88_rice_elastic.sv'
    new = FPGA / old.name
    original = old.read_text()
    edits = [dict(name='consumed_width_only', before='    logic [63:0] suffix_extracted;',
                  after='    logic [23:0] suffix_extracted;', expected_occurrences=1),
             dict(name='explicit_projection_at_shift_result',
                  before="        suffix_extracted=suffix_take_bits==0 ? 64'd0 : reservoir >> (available-7'(suffix_take_bits));",
                  after="        suffix_extracted=suffix_take_bits==0 ? 24'd0 : 24'(reservoir >> (available-7'(suffix_take_bits)));",
                  expected_occurrences=1)]
    candidate = original
    for edit in edits:
        assert candidate.count(edit['before']) == 1
        candidate = candidate.replace(edit['before'], edit['after'], 1)
    assert candidate[:candidate.index(');') + 2] == original[:original.index(');') + 2]
    # The only functional consumers already project to24 bits. No clocked
    # statement, public field, guard or arithmetic input domain is changed.
    uses = [s.strip() for s in original.splitlines() if 'suffix_extracted' in s]
    assert len(uses) == 3 and uses[-1] == "suffix_value=serial ? ((suffix_acc<<1) | 24'(suffix_extracted)) : 24'(suffix_extracted);"
    recipe = dict(schema='v106-edit-recipe-v1', variant='suffix24', original_path=str(old.relative_to(ROOT)),
                  original_sha256=sha(old), candidate_path=str(new.relative_to(ROOT)),
                  candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(), edits=edits)
    recipe_path = FPGA / 'edit-recipe.json'
    encoded = json.dumps(recipe, indent=2, sort_keys=True) + '\n'
    if args.verify:
        assert new.read_text() == candidate and recipe_path.read_text() == encoded
    else:
        assert not new.exists() and not recipe_path.exists(), 'Use --verify for frozen files'
        new.write_text(candidate)
        recipe_path.write_text(encoded)
    mask = (1 << 24) - 1
    digest = hashlib.sha256()

    def check(reservoir, available, take, accum, serial):
        shift = (available - take) & 127
        before64 = 0 if take == 0 or shift >= 64 else reservoir >> shift
        after24 = 0 if take == 0 or shift >= 64 else (reservoir >> shift) & mask
        old_value = ((accum << 1) | (before64 & mask)) & mask if serial else before64 & mask
        new_value = ((accum << 1) | after24) & mask if serial else after24
        assert old_value == new_value
        digest.update(f'{reservoir}\t{available}\t{take}\t{accum}\t{serial}\t{new_value}\n'.encode())

    patterns = (0, (1 << 64) - 1, 0xaaaaaaaaaaaaaaaa, 1 << 63)
    count = 0
    for available in range(128):
        for take in range(64):
            for reservoir in patterns:
                for accum in (0, mask, 0x555555):
                    for serial in range(2):
                        check(reservoir, available, take, accum, serial)
                        count += 1
    rng = random.Random(1062401)
    for _ in range(100000):
        check(rng.getrandbits(64), rng.randrange(128), rng.randrange(64), rng.getrandbits(24), rng.randrange(2))
    result = dict(schema='v106-suffix24-projection-model-v1', status='PASS_EXACT_PROJECTION_AND_RECIPES',
        generator=pin(Path(__file__)), original=pin(old), candidate=pin(new), recipe=pin(recipe_path),
        original_all_consumers=uses, exhaustive_boundary_pattern_cases=count, full_width_random_cases=100000,
        transcript_sha256=digest.hexdigest(), actual_RTL_run=False, integrated_RTL_required=True,
        identity='lo24(take==0?0:(reservoir >> ((available-take) mod128))) equals the explicit24-bit shift-result projection for every64-bit reservoir and every7-bit available/6-bit take, including shifts>=64. Existing serial accumulation already consumes onlylo24.',
        motivation='Rejected fifth candidate has unused suffix_extracted[63:24] in strict full-production lint; focused wrapper exports masked that warning. Reject the candidate, retain failure, use exact private projection rather than suppressing lint.',
        limits=['Algebra/source proof plus deterministic pattern/random checks, not standalone clocked parser or four-state proof.',
                'Full-production strict lint and paired pipeline RTL must pass for the replacement before selection.'])
    p = AREA / 'results.json'
    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.verify:
        assert p.read_text() == text
    else:
        p.write_text(text)
    print('V106_SUFFIX24_PROJECTION_PASS', count + 100000, 'cases; full pipeline RTL required')


if __name__ == '__main__':
    main()
