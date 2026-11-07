#!/usr/bin/env python3
"""Bind V99's fresh encoder unit-test command, output and frozen dependencies."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v99'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    index = json.loads((AREA/'fresh/index.json').read_text())
    measured = ROOT/index['attempt_json']
    assert sha(measured) == index['sha256']
    pins = json.loads(measured.read_text())['source_sha256']
    for path in (Path(__file__).resolve(), AREA/'encoder/test_fresh_cu66.py'):
        pins[str(path.relative_to(ROOT))] = sha(path)
    assert all(sha(ROOT/name) == digest for name, digest in pins.items())
    out = AREA/'validation'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True)
    command = [sys.executable, '-m', 'unittest', 'discover', '-s',
               'experiments/python-gamebub-v99/encoder', '-p', 'test_fresh_cu66.py', '-v']
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out/'tests.log').write_bytes(result.stdout)
    assert all(sha(ROOT/name) == digest for name, digest in pins.items())
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
