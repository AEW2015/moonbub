#!/usr/bin/env python3
"""Run the four explicitly declared V107 full-pipeline comparison lanes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from regress import LANES, OVERRIDES, ROOT


def main():
    focus = json.loads((ROOT / 'experiments/python-gamebub-v107/rice/probe-results.json').read_text())
    assert focus['status'] == 'PASS_ACTUAL_RICE_FIXED_TAP_EQUIVALENCE', 'focused actual RTL proof must pass first'
    receipt = ROOT / focus['selected_receipt']
    assert hashlib.sha256(receipt.read_bytes()).hexdigest() == focus['sha256']
    candidate = ROOT / 'fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv'
    frozen_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    for variant, mode in LANES:
        assert hashlib.sha256(candidate.read_bytes()).hexdigest() == frozen_sha
        assert OVERRIDES[variant]['fpga/experiments/cu66-v91/br88_rice_elastic.sv'] == str(candidate.relative_to(ROOT))
        subprocess.run([sys.executable, str(Path(__file__).with_name('regress.py')),
                        '--variant', variant, '--mode', mode], cwd=ROOT, check=True)
    print('V107_FOUR_LANE_MATRIX_PASS', flush=True)


if __name__ == '__main__':
    main()
