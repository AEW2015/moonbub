#!/usr/bin/env python3
"""Root-dispatched strict Verilator exhaustive proof for the V119 range probe."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'fpga/experiments/cu66-v119-range-probe'
AREA = ROOT / 'experiments/python-gamebub-v119/range-probe'
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
FILES = (Path(__file__).resolve(), SRC / 'range_probe.sv', SRC / 'tb_range_probe.cpp')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def memory():
    fields = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, rest = line.split(':', 1)
        fields[key] = int(rest.split()[0]) * 1024
    full = next(line for line in Path('/proc/pressure/memory').read_text().splitlines()
                if line.startswith('full '))
    return {
        'available_bytes': fields['MemAvailable'],
        'psi_full_avg10': float(full.split('avg10=')[1].split()[0]),
        'combined_used_ratio': (fields['MemTotal'] - fields['MemAvailable']
                                + fields['SwapTotal'] - fields['SwapFree'])
                               / (fields['MemTotal'] + fields['SwapTotal']),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true', help='execute the prepared RTL model')
    parser.add_argument('--root-grant', help='Root dispatch token supplied by the coordinating runner')
    args = parser.parse_args()
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in FILES}
    if not args.run:
        print(json.dumps({'status': 'PREPARED_NOT_RUN', 'command':
                          'python3 scripts/cu66-v119/range_probe.py --run --root-grant <root-token>',
                          'source_sha256': hashes}, sort_keys=True))
        return
    if not args.root_grant:
        raise SystemExit('coordinating-agent dispatch requires --root-grant')

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    attempt = AREA / 'attempts' / stamp
    attempt.mkdir(parents=True, exist_ok=False)
    build = Path('/home/lori/gamebub-build/cu66-v69') / ('v119-range-probe-' + stamp)
    build.mkdir(parents=True, exist_ok=False)
    mapped = '/build/' + build.name
    receipt = {
        'schema': 'v119-standalone-signed16-range-verilator-v1',
        'status': 'FAIL', 'actual_RTL_run': False, 'simulation_started': False,
        'root_grant': args.root_grant, 'image_id': IMAGE,
        'source_sha256': hashes, 'commands': [], 'runs': [], 'memory_samples': [],
        'assertions_disabled_or_downgraded': False,
        'domain_patterns': 65536, 'named_endpoint_checks': 9,
        'scope': 'Standalone combinational predicate equivalence; no qualifiers, clocks, physical timing, FPS, or production source claim.',
    }
    initial_hashes = dict(hashes)

    def persist():
        (attempt / 'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')

    def run(argv, logname, timeout_s, rtl=False):
        active = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'],
                                check=True, capture_output=True, text=True).stdout.splitlines()
        active_v11 = [name for name in active if 'gamebub-v11' in name]
        if len(active_v11) >= 2:
            raise RuntimeError('Docker heavy-slot gate closed: ' + repr(active_v11))
        before = memory()
        if (before['available_bytes'] < 8 * 1024**3 or before['psi_full_avg10'] >= 1
                or before['combined_used_ratio'] >= .85):
            raise RuntimeError('resource gate closed: ' + repr(before))
        container = 'gamebub-v119-range-' + stamp.lower() + '-' + str(len(receipt['commands']))
        cmd = ['docker', 'run', '--rm', '--init', '--name', container,
               '--memory', '8g', '--memory-swap', '8g', '--cpus', '2',
               '--pids-limit', '2048', '--network', 'none', '--ulimit', 'core=0',
               '--mount', f'type=bind,src={build},dst={mapped}', '-w', mapped, IMAGE,
               'timeout', '--kill-after=5s', str(timeout_s) + 's', *argv]
        row = {'argv': cmd, 'timeout_seconds': timeout_s, 'resource_before': before}
        receipt['commands'].append(row)
        if rtl:
            # Durable provenance says an actual RTL model invocation is starting.
            receipt.update(actual_RTL_run=True, simulation_started=True)
        persist()
        started = time.monotonic()
        high_psi = 0
        with (attempt / logname).open('w') as log:
            process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            while process.poll() is None:
                sample = {'elapsed_seconds': time.monotonic() - started,
                          'command': logname, **memory()}
                receipt['memory_samples'].append(sample)
                high_psi = high_psi + 1 if sample['psi_full_avg10'] >= 5 else 0
                stop = (sample['available_bytes'] < 4 * 1024**3 or high_psi >= 2
                        or sample['combined_used_ratio'] >= .90
                        or sample['elapsed_seconds'] > timeout_s + 20)
                if stop:
                    subprocess.run(['docker', 'stop', '--time', '5', container],
                                   capture_output=True, timeout=15)
                    row['resource_stop'] = sample
                    break
                time.sleep(2)
            row['exit_code'] = process.wait(timeout=20)
            row['wall_seconds'] = time.monotonic() - started
        persist()
        if row['exit_code'] != 0 or 'resource_stop' in row:
            raise RuntimeError('command failed: ' + logname)

    started = time.monotonic()
    try:
        for path in FILES:
            dest = attempt / 'sources' / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
        shutil.copyfile(SRC / 'range_probe.sv', build / 'range_probe.sv')
        shutil.copyfile(SRC / 'tb_range_probe.cpp', build / 'tb_range_probe.cpp')
        run(['verilator', '--version'], 'version.log', 30)
        version_text = (attempt / 'version.log').read_text()
        if not version_text.strip().startswith('Verilator 5.020'):
            raise RuntimeError('unexpected Verilator version: ' + repr(version_text))
        run(['verilator', '--cc', '--exe', '--build', '-j', '1', '--assert', '-Wall',
             '--language', '1800-2017', '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
             '--top-module', 'range_probe', '--Mdir', mapped + '/obj',
             mapped + '/range_probe.sv', mapped + '/tb_range_probe.cpp'], 'compile.log', 600)
        for line in (attempt / 'compile.log').read_text().splitlines():
            if '%Warning-' in line:
                raise RuntimeError('strict warning found in compile log')
        binary = build / 'obj/Vrange_probe'
        receipt['binary_sha256'] = sha(binary)
        run([mapped + '/obj/Vrange_probe'], 'simulation.log', 240, rtl=True)
        output = (attempt / 'simulation.log').read_text()
        if output.count('TEST_PASS patterns=65536 endpoint_checks=9 mismatches=0') != 1:
            raise RuntimeError('missing unique exhaustive C++ oracle pass marker')
        if {str(path.relative_to(ROOT)): sha(path) for path in FILES} != initial_hashes:
            raise RuntimeError('source changed during attempt')
        receipt['runs'].append({'patterns_checked': 65536, 'endpoint_checks': 9,
                                'mismatches': 0, 'oracle': 'independent signed C++ integer bounds'})
        receipt['status'] = 'PASS'
    except BaseException as exc:
        receipt['error'] = repr(exc)
        raise
    finally:
        receipt['wall_seconds'] = time.monotonic() - started
        receipt['final_source_sha256'] = {
            str(path.relative_to(ROOT)): sha(path) for path in FILES
        }
        if receipt['final_source_sha256'] != initial_hashes:
            receipt['status'] = 'FAIL'
            receipt['error'] = 'source hash changed during attempt'
        receipt['artifact_sha256'] = {
            str(path.relative_to(attempt)): sha(path)
            for path in attempt.rglob('*') if path.is_file() and path.name != 'receipt.json'
        }
        persist()
        selector = {'status': receipt['status'],
                    'actual_RTL_run': receipt['actual_RTL_run'],
                    'path': str((attempt / 'receipt.json').relative_to(ROOT)),
                    'sha256': sha(attempt / 'receipt.json')}
        (AREA / 'results.json').write_text(json.dumps(selector, indent=2, sort_keys=True) + '\n')
        print('V119_RANGE_PROBE', receipt['status'], attempt, flush=True)


if __name__ == '__main__':
    main()
