#!/usr/bin/env python3
"""Retain exact bounded unit-test commands, output and source pins."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v98'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = AREA/'validation'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True)
    paths = [Path(__file__).resolve(), *AREA.glob('*.py')]
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    command = [sys.executable, '-m', 'unittest', 'discover', '-s',
               'experiments/python-gamebub-v98', '-p', 'test*.py', '-v']
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out/'tests.log').write_bytes(result.stdout)
    assert pins == {str(p.relative_to(ROOT)): sha(p) for p in paths}
    receipt = {'status': 'PASS' if result.returncode == 0 else 'FAIL', 'command': command,
               'returncode': result.returncode, 'source_sha256': pins,
               'artifacts_sha256': {'tests.log': sha(out/'tests.log')}}
    path = out/'receipt.json'
    path.write_text(json.dumps(receipt, indent=2)+'\n')
    if result.returncode == 0:
        (AREA/'validation/index.json').write_text(json.dumps({
            'receipt': str(path.relative_to(ROOT)), 'sha256': sha(path)}, indent=2)+'\n')
    print(receipt['status'], path.relative_to(ROOT))
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
