#!/usr/bin/env python3
"""Resume unchanged frozen lanes; retain and retry only host-gate denials."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v106'


def module(name):
    path = ROOT / 'scripts/cu66-v106' / name / 'regress.py'
    spec = importlib.util.spec_from_file_location('v106_resume_' + name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value, path


def log(value):
    value['time'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (AREA / 'coordination.jsonl').open('a') as stream:
        stream.write(json.dumps(value, sort_keys=True) + '\n')
    print('V106_RESUME', json.dumps(value, sort_keys=True), flush=True)


def already_passed(path, variant, mode, runner):
    if not path.exists():
        return False
    result = json.loads(path.read_text())
    if result['status'] != 'PASS':
        return False
    assert result['variant'] == variant and result['mode'] == mode
    assert result['baseline_revision'] == runner.BASELINE
    assert result['baseline_overrides'] == runner.BASELINE_OVERRIDES
    expected = {k: v for k, v in runner.OVERRIDES[variant].items()}
    assert {row['original']: row['path'] for row in result['candidates']} == expected
    for name, digest in result['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    selected = json.loads((ROOT / result['selected_report']).read_text())
    assert {k: v for k, v in result.items() if k != 'selected_report'} == selected
    return True


def stable_gate(runner):
    deadline, consecutive = time.monotonic() + 180, 0
    while time.monotonic() < deadline:
        try:
            runner.resources()
            consecutive += 1
            if consecutive == 2:
                return
        except RuntimeError as error:
            if not str(error).startswith('resource gate:'):
                raise
            consecutive = 0
        time.sleep(5)
    raise RuntimeError('host gate did not stabilize within 180 seconds')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner', nargs='+', choices=('followup', 'final'), default=['followup', 'final'])
    args = parser.parse_args()
    for name in args.runner:
        runner, source = module(name)
        for variant, mode in runner.LANES:
            path = AREA / 'regression' / variant / mode / 'results.json'
            if already_passed(path, variant, mode, runner):
                log(dict(action='skip hash-current PASS lane', runner=name, variant=variant, mode=mode))
                continue
            for retry in range(3):
                stable_gate(runner)
                log(dict(action='run unchanged lane', runner=name, variant=variant, mode=mode, retry=retry))
                result = subprocess.run([sys.executable, str(source), '--variant', variant, '--mode', mode], cwd=ROOT)
                if result.returncode == 0:
                    assert already_passed(path, variant, mode, runner)
                    break
                report = json.loads(path.read_text())
                error = report.get('error', report.get('failure', ''))
                # Only the exact inherited resource guard is retryable. Any
                # compile, simulation, assertion or transcript mismatch stops.
                if not isinstance(error, str) or 'resource gate:' not in error:
                    raise RuntimeError(('lane failed; no automatic functional retry', variant, mode, error))
                log(dict(action='retained resource-gated attempt', runner=name, variant=variant, mode=mode,
                         retry=retry, error=error))
            else:
                raise RuntimeError(('three resource-gated attempts; stopping', variant, mode))
    print('V106_RESUMED_MATRIX_PASS', flush=True)


if __name__ == '__main__':
    main()
