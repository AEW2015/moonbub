#!/usr/bin/env python3
"""Run the v71 memory bridge against the frozen checked SDRAM command model."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
H = ROOT / 'fpga/experiments/cu66-v71/memory'
OLD = ROOT / 'fpga/experiments/cu66-v70/memory'
CONTAINER = os.environ.get('TASK_CONTAINER', 'gamebub-cu66-v69-build')
SOURCES = [H / n for n in ('tb_memory_v71.sv', 'cu71_word_bridge.sv', 'cu71_memory_system.sv')]
SOURCES += [OLD / n for n in ('cu70_tile_memory.sv', 'cu70_sdram_controller.sv', 'cu70_sdram_model.sv')]
PINS = SOURCES + [H / 'cu71_memory_sim.sv', OLD / 'cu70_memory_map.svh', Path(__file__).resolve()]

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
for corner in (2, 7):
    suffix = f'tac{corner}'
    builddir = '/build/v71-memory-' + suffix
    common = ['-DSIMULATION', '-I' + str(OLD), *map(str, SOURCES)]
    run(['docker', 'exec', CONTAINER, 'verilator', '--binary', '--timing', '--Wall', '-Wno-BLKSEQ', '--top-module', 'tb_memory_v71', '-GTAC_NS=' + str(corner) + '.0', '--Mdir', builddir, '-j', '1', *common], 'build-' + suffix + '.log')
    run(['docker', 'exec', CONTAINER, 'iverilog', '-g2012', '-Ptb_memory_v71.TAC_NS=' + str(corner) + '.0', '-s', 'tb_memory_v71', '-o', builddir + '.vvp', *common], 'iverilog-build-' + suffix + '.log')
    for seed in (7101, 7102):
        for scenario, bubble, adversarial in (('continuous', 0, 0), ('bubble', 1, 0), ('bank3-conflict', 1, 1)):
            pair = []
            for backend, command in (('verilator', [builddir + '/Vtb_memory_v71']), ('iverilog', ['vvp', builddir + '.vvp'])):
                text = run(['docker', 'exec', CONTAINER, *command, '+SEED=' + str(seed), '+LCD_BUBBLE=' + str(bubble), '+LCD_ADVERSARIAL=' + str(adversarial)], f'{backend}-{suffix}-{seed}-{scenario}.log')
                match = re.search(r'^MEMORY_V71_PASS (.+)$', text, re.M)
                assert match and not any(token in text for token in ('FATAL', 'Error:', 'FAIL')), text[-3000:]
                row = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', match[1])}
                assert row['seed'] == seed and row['tiles'] >= 231 and row['aborts'] == 43
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
    for backend, command in (('verilator', [builddir + '/Vtb_memory_v71']), ('iverilog', ['vvp', builddir + '.vvp'])):
        text = run(['docker', 'exec', CONTAINER, *command, '+RESET_ONLY'], f'{backend}-{suffix}-reset.log')
        match = re.search(r'^MEMORY_V71_RESET_PASS (.+)$', text, re.M)
        assert match and not any(token in text for token in ('FATAL', 'Error:', 'FAIL'))
        values = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', match[1]) if key != 'held_positions'}
        assert values['probes'] == 4 and values['fresh_bursts'] == 4 and values['fresh_words'] == 32
        runs.append(dict(backend=backend, tac_ns=corner, scenario='reset', **values))
        print('PASS', backend, suffix, 'reset', flush=True)
assert pins == {str(p.relative_to(ROOT)): sha(p) for p in PINS}, 'sources changed during regression'
result = dict(schema='cu71-memory-component-results-v1', status='PASS', source_sha256=pins, commands=commands, runs=runs,
              scope='Real frozen SDRAM controller commands, 32MiB functional checked model, canonical tile adapter, scalar aux and independent LCD BL8 requests.',
              limitations=['Functional simulation only; no board electrical timing, placement or routed Fmax claim.',
                           'Four-LCD-grant bound applies at transaction boundaries, not cycles; stalled clients can hold responses indefinitely.',
                           'Line timing includes bench request bubbles and concurrent scalar traffic, not physical sustained panel qualification.',
                           'Controller still single-word writes.'])
(H / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print('MEMORY_V71_REGRESSION_PASS runs=28 sources_stable=true')
