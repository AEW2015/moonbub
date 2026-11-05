#!/usr/bin/env python3
"""Generic Yosys leaf elaboration; not FPGA mapping, fit or timing evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
H = ROOT / 'fpga/experiments/cu66-v71/memory'
OLD = ROOT / 'fpga/experiments/cu66-v70/memory'
CONTAINER = os.environ.get('TASK_CONTAINER', 'gamebub-cu66-v69-build')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

sources = [OLD / 'cu70_word_bridge.sv', H / 'cu71_word_bridge.sv', OLD / 'cu70_memory_map.svh', Path(__file__).resolve()]
pins = {str(p.relative_to(ROOT)): sha(p) for p in sources}
commands = []

def run(argv, output_path):
    with output_path.open('w') as output:
        proc = subprocess.run(argv, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=120)
    commands.append(dict(argv=argv, log=str(output_path.relative_to(ROOT)), exit_code=proc.returncode, sha256=sha(output_path)))
    if proc.returncode:
        raise RuntimeError(f'{output_path}: exit {proc.returncode}; retained log')
    return output_path.read_text()

version = run(['docker', 'exec', CONTAINER, 'yosys', '-V'], H / 'elaboration-version.log').strip()
rows = []
for name, source in (('v70', sources[0]), ('v71', sources[1])):
    top = 'cu70_word_bridge' if name == 'v70' else 'cu71_word_bridge'
    stat = H / ('elaboration-' + name + '-stat.json')
    netlist = H / ('elaboration-' + name + '-netlist.json')
    yosys_script = '\n'.join([
        f'read_verilog -sv -I{OLD} {source}',
        f'hierarchy -check -top {top}',
        'proc',
        'opt',
        'check -assert',
        f'tee -o {stat} stat -json',
        f'write_json {netlist}',
    ]) + '\n'
    script_path = H / ('elaboration-' + name + '.ys')
    script_path.write_text(yosys_script)
    transcript = run(['docker', 'exec', CONTAINER, 'yosys', '-Q', '-T', '-s', str(script_path)], H / ('elaboration-' + name + '.log'))
    assert 'Found and reported 0 problems.' in transcript
    data = json.loads(stat.read_text())
    mod = data['modules']['\\' + top]
    cells = json.loads(netlist.read_text())['modules'][top]['cells']
    ff_cells = {}
    ff_bits = 0
    for cell in cells.values():
        kind = cell['type']
        if kind in ('$dff', '$dffe', '$adff', '$adffe', '$sdff', '$sdffe', '$sdffce'):
            width = int(cell['parameters']['WIDTH'], 2)
            ff_bits += width
            ff_cells[kind] = ff_cells.get(kind, 0) + 1
    rows.append(dict(name=name, top=top, statistics=mod, generic_flip_flop_bits=ff_bits, generic_flip_flop_cells=ff_cells,
                     files={str(p.relative_to(ROOT)): sha(p) for p in (script_path, stat, netlist)}))
assert pins == {str(p.relative_to(ROOT)): sha(p) for p in sources}, 'sources changed during elaboration'
result = dict(schema='cu71-generic-leaf-elaboration-v1', status='PASS', tool=version,
              source_sha256=pins, commands=commands, runs=rows,
              scope='Yosys generic word-bridge leaf only: hierarchy, process conversion, optimization, structural check and unmapped statistics.',
              limitations=['No controller, tile adapter, full system, pads, clock constraints, or board constraints in this leaf.',
                           'Generic flip-flop bit counts are sums of retained Yosys dff-family WIDTH parameters after proc/opt; no techmap/synth_xilinx run.',
                           'Arrays remain generic Yosys memories in this flow; report their bits separately from dff-family bits. Counts establish neither FPGA LUT/FF/BRAM usage nor timing, placement or fit.'])
(H / 'elaboration-results.json').write_text(json.dumps(result, indent=2) + '\n')
for row in rows:
    print(row['name'], 'cells', row['statistics']['num_cells'], 'generic_ff_bits', row['generic_flip_flop_bits'])
print('ELABORATION_V71_PASS leaves=2 structural_problems=0 sources_stable=true')
