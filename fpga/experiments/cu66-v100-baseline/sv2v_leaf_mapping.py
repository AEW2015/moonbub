#!/usr/bin/env python3
"""Bounded direct sv2v/Yosys leaf mapping, with no IR normalization.

Root-approved exception: one 512000-KiB leaf alongside the bounded full job.
Launch below 2GB cgroup use; terminate only the leaf above 3.5GB. Full source
behavioral verification must identify the exact input converted Verilog.
"""
import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('physical', ROOT / 'scripts/cu66-v100/physical.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
CONTAINER = 'gamebub-cu66-v69-build'


def cgroup():
    output = subprocess.check_output(['docker', 'exec', CONTAINER, 'cat', '/sys/fs/cgroup/memory.current',
                                      '/sys/fs/cgroup/memory.max'], text=True, timeout=10).splitlines()
    return dict(current_bytes=int(output[0]), maximum_bytes=int(output[1]))


def run(build, top, source, verification, solo, dsp_only):
    check = json.loads(verification.read_text())
    if check.get('status') != 'PAIRED_RTL_PASS' or check.get('converted_sha256') != p.sha(source) or len(set(check.get('seeds', []))) != 2:
        raise ValueError('requires paired full-source qualification for exact generated input')
    build = p.external_path(build)
    gate = p.resource_gate()
    memory = cgroup()
    if not gate['pass'] or memory['current_bytes'] >= 2000000000:
        raise RuntimeError('launch gate requires passing host gate and cgroup usage below2GB')
    limit = 2684354560 if solo else 524288000
    timeout = 600 if solo else 180
    with contextlib.ExitStack() as stack:
        lock = stack.enter_context(open('/tmp/gamebub-v100-leaf.lock', 'w'))
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if solo:
            full_lock = stack.enter_context(open('/tmp/gamebub-v100-physical.lock', 'w'))
            fcntl.flock(full_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        p.prepare(build)
        shutil.copyfile(source, build / 'converted.v')
        shutil.copyfile(verification, build / 'paired-verification.json')
        shutil.copyfile(Path(__file__), build / 'leaf-recipe.py')
        (build / 'reports').mkdir()
        script = ('read_verilog -sv -noassert -defer converted.v\nhierarchy -check -top ' + top +
                  '\nproc\nwrite_json premap.json\n' +
                  'synth_xilinx -top ' + top + ' -family xc7 -noiopad -noclkbuf -run begin:coarse\n' +
                  'tee -o reports/dsp-stage-stat.json stat -json -top ' + top + '\n' +
                  'write_json dsp-stage.json\n')
        if not dsp_only:
            script += ('synth_xilinx -top ' + top + ' -family xc7 -noiopad -noclkbuf -run coarse:\n' +
                       'tee -o reports/mapped-stat.json stat -json -top ' + top + '\n' +
                       'write_json mapped.json\nwrite_verilog -noattr mapped.v\n')
        (build / 'leaf.ys').write_text(script)
        tool = p.container_path(build, CONTAINER)
        prefix = ['docker', 'exec', '-e', 'OMP_NUM_THREADS=1', '-w', str(tool), CONTAINER]
        with (build / 'tool-sha256.txt').open('w') as stream:
            subprocess.run(prefix + ['sha256sum', '/usr/bin/yosys', '/usr/bin/yosys-abc', '/usr/share/yosys/simlib.v'],
                           cwd=build, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=20)
        with (build / 'tool-version.txt').open('w') as stream:
            subprocess.run(prefix + ['/usr/bin/yosys', '-V'], cwd=build, stdout=stream,
                           stderr=subprocess.STDOUT, check=True, timeout=20)
        library_command = ['python3', '-c',
            'import hashlib,pathlib; root=pathlib.Path("/usr/share/yosys"); '
            'print("\\n".join(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+str(p) '
            'for p in sorted(root.rglob("*")) if p.is_file()))']
        with (build / 'yosys-library-sha256.txt').open('w') as stream:
            subprocess.run(prefix + library_command, cwd=build, stdout=stream,
                           stderr=subprocess.STDOUT, check=True, timeout=20)
        shell = 'echo "$$" > leaf-driver.pid; exec timeout --kill-after=5s ' + str(timeout) + 's prlimit --core=0 --as=' + str(limit) + ' /usr/bin/yosys -T -s leaf.ys'
        argv = prefix + ['sh', '-c', shell]
        report = dict(schema='v100-generic-xc7-direct-converted-leaf-v1', top=top, status='RUNNING', argv=argv,
                      original_source_manifest_sha256=p.sha(build / 'frozen-inputs.json'), converted_sha256=p.sha(build / 'converted.v'),
                      verification_sha256=p.sha(verification), recipe_sha256=p.sha(Path(__file__)),
                      script_sha256=p.sha(build / 'leaf.ys'), ir_normalization=False,
                      stop_after_map_dsp=dsp_only,
                      address_space_limit_bytes=limit, address_space_limit_KiB=limit//1024, timeout_seconds=timeout,
                      sole_job_physical_lock=solo, tool_library_catalog_sha256=p.sha(build / 'yosys-library-sha256.txt'),
                      resource_gate=gate, launch_cgroup=memory, monitor=[],
                      target_part_fit_qualified=False, timing_qualified=False, full_component_mapped=False)
        began = time.monotonic()
        with (build / 'mapping.log').open('w') as log:
            child = subprocess.Popen(argv, cwd=build, stdout=log, stderr=subprocess.STDOUT)
            while child.poll() is None:
                observed = cgroup()
                report['monitor'].append(dict(elapsed_seconds=time.monotonic() - began, **observed))
                if observed['current_bytes'] >= 3500000000 or time.monotonic() - began > timeout + 15:
                    driver = int((build / 'leaf-driver.pid').read_text())
                    subprocess.run(['docker', 'exec', CONTAINER, 'kill', '-TERM', str(driver)], check=True, timeout=10)
                    report['terminated_for_resource_gate'] = True
                    break
                time.sleep(5)
            code = child.wait(timeout=15)
        report.update(exit_code=code, wall_seconds=time.monotonic() - began)
        if (build / 'dsp-stage.json').exists():
            stage = json.loads((build / 'dsp-stage.json').read_text())
            stage_module = stage['modules'][top]
            original = json.loads((build / 'premap.json').read_text())['modules'][top]
            ports = {k: (x['direction'], len(x['bits'])) for k, x in stage_module['ports'].items()}
            original_ports = {k: (x['direction'], len(x['bits'])) for k, x in original['ports'].items()}
            if ports != original_ports:
                raise ValueError('DSP-stage public port contract changed')
            counts = {}
            dsp = []
            for name, cell in stage_module['cells'].items():
                counts[cell['type']] = counts.get(cell['type'], 0) + 1
                if cell['type'] == 'DSP48E1':
                    dsp.append(dict(cell=name, parameters=cell['parameters'], connections=cell['connections']))
            canonical = json.dumps(stage, sort_keys=True, separators=(',', ':')).encode()
            report['dsp_stage'] = dict(status='PARTIAL_DSP_STAGE_ONLY', cell_type_counts=counts, dsp48e1=dsp,
                 raw_sha256=p.sha(build / 'dsp-stage.json'), canonical_sha256=hashlib.sha256(canonical).hexdigest(),
                 public_ports_preserved=len(ports), exact_port_names_directions_widths_preserved=True,
                 qualification='DSP primitive inference/packing checkpoint only; generic cells remain. No completed LUT/FF/BRAM/SRL technology map, area/fit, placement, route or timing result.')
            p.write_json(build / 'reports' / 'dsp-stage-summary.json', report['dsp_stage'])
        if code == 0 and not dsp_only:
            netlist = json.loads((build / 'mapped.json').read_text())
            original = json.loads((build / 'premap.json').read_text())['modules'][top]
            module = netlist['modules'][top]
            original_ports = {k: (x['direction'], len(x['bits'])) for k, x in original['ports'].items()}
            mapped_ports = {k: (x['direction'], len(x['bits'])) for k, x in module['ports'].items()}
            if original_ports != mapped_ports:
                raise ValueError('leaf public port contract changed')
            counts = {}
            dsp = []
            for name, cell in module['cells'].items():
                kind = cell['type']
                counts[kind] = counts.get(kind, 0) + 1
                if kind == 'DSP48E1':
                    dsp.append(dict(cell=name, parameters=cell['parameters'], connections=cell['connections']))
            # The generated source is local converted.v in both cold roots;
            # no provenance path substitution is needed or performed.
            canonical = json.dumps(netlist, sort_keys=True, separators=(',', ':')).encode()
            report.update(status='GENERIC_XC7_LEAF_MAPPED', primitive_counts=counts, dsp48e1=dsp,
                          premap_memories=original.get('memories', {}), public_ports_preserved=len(mapped_ports),
                          exact_port_names_directions_widths_preserved=True, mapped_sha256=p.sha(build / 'mapped.json'),
                          canonical_netlist_sha256=hashlib.sha256(canonical).hexdigest(),
                          canonicalization='JSON key order/spacing only; no fields, paths, cell types, parameters or connections removed.')
        elif code == 0 and dsp_only:
            report['status'] = 'PARTIAL_DSP_STAGE_ONLY'
        else:
            report['status'] = 'LEAF_MAPPING_FAILED_OR_RESOURCE_LIMIT'
        p.write_json(build / 'leaf-receipt.json', report)
    collect(build)
    print(json.dumps(dict(status=report['status'], top=top, build=str(build))))


def collect(build):
    dest = ROOT / 'experiments/python-gamebub-v100/physical' / build.name
    dest.mkdir(parents=True, exist_ok=True)
    artifacts = {}
    for source in sorted(build.rglob('*')):
        if not source.is_file() or 'snapshot' in source.relative_to(build).parts:
            continue
        name = str(source.relative_to(build))
        artifacts[name] = dict(sha256=p.sha(source), bytes=source.stat().st_size, external_path=str(source))
        if source.name in {'leaf-receipt.json', 'paired-verification.json', 'tool-sha256.txt', 'tool-version.txt',
                           'frozen-inputs.json', 'leaf.ys', 'yosys-library-sha256.txt'} or source.parent.name == 'reports' or (source.suffix == '.log' and source.stat().st_size <=65536):
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    p.write_json(dest / 'artifacts.json', artifacts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--top', required=True, choices=['cu66_idct8x8', 'cu66_dequant'])
    parser.add_argument('--converted', required=True, type=Path)
    parser.add_argument('--verification', required=True, type=Path)
    parser.add_argument('--solo', action='store_true', help='Sole physical-job lock, 2.5GiB/600s; no concurrent full job')
    parser.add_argument('--dsp-only', action='store_true', help='Retain partial map_dsp checkpoint; do not claim completed leaf mapping')
    args = parser.parse_args()
    run(args.build, args.top, args.converted, args.verification, args.solo, args.dsp_only)


if __name__ == '__main__':
    main()
