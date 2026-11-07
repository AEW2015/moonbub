#!/usr/bin/env python3
"""Separate sv2v/Yosys xc7 diagnostic; never qualifies the exact Vivado target.

Conversion and frontend elaboration may run before paired RTL verification.
Technology mapping requires an explicit verification receipt from the owner.
All generated Verilog/netlists remain in a fresh directory outside Git.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('physical', ROOT / 'scripts/cu66-v100/physical.py')
physical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(physical)
SV2V = '/build/tools/sv2v-v0.0.13/sv2v'
CONTAINER = 'gamebub-cu66-v69-build'
AREA = ROOT / 'experiments/python-gamebub-v100/physical'


def command(build, argv, name, limit=600):
    gate = physical.resource_gate()
    if not gate['pass']:
        raise RuntimeError('resource gate denied ' + name)
    tool = physical.container_path(build, CONTAINER)
    # GHC reserves a large virtual arena even with a bounded live heap. Keep
    # sv2v single-capability/1GiB-heap instead of an incompatible RLIMIT_AS;
    # Yosys and its ABC child retain the 2.5GiB address-space cap.
    constrained = ([*argv, '+RTS', '-N1', '-M1024m', '-RTS'] if argv[0] == SV2V else
                   ['prlimit', '--as=2684354560', *argv])
    full = ['docker', 'exec', '-e', 'OMP_NUM_THREADS=1', '-w', str(tool), CONTAINER,
            'timeout', '--kill-after=5s', str(limit) + 's', *constrained]
    start = time.monotonic()
    with (build / (name + '.log')).open('w') as log:
        result = subprocess.run(full, stdout=log, stderr=subprocess.STDOUT, cwd=build, timeout=limit + 15)
    return dict(argv=full, exit_code=result.returncode, log=name + '.log', wall_seconds=time.monotonic() - start,
                resource_gate=gate)


def convert(build):
    build = physical.external_path(build)
    physical.prepare(build)
    local = dict(schema='v100-sv2v-conversion-v1', scope='Generic xc7 frontend diagnostic, no exact-part or timing qualification',
                 original_inputs_sha256=physical.sha(build / 'frozen-inputs.json'),
                 recipe_sha256=physical.sha(Path(__file__)),
                 top='cs88_pipeline_v91k', full_candidate=False,
                 sv2v_release_url='https://github.com/zachjs/sv2v/releases/tag/v0.0.13',
                 sv2v_asset_url='https://github.com/zachjs/sv2v/releases/download/v0.0.13/sv2v-Linux.zip',
                 publisher_checksum_available=False, commands=[])
    (build / 'reports').mkdir()
    tool = physical.container_path(build, CONTAINER)
    with open('/tmp/gamebub-v100-physical.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for argv, name in (([SV2V, '--version'], 'sv2v-version'),
                           ([SV2V, '--help'], 'sv2v-help'),
                           (['sha256sum', SV2V, '/build/tools/sv2v-v0.0.13/sv2v-Linux.zip', '/usr/bin/yosys', '/usr/bin/yosys-abc', '/usr/share/yosys/simlib.v'], 'tool-sha256')):
            local['commands'].append(command(build, argv, name, 30))
        library_command = ['python3', '-c',
            'import hashlib,pathlib; root=pathlib.Path("/usr/share/yosys"); '
            'print("\\n".join(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+str(p) '
            'for p in sorted(root.rglob("*")) if p.is_file()))']
        local['commands'].append(command(build, library_command, 'yosys-library-sha256', 30))
        inputs = ['snapshot/' + x for x in physical.RTL]
        argv = [SV2V, '--exclude=Always', '-D', 'SYNTHESIS', '-I', 'snapshot/fpga/experiments/cu66-v69/inverse',
                '--top=cs88_pipeline_v91k', '-w', 'converted.v', *inputs]
        local['commands'].append(command(build, argv, 'convert'))
        if local['commands'][-1]['exit_code'] == 0:
            local['converted_sha256'] = physical.sha(build / 'converted.v')
            local['converted_bytes'] = (build / 'converted.v').stat().st_size
            # A single command chain permits correction before Yosys's
            # command-boundary design validation. Exactly two fixed stages;
            # never normalize arbitrary cells or iterate after synthesis.
            normalize = 'setparam -set B_SIGNED 0 t:$shl t:$shr t:$sshl t:$sshr'
            stages = ['read_verilog -sv -noassert converted.v',
                      'dump -o stage1-before.il', normalize, 'dump -o stage1-after.il',
                      'hierarchy -check -top cs88_pipeline_v91k',
                      'dump -o stage2-before.il', normalize, 'dump -o stage2-after.il',
                      'write_rtlil elaborated-full.il',
                      'tee -o reports/premap-stat.json stat -json -top cs88_pipeline_v91k']
            script = '; '.join(stages)
            (build / 'frontend.ys').write_text(script + '\n')
            local['commands'].append(command(build, ['/usr/bin/yosys', '-T', '-p', script], 'frontend', 120))
            if local['commands'][-1]['exit_code'] == 0:
                auditor = Path(__file__).with_name('audit_shift_ir.py')
                shutil.copyfile(auditor, build / 'audit_shift_ir.py')
                local['normalization'] = dict(yosys_version='0.33', max_stages=2,
                    allowed_types=['$shl', '$shr', '$sshl', '$sshr'], parameter='B_SIGNED',
                    allowed_delta='1 -> 0 only', source_and_generated_Verilog_unchanged=True,
                    basis='Pinned simlib.v ignores B_SIGNED for exactly these four cell types; unsigned B port, A_SIGNED unchanged.')
                for stage in (1, 2):
                    subprocess.run(['python3', str(build / 'audit_shift_ir.py'), str(build / f'stage{stage}-before.il'),
                                    str(build / f'stage{stage}-after.il'), '--output', str(build / 'reports' / f'stage{stage}-delta-audit.json')],
                                   cwd=ROOT, check=True)
                local['elaborated_ir_sha256'] = physical.sha(build / 'elaborated-full.il')
                memories = []
                module = None
                for line in (build / 'elaborated-full.il').read_text().splitlines():
                    if line.startswith('module '):
                        module = line.split()[1]
                    if line.startswith('  memory '):
                        fields = line.split()
                        width = int(fields[fields.index('width') + 1]) if 'width' in fields else 1
                        size = int(fields[fields.index('size') + 1])
                        memories.append(dict(module=module, name=fields[-1], width_bits=width, depth=size, bits=width * size,
                                             declaration=line.strip()))
                physical.write_json(build / 'reports' / 'premap-memory-ledger.json', dict(memories=memories,
                    note='Logical frontend arrays before process/memory mapping; arrays replaced with registers are reported in frontend warnings. Physical primitive inference is a separate result.'))
        local['status'] = 'FRONTEND_ELABORATED_PAIRED_RTL_REQUIRED' if all(x['exit_code'] == 0 for x in local['commands']) else 'CONVERSION_OR_FRONTEND_FAILED'
    physical.write_json(build / 'conversion.json', local)
    collect(build)
    print(json.dumps(dict(status=local['status'], build=str(build))))


def mapping(build, verification):
    build = physical.external_path(build)
    conversion = json.loads((build / 'conversion.json').read_text())
    if conversion['status'] != 'FRONTEND_ELABORATED_PAIRED_RTL_REQUIRED':
        raise ValueError('conversion/frontend must succeed before mapping')
    if conversion['converted_sha256'] != physical.sha(build / 'converted.v'):
        raise ValueError('converted Verilog changed')
    check = json.loads(verification.read_text())
    # Verification is an explicit owner-authored receipt; compare its pinned
    # generated input, complete-case verdict, and both deterministic seeds.
    if check.get('converted_sha256') != conversion['converted_sha256'] or check.get('status') != 'PAIRED_RTL_PASS' or len(set(check.get('seeds', []))) != 2:
        raise ValueError('requires paired complete V99-vector RTL receipt for this exact generated Verilog and two seeds')
    local = dict(schema='v100-sv2v-yosys-mapping-v1', verification_receipt_sha256=physical.sha(verification),
                 converted_sha256=conversion['converted_sha256'], recipe_sha256=physical.sha(Path(__file__)),
                 scope='Generic xc7 technology mapping of converted available component; no placement/routing/timing or full candidate proof',
                 commands=[], full_top_qualified=False, target_part_fit_qualified=False)
    shutil.copyfile(verification, build / 'paired-verification.json')
    if physical.sha(build / 'elaborated-full.il') != conversion['elaborated_ir_sha256']:
        raise ValueError('normalized elaborated IR changed')
    script = 'read_rtlil elaborated-full.il\nsynth_xilinx -top cs88_pipeline_v91k -family xc7 -noiopad -noclkbuf\ntee -o reports/mapped-stat.json stat -json -top cs88_pipeline_v91k\nwrite_json mapped-full.json\nwrite_verilog -noattr mapped-full.v\n'
    (build / 'mapping.ys').write_text(script)
    with open('/tmp/gamebub-v100-physical.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        local['commands'].append(command(build, ['/usr/bin/yosys', '-T', '-s', 'mapping.ys'], 'mapping', 1200))
    local['status'] = 'GENERIC_XC7_COMPONENT_MAPPED' if local['commands'][-1]['exit_code'] == 0 else 'MAPPING_FAILED_OR_RESOURCE_LIMIT'
    if local['status'] == 'GENERIC_XC7_COMPONENT_MAPPED':
        local['summary'] = summarize_mapping(build, check)
    physical.write_json(build / 'mapping.json', local)
    collect(build)
    print(json.dumps(dict(status=local['status'], build=str(build))))


def collect(build):
    target = AREA / build.name
    target.mkdir(parents=True, exist_ok=True)
    artifacts = {}
    for file in sorted(build.rglob('*')):
        if not file.is_file() or 'snapshot' in file.relative_to(build).parts:
            continue
        name = str(file.relative_to(build))
        artifacts[name] = dict(sha256=physical.sha(file), bytes=file.stat().st_size, external_path=str(file))
        if file.name in {'conversion.json', 'mapping.json', 'paired-verification.json', 'frozen-inputs.json',
                         'sv2v-help.log', 'sv2v-version.log', 'tool-sha256.log', 'yosys-library-sha256.log', 'convert.log'} or file.parent.name == 'reports' or (file.suffix in {'.ys', '.log'} and file.stat().st_size <= 65536):
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, dest)
    physical.write_json(target / 'artifacts.json', artifacts)


def summarize_mapping(build, verification):
    netlist_file = build / 'mapped-full.json'
    netlist = json.loads(netlist_file.read_text())
    modules = netlist['modules']
    instances = []
    dsps = []

    def walk(module_name, path):
        counts = {}
        for name, cell in modules[module_name].get('cells', {}).items():
            kind = cell['type']
            if kind in modules and not int(modules[kind].get('attributes', {}).get('blackbox', '0'), 2):
                child = walk(kind, path + '/' + name)
                for primitive, number in child.items():
                    counts[primitive] = counts.get(primitive, 0) + number
            else:
                counts[kind] = counts.get(kind, 0) + 1
                if kind == 'DSP48E1':
                    dsps.append(dict(path=path + '/' + name, parameters=cell['parameters'], connections=cell['connections']))
        instances.append(dict(path=path, module=module_name, subtree_primitive_counts=counts))
        return counts

    total = walk('cs88_pipeline_v91k', 'cs88_pipeline_v91k')
    # Normalize only external cold-build path prefixes in provenance attributes.
    # Raw netlist hashes are retained alongside this explicitly narrow digest.
    def provenance(value):
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                if key == 'attributes' and isinstance(item, dict):
                    result[key] = {name: text.replace(str(build), '${COLD_BUILD}').replace(str(physical.container_path(build, CONTAINER)), '${COLD_BUILD}')
                                   if name == 'src' and isinstance(text, str) else text for name, text in item.items()}
                else:
                    result[key] = provenance(item)
            return result
        if isinstance(value, list):
            return [provenance(x) for x in value]
        return value

    normalized = json.dumps(provenance(netlist), sort_keys=True, separators=(',', ':')).encode()
    audit_file = ROOT / verification['port_audit']
    if physical.sha(audit_file) != verification['port_audit_sha256']:
        raise ValueError('paired public-port audit changed')
    audit = json.loads(audit_file.read_text())
    expected = {x['name']: (x['direction'], x['total_bits']) for x in audit['all_port_rows']}
    actual = {name: (port['direction'], len(port['bits'])) for name, port in modules['cs88_pipeline_v91k']['ports'].items()}
    if expected != actual:
        raise ValueError('mapped public port contract changed')
    result = dict(primitive_counts=total, hierarchy=instances, dsp48e1=dsps,
                  mapped_netlist_sha256=physical.sha(netlist_file),
                  provenance_normalized_sha256=hashlib.sha256(normalized).hexdigest(),
                  normalization='Canonical JSON key order; only attributes.src external cold-build absolute prefixes replaced by ${COLD_BUILD}. All cell types/parameters/ports/connections retained.',
                  public_ports_verified=len(actual), all_public_names_directions_widths_preserved=True)
    physical.write_json(build / 'reports' / 'mapped-summary.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--convert', type=Path)
    group.add_argument('--map', type=Path)
    group.add_argument('--collect', type=Path)
    parser.add_argument('--verification', type=Path)
    args = parser.parse_args()
    if args.convert:
        convert(args.convert)
    elif args.map:
        if not args.verification:
            parser.error('--map requires --verification')
        mapping(args.map, args.verification)
    else:
        collect(physical.external_path(args.collect))


if __name__ == '__main__':
    main()
