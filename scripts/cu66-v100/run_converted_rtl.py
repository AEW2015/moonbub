#!/usr/bin/env python3
"""Qualify the full sv2v V91k conversion against unchanged RTL and benches."""
import argparse
from collections import Counter
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
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v100/converted-rtl'
SIM_AREA = ROOT / 'fpga/experiments/cu66-v100-sim'
CONTAINER = 'gamebub-cu66-v69-build'
sys.path.insert(0, str(Path(__file__).parent))
from run_rtl import resources


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def compress(path):
    if not path.exists():
        return None
    raw_sha = sha(path)
    target = path.with_suffix(path.suffix + '.gz')
    with path.open('rb') as src, target.open('wb') as dest:
        with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=9) as packed:
            shutil.copyfileobj(src, packed)
    need(hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest() == raw_sha, 'gzip roundtrip')
    receipt = dict(path=target.name, raw_sha256=raw_sha, gzip_sha256=sha(target))
    path.unlink()
    return receipt


def make_wrapper(original, converted, target):
    top = 'cs88_pipeline_v91k'
    header = original.read_text().split(');', 1)[0] + ');'
    # All declarations in this frozen top use literal packed/unpacked bounds.
    declarations = header.split('(', 1)[1].rsplit(');', 1)[0].split(',')
    ports = []
    direction = packed = signed = None
    for item in declarations:
        item = item.strip()
        match = re.fullmatch(r'(input|output)\s+logic\s+(signed\s+)?(\[\d+:\d+\]\s+)?(.+)', item)
        if match:
            direction, signed, packed, item = match.groups()
        match = re.fullmatch(r'(\w+)\s*(?:\[(\d+):(\d+)\])?', item.strip())
        need(match is not None and direction is not None, 'unparsed port ' + item)
        name, left, right = match.groups()
        bounds = re.findall(r'\d+', packed or '')
        width = abs(int(bounds[0]) - int(bounds[1])) + 1 if bounds else 1
        ports.append(dict(name=name, direction=direction, width=width,
                          unpacked=None if left is None else [int(left), int(right)]))
    text = converted.read_text()
    need(len(re.findall(r'\bmodule\s+' + top + r'\b', text)) == 1, 'converted top uniqueness')
    renamed = re.sub(r'\bmodule\s+' + top + r'\b', 'module ' + top + '_sv2v', text)
    renamed_path = target / 'br88_rice_elastic.v'
    renamed_path.write_text(renamed)
    lines = [header, '// Verification adapter: only direct port wires and array unpacking.']
    connections = []
    array_mappings = []
    for port in ports:
        name, width, unpacked = port['name'], port['width'], port['unpacked']
        if unpacked is None:
            connections.append('.' + name + '(' + name + ')')
            continue
        need(port['direction'] == 'output' and unpacked[0] == 0, 'unsupported array direction/bounds')
        count = unpacked[1] + 1
        flat = 'flat_' + name
        lines.append(f'wire [{count * width - 1}:0] {flat};')
        connections.append('.' + name + '(' + flat + ')')
        for index in range(count):
            low = (count - 1 - index) * width
            lines.append(f'assign {name}[{index}] = {flat}[{low} +: {width}];')
        array_mappings.append(dict(name=name, element_width=width, elements=count,
                                   rule='original[i] = converted[(elements-1-i)*width +: width]'))
    lines.append(top + '_sv2v dut(' + ','.join(connections) + ');')
    lines.append('endmodule')
    wrapper = target / 'cs88_pipeline_v91k.sv'
    wrapper.write_text('\n'.join(lines) + '\n')
    # No new behavior: ensure every original port appears exactly once by name.
    need(len(connections) == len(ports) and len({p['name'] for p in ports}) == len(ports), 'port bijection')
    return wrapper, renamed_path, dict(ports=len(ports), arrays=array_mappings,
                                       top_rename_count=1, all_ports_preserved_once=True,
                                       wrapper_contains_only_direct_connections_and_slice_assignments=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--converted', type=Path, required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=[911501, 911502])
    args = parser.parse_args()
    need(len(args.seeds) == 2 and len(set(args.seeds)) == 2, 'two distinct seeds required')
    converted = args.converted.resolve()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    manifest_path = ROOT / 'fpga/experiments/cu66-v100-baseline/frozen-inputs.json'
    manifest = json.loads(manifest_path.read_text())
    rtl = [ROOT / p for p in manifest['rtl_sources']]
    header = ROOT / manifest['include_headers'][0]
    bench = ROOT / 'fpga/experiments/cu66-v91k/tb_pipeline.cpp'
    rgb_sv = ROOT / 'fpga/experiments/cu66-v91k/rgb/canonical_rgb565_v91k.sv'
    rgb_cpp = rgb_sv.with_name('tb_rgb.cpp')
    sources = rtl + [header, bench, rgb_sv, rgb_cpp, Path(__file__).resolve(),
                     ROOT / 'scripts/cu66-v100/run_rtl.py', manifest_path]
    report = dict(schema='cu66-v100-paired-full-v91k-sv2v-rtl-v1', status='FAIL',
                  baseline_revision=manifest['baseline_commit'], top='cs88_pipeline_v91k',
                  backend='Verilator 5.020, explicitly configured behavioral simulation',
                  converted_source=str(converted), converted_sha256=sha(converted),
                  seeds=args.seeds, commands=[], runs=[], actual_RTL_run=False,
                  conversion_flags=['--exclude=Always', '-D SYNTHESIS'],
                  warning_policy_documentation='https://verilator.org/guide/latest/exe_verilator.html#cmdoption-Wno-fatal',
                  assertion_policy='Original RTL --assert active; converted physical SYNTHESIS branch omits guarded RTL assertions; unchanged C++ checker active in both.',
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  limitations=['Bounded behavioral regression; not formal equivalence.',
                               'Verification-only wrapper restores public unpacked arrays with wires.',
                               'Converted-only -Wno-fatal retains all warnings; exact observed class allowlist enforced after compile.',
                               'No mapped-netlist simulation, timing, full board publication or hardware FPS proof.'])
    began = time.monotonic()
    plain = []
    build = '/build/v100-converted-' + out.name

    def command(argv, log_name, timeout=900):
        entry = dict(argv=argv, log=log_name, timeout_seconds=timeout, exit_code=None)
        report['commands'].append(entry)
        start = time.monotonic()
        with (out / log_name).open('w') as log:
            try:
                done = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
                entry['exit_code'] = done.returncode
            finally:
                entry['wall_seconds'] = time.monotonic() - start
        need(done.returncode == 0, 'command failure ' + log_name)
        return (out / log_name).read_text()

    def expand(source, name):
        dest = out / 'inputs' / source.name
        shutil.copyfile(source, dest)
        path = out / name
        path.write_bytes(gzip.decompress(dest.read_bytes()))
        plain.append(path)
        report.setdefault('inputs', []).append(dict(source=str(source.relative_to(ROOT)),
            gzip_sha256=sha(dest), expanded_sha256=sha(path), rows=len(path.read_bytes().splitlines())))
        return path

    def parse_pass(path, seed, expected_cases, expected_directed):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        verdicts = [r for r in rows if r['type'] == 'verdict']
        need(len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS' and
             verdicts[0]['seed'] == seed and verdicts[0]['cases'] == expected_cases and
             verdicts[0]['directed_checks'] == expected_directed, 'terminal contract ' + path.name)
        need(len([r for r in rows if r['type'] == 'case']) == expected_cases, 'case completeness')
        need(all(r.get('status') == 'PASS' for r in rows if r['type'] in ('case', 'directed')), 'nonpass row')
        return verdicts[0]

    try:
        report['resource_preflight'] = resources()
        for relative, expected in manifest['baseline_rtl_sha256'].items():
            need(sha(ROOT / relative) == expected, 'baseline source mismatch ' + relative)
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        (out / 'inputs').mkdir()
        shutil.copyfile(converted, out / 'converted.v')
        wrapper, renamed, mapping = make_wrapper(rtl[-1], out / 'converted.v', out)
        report['port_adapter'] = mapping
        SIM_AREA.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(wrapper, SIM_AREA / wrapper.name)
        (SIM_AREA / 'port-mapping.json').write_text(json.dumps(mapping, indent=2) + '\n')
        cases = ROOT / 'experiments/python-gamebub-v91i2/vectors/cases.tsv'
        shutil.copyfile(cases, out / 'cases.tsv')
        report['cases_sha256'] = sha(cases)
        transforms = expand(ROOT / 'experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz', 'transform_tiles.tsv')
        canonical = expand(ROOT / 'experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz', 'canonical_goldens.tsv')
        rgb_goldens = expand(ROOT / 'experiments/python-gamebub-v91k/vectors/rgb_goldens.tsv.gz', 'rgb_goldens.tsv')
        snapshot = lambda p: str(out / 'sources' / p.relative_to(ROOT))
        base = ['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2', '--assert', '-Wall', '--language', '1800-2017']
        flags = ['-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror']
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        for variant, paths in [('original', [snapshot(p) for p in rtl]),
                               ('converted', [str(renamed), str(wrapper)])]:
            report['resource_before_compile_' + variant] = resources()
            compile_base = base + (['-Wno-fatal'] if variant == 'converted' else [])
            command(compile_base + ['--top-module', 'cs88_pipeline_v91k', '--Mdir', build + '-' + variant,
                            '-I' + str(out / 'sources/fpga/experiments/cu66-v69/inverse'),
                            *flags, *paths, snapshot(bench)], 'compile-' + variant + '.log', 300)
            warnings = Counter(re.findall(r'%Warning-([A-Z0-9_]+):', (out / ('compile-' + variant + '.log')).read_text()))
            allowed = {'WIDTHEXPAND', 'WIDTHTRUNC', 'UNUSEDSIGNAL', 'EOFNEWLINE', 'DECLFILENAME', 'ASCRANGE', 'UNUSEDPARAM'} if variant == 'converted' else set()
            need(set(warnings) <= allowed, 'unexpected compile warning class')
            report.setdefault('compile_warnings', {})[variant] = dict(warnings)
            report.setdefault('binary_hashes', {})[variant] = command(['docker', 'exec', CONTAINER,
                'sha256sum', build + '-' + variant + '/Vcs88_pipeline_v91k'], 'binary-' + variant + '.log', 30).split()[0]
        command(base + ['--top-module', 'canonical_rgb565_v91k', '--Mdir', build + '-rgb',
                        *flags, snapshot(rgb_sv), snapshot(rgb_cpp)], 'compile-rgb.log', 300)
        report.setdefault('binary_hashes', {})['rgb'] = command(['docker', 'exec', CONTAINER,
            'sha256sum', build + '-rgb/Vcanonical_rgb565_v91k'], 'binary-rgb.log', 30).split()[0]
        print('V100_CONVERTED_COMPILES_COMPLETE', out, flush=True)
        for seed in args.seeds:
            result = dict(seed=seed, variants={})
            for variant in ('original', 'converted'):
                resources()
                name = f'{variant}-seed-{seed}'
                command(['docker', 'exec', CONTAINER, build + '-' + variant + '/Vcs88_pipeline_v91k',
                         str(out / 'cases.tsv'), str(transforms), str(canonical), str(seed),
                         str(out / (name + '-events.jsonl')), str(out / (name + '-canonical.tsv'))], name + '-simulation.jsonl')
                verdict = parse_pass(out / (name + '-simulation.jsonl'), seed, 22, 21)
                result['variants'][variant] = dict(terminal_verdict=verdict)
                report['actual_RTL_run'] = True
            original = f'original-seed-{seed}'
            adapted = f'converted-seed-{seed}'
            equalities = {}
            for suffix in ('-simulation.jsonl', '-events.jsonl', '-canonical.tsv'):
                equalities[suffix] = sha(out / (original + suffix)) == sha(out / (adapted + suffix))
                need(equalities[suffix], 'original/converted exact divergence ' + suffix)
            result['original_converted_byte_equality'] = equalities
            # Identical actual canonical SRAM bytes make one shared RGB replay per seed sufficient.
            command(['docker', 'exec', CONTAINER, build + '-rgb/Vcanonical_rgb565_v91k',
                     str(out / (adapted + '-canonical.tsv')), str(rgb_goldens), str(seed)], f'rgb-seed-{seed}.jsonl')
            result['rgb_verdict'] = parse_pass(out / f'rgb-seed-{seed}.jsonl', seed, 12, 8)
            need(result['rgb_verdict']['pixels'] == 4147200, 'RGB pixel completeness')
            for variant in ('original', 'converted'):
                name = f'{variant}-seed-{seed}'
                result['variants'][variant]['events'] = compress(out / (name + '-events.jsonl'))
                result['variants'][variant]['canonical_actual'] = compress(out / (name + '-canonical.tsv'))
            report['runs'].append(result)
        need(report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sources}, 'sources changed')
        need(sha(converted) == report['converted_sha256'], 'converted source changed')
        report.update(status='PASS_PAIRED_FULL_V91K_STANDARD_FRONTEND_BEHAVIOR', functional_verdict='PASS',
                      pipeline_case_runs=88, pipeline_directed_checks=84, rgb_case_runs=24,
                      rgb_directed_checks=16, exact_same_seed_cycle_counters_and_event_bytes=True)
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        for path in plain:
            path.unlink(missing_ok=True)
        for pattern in ('*-events.jsonl', '*-canonical.tsv'):
            for path in out.glob(pattern):
                report.setdefault('partial_artifacts', []).append(compress(path))
        report['wall_seconds'] = time.monotonic() - began
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'results.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V100_CONVERTED_RTL', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
