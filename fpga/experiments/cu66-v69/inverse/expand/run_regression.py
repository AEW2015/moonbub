#!/usr/bin/env python3
"""Independent-mask expansion test on Icarus and Verilator."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DUT = ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_expand_tiles.sv'
TB = HERE / 'tb_expand_tiles.sv'
NATIVE = ROOT / 'experiments/cu66-native-v69'
RESULTS = HERE / 'results'
CONTAINER = 'gamebub-cu66-v69-build'
BUILD = '/build/cu66-v69/expand-v69'
SEEDS = (69004701, 69004702, 69004703)
PASS_RE = re.compile(
    r'^CU66_EXPAND_TILES_PASS outputs=(\d+) streams=(\d+) inputs=(\d+) '
    r'stalls=(\d+) seed=(\d+) first_hidden_y=(\d+)$', re.M)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha(path.read_bytes())


def docker(*args):
    return ['docker', 'exec', CONTAINER, *map(str, args)]


def run(label, argv, timeout=120):
    proc = subprocess.run(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=False)
    (RESULTS / f'{label}.log').write_text(proc.stdout)
    if proc.returncode:
        raise RuntimeError(f'{label} exited {proc.returncode}; inspect its log')
    return proc.stdout


def main():
    RESULTS.mkdir(exist_ok=True)
    exporter = HERE / 'export_masks.py'
    proc = subprocess.run([sys.executable, str(exporter)], cwd=ROOT, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=30, check=False)
    (RESULTS / 'mask-export.log').write_text(proc.stdout)
    if proc.returncode:
        raise RuntimeError('mask exporter failed')

    masks = json.loads((HERE / 'masks.json').read_text())
    assert masks['plane_masks']['y']['hidden_blocks'] == 256
    assert masks['plane_masks']['cb']['hidden_blocks'] == 19
    assert masks['plane_masks']['cr']['hidden_blocks'] == 19
    source_paths = {
        'DUT': DUT,
        'testbench': TB,
        'mask_exporter': exporter,
        'runner': Path(__file__),
        'mask_manifest': HERE / 'masks.json',
        'mask_y': HERE / 'mask_y.hex',
        'mask_cb': HERE / 'mask_cb.hex',
        'mask_cr': HERE / 'mask_cr.hex',
        'native_manifest': NATIVE / 'manifest.json',
    }
    for name, record in masks['plane_masks'].items():
        source_paths[f'native_mask_{name}'] = NATIVE / record['source_path']
    source_hashes = {name: sha_file(path) for name, path in source_paths.items()}

    image = subprocess.check_output(
        ['docker', 'inspect', '--format', '{{.Image}}', CONTAINER], text=True).strip()
    versions = {}
    for name, command in {'iverilog': ('iverilog', '-V'),
                          'vvp': ('vvp', '-V'),
                          'verilator': ('verilator', '--version')}.items():
        result = subprocess.run(docker(*command), text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=15, check=False)
        versions[name] = result.stdout.splitlines()[:4]
    subprocess.run(docker('mkdir', '-p', BUILD), check=True)
    sources = [str(DUT), str(TB)]
    iv_bin = f'{BUILD}/expand-iverilog'
    run('iverilog-compile', docker('iverilog', '-g2012', '-s', 'tb_expand_tiles',
                                   '-o', iv_bin, *sources))
    vobj = f'{BUILD}/verilator-obj'
    run('verilator-compile', docker('verilator', '--binary', '--timing', '--Wall',
                                    '-j', '2', '--top-module', 'tb_expand_tiles',
                                    '--Mdir', vobj, *sources))

    observations = {'iverilog': {}, 'verilator': {}}
    for seed in SEEDS:
        plusargs = [f'+SEED={seed}', f'+MASK_Y={HERE}/mask_y.hex',
                    f'+MASK_CB={HERE}/mask_cb.hex', f'+MASK_CR={HERE}/mask_cr.hex']
        iv = run(f'iverilog-seed-{seed}', docker('vvp', iv_bin, *plusargs))
        vl = run(f'verilator-seed-{seed}', docker(f'{vobj}/Vtb_expand_tiles', *plusargs))
        parsed = {}
        for backend, output in (('iverilog', iv), ('verilator', vl)):
            matches = PASS_RE.findall(output)
            if len(matches) != 1:
                raise RuntimeError(f'{backend} seed {seed}: missing unique terminal PASS')
            row = tuple(map(int, matches[0]))
            record = dict(zip(('outputs', 'streams', 'inputs', 'stalls', 'seed',
                               'first_hidden_y'), row))
            if record['seed'] != seed or record['outputs'] != 16833 or record['streams'] != 6:
                raise RuntimeError(f'{backend} seed {seed}: incomplete coverage {record}')
            if record['first_hidden_y'] != 633 or record['stalls'] == 0:
                raise RuntimeError(f'{backend} seed {seed}: mask/stall coverage {record}')
            observations[backend][str(seed)] = record
            parsed[backend] = record
        if parsed['iverilog'] != parsed['verilator']:
            raise RuntimeError(f'backend summary disagreement seed={seed}: {parsed}')

    after = {name: sha_file(path) for name, path in source_paths.items()}
    if after != source_hashes:
        raise RuntimeError('DUT, fixture, or mask source changed during run')
    logs = {p.name: {'bytes': p.stat().st_size, 'sha256': sha_file(p)}
            for p in sorted(RESULTS.glob('*.log'))}
    result = {
        'schema': 'cu66-expand-tiles-v69-test-evidence-v1',
        'status': 'PASS',
        'container': CONTAINER,
        'container_image_id': image,
        'tool_versions': versions,
        'seeds': list(SEEDS),
        'oracle': 'Archived native manifest safe_hidden_mask object bytes; no DUT rectangle predicate is copied into the Python vector exporter.',
        'dispatch_coverage': {
            'full_dispatch5_blocks': {'Y': 5400, 'Cb': 1350, 'Cr': 1350},
            'compact_dispatch6_input_blocks': {'Y': 5144, 'Cb': 1331, 'Cr': 1331},
            'expanded_output_blocks_per_seed': 16833,
            'hidden_blocks_from_masks': {'Y': 256, 'Cb': 19, 'Cr': 19},
        },
        'malformed_and_control_cases': [
            'invalid plane geometry', 'wrong configured block count',
            'wrong encoded index', 'incorrect in_last',
            'nonzero hidden coefficient in full dispatch5',
            'abort while output is stalled', 'synchronous reset while output is stalled',
        ],
        'source_sha256': source_hashes,
        'source_sha256_after': after,
        'results': observations,
        'backend_stall_and_output_agreement': True,
        'logs': logs,
        'scope': 'RTL tile expansion component with deterministic pseudo-random output backpressure; not complete CU66 decode or hardware timing.',
    }
    (RESULTS / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'seeds': list(SEEDS),
                      'outputs_per_seed_backend': 16833,
                      'backend_agreement': True}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.SubprocessError, RuntimeError, AssertionError) as exc:
        print(f'CU66_EXPAND_REGRESSION_FAIL: {exc}', file=sys.stderr)
        raise SystemExit(1)
