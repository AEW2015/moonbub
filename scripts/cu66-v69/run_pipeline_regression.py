#!/usr/bin/env python3
"""Build and test the connected base-layer RTL, retaining actual logs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
RTL = ROOT / 'fpga/experiments/cu66-v69'
OUT = RTL / 'integration'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--per-chain', type=int, default=9999)
    parser.add_argument('--seeds', default='0,6901,6902')
    parser.add_argument('--shared-bus', action='store_true')
    args = parser.parse_args()
    container = os.environ.get('TASK_CONTAINER', 'gamebub-cu66-v69-build')
    sources = [RTL / x for x in (
        'integration/cu66_base_pipeline.sv', 'inverse/cu66_expand_tiles.sv',
        'inverse/cu66_dequant.sv', 'inverse/cu66_idct8x8.sv',
        'inverse/cu66_reconstruct_tile.sv', 'entropy/cu66_ab38_decoder.sv',
        'rows/cu66_tile_rows.sv', 'rows/cu66_rows_sha256.sv',
        'hash/cu66_sha256_bytes.sv')]
    native = ROOT / 'experiments/cu66-native-v69'
    pins = sources + [OUT / 'tb_pipeline.cpp', RTL / 'inverse/cu66_quant_rom.svh',
                      Path(__file__).resolve(), native / 'index.tsv',
                      *sorted(native.glob('*.hpp')), *sorted((native / 'fixtures').glob('*.cu66'))]
    def hashes():
        return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in pins}
    before = hashes()
    commands = []
    def run(argv, name, timeout):
        path = OUT / name
        with path.open('w') as log:
            proc = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        commands.append({'argv': argv, 'log': str(path.relative_to(ROOT)), 'exit_code': proc.returncode,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        if proc.returncode:
            raise RuntimeError(f'{name}: exit {proc.returncode}; see retained log')
        return path.read_text()
    run(['docker', 'exec', container, 'verilator', '--cc', '--exe', '--build', '-j', '2',
         '--Wall', '-Wno-PINCONNECTEMPTY', '--top-module', 'cu66_base_pipeline',
         '--Mdir', '/build/integration', '-CFLAGS', '-O2 -std=c++17',
         '-I' + str(RTL / 'inverse'), *map(str, sources), str(OUT / 'tb_pipeline.cpp')],
        'build-regression.log', 600)
    summaries = []
    for seed in map(int, args.seeds.split(',')):
        log = run(['docker', 'exec', container, '/build/integration/Vcu66_base_pipeline',
                   str(native / 'index.tsv'), str(seed), str(args.per_chain),
                   *(['--shared-bus'] if args.shared_bus else [])], f'seed{seed}{"-shared" if args.shared_bus else ""}.log', 1800)
        terminal = re.search(r'^PASS actual_frames=(\d+) faults=5 aborts=(\d+) recovery=1 seed=(\d+) clocks=(\d+) shared_bus=(\d+) bus_beats=(\d+) display_reserved=(\d+) refresh_reserved=(\d+)$', log, re.M)
        if not terminal or 'FAIL' in log or int(terminal[3]) != seed:
            raise RuntimeError(f'seed {seed}: missing explicit PASS')
        rows = [dict((k, int(v)) for k, v in re.findall(r'(\w+)=(\d+)', line))
                for line in log.splitlines() if line.startswith('FRAME_PASS')]
        good = [x for x in rows if x['mode'] == 0][:-1]  # final recovery is separate
        if len(good) != int(terminal[1]) or any(x['tiles'] != 8100 for x in good):
            raise RuntimeError('frame coverage mismatch')
        summaries.append({'seed': seed, 'shared_bus': args.shared_bus, 'bus_beats': int(terminal[6]), 'display_reserved': int(terminal[7]), 'refresh_reserved': int(terminal[8]), 'actual_frames': len(good), 'faults': 5,
                          'aborts': int(terminal[2]), 'recovery_frames': 1,
                          'min_cycles': min(x['clocks'] for x in good),
                          'max_cycles': max(x['clocks'] for x in good),
                          'mean_cycles': sum(x['clocks'] for x in good) / len(good),
                          'frames': good})
        print(f'PASS seed={seed} actual_frames={len(good)} max_cycles={max(x["clocks"] for x in good)}', flush=True)
    if before != hashes():
        raise RuntimeError('source/fixture mutation during regression')
    result = {'status': 'PASS', 'scope': 'connected base-layer RTL; not complete CU66/display/ESP32',
              'pinconnectempty_waiver': 'unconsumed diagnostic outputs only; all functional ports connected',
              'source_sha256': before, 'commands': commands, 'runs': summaries,
              'memory_model': {'compressed': 'one byte request, 0 or 1..8 wait clocks plus protocol',
                               'reference': 'one 64-byte tile request, 0 or 32..96 wait clocks plus protocol',
                               'writer': 'one accepted64-byte tile, separate write_done/error completion after 0 or32..96 clocks; lease held until completion',
                               'qmap': 'one-cycle response, randomized request-ready',
                               'shared_bus': args.shared_bus,
                               'shared_schedule': 'one x16 beat/clock max, RR clients; compressed byte consumes one beat; reference/write tile each32beats; reserve alternate clocks for display and16/7800 for refresh;10percent random availability loss',
                               'limitation': 'modeled arbitration/refresh/display reservation only; no actual SDRAM commands, controller timing, CDC or ESP32 timing'},
              'not_proven': ['physical target Fmax/fit', 'actual memory/controller throughput',
                             'HUD decode/composition RTL', 'full packet-to-bank integration',
                             'physical 30fps or input-to-photon latency']}
    (OUT / ('results-shared.json' if args.shared_bus else 'results.json')).write_text(json.dumps(result, indent=2) + '\n')
    print('PASS connected pipeline regression and source stability')


if __name__ == '__main__':
    main()
