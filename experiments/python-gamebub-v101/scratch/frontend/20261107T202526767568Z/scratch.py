#!/usr/bin/env python3
"""Bounded V101 actual-RTL scratch priority comparison and frontend probe."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v101/scratch'
SRC = ROOT / 'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'
CAND = ROOT / 'fpga/experiments/cu66-v101-scratch/packed_scratch_v91g2.sv'
CONTAINER = 'gamebub-cu66-v69-build'
sys.path.insert(0, str(ROOT / 'scripts/cu66-v100'))
from run_rtl import resources


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, obj):
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def ports():
    header = SRC.read_text().split(');', 1)[0] + ');'
    result = []
    inherited = None
    for item in header.split('(', 1)[1].rsplit(');', 1)[0].split(','):
        item = re.sub(r'//[^\n]*', '', item).strip()
        m = re.fullmatch(r'(input|output)\s+logic\s+(signed\s+)?(\[\d+:\d+\]\s+)?(.+)', item, re.S)
        if m:
            direction, signed, packed, item = m.groups()
            inherited = (direction, signed or '', packed or '')
        assert inherited, item
        item = item.split('=')[0].strip()
        n = re.fullmatch(r'(\w+)\s*(\[\d+:\d+\])?', item)
        assert n, item
        result.append(dict(name=n[1], unpacked=n[2] or '', direction=inherited[0], signed=inherited[1], packed=inherited[2]))
    return header, result


def prepare(build):
    header, pp = ports()
    for src, name in [(SRC, 'scratch_original'), (CAND, 'scratch_candidate')]:
        (build / (name + '.sv')).write_text(src.read_text().replace('module packed_scratch_v91g2 (', 'module ' + name + ' (', 1))
    header = header.replace('module packed_scratch_v91g2 (', 'module scratch_probe (', 1).replace(');', ', output logic probe_outputs_equal, probe_internal_equal);')
    lines = [header]
    for p in pp:
        if p['direction'] == 'output':
            lines.append(f"logic {p['signed']}{p['packed']} old_{p['name']}{p['unpacked']};")
    for module, inst, old in [('scratch_original', 'old_dut', True), ('scratch_candidate', 'new_dut', False)]:
        conns = ['.' + p['name'] + '(' + ('old_' if old and p['direction'] == 'output' else '') + p['name'] + ')' for p in pp]
        lines.append(module + ' ' + inst + '(' + ','.join(conns) + ');')
    checks = ['old_' + p['name'] + ' == ' + p['name'] for p in pp if p['direction'] == 'output']
    lines.append('assign probe_outputs_equal = ' + ' && '.join('(' + x + ')' for x in checks) + ';')
    lines.append('assign probe_internal_equal = ' + ' && '.join('(old_dut.' + x + ' == new_dut.' + x + ')' for x in ['candidate_valid', 'candidate_segment', 'candidate_address', 'candidate_word_address', 'prefetch_launch']) + ';')
    lines.append('endmodule')
    (build / 'scratch_probe.sv').write_text('\n'.join(lines) + '\n')
    write(build / 'public-ports.json', pp)
    shutil.copyfile(ROOT / 'fpga/experiments/cu66-v101-scratch/tb_probe.cpp', build / 'tb_probe.cpp')


def command(build, args, name, timeout, cap=False):
    gate = resources()
    cpath = '/build/' + build.name
    full = ['docker', 'exec', '-e', 'OMP_NUM_THREADS=1', '-w', cpath, CONTAINER,
            'timeout', '--kill-after=5s', str(timeout) + 's']
    if cap:
        full += ['prlimit', '--as=2684354560']
    full += args
    start = time.monotonic()
    with (build / name).open('w') as log:
        p = subprocess.run(full, stdout=log, stderr=subprocess.STDOUT, timeout=timeout + 15)
    return dict(argv=full, exit_code=p.returncode, wall_seconds=time.monotonic() - start,
                log=name, resource_gate=gate)


def collect(build, out):
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name in ['scratch.py', 'tool-versions.log', 'tool-hashes.log', 'candidate.sv', 'receipt.json', 'scratch_original.sv', 'scratch_candidate.sv', 'scratch_probe.sv', 'public-ports.json', 'tb_probe.cpp', 'compile.log', 'seed-101401.log', 'seed-101402.log', 'probe-seed-101401.jsonl', 'probe-seed-101402.jsonl', 'frontend.log', 'conversion.log', 'frontend.ys', 'converted.sv', 'frontend-stat.json']:
        p = build / name
        if not p.is_file():
            continue
        if p.suffix == '.jsonl':
            q = out / (name + '.gz')
            with q.open('wb') as raw:
                with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as z:
                    z.write(p.read_bytes())
            artifacts[q.name] = {'sha256': sha(q), 'uncompressed_sha256': sha(p), 'records': sum(1 for _ in p.open())}
        else:
            q = out / name
            shutil.copyfile(p, q)
            artifacts[q.name] = {'sha256': sha(q), 'bytes': q.stat().st_size}
    write(out / 'artifacts.json', artifacts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend', action='store_true')
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    build = Path('/home/lori/gamebub-build/cu66-v69') / ('v101-scratch-' + stamp)
    build.mkdir(parents=True, exist_ok=False)
    out = AREA / ('frontend' if args.frontend else 'probe') / stamp
    shutil.copyfile(Path(__file__), build / 'scratch.py')
    receipt = dict(schema='v101-scratch-frontend-v1' if args.frontend else 'v101-scratch-priority-probe-v1', status='FAIL',
                   baseline_commit='e8bb1c9cc3cec6775cf128c8fd538a56f022575f',
                   original={'path': str(SRC.relative_to(ROOT)), 'sha256': sha(SRC)},
                   candidate={'path': str(CAND.relative_to(ROOT)), 'sha256': sha(CAND)},
                   runner_sha256=sha(Path(__file__)), commands=[],
                   scope='Combinational-state actual RTL comparison, no clock edges or sequential/hardware claim.' if not args.frontend else 'Scratch-only standard conversion/process lowering; not complete component mapping or physical timing.')
    receipt['commands'].append(command(build, ['sh', '-c', 'verilator --version; g++ --version; yosys -V; /build/tools/sv2v-v0.0.13/sv2v --version'], 'tool-versions.log', 30))
    receipt['commands'].append(command(build, ['sha256sum', '/usr/bin/verilator_bin', '/usr/bin/g++', '/usr/bin/yosys', '/usr/share/yosys/simlib.v', '/build/tools/sv2v-v0.0.13/sv2v'], 'tool-hashes.log', 30))
    if args.frontend:
        shutil.copyfile(CAND, build / 'candidate.sv')
        sv = '/build/tools/sv2v-v0.0.13/sv2v'
        cmd = [sv, '-D', 'SYNTHESIS', '--exclude=Always', 'candidate.sv', '+RTS', '-N1', '-M1024m', '-RTS']
        entry = command(build, cmd, 'conversion.log', 120)
        receipt['commands'].append(entry)
        if entry['exit_code'] == 0:
            shutil.copyfile(build / 'conversion.log', build / 'converted.sv')
            ys = 'read_verilog -sv converted.sv; hierarchy -check -top packed_scratch_v91g2; proc; tee -o frontend-stat.json stat -json -top packed_scratch_v91g2'
            (build / 'frontend.ys').write_text(ys + '\n')
            entry = command(build, ['yosys', '-T', '-p', ys], 'frontend.log', 360, cap=True)
            receipt['commands'].append(entry)
            receipt['status'] = 'PASS_SCRATCH_PROCESS_LOWERING' if entry['exit_code'] == 0 else 'FRONTEND_FAILED_OR_LIMITED'
            text = (build / 'frontend.log').read_text()
            receipt['old_iterator_latch_fatal_present'] = 'Latch inferred for signal' in text and 'sv2v_autoblock' in text
            receipt['postprocess_mapped_or_routed'] = False
    else:
        prepare(build)
        entry = command(build, ['verilator', '--cc', '--exe', '--build', '--top-module', 'scratch_probe', '--assert', '-Wall', '-Wno-DECLFILENAME', '--public-flat-rw', '-j', '2', '-Mdir', 'obj', '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror', 'scratch_original.sv', 'scratch_candidate.sv', 'scratch_probe.sv', 'tb_probe.cpp'], 'compile.log', 300)
        receipt['commands'].append(entry)
        if entry['exit_code'] == 0:
            verdicts = []
            for seed in [101401, 101402]:
                e = command(build, ['./obj/Vscratch_probe', str(seed)], f'seed-{seed}.log', 120)
                receipt['commands'].append(e)
                text = (build / f'seed-{seed}.log').read_text()
                lines = [json.loads(x) for x in text.splitlines() if x.startswith('{')]
                assert e['exit_code'] == 0 and len(lines) == 1 and lines[0]['status'] == 'TEST_PASS', text
                verdicts.extend(lines)
            receipt['binary_sha256'] = sha(build / 'obj/Vscratch_probe')
            receipt['verdicts'] = verdicts
            receipt['status'] = 'PASS_ACTUAL_RTL_PRIORITY_CONE'
    write(build / 'receipt.json', receipt)
    collect(build, out)
    AREA.mkdir(parents=True, exist_ok=True)
    write(AREA / ('frontend-results.json' if args.frontend else 'probe-results.json'), dict(status=receipt['status'], selected_receipt=str((out / 'receipt.json').relative_to(ROOT)), sha256=sha(out / 'receipt.json')))
    print(out.relative_to(ROOT), receipt['status'])
    if receipt['status'] == 'FAIL':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
