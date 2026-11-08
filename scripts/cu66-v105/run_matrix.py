#!/usr/bin/env python3
"""Run the frozen V105 paired regression matrix sequentially and fail closed."""
import subprocess
import sys
from pathlib import Path
from regress import LANES, ROOT


def main():
    for variant, mode in LANES:
        subprocess.run([sys.executable, str(Path(__file__).with_name('regress.py')),
                        '--variant', variant, '--mode', mode], cwd=ROOT, check=True)
    print('V105_MATRIX_PASS', len(LANES), 'lanes', flush=True)


if __name__ == '__main__':
    main()
