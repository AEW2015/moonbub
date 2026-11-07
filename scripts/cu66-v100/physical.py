#!/usr/bin/env python3
"""Freeze, cold-prepare, run, and receipt the unchanged V100 OOC component.

Preparing never invokes Vivado. Binary/tool outputs stay outside the repository.
Use the connected Vivado Tcl session where available; run is the explicit batch
fallback and must be coordinated with the physical-job owner.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v100-baseline'
EVIDENCE = ROOT / 'experiments/python-gamebub-v100/physical'
RTL = ['fpga/experiments/' + name for name in (
    'cu66-v91/br88_rice_elastic.sv', 'cu66-v91b/br88_context.sv',
    'cu66-v91d/br88_packet_ingress.sv', 'cu66-v91g2/packed_scratch_v91g2.sv',
    'cu66-v91h/br88_packet_ingress_v91h.sv', 'cu66-v91h/br88_packet_ingress_sync_v91h.sv',
    'cu66-v91h/br88_pipeline_v91h.sv', 'cu66-v91i2/cs88_admission_v91i2a.sv',
    'cu66-v91i2b/byte_refill_queue_v91i2b.sv', 'cu66-v91j/cu66_inverse_stream_v91j.sv',
    'cu66-v69/inverse/cu66_dequant.sv', 'cu66-v69/inverse/cu66_idct8x8.sv',
    'cu66-v69/inverse/cu66_reconstruct_tile.sv', 'cu66-v91k/cs88_coefficients_v91k.sv',
    'cu66-v91k/cu66_reconstruct_stream_v91k.sv', 'cu66-v91k/cs88_pipeline_v91k.sv')]
HEADERS = ['fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh']
RECIPE = ['fpga/experiments/cu66-v100-baseline/' + x for x in
          ('build.tcl', 'component.xdc', 'policy.json')]
SCRIPT = 'scripts/cu66-v100/physical.py'
HOST_BUILD = Path('/home/lori/gamebub-build/cu66-v69')
LEAVES = dict(br88_rice_elastic=RTL[0], cu66_dequant=RTL[10],
              cu66_idct8x8=RTL[11], cu66_reconstruct_tile=RTL[12])


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def expected_manifest():
    policy = json.loads((AREA / 'policy.json').read_text())
    files = RTL + HEADERS + RECIPE + [SCRIPT]
    baseline = policy['baseline_commit']
    rtl_baseline = {}
    for name in RTL + HEADERS:
        original = subprocess.check_output(['git', 'show', baseline + ':' + name], cwd=ROOT)
        rtl_baseline[name] = hashlib.sha256(original).hexdigest()
        if rtl_baseline[name] != sha(ROOT / name):
            raise ValueError('baseline RTL modified: ' + name)
    return dict(schema='v100-frozen-component-inputs-v1', baseline_commit=baseline,
                top=policy['top'], part=policy['part'], policy=policy,
                rtl_sources=RTL, include_headers=HEADERS,
                include_directories=['fpga/experiments/cu66-v69/inverse'],
                init_files=[], xdc_files=[RECIPE[1]],
                source_sha256={name: sha(ROOT / name) for name in files},
                baseline_rtl_sha256=rtl_baseline)


def frozen_manifest():
    frozen = json.loads((AREA / 'frozen-inputs.json').read_text())
    if frozen != expected_manifest():
        raise ValueError('frozen input mismatch; review changes then explicitly --freeze')
    return frozen


def external_path(value):
    path = Path(value).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('build output must be outside the repository')
    return path


def tcl_word(value):
    value = str(value)
    if any(c in value for c in '{}\n\r'):
        raise ValueError('unsupported Tcl path characters')
    return '{' + value + '}'


def prepare(path):
    frozen = frozen_manifest()
    path = external_path(path)
    path.mkdir(parents=True, exist_ok=False)
    for name, digest in frozen['source_sha256'].items():
        target = path / 'snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
        if sha(target) != digest:
            raise ValueError('snapshot mismatch: ' + name)
    write_json(path / 'frozen-inputs.json', frozen)
    lines = ['# Generated from frozen-inputs.json; source snapshot is immutable.']
    for key in ('part', 'top'):
        lines.append('set ' + key + ' ' + tcl_word(frozen[key]))
    for key, names in (('rtl_sources', RTL), ('include_dirs', frozen['include_directories'])):
        lines.append('set ' + key + ' [list ' + ' '.join('[file join $build_dir snapshot ' + tcl_word(n) + ']' for n in names) + ']')
    lines.append('set constraint_file [file join $build_dir snapshot ' + tcl_word(RECIPE[1]) + ']')
    (path / 'frozen_inputs.tcl').write_text('\n'.join(lines) + '\n')
    include = '-I snapshot/fpga/experiments/cu66-v69/inverse'
    (path / 'yosys-full.ys').write_text('read_verilog -sv -noassert -D SYNTHESIS ' + include + ' ' +
                                      ' '.join('snapshot/' + x for x in RTL) + '\n' +
                                      'hierarchy -check -top ' + frozen['top'] + '\n')
    for top, source in LEAVES.items():
        commands = ['read_verilog -sv -noassert -D SYNTHESIS ' + include + ' snapshot/' + source,
                    'hierarchy -check -top ' + top, 'proc',
                    'write_json elaborated-' + top + '.json',
                    'synth_xilinx -top ' + top + ' -family xc7 -noiopad -noclkbuf',
                    'tee -o reports/yosys-' + top + '-stat.json stat -json -top ' + top,
                    'write_json mapped-' + top + '.json',
                    'write_verilog -noattr mapped-' + top + '.v']
        (path / ('yosys-' + top + '.ys')).write_text('\n'.join(commands) + '\n')
    write_json(path / 'preparation.json', dict(prepared_utc=now(), build_dir=str(path),
               source_manifest_sha256=sha(path / 'frozen-inputs.json'), cold_build=True,
               prior_checkpoints=[], note='Preparation only; Vivado has not run.'))
    print(path)


def resource_gate():
    mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    available = int(mem['MemAvailable'].split()[0]) * 1024
    full = next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    avg10 = float(dict(x.split('=') for x in full.split()[1:])['avg10'])
    result = dict(utc=now(), mem_available_bytes=available, memory_full_psi_avg10=avg10,
                  minimum_available_bytes=8 * 1024**3, maximum_full_psi_avg10_exclusive=1.0)
    result['pass'] = available >= result['minimum_available_bytes'] and avg10 < 1.0
    return result


def container_path(path, container):
    if container:
        return Path('/build') / path.relative_to(HOST_BUILD)
    return path


def run(path, vivado, container):
    path = external_path(path)
    frozen = json.loads((path / 'frozen-inputs.json').read_text())
    if list(path.glob('*.dcp')) or (path / 'vivado.log').exists():
        raise ValueError('cold run requires an unused prepared directory')
    for name, digest in frozen['source_sha256'].items():
        if sha(path / 'snapshot' / name) != digest:
            raise ValueError('snapshot changed: ' + name)
    # All V100 batch physical launches share one host lock; manual/MCP users
    # must obey the same one-physical-job ownership protocol.
    with open('/tmp/gamebub-v100-physical.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        gate = resource_gate()
        write_json(path / 'resource-gate.json', gate)
        if not gate['pass']:
            raise RuntimeError('resource gate denied launch; resume when pressure subsides')
        tool_path = container_path(path, container)
        prefix = ["docker", "exec", "-w", str(tool_path), container] if container else []
        with (path / 'vivado-tool-sha256.txt').open('w') as stream:
            subprocess.run(prefix + ['sha256sum', vivado], cwd=path, stdout=stream,
                           stderr=subprocess.STDOUT, check=True, timeout=30)
        argv = prefix + ['timeout', '--kill-after=10s', '1800s',
                vivado, '-mode', 'batch', '-nojournal', '-log', 'vivado.log', '-source',
                str(tool_path / 'snapshot' / RECIPE[0]), '-tclargs', str(tool_path)]
        receipt = dict(started_utc=now(), argv=argv, cwd=str(path), cold_build=True)
        write_json(path / 'launch.json', receipt)
        with (path / 'console.log').open('w') as log:
            result = subprocess.run(argv, cwd=path, stdout=log, stderr=subprocess.STDOUT, timeout=1820)
        receipt.update(exit_code=result.returncode, ended_utc=now())
        write_json(path / 'launch.json', receipt)
    collect(path)
    # A retained exact-part negative preflight is an expected prerequisite result.
    if 'V100_TARGET_PART_UNAVAILABLE' in (path / 'console.log').read_text() and not (path / 'synthesis-started.txt').exists():
        return 0
    return result.returncode


def yosys(path, container):
    path = external_path(path)
    if list(path.glob('mapped-*.json')) or (path / 'yosys-launch.json').exists():
        raise ValueError('Yosys requires an unused prepared cold directory')
    frozen = json.loads((path / 'frozen-inputs.json').read_text())
    if not all(sha(path / 'snapshot' / n) == h for n, h in frozen['source_sha256'].items()):
        raise ValueError('snapshot changed')
    tool_path = container_path(path, container)
    prefix = ['docker', 'exec', '-e', 'OMP_NUM_THREADS=1', '-w', str(tool_path), container] if container else []
    (path / 'reports').mkdir(exist_ok=True)
    launch = dict(started_utc=now(), commands=[], max_processes=1, address_space_bytes=2684354560,
                  scope='Generic xc7 technology mapping diagnostic only; no placement, routing, clock or exact-part fit.')
    with open('/tmp/gamebub-v100-physical.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        gate = resource_gate()
        write_json(path / 'resource-gate.json', gate)
        if not gate['pass']:
            raise RuntimeError('resource gate denied Yosys')
        for command, log in ((['/usr/bin/yosys', '-V'], 'yosys-version.txt'),
                             (['/usr/bin/yosys', '-Q', '-T', '-p', 'help synth_xilinx; help read_verilog; help stat'], 'yosys-help.txt'),
                             (['sha256sum', '/usr/bin/yosys', '/usr/bin/yosys-abc'], 'yosys-tool-sha256.txt')):
            with (path / log).open('w') as stream:
                subprocess.run(prefix + command, cwd=path, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=30)
        library_command = ['python3', '-c',
            'import hashlib,pathlib; root=pathlib.Path("/usr/share/yosys"); '
            'print("\\n".join(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+str(p) '
            'for p in sorted(root.rglob("*")) if p.is_file()))']
        with (path / 'yosys-library-sha256.txt').open('w') as stream:
            subprocess.run(prefix + library_command, cwd=path, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=30)
        for name, script in [('full-component-frontend', 'yosys-full.ys')] + [(x, 'yosys-' + x + '.ys') for x in LEAVES]:
            command = prefix + ['timeout', '--kill-after=5s', '600s', '/usr/bin/prlimit', '--as=2684354560', '/usr/bin/yosys', '-T', '-s', script]
            entry = dict(name=name, argv=command, script_sha256=sha(path / script), log='yosys-' + name + '.log')
            launch['commands'].append(entry)
            entry['resource_gate'] = resource_gate()
            if not entry['resource_gate']['pass']:
                raise RuntimeError('resource gate denied next Yosys leaf')
            began = time.monotonic()
            with (path / entry['log']).open('w') as stream:
                try:
                    result = subprocess.run(command, cwd=path, stdout=stream, stderr=subprocess.STDOUT, timeout=615)
                    entry['exit_code'] = result.returncode
                except subprocess.TimeoutExpired:
                    entry.update(exit_code=None, timeout=True)
            entry['wall_seconds'] = time.monotonic() - began
            write_json(path / 'yosys-launch.json', launch)
    launch['ended_utc'] = now()
    write_json(path / 'yosys-launch.json', launch)
    collect(path)


def collect(path):
    path = external_path(path)
    frozen = json.loads((path / 'frozen-inputs.json').read_text())
    receipt = dict(schema='v100-component-physical-receipt-v1', collected_utc=now(),
                   build_dir=str(path), top=frozen['top'], part=frozen['part'],
                   source_manifest_sha256=sha(path / 'frozen-inputs.json'),
                   status='COMPONENT_ROUTE_COMPLETE' if (path / 'flow-complete.txt').exists() else 'INCOMPLETE',
                   full_top_qualified=False, board_timing_qualified=False,
                   source_snapshot_verified=all(sha(path / 'snapshot' / n) == h for n, h in frozen['source_sha256'].items()),
                   artifacts={}, metrics={})
    receipt.update(synthesis_started=(path / 'synthesis-started.txt').exists(),
                   implementation_started=(path / 'implementation-started.txt').exists())
    if (path / 'console.log').exists() and 'V100_TARGET_PART_UNAVAILABLE' in (path / 'console.log').read_text():
        receipt['status'] = 'BLOCKED_TARGET_PART_UNAVAILABLE'
    if (path / 'yosys-launch.json').exists():
        receipt['yosys'] = json.loads((path / 'yosys-launch.json').read_text())
        frontend = receipt['yosys']['commands'][0]
        receipt['full_component_frontend'] = 'UNSUPPORTED' if frontend.get('exit_code') else 'ELABORATED_ONLY'
        receipt['status'] = 'DIAGNOSTIC_XC7_LEAF_MAPPING'
    target = EVIDENCE / path.name
    target.mkdir(parents=True, exist_ok=True)
    small = {'preparation.json', 'resource-gate.json', 'launch.json', 'tool-version.txt',
             'part-preflight.txt', 'report-status.tsv', 'flow-complete.txt', 'effective-constraints.xdc'}
    small |= {'yosys-launch.json', 'yosys-version.txt', 'yosys-help.txt', 'yosys-tool-sha256.txt',
              'yosys-library-sha256.txt', 'vivado-tool-sha256.txt', 'frozen-inputs.json'}
    for file in sorted(path.rglob('*')):
        if not file.is_file() or 'snapshot' in file.relative_to(path).parts:
            continue
        name = str(file.relative_to(path))
        receipt['artifacts'][name] = dict(sha256=sha(file), bytes=file.stat().st_size, external_path=str(file))
        # Compact reports only; DCP/log/binary data remains external, hash-pinned.
        compact_log = file.suffix == '.log' and file.stat().st_size <= 64 * 1024
        if (file.parent.name == 'reports' and file.stat().st_size <= 2 * 1024**2) or file.name in small or compact_log:
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, dest)
        if file.name.endswith('-metrics.tsv'):
            receipt['metrics'][file.stem] = dict(line.split('\t', 1) for line in file.read_text().splitlines()[1:])
        if file.name.startswith('yosys-') and file.name.endswith('-stat.json'):
            receipt['metrics'][file.stem] = json.loads(file.read_text())
    receipt['yosys_leaves'] = {}
    for top in LEAVES:
        file = path / ('mapped-' + top + '.json')
        if file.exists():
            netlist = json.loads(file.read_text())
            module = netlist['modules'][top]
            counts = {}
            dsp = []
            for cell_name, cell in module['cells'].items():
                kind = cell['type']
                counts[kind] = counts.get(kind, 0) + 1
                if kind == 'DSP48E1':
                    dsp.append(dict(cell=cell_name, type=kind, parameters=cell['parameters']))
            original = json.loads((path / ('elaborated-' + top + '.json')).read_text())['modules'][top]
            detail = dict(status='GENERIC_XC7_LEAF_MAPPED', primitive_counts=counts, dsp48e1=dsp,
                          module_instance_counts={k: v for k, v in counts.items() if k in netlist['modules'] and k != top and not int(netlist['modules'][k].get('attributes', {}).get('blackbox', '0'), 2)},
                          original_port_count=len(original['ports']), mapped_port_count=len(module['ports']),
                          exact_port_names_and_directions_preserved={k: v['direction'] for k, v in original['ports'].items()} == {k: v['direction'] for k, v in module['ports'].items()},
                          premap_memories=original.get('memories', {}),
                          mapped_netlist_sha256=sha(file))
            # Bit indices are encoding details; widths and directions are the port contract.
            detail['exact_port_widths_preserved'] = {k: len(v['bits']) for k, v in original['ports'].items()} == {k: len(v['bits']) for k, v in module['ports'].items()}
            receipt['yosys_leaves'][top] = detail
            write_json(target / ('yosys-' + top + '-mapping.json'), detail)
    if receipt.get('full_component_frontend') == 'UNSUPPORTED':
        receipt['status'] = 'PARTIAL_XC7_LEAF_MAPPING_FULL_TOP_FRONTEND_UNSUPPORTED'
    write_json(target / 'receipt.json', receipt)
    print(json.dumps(dict(status=receipt['status'], receipt=str(target / 'receipt.json'))))
    return receipt


def compare(paths):
    receipts = [collect(x) for x in paths]
    same_inputs = len({x['source_manifest_sha256'] for x in receipts}) == 1
    routed = all(x['status'] == 'COMPONENT_ROUTE_COMPLETE' for x in receipts)
    metrics_equal = receipts[0]['metrics'] == receipts[1]['metrics']
    leaves_equal = receipts[0]['yosys_leaves'] == receipts[1]['yosys_leaves']
    leaf_mapping_repeated = same_inputs and bool(receipts[0]['yosys_leaves']) and leaves_equal
    report = dict(schema='v100-component-repeatability-v1', build_dirs=[x['build_dir'] for x in receipts],
                  same_frozen_inputs=same_inputs, both_routed=routed, metrics_equal=metrics_equal,
                  status='REPEATABLE_COMPONENT_METRICS' if same_inputs and routed and metrics_equal else 'NOT_ESTABLISHED',
                  generic_xc7_leaf_mapping_repeated=leaf_mapping_repeated,
                  generic_leaf_mapped_netlist_hashes_equal=leaves_equal,
                  generic_leaf_names=sorted(receipts[0]['yosys_leaves']),
                  note='Metrics equality does not imply binary DCP equality, board timing, or whole-top fit.')
    name = 'yosys-repeatability.json' if any('yosys' in x for x in receipts) else 'repeatability.json'
    write_json(EVIDENCE / name, report)
    print(json.dumps(report))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--freeze', action='store_true')
    group.add_argument('--verify', action='store_true')
    group.add_argument('--prepare', metavar='EXTERNAL_BUILD_DIR')
    group.add_argument('--run', metavar='PREPARED_EXTERNAL_BUILD_DIR')
    group.add_argument('--collect', metavar='EXTERNAL_BUILD_DIR')
    group.add_argument('--yosys', metavar='PREPARED_EXTERNAL_BUILD_DIR')
    group.add_argument('--compare', nargs=2, metavar=('BUILD_A', 'BUILD_B'))
    parser.add_argument('--vivado', default='vivado')
    parser.add_argument('--container', help='Existing container, with HOST_BUILD mounted at /build')
    args = parser.parse_args()
    if args.freeze:
        write_json(AREA / 'frozen-inputs.json', expected_manifest())
    elif args.verify:
        frozen_manifest()
        print('FROZEN_INPUTS_MATCH_BASELINE')
    elif args.prepare:
        prepare(args.prepare)
    elif args.run:
        raise SystemExit(run(args.run, args.vivado, args.container))
    elif args.collect:
        collect(args.collect)
    elif args.yosys:
        yosys(args.yosys, args.container)
    else:
        compare(args.compare)


if __name__ == '__main__':
    main()
