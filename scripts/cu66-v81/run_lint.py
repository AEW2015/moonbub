#!/usr/bin/env python3
"""Strict behavioral Verilator lint with immutable source/log evidence."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v81/system'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec_path = AREA / 'sources.json'
    spec = json.loads(spec_path.read_text())
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'lint-attempts' / f'attempt-{stamp}-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True)
    paths = [ROOT / p for p in spec['rtl_sources']] + [spec_path, Path(__file__).resolve()]
    for folder in spec['include_dirs']:
        paths.extend((ROOT / folder).glob('*.svh'))
    paths = sorted(set(paths))
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    archive = out / 'sources.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for p in paths:
            if 'cu66-v81' in p.parts:
                tar.add(p, arcname=str(p.relative_to(ROOT)), recursive=False)
    results = dict(schema='cu81-strict-lint-v1', status='FAIL', source_sha256=pins,
                   source_snapshot=dict(path=str(archive.relative_to(ROOT)), sha256=sha(archive)),
                   commands=[], scope='Behavioral elaboration/lint only; not synthesis, timing or CDC.')
    try:
        for mode in (0, 2, 3):
            log = out / f'prefetch{mode}.log'
            command = ['docker', 'exec', 'gamebub-cu66-v69-build', 'verilator', '--lint-only',
                       *spec['verilator_options'], '-DSIMULATION', f'-GPREFETCH_ENABLE={mode}',
                       '--top-module', spec['top'],
                       *['-I' + str(ROOT / p) for p in spec['include_dirs']],
                       *[str(ROOT / p) for p in spec['rtl_sources']]]
            with log.open('w') as stream:
                completed = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
            results['commands'].append(dict(mode=mode, command=command, exit_code=completed.returncode,
                                           log=str(log.relative_to(ROOT)), sha256=sha(log)))
        assert pins == {p: sha(ROOT / p) for p in pins}, 'sources changed during lint'
        assert all(c['exit_code'] == 0 for c in results['commands']), 'strict lint failed; retained logs'
        results['status'] = 'PASS'
    except Exception as exc:
        results['failure'] = str(exc)
        raise
    finally:
        (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        print(results['status'], out / 'results.json', flush=True)


if __name__ == '__main__':
    main()
