#!/usr/bin/env python3
"""Create or verify a reversible V129 parser timing experiment."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ORIGINAL = ROOT / 'fpga/experiments/cu66-v116-rice/br88_rice_elastic.sv'
CANDIDATE = HERE / 'br88_rice_elastic.sv'
ORIGINAL_SHA = 'c118357680db9825786d8b78fd7222abb24f7bf2039f6174c61c6ed2edd7e4b9'
EDITS = [
    ('    logic [5:0] suffix_take_bits;\n',
     '    logic [5:0] suffix_take_bits;\n'
     '    // Independent existing-edge response candidates; no new state.\n'
     '    logic [5:0] prefix_response_take;\n'
     '    logic [31:0] prefix_response_consumed, suffix_response_consumed;\n'
     '    logic suffix_response_truncated;\n'),
    ("        suffix_take_bits=serial && suffix_left!=0 ? 6'd1 : 6'(suffix_left);\n",
     "        suffix_take_bits=serial && suffix_left!=0 ? 6'd1 : 6'(suffix_left);\n"
     "        prefix_response_take=serial ? 6'd1 :\n"
     "            (found_one ? 6'(prefix_rank)+6'd1 : window);\n"
     "        prefix_response_consumed=consumed+32'(prefix_response_take);\n"
     "        suffix_response_consumed=consumed+32'(suffix_take_bits);\n"
     "        suffix_response_truncated=!(|remaining[31:5]) && remaining[4:0]<suffix_left;\n"),
    ("                        output_zero<=1; out_consumed<=consumed+32'(take_bits); state<=RESPONSE;\n",
     "                        output_zero<=1; out_consumed<=prefix_response_consumed; state<=RESPONSE;\n"),
    ("                if (remaining<32'(suffix_left)) respond_error(TRUNCATED);\n",
     "                if (suffix_response_truncated) respond_error(TRUNCATED);\n"),
    ("                        out_consumed<=consumed+32'(take_bits); state<=RESPONSE;\n",
     "                        out_consumed<=suffix_response_consumed; state<=RESPONSE;\n"),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build():
    before = ORIGINAL.read_text()
    assert digest(before.encode()) == ORIGINAL_SHA
    result = before
    for old, new in EDITS:
        assert result.count(old) == 1, (old, result.count(old))
        result = result.replace(old, new, 1)
    restored = result
    for old, new in reversed(EDITS):
        assert restored.count(new) == 1
        restored = restored.replace(new, old, 1)
    assert restored == before
    guards = re.findall(r'`ifndef SYNTHESIS\n.*?`endif', before, re.S)
    assert all(block in result for block in guards)
    assert re.findall(r'\(\*.*?\*\)', before, re.S) == re.findall(r'\(\*.*?\*\)', result, re.S)
    assert result.count('always_ff') == before.count('always_ff')
    return before, result, len(guards)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    before, result, guards = build()
    record = dict(schema='v129-rice-response-split-recipe-v1',
                  status='CANDIDATE_PREPARED_NOT_QUALIFIED',
                  original=dict(path=str(ORIGINAL.relative_to(ROOT)), sha256=ORIGINAL_SHA),
                  candidate=dict(path=str(CANDIDATE.relative_to(ROOT)), sha256=digest(result.encode())),
                  alias='fpga/experiments/cu66-v91/br88_rice_elastic.sv',
                  prepare_sha256=digest(Path(__file__).read_bytes()),
                  edits=[dict(before=old, after=new, count=1) for old,new in EDITS],
                  reverse_reconstruction_exact=True, retained_guard_blocks=guards,
                  original_guard_blocks_unchanged=True, new_public_cycles=0,
                  new_state_bits=0, added_attributes=0, functional_or_timing_qualified=False,
                  scope='Source-level response-path duplication and full32-preserving suffix comparison; physical sharing and timing require measurement.')
    if args.write:
        assert not CANDIDATE.exists() and not (HERE/'edit-recipe.json').exists()
        CANDIDATE.write_text(result)
        (HERE/'edit-recipe.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    else:
        assert CANDIDATE.read_text()==result
        assert json.loads((HERE/'edit-recipe.json').read_text())==record
    print(json.dumps(dict(status='PASS_SOURCE_RECONSTRUCTION_NOT_RTL', candidate_sha256=record['candidate']['sha256'], retained_guard_blocks=guards, edits=len(EDITS))))


if __name__ == '__main__':
    main()
