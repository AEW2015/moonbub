#!/usr/bin/env python3
"""Create or verify a bounded V129 phase/count timing factor from V128 RTL."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'fpga/experiments/cu66-v128-raw/packed_scratch_v91g2.sv'
OLD_SHA = '4254026004142414376d9b848f7b50f05d8a484b7f932b5c91d0a5a7efde92c4'
AREA = ROOT / 'fpga/experiments/cu66-v129-scratch'
NEW = AREA / OLD.name
RECIPE = AREA / 'edit-recipe.json'
ANCHOR = '    logic [2:0] phase;\n'
LANES = '''    logic [2:0] phase;
    // V129: evaluate each full-width count comparison before phase selection.
    // No stored payload, reset, enable, interface, or cycle is added.
    wire [3:0] band_count_matches;
    for(genvar count_lane=0;count_lane<4;count_lane=count_lane+1)begin: band_count_lanes
        assign band_count_matches[count_lane]=written==counts[count_lane];
    end
    wire selected_band_count_match=band_count_matches[phase[1:0]];
'''
EDITS = [
    ('four_full32_count_lanes', ANCHOR, LANES),
    ('debug_enqueue_equality', 'band_end_epoch==active_epoch && band_end_band==phase[1:0] && written==counts[phase[1:0]]',
     'band_end_epoch==active_epoch && band_end_band==phase[1:0] && selected_band_count_match'),
    ('original_error_priority_inequality', 'band_end_epoch!=active_epoch || band_end_band!=phase[1:0] || written!=counts[phase[1:0]]',
     'band_end_epoch!=active_epoch || band_end_band!=phase[1:0] || !selected_band_count_match'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    before = OLD.read_bytes()
    assert sha(before) == OLD_SHA
    after = before.decode()
    entries = []
    for tag, old, new in EDITS:
        assert after.count(old) == 1, tag
        after = after.replace(old, new, 1)
        entries.append(dict(tag=tag, old=old, new=new, occurrences=1))
    reverse = after
    for entry in reversed(entries):
        assert reverse.count(entry['new']) == 1
        reverse = reverse.replace(entry['new'], entry['old'], 1)
    assert reverse.encode() == before
    return before, after.encode(), entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    before, after, entries = build()
    record = dict(schema='v129-scratch-full32-band-count-factor-v1',
        status='SOURCE_PREPARED_NOT_RTL_QUALIFIED',
        baseline=dict(path=str(OLD.relative_to(ROOT)), sha256=sha(before)),
        candidate=dict(path=str(NEW.relative_to(ROOT)), sha256=sha(after)),
        source_alias='fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv',
        preparer=dict(path=str(Path(__file__).resolve().relative_to(ROOT)), sha256=sha(Path(__file__).read_bytes())),
        edits=entries, reverse_byte_exact=True, full_count_width=32,
        phase_width=3, phase_selection_bits=2, added_production_registers=0,
        added_public_cycles=0, synthesis_attributes_added=0,
        original_error_priority_unchanged=True, original_assertions_retained=True,
        memory_request_ack_logic_unchanged=True,
        scope='Two-state Boolean identity for all count values and phases, including invalid/unready views. Physical mapping and four-state behavior need separate evidence.')
    if args.apply:
        AREA.mkdir(parents=True, exist_ok=True)
        assert not NEW.exists() and not RECIPE.exists(), 'Refuse to overwrite candidate'
        NEW.write_bytes(after)
        RECIPE.write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
    else:
        assert NEW.read_bytes() == after
        assert json.loads(RECIPE.read_text()) == record
    print(json.dumps({'status':'PASS_SOURCE_RECONSTRUCTION_ONLY', 'candidate_sha256':sha(after),
                      'edits':len(entries), 'public_cycle_delta':0}, sort_keys=True))


if __name__ == '__main__':
    main()
