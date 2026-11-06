#!/usr/bin/env python3
"""Run the V74 tile-major memory bridge against the frozen V72 SDRAM command model."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / 'fpga/experiments/cu66-v74/memory'
H = M / 'adapters'
OLD = ROOT / 'fpga/experiments/cu66-v70/memory'
CONTAINER = os.environ.get('TASK_CONTAINER', 'gamebub-cu66-v69-build')
CTRL = ROOT / 'fpga/experiments/cu66-v72/memory'
SOURCES = [H / 'tb_memory_v74.sv'] + [M / n for n in ('cu74_word_bridge.sv','cu74_memory_system.sv','cu74_tile_memory.sv')] + [CTRL / n for n in ('cu72_sdram_controller.sv','cu72_sdram_model.sv')]
PINS = SOURCES + [H / 'tb_rows_v74.sv', H / 'tb_cache_v74.sv', H / 'tb_p1wide_v74.sv', OLD / 'cu70_memory_map.svh', Path(__file__).resolve()]

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
row_runs=[]
p1wide_runs=[]
for corner in (2, 7):
    suffix = f'tac{corner}'
    builddir = '/build/v74-memory-' + suffix
    common = ['-DSIMULATION', '-I' + str(OLD), *map(str, SOURCES)]
    run(['docker', 'exec', CONTAINER, 'verilator', '--binary', '--timing', '--Wall', '-Wno-BLKSEQ', '--top-module', 'tb_memory_v74', '-GTAC_NS=' + str(corner) + '.0', '--Mdir', builddir, '-j', '1', *common], 'build-' + suffix + '.log')
    run(['docker', 'exec', CONTAINER, 'iverilog', '-g2012', '-Ptb_memory_v74.TAC_NS=' + str(corner) + '.0', '-s', 'tb_memory_v74', '-o', builddir + '.vvp', *common], 'iverilog-build-' + suffix + '.log')
    for seed in (7101, 7102):
        for scenario, bubble, adversarial in (('continuous', 0, 0), ('bubble', 1, 0), ('bank3-conflict', 1, 1)):
            pair = []
            for backend, command in (('verilator', [builddir + '/Vtb_memory_v74']), ('iverilog', ['vvp', builddir + '.vvp'])):
                text = run(['docker', 'exec', CONTAINER, *command, '+SEED=' + str(seed), '+LCD_BUBBLE=' + str(bubble), '+LCD_ADVERSARIAL=' + str(adversarial)], f'{backend}-{suffix}-{seed}-{scenario}.log')
                match = re.search(r'^MEMORY_V74_PASS (.+)$', text, re.M)
                assert match and not any(token in text for token in ('FATAL', 'Error:', 'FAIL')), text[-3000:]
                row = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', match[1])}
                profile_match = re.search(r'^MEMORY_V74_PROFILE (.+)$', text, re.M)
                assert profile_match
                profile = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', profile_match[1])}
                assert profile['row_reads'] == 454 and profile['p0_hits'] + profile['p0_misses'] == 454
                row.update(profile)
                assert row['seed'] == seed and row['tiles'] >= 237 and row['aborts'] == 39
                assert row['burst_checks'] == 23 and row['burst_aborts'] == 8
                assert row['wide_read_checks'] == 17 and row['wide_read_aborts'] == 9
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
    for backend, command in (('verilator', [builddir + '/Vtb_memory_v74']), ('iverilog', ['vvp', builddir + '.vvp'])):
        text = run(['docker', 'exec', CONTAINER, *command, '+RESET_ONLY'], f'{backend}-{suffix}-reset.log')
        match = re.search(r'^MEMORY_V74_RESET_PASS (.+)$', text, re.M)
        assert match and not any(token in text for token in ('FATAL', 'Error:', 'FAIL'))
        values = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', match[1]) if key != 'held_positions'}
        assert values['probes'] == 4 and values['fresh_bursts'] == 4 and values['fresh_words'] == 32
        runs.append(dict(backend=backend, tac_ns=corner, scenario='reset', **values))
        print('PASS', backend, suffix, 'reset', flush=True)
    cache_builddir = '/build/v74-memory-cache-' + suffix
    cache_sources = [H / 'tb_cache_v74.sv'] + [M / 'cu74_word_bridge.sv'] + [CTRL / n for n in ('cu72_sdram_controller.sv','cu72_sdram_model.sv')]
    cache_common = ['-DSIMULATION', '-I' + str(OLD), *map(str, cache_sources)]
    run(['docker', 'exec', CONTAINER, 'verilator', '--binary', '--timing', '--Wall', '-Wno-BLKSEQ', '--top-module', 'tb_cache_v74', '-GTAC_NS=' + str(corner) + '.0', '--Mdir', cache_builddir, '-j', '1', *cache_common], 'cache-build-' + suffix + '.log')
    run(['docker', 'exec', CONTAINER, 'iverilog', '-g2012', '-Ptb_cache_v74.TAC_NS=' + str(corner) + '.0', '-s', 'tb_cache_v74', '-o', cache_builddir + '.vvp', *cache_common], 'cache-iverilog-build-' + suffix + '.log')
    pair = []
    for backend, command in (('verilator', [cache_builddir + '/Vtb_cache_v74']), ('iverilog', ['vvp', cache_builddir + '.vvp'])):
        text = run(['docker', 'exec', CONTAINER, *command], f'{backend}-{suffix}-cache.log')
        match = re.search(r'^MEMORY_V74_CACHE_PASS (.+)$', text, re.M)
        assert match and not any(token in text for token in ('FATAL', 'Error:', 'FAIL'))
        row = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', match[1])}
        assert row['checks'] == 19 and row['cache_misses'] == 1
        pair.append(row)
        cache_runs.append(dict(backend=backend, tac_ns=corner, **row))
        print('PASS', backend, suffix, 'masked-cache-alias', flush=True)
    assert pair[0] == pair[1], ('cache', suffix, pair)
for corner in (2,7):
    suffix=f'tac{corner}'
    for lines in (1,8):
        rowdir=f'/build/v74-memory-rows-{suffix}-{lines}'
        sources=[H/'tb_rows_v74.sv',M/'cu74_word_bridge.sv',CTRL/'cu72_sdram_controller.sv',CTRL/'cu72_sdram_model.sv']
        common=['-DSIMULATION','-I'+str(OLD),*map(str,sources)]
        run(['docker','exec',CONTAINER,'verilator','--binary','--timing','--Wall','-Wno-BLKSEQ','--top-module','tb_rows_v74','-GTAC_NS='+str(corner)+'.0','-GCACHE_LINES='+str(lines),'--Mdir',rowdir,'-j','1',*common],f'rows-build-{suffix}-{lines}.log')
        run(['docker','exec',CONTAINER,'iverilog','-g2012','-Ptb_rows_v74.TAC_NS='+str(corner)+'.0','-Ptb_rows_v74.CACHE_LINES='+str(lines),'-s','tb_rows_v74','-o',rowdir+'.vvp',*common],f'rows-iverilog-build-{suffix}-{lines}.log')
        pair=[]
        for backend,command in (('verilator',[rowdir+'/Vtb_rows_v74']),('iverilog',['vvp',rowdir+'.vvp'])):
            text=run(['docker','exec',CONTAINER,*command],f'{backend}-{suffix}-rows-{lines}.log')
            match=re.search(r'^MEMORY_V74_ROWS_PASS (.+)$',text,re.M)
            assert match and not any(token in text for token in ('FATAL','Error:','FAIL'))
            row={key:int(value)for key,value in re.findall(r'(\w+)=(\d+)',match[1])}
            assert row['cache_lines']==lines and row['first_tile_misses']==8 and row['second_tile_misses']==(0 if lines==8 else 8)
            pair.append(row);row_runs.append(dict(backend=backend,tac_ns=corner,**row));print('PASS',backend,suffix,'rows',lines,flush=True)
        assert pair[0]==pair[1],('wide rows',suffix,lines,pair)
for corner in (2,7):
    suffix=f'tac{corner}'
    d='/build/v74-memory-p1wide-'+suffix
    ss=[H/'tb_p1wide_v74.sv',M/'cu74_word_bridge.sv',CTRL/'cu72_sdram_controller.sv',CTRL/'cu72_sdram_model.sv']
    common=['-DSIMULATION','-I'+str(OLD),*map(str,ss)]
    run(['docker','exec',CONTAINER,'verilator','--binary','--timing','--Wall','-Wno-BLKSEQ','--top-module','tb_p1wide_v74','-GTAC_NS='+str(corner)+'.0','--Mdir',d,'-j','1',*common],f'p1wide-build-{suffix}.log')
    run(['docker','exec',CONTAINER,'iverilog','-g2012','-Ptb_p1wide_v74.TAC_NS='+str(corner)+'.0','-s','tb_p1wide_v74','-o',d+'.vvp',*common],f'p1wide-iverilog-build-{suffix}.log')
    pair=[]
    for backend,command in (('verilator',[d+'/Vtb_p1wide_v74']),('iverilog',['vvp',d+'.vvp'])):
        text=run(['docker','exec',CONTAINER,*command],f'{backend}-{suffix}-p1wide.log')
        match=re.search(r'^MEMORY_V74_P1WIDE_PASS (.+)$',text,re.M)
        assert match and not any(token in text for token in ('FATAL','Error:','FAIL'))
        row={key:int(value) for key,value in re.findall(r'(\w+)=(\d+)',match[1])}
        assert row['checks']==31 and row['cache_misses']==1
        pair.append(row);p1wide_runs.append(dict(backend=backend,tac_ns=corner,**row));print('PASS',backend,suffix,'p1wide',flush=True)
    assert pair[0]==pair[1],('p1wide',suffix,pair)
assert pins == {str(p.relative_to(ROOT)): sha(p) for p in PINS}, 'sources changed during regression'
result = dict(schema='cu73-memory-component-results-v1', status='PASS', source_sha256=pins, commands=commands, runs=runs, cache_runs=cache_runs, row_runs=row_runs, p1wide_runs=p1wide_runs,
              scope='Real masked BL8 SDRAM commands, checked32MiB model, tile-major four full BL8 blocks, wide P0/P1 snapshots with physical cache tags, scalar/burst aux and independent LCD requests.',
              limitations=['Functional simulation only; no board electrical timing, placement or routed Fmax claim.',
                           'Four-LCD-grant bound applies at transaction boundaries, not cycles; stalled clients can hold responses indefinitely.',
                           'Line timing includes bench request bubbles and concurrent scalar traffic, not physical sustained panel qualification.',
                           'Masked BL8 controller writes are checked through actual command pins; no physical throughput claim.'])
(H / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print('MEMORY_V74_REGRESSION_PASS runs=28 cache_runs=4 row_runs=8 p1wide_runs=4 sources_stable=true')
