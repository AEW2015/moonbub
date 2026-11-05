#!/usr/bin/env python3
"""Single entrypoint scaffold; never claims NOT_CONFIGURED tasks passed."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def run(argv, *, capture=True):
    return subprocess.run(argv, cwd=ROOT, text=True, check=False,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.STDOUT if capture else None)


def doctor():
    names = ('python3', 'g++', 'iverilog', 'vvp', 'verilator', 'yosys', 'cmake', 'vivado', 'docker')
    local = {name: shutil.which(name) for name in names}
    print(json.dumps({'host_path_tools': local}, indent=2))
    image = run(['docker', 'inspect', '--format', '{{.Image}}', 'gamebub-cu66-v69-build'])
    if image.returncode == 0:
        print('build_container_image_id=' + image.stdout.strip())
        versions = run(['docker', 'exec', 'gamebub-cu66-v69-build', 'bash', '-lc',
                        'verilator --version; iverilog -V 2>&1 | head -n 1; g++ --version | head -n 1; yosys -V; cmake --version | head -n 1'])
        print(versions.stdout, end='')
    else:
        print('build_container=NOT_AVAILABLE')
    vivado = run(['docker', 'inspect', '--format', '{{.Image}}', 'gamebub-cu66-v69-vivado'])
    print('vivado_container_image_id=' + (vivado.stdout.strip() if vivado.returncode == 0 else 'NOT_AVAILABLE'))


def validate_task(name, task):
    status = task.get('status')
    argv = task.get('argv')
    if status != 'READY' or not isinstance(argv, list) or not argv:
        return False, f'{name}: {status or "MISSING_STATUS"}'
    for path in task.get('fixture', []) if isinstance(task.get('fixture'), list) else []:
        if not (ROOT / path).is_file():
            return False, f'{name}: missing fixture {path}'
    return True, name


def execute():
    plan_path = HERE / 'run-plan.json'
    plan = json.loads(plan_path.read_text())
    pending = []
    results = []
    for name, task in plan['tasks'].items():
        ready, label = validate_task(name, task)
        if not ready:
            pending.append(label)
            continue
        proc = run(task['argv'])
        results.append({'task': name, 'argv': task['argv'], 'exit_code': proc.returncode,
                         'stdout_stderr': proc.stdout})
        if proc.returncode:
            print(proc.stdout, file=sys.stderr, end='')
            return proc.returncode
    if pending:
        print(json.dumps({'status': 'NOT_RUN', 'not_configured': pending}, indent=2))
        return 2
    print(json.dumps({'status': 'COMMANDS_EXITED_ZERO', 'results': results}, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check-sources', action='store_true')
    group.add_argument('--doctor', action='store_true')
    group.add_argument('--idct-regression', action='store_true',
                       help='run the frozen dense-Q14 inverse RTL regression in both simulators')
    group.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.check_sources:
        proc = run([sys.executable, str(HERE / 'pin_sources.py'), '--check'])
        print(proc.stdout, end='')
        return proc.returncode
    if args.doctor:
        doctor()
        return 0
    if args.idct_regression:
        pins = run([sys.executable, str(HERE / 'pin_sources.py'), '--check'])
        print(pins.stdout, end='')
        if pins.returncode:
            return pins.returncode
        proc = run([sys.executable, str(HERE / 'run_idct_regression.py')])
        print(proc.stdout, end='')
        return proc.returncode
    proc = run([sys.executable, str(HERE / 'pin_sources.py'), '--check'])
    print(proc.stdout, end='')
    if proc.returncode:
        return proc.returncode
    return execute()


if __name__ == '__main__':
    raise SystemExit(main())
