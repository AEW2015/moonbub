#!/usr/bin/env python3
"""Nine frozen V79 observer tests; synthetic outputs, no hardware fault injection."""
import datetime
import hashlib
import json
import subprocess
import tarfile
import time
import uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v81/system'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'monitor-tests' / f'attempt-{stamp}-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True, exist_ok=False)
    paths = [AREA/'monitor.hpp', AREA/'monitor_tb.cpp', Path(__file__).resolve()]
    pins = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    with tarfile.open(out/'sources.tar.gz', 'w:gz') as archive:
        for path in paths:
            archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    (out/'source-manifest.json').write_text(json.dumps(pins, indent=2)+'\n')
    commands = []
    report = dict(schema='cu81-observer-unit-v1', status='FAIL', tests=9, observer_unit_only=True, hardware_fault_injection=False, source_sha256=pins, source_snapshot_sha256=sha(out/'sources.tar.gz'), commands=commands)
    binary = '/build/v81-monitor-unit-'+uuid.uuid4().hex
    started = time.monotonic()
    try:
        for argv, name in [(['docker', 'exec', CONTAINER, 'g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror', str(AREA/'monitor_tb.cpp'), '-o', binary], 'build.log'), (['docker', 'exec', CONTAINER, binary], 'run.log')]:
            begin = time.monotonic()
            entry = dict(argv=argv, log=str((out/name).relative_to(ROOT)), exit_code=None, timed_out=False, timeout_seconds=60)
            commands.append(entry)
            try:
                with (out/name).open('w') as stream:
                    result = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, timeout=60, cwd=ROOT)
                entry['exit_code'] = result.returncode
            except subprocess.TimeoutExpired:
                entry['timed_out'] = True
            finally:
                entry.update(wall_seconds=time.monotonic()-begin, sha256=sha(out/name))
            assert entry['exit_code'] == 0 and not entry['timed_out'], f'{name} failed; retained log'
        log = (out/'run.log').read_text()
        assert 'MONITOR_UNIT_PASS tests=9 observer_unit_only=1 hardware_fault_injection=0' in log
        assert pins == {path: sha(ROOT/path) for path in pins}, 'observer sources changed during attempt'
        assert (AREA/'monitor.hpp').read_bytes() == (ROOT/'fpga/experiments/cu66-v79/system/monitor.hpp').read_bytes(), 'frozen observer changed'
        assert (AREA/'monitor_tb.cpp').read_bytes() == (ROOT/'fpga/experiments/cu66-v79/system/monitor_tb.cpp').read_bytes(), 'frozen observer proof changed'
        report['status'] = 'PASS'
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        begin = time.monotonic()
        cleanup = ['docker', 'exec', CONTAINER, 'rm', '-f', binary]
        entry = dict(argv=cleanup, log=str((out/'cleanup.log').relative_to(ROOT)), exit_code=None, timed_out=False, timeout_seconds=30)
        commands.append(entry)
        try:
            with (out/'cleanup.log').open('w') as stream:
                result = subprocess.run(cleanup, stdout=stream, stderr=subprocess.STDOUT, timeout=30, cwd=ROOT)
            entry['exit_code'] = result.returncode
        except Exception as error:
            entry['failure'] = str(error)
            entry['timed_out'] = isinstance(error, subprocess.TimeoutExpired)
        entry.update(wall_seconds=time.monotonic()-begin, sha256=sha(out/'cleanup.log'))
        report['wall_seconds'] = time.monotonic()-started
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(dict(status='V81_MONITOR_UNIT_PASS' if report['status'] == 'PASS' else 'V81_MONITOR_UNIT_FAIL', tests=9, observer_unit_only=1, hardware_fault_injection=0, results_path=str(out/'results.json'))), flush=True)


if __name__ == '__main__':
    main()
