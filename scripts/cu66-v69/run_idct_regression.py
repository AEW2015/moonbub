#!/usr/bin/env python3
"""Compile/run the frozen CU66 IDCT testbench with Icarus and Verilator."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RTL = ROOT / 'fpga/experiments/cu66-v69/inverse'
OUT = RTL / 'results'
CONTAINER = 'gamebub-cu66-v69-build'
BUILD = '/build/cu66-v69/idct-v69'
SEEDS = (69004501, 69004502, 69004503)
PASS_RE = re.compile(
    r'^CU66_IDCT_TEST_PASS tiles=(\d+) aborts=(\d+) reset_cancelled=(\d+) '
    r'stall_cancelled=(\d+) cycles=(\d+) maximum_work_cycles=(\d+) seed=(\d+)$', re.M)
COMMANDS = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(label, argv, timeout=180):
    proc = subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=False)
    (OUT / f'{label}.log').write_text(proc.stdout)
    COMMANDS.append({'log': f'{label}.log', 'argv': list(map(str, argv)),
                     'exit_code': proc.returncode})
    if proc.returncode:
        raise RuntimeError(f'{label} exited {proc.returncode}; see results/{label}.log')
    return proc.stdout


def docker(*argv):
    return ['docker', 'exec', CONTAINER, *map(str, argv)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = {
        name: sha(RTL / name) for name in
        ('cu66_idct8x8.sv', 'tb_idct.sv', 'tiles.hex', 'fixtures.json', 'export.py')
    }
    image = subprocess.check_output(
        ['docker', 'inspect', '--format', '{{.Image}}', CONTAINER], text=True).strip()
    tool_versions = {}
    for name, command in {
        'verilator': ('verilator', '--version'),
        'iverilog': ('iverilog', '-V'),
        'vvp': ('vvp', '-V'),
    }.items():
        proc = subprocess.run(docker(*command), text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=15, check=False)
        tool_versions[name] = proc.stdout.splitlines()[:4]
    subprocess.run(docker('mkdir', '-p', BUILD), check=True)
    sources = [str(RTL / 'cu66_idct8x8.sv'), str(RTL / 'tb_idct.sv')]
    fixture = str(RTL / 'tiles.hex')

    iverilog_bin = f'{BUILD}/idct-iverilog'
    run('iverilog-compile', docker(
        'iverilog', '-g2012', '-s', 'tb_idct', '-o', iverilog_bin, *sources))
    verilator_dir = f'{BUILD}/verilator-obj'
    run('verilator-compile', docker(
        'verilator', '--binary', '--timing', '--Wall', '-j', '2',
        '--top-module', 'tb_idct', '--Mdir', verilator_dir, *sources))

    observations = {'iverilog': {}, 'verilator': {}}
    for seed in SEEDS:
        iv = run(f'iverilog-seed-{seed}', docker(
            'vvp', iverilog_bin, f'+FIXTURE={fixture}', f'+SEED={seed}'))
        vl = run(f'verilator-seed-{seed}', docker(
            f'{verilator_dir}/Vtb_idct', f'+FIXTURE={fixture}', f'+SEED={seed}'))
        parsed = {}
        for backend, output in (('iverilog', iv), ('verilator', vl)):
            matches = PASS_RE.findall(output)
            if len(matches) != 1:
                raise RuntimeError(f'{backend} seed {seed}: expected one terminal PASS marker')
            row = tuple(map(int, matches[0]))
            result = dict(zip(('tiles', 'aborts', 'reset_cancelled', 'stall_cancelled',
                               'cycles', 'maximum_work_cycles', 'seed'), row))
            if result['seed'] != seed or result['tiles'] != 3471:
                raise RuntimeError(f'{backend} seed {seed}: wrong coverage marker {result}')
            if result['reset_cancelled'] != 1 or result['stall_cancelled'] != 1:
                raise RuntimeError(f'{backend} seed {seed}: cancellation case missing {result}')
            observations[backend][str(seed)] = result
            parsed[backend] = result
        comparable = ('tiles', 'aborts', 'reset_cancelled', 'stall_cancelled',
                      'cycles', 'maximum_work_cycles', 'seed')
        if any(parsed['iverilog'][key] != parsed['verilator'][key] for key in comparable):
            raise RuntimeError(f'backend disagreement seed {seed}: {parsed}')

    final_inputs = {name: sha(RTL / name) for name in inputs}
    if final_inputs != inputs:
        raise RuntimeError('DUT or pinned test fixture changed during regression')
    result = {
        'schema': 'cu66-idct-v69-dual-simulator-regression-v1',
        'status': 'PASS',
        'container': CONTAINER,
        'container_image_id': image,
        'tool_versions': tool_versions,
        'seed_default': 69004501,
        'seeds': list(SEEDS),
        'source_sha256': {f'fpga/experiments/cu66-v69/inverse/{k}': v for k, v in inputs.items()},
        'source_sha256_after': {f'fpga/experiments/cu66-v69/inverse/{k}': v for k, v in final_inputs.items()},
        'results': observations,
        'commands': COMMANDS,
        'backend_cycle_agreement': True,
        'watchdog': 'testbench #100000000; runner timeout 180 seconds per compile/run',
        'scope': '3471 dense-Q14 independent golden tiles per seed/backend; RTL component test only, not CU66 full receiver or hardware timing.',
    }
    (OUT / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'seeds': list(SEEDS),
                      'tiles_per_backend_seed': 3471,
                      'backend_cycle_agreement': True}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        print(f'IDCT_REGRESSION_FAIL: {exc}', file=sys.stderr)
        raise SystemExit(1)
