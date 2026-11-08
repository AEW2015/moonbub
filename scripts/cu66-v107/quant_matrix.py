#!/usr/bin/env python3
"""Integrate the independently checked Rice, quant prefetch and exact range test."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from quant_regress import LANES, ROOT


def main():
    for name, status in [('quant', 'PASS'), ('value-check', 'PASS_EXACT_RANGE_RECODE')]:
        result = json.loads((ROOT / 'experiments/python-gamebub-v107' / name / 'results.json').read_text())
        assert result['status'] == status
        for source, digest in result['source_sha256'].items():
            assert hashlib.sha256((ROOT / source).read_bytes()).hexdigest() == digest, source
    for variant, mode in LANES:
        subprocess.run([sys.executable, str(Path(__file__).with_name('quant_regress.py')),
                        '--variant', variant, '--mode', mode], cwd=ROOT, check=True)
    print('V107_QUANT_PAIR_PASS', flush=True)


if __name__ == '__main__':
    main()
