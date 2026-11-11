#!/usr/bin/env python3
"""Create or check source-bound paired scratch and count-factor fixtures."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v129-scratch'
V = AREA / 'verification'
OLD = ROOT / 'fpga/experiments/cu66-v128-raw/packed_scratch_v91g2.sv'
NEW = AREA / 'packed_scratch_v91g2.sv'
OLD_TOP = ROOT / 'fpga/experiments/cu66-v128-raw/verification/raw_probe.sv'
OLD_SCALAR = ROOT / 'fpga/experiments/cu66-v128-raw/verification/v128_raw_scalar_probe.sv'
OLD_CPP = ROOT / 'fpga/experiments/cu66-v128-raw/verification/tb_raw.cpp'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(p):
    return dict(path=str(p.relative_to(ROOT)), sha256=sha(p.read_bytes()))


def files():
    old = OLD.read_text()
    assert old.count('module packed_scratch_v91g2 (') == 1
    baseline = old.replace('module packed_scratch_v91g2 (', 'module v128_scratch_baseline (', 1)
    top = OLD_TOP.read_text()
    start = top.index('    packed_scratch_v91g2 candidate (')
    prior, candidate = top[:start], top[start:]
    marker = '        .debug_head_valid(b_debug_head_valid)\n    );'
    assert prior.count(marker) == 1
    ports = '''        .debug_head_valid(b_debug_head_valid),
        .coef_select_raw(coef_select_raw),
        .coef_raw_epoch(coef_raw_epoch),
        .coef_raw_block(coef_raw_block),
        .coef_raw_index(coef_raw_index),
        .coef_raw_value(coef_raw_value),
        .coef_raw_band(coef_raw_band),
        .coef_context_epoch(coef_context_epoch),
        .coef_context_block(coef_context_block),
        .coef_context_index(coef_context_index),
        .coef_context_value(coef_context_value),
        .coef_context_band(coef_context_band)
    );'''
    top = prior.replace(marker, ports, 1) + candidate
    predicate = 'pair_predicate_equal=(baseline.input_bad==candidate.input_bad)'
    assert top.count(predicate) == 1
    top = top.replace(predicate,
        'pair_predicate_equal=(candidate.selected_band_count_match==(baseline.written==baseline.counts[baseline.phase[1:0]])) && (baseline.input_bad==candidate.input_bad)', 1)
    text = NEW.read_text()
    first = text.index('    // V129: evaluate each full-width count comparison')
    last = text.index('    logic [127:0] assembler;', first)
    fragment = text[first:last]
    assert fragment.count('wire selected_band_count_match=band_count_matches[phase[1:0]];') == 1
    probe = '''module count_factor_probe (
    input logic [31:0] written,
    input logic [31:0] counts [0:3],
    input logic [2:0] phase,
    output logic old_equal, new_equal
);
''' + fragment + '''    assign old_equal=written==counts[phase[1:0]];
    assign new_equal=selected_band_count_match;
endmodule
'''
    output = {'v128_scratch_baseline.sv': baseline, 'raw_probe.sv': top,
              'v128_raw_scalar_probe.sv': OLD_SCALAR.read_text(),
              'tb_raw.cpp': OLD_CPP.read_text(), 'count_factor_probe.sv': probe}
    return output, fragment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    a = parser.parse_args()
    output, fragment = files()
    if a.write:
        assert not V.exists(), 'Refuse to overwrite verification fixtures'
        V.mkdir(parents=True)
        for name, data in output.items():
            (V/name).write_text(data)
    for name, data in output.items():
        assert (V/name).read_text() == data, name
    print(json.dumps(dict(status='PASS_PREPARED_NOT_RTL_EXECUTED', baseline=pin(OLD), candidate=pin(NEW),
        original_top=pin(OLD_TOP), original_bench=pin(OLD_CPP), original_scalar=pin(OLD_SCALAR),
        files={str((V/name).relative_to(ROOT)):sha(data.encode()) for name,data in output.items()},
        fragment_sha256=sha(fragment.encode()), baseline_module_rename_only=True,
        original_bench_unchanged=True, original_assertions_retained=True,
        prepared_state_forces=0, actual_RTL_run=False),sort_keys=True))


if __name__ == '__main__':
    main()
