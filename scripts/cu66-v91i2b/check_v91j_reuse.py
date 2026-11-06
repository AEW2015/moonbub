#!/usr/bin/env python3
"""Check existing inverse-block constants against the current native profile."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91i2b'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    constants = ROOT / 'experiments/cu66-native-v69/generated_constants.hpp'
    rom = ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh'
    inverse = ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv'
    dequant = ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv'
    parser = ROOT / 'experiments/python-gamebub-v91/parser.py'
    old_result = ROOT / 'fpga/experiments/cu66-v69/inverse/results/results.json'
    def array(name):
        match = re.search(r'\b' + name + r'(?:\[\d+\])+=(.*?);', constants.read_text())
        assert match, name
        return json.loads(match[1].replace('{', '[').replace('}', ']'))
    tables, dct = array('QTABLES'), array('DCT')
    base = {int(index): int(value) for index, value in re.findall(
        r"7'd(\d+): base_quant=8'd(\d+);", rom.read_text())}
    assert set(base) == set(range(128))
    checks = 0
    for chroma in range(2):
        for scale in range(3):
            for pos in range(64):
                quant = base[chroma * 64 + pos]
                actual = ((quant + 1) // 2, quant, min(255, quant * 2))[scale]
                assert actual == tables[chroma][scale][pos // 8][pos % 8]
                checks += 1
    basis = {}
    for indices, sign, value in re.findall(
            r"((?:5'd\d+[, ]*)+):\s*basis=(-?)14'sd(\d+);", inverse.read_text()):
        for index in re.findall(r"5'd(\d+)", indices):
            basis[int(index)] = (-1 if sign else 1) * int(value)
    assert set(basis) == set(range(32))
    for k in range(8):
        for x in range(4):
            assert basis[k * 4 + x] == dct[k][x]
            assert (-1 if k % 2 else 1) * basis[k * 4 + x] == dct[k][7 - x]
    assert 'not -2048 <= value <= 2048' in parser.read_text()
    assert "16'sd2048" in dequant.read_text()
    historical = json.loads(old_result.read_text())
    assert historical['status'] == 'PASS' and historical['backend_cycle_agreement']
    report = dict(schema='cu66-v91j-inverse-reuse-readiness-v1', status='PASS_CONSTANT_COMPATIBILITY',
                  source_sha256={str(path.relative_to(ROOT)): sha(path) for path in
                                 (constants, rom, inverse, dequant, parser, old_result, Path(__file__).resolve())},
                  exact_quantizer_entries=checks, exact_dct_entries=64,
                  common_coefficient_profile=[-2048, 2048],
                  historical_inverse_regression='Retained V69 PASS with backend cycle agreement; not rerun by this script.',
                  scope='Source-data compatibility check only. No current-stream adapter, inverse RTL rerun, integrated residual proof, timing or hardware result.',
                  next_milestone='V91j: reuse and requalify existing inverse blocks behind bounded coefficient-tile assembly and metadata/epoch ownership; compare exact signed residuals.')
    AREA.mkdir(parents=True, exist_ok=True)
    (AREA / 'v91j-reuse-readiness.json').write_text(json.dumps(report, indent=2) + '\n')
    print('V91J_REUSE_CONSTANTS_PASS', checks, 'quantizers, 64 DCT entries; integration remains open')


if __name__ == '__main__':
    main()
