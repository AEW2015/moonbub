#!/usr/bin/env python3
"""Read-only focused input connectivity from frozen routed DCP's compressed EDF."""
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AREA = ROOT / 'experiments/python-gamebub-v116/admission'
BUILD = Path('/home/lori/gamebub-build/cu66-v69/v115-integrated-100-20261109T035613740494Z-60d7e2/results')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    with zipfile.ZipFile(BUILD/'route.dcp') as archive:
        compressed = archive.read('cs88_pipeline_v91k.edf')
    text = subprocess.run(['zstd', '-d', '-q', '-c'], input=compressed, stdout=subprocess.PIPE, check=True, timeout=30).stdout.decode()
    point = text.index('"error[0]_i_22"')
    begin = text.rfind('\n   (cell ', 0, point)
    end = text.index('\n   (cell ', point)
    cell = text[begin:end]
    assert cell.startswith('\n   (cell cs88_admission_v91i2a ')
    instances = {}
    for match in re.finditer(r'\(instance (?:\(rename (\S+) "([^"]+)"\)|(\S+)) \(viewref netlist \(cellref (\S+)', cell):
        internal, name, plain, kind = match.groups()
        instances[internal or plain] = dict(name=name or plain, primitive=kind)
    nets = {}
    for match in re.finditer(r'\n         \(net (.*?)(?=\n         \(net |\n       \))', cell, re.S):
        block = match.group(1)
        refs = re.findall(r'\(portref (.*?) \(instanceref ([^)]+)\)\)', block)
        header = block.split('(joined', 1)[0].strip()
        drivers = [(pin, instance) for pin, instance in refs if pin in ('O', 'Q') or pin.startswith('(member CO ')]
        for pin, instance in refs:
            nets[(instance, pin)] = dict(net=header, drivers=[dict(pin=p, instance=i, **instances.get(i, {})) for p, i in drivers],
                                         loads=len(refs), source_fragment=block if len(block)<12000 else None)
    targets = ['state_0__i_116__0', 'error_0__i_29', 'error_0__i_26', 'error_0__i_23', 'error_0__i_22', 'error_reg_0__i_14', 'error_reg_0__i_10', 'error_reg_0__i_8']
    result = {}
    for instance in targets:
        pins = {pin:entry for (owner, pin), entry in nets.items() if owner == instance}
        assert pins, instance
        result[instance] = dict(**instances[instance], pins=pins)
    # Recursively trace LUT-only inputs to named sequential/count/port leaves.
    # Carry roles are reported from their actual pins; no multiplier inference.
    leaves = {}
    visited = set()

    def walk(instance):
        if instance in visited:
            return
        visited.add(instance)
        info = instances.get(instance, {})
        if not info.get('primitive', '').startswith('LUT'):
            leaves[instance] = info
            return
        for (owner, pin), entry in nets.items():
            if owner != instance or not pin.startswith('I'):
                continue
            if not entry['drivers']:
                leaves[entry['net']] = dict(kind='hierarchical-port-or-constant')
            for driver in entry['drivers']:
                walk(driver['instance'])

    walk('error_0__i_22')
    AREA.mkdir(parents=True, exist_ok=True)
    payload = dict(schema='v116-admission-frozen-routed-edf-inputs-v1', actual_RTL_run=False,
                   dcp=str(BUILD/'route.dcp'), dcp_sha256=sha(BUILD/'route.dcp'),
                   setup_report=str(BUILD/'route-setup-paths.rpt'), setup_report_sha256=sha(BUILD/'route-setup-paths.rpt'),
                   compressed_edf_sha256=hashlib.sha256(compressed).hexdigest(), decompressed_edf_sha256=hashlib.sha256(text.encode()).hexdigest(),
                   admission_cell_sha256=hashlib.sha256(cell.encode()).hexdigest(), targets=result,
                   first_carry_S_input_lut_leaves=leaves,
                   interpretation='The actual worst carry S cone depends on plane-selected plane_blocks and word_value. Source comparison predicates are prepared without changing residual-end arithmetic; CARRY4 names alone do not identify multiplication.',
                   exclusions='No Vivado execution, timing recomputation, native build, or claim that this candidate closes the routed path.')
    out = AREA/'mapped-path.json'
    out.write_text(json.dumps(payload, indent=2, sort_keys=True)+'\n')
    print('V116_MAPPED_INPUTS', sha(out), 'nodes', len(visited), 'leaves', len(leaves))


if __name__ == '__main__':
    main()
