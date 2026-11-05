#!/usr/bin/env python3
"""Run the v72 memory bridge against the frozen checked SDRAM command model."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / 'fpga/experiments/cu66-v72/memory'
H = M / 'adapters'
OLD = ROOT / 'fpga/experiments/cu66-v70/memory'
CONTAINER = os.environ.get('TASK_CONTAINER', 'gamebub-cu66-v69-build')
SOURCES = [H / 'tb_memory_v72.sv'] + [M / n for n in ('cu72_word_bridge.sv', 'cu72_memory_system.sv', 'cu72_tile_memory.sv', 'cu72_sdram_controller.sv', 'cu72_sdram_model.sv')]
PINS = SOURCES + [H / 'tb_cache_v72.sv', OLD / 'cu70_memory_map.svh', Path(__file__).resolve()]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

pins = {str(p.relative_to(ROOT)): sha(p) for p in PINS}
commands = []

def run(argv, name, timeout=300):
    path = H / name
    with path.open('w') as output:
        try:
            proc = subprocess.run(argv, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired:
            commands.append(dict(argv=argv, log=name, timeout_seconds=timeout, sha256=sha(path)))
            raise
    commands.append(dict(argv=argv, log=name, exit_code=proc.returncode, sha256=sha(path)))
    if proc.returncode:
        raise RuntimeError(f'{name}: exit {proc.returncode}; see retained log')
    return path.read_text()

runs = []
cache_runs = []
for corner in (2, 7):
    suffix = f'tac{corner}'
    builddir = '/build/v72-memory-' + suffix
    common = ['-DSIMULATION', '-I' + str(OLD), *map(str, SOURCES)]
    run(['docker', 'exec', CONTAINER, 'verilator', '--binary', '--timing', '--Wall', '-Wno-BLKSEQ', '--top-module', 'tb_memory_v72', '-GTAC_NS=' + str(corner) + '.0', '--Mdir', builddir, '-j', '1', *common], 'build-' + suffix + '.log')
    run(['docker', 'exec', CONTAINER, 'iverilog', '-g2012', '-Ptb_memory_v72.TAC_NS=' + str(corner) + '.0', '-s', 'tb_memory_v72', '-o', builddir + '.vvp', *common], 'iverilog-build-' + suffix + '.log')
    for seed in (7101, 7102):
        for scenario, bubble, adversarial in (('continuous', 0, 0), ('bubble', 1, 0), ('bank3-conflict', 1, 1)):
            pair = []
            for backend, command in (('verilator', [builddir + '/Vtb_memory_v72']), ('iverilog', ['vvp', builddir + '.vvp'])):
                text = run(['docker', 'exec', CONTAINER, *command, '+SEED=' + str(seed), '+LCD_BUBBLE=' + str(bubble), '+LCD_ADVERSARIAL=' + str(adversarial)], f'{backend}-{suffix}-{seed}-{scenario}.log')
                match = re.search(r'^MEMORY_V72_PASS (.+)$', text, re.M)
                assert match and not any(token in text for token in ('FATAL', 'Error:', 'FAIL')), text[-3000:]
                row = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', match[1])}
                assert row['seed'] == seed and row['tiles'] >= 237 and row['aborts'] == 43
                assert row['burst_checks'] == 23 and row['burst_aborts'] == 8
                assert row['lcd_bursts'] == 250 and row['lcd_words'] == 2000 and row['lcd_rejects'] == 3
                assert row['max_lcd_streak'] <= 4 and row['REF'] > 4
                if bubble == 0:
                    assert row['max_lcd_streak'] == 4
                assert row['lcd_bubble'] == bubble and row['lcd_adversarial'] == adversarial
                assert row['lcd_line_max'] <= 1842 and row['grace_blocks'] > 0 and row['silent_wait'] <= 80
                pair.append(row)
                runs.append(dict(backend=backend, tac_ns=corner, scenario=scenario, **row))
                print('PASS', backend, suffix, seed, scenario, row['cycles'], flush=True)
            assert pair[0] == pair[1], (suffix, seed, scenario, pair)
    for backend, command in (('verilator', [builddir + '/Vtb_memory_v72']), ('iverilog', ['vvp', builddir + '.vvp'])):
        text = run(['docker', 'exec', CONTAINER, *command, '+RESET_ONLY'], f'{backend}-{suffix}-reset.log')
        match = re.search(r'^MEMORY_V72_RESET_PASS (.+)$', text, re.M)
        assert match and not any(token in text for token in ('FATAL', 'Error:', 'FAIL'))
        values = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', match[1]) if key != 'held_positions'}
        assert values['probes'] == 4 and values['fresh_bursts'] == 4 and values['fresh_words'] == 32
        runs.append(dict(backend=backend, tac_ns=corner, scenario='reset', **values))
        print('PASS', backend, suffix, 'reset', flush=True)
    cache_builddir = '/build/v72-cache-' + suffix
    cache_sources = [H / 'tb_cache_v72.sv'] + [M / n for n in ('cu72_word_bridge.sv', 'cu72_sdram_controller.sv', 'cu72_sdram_model.sv')]
    cache_common = ['-DSIMULATION', '-I' + str(OLD), *map(str, cache_sources)]
    run(['docker', 'exec', CONTAINER, 'verilator', '--binary', '--timing', '--Wall', '-Wno-BLKSEQ', '--top-module', 'tb_cache_v72', '-GTAC_NS=' + str(corner) + '.0', '--Mdir', cache_builddir, '-j', '1', *cache_common], 'cache-build-' + suffix + '.log')
    run(['docker', 'exec', CONTAINER, 'iverilog', '-g2012', '-Ptb_cache_v72.TAC_NS=' + str(corner) + '.0', '-s', 'tb_cache_v72', '-o', cache_builddir + '.vvp', *cache_common], 'cache-iverilog-build-' + suffix + '.log')
    pair = []
    for backend, command in (('verilator', [cache_builddir + '/Vtb_cache_v72']), ('iverilog', ['vvp', cache_builddir + '.vvp'])):
        text = run(['docker', 'exec', CONTAINER, *command], f'{backend}-{suffix}-cache.log')
        match = re.search(r'^MEMORY_V72_CACHE_PASS (.+)$', text, re.M)
        assert match and not any(token in text for token in ('FATAL', 'Error:', 'FAIL'))
        row = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', match[1])}
        assert row['checks'] == 19 and row['cache_misses'] == 1
        pair.append(row)
        cache_runs.append(dict(backend=backend, tac_ns=corner, **row))
        print('PASS', backend, suffix, 'masked-cache-alias', flush=True)
    assert pair[0] == pair[1], ('cache', suffix, pair)
assert pins == {str(p.relative_to(ROOT)): sha(p) for p in PINS}, 'sources changed during regression'
result = dict(schema='cu72-memory-component-results-v1', status='PASS', source_sha256=pins, commands=commands, runs=runs, cache_runs=cache_runs,
              scope='Real masked BL8 SDRAM commands, checked32MiB model, canonical four-word masked rows, scalar/burst aux and independent LCD requests.',
              limitations=['Functional simulation only; no board electrical timing, placement or routed Fmax claim.',
                           'Four-LCD-grant bound applies at transaction boundaries, not cycles; stalled clients can hold responses indefinitely.',
                           'Line timing includes bench request bubbles and concurrent scalar traffic, not physical sustained panel qualification.',
                           'Masked BL8 controller writes are checked through actual command pins; no physical throughput claim.'])
(H / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print('MEMORY_V72_REGRESSION_PASS runs=28 cache_runs=4 sources_stable=true')
