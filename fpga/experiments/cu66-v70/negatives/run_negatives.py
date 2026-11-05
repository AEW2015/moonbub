#!/usr/bin/env python3
"""Compile and run the existing CU70 receiver bench over all 28 negatives."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/cu66-v70'))
from run_receiver import NATIVE, REL  # noqa: E402

CONTAINER = os.environ.get('TASK_CONTAINER', 'gamebub-cu66-v69-build')
MANIFEST = NATIVE / 'negative_manifest.json'
EXPORTER = HERE / 'prepare_cases.py'
CASES = HERE / 'case-list.tsv'
BENCH = ROOT / 'fpga/experiments/cu66-v70/receiver/tb_receiver.cpp'
RTL = ROOT / 'fpga/experiments/cu66-v70/receiver/cu70_receiver.sv'
RUNNER = ROOT / 'scripts/cu66-v70/run_receiver.py'
CPP = HERE / 'tb_negatives.cpp'
SELF = HERE / 'run_negatives.py'
BUILD = '/build/v70-negatives'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_paths():
    paths = [ROOT / item for item in REL]
    paths += [BENCH, RTL, RUNNER, SELF, MANIFEST, EXPORTER, CASES, CPP,
              ROOT / 'fpga/experiments/cu66-v69/packet/cu66_profile.svh',
              ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',
              ROOT / 'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',
              ROOT / 'fpga/experiments/cu66-v70/memory/memory_map.hpp',
              ROOT / 'experiments/cu66-native-v69/index.tsv']
    paths += list(NATIVE.glob('*.hpp'))
    paths += list((NATIVE / 'fixtures').glob('*.cu66'))
    paths += [NATIVE / item['packet']['path'] for item in json.loads(MANIFEST.read_text())['cases']]
    paths += [NATIVE / json.loads(MANIFEST.read_text())[key]['path']
              for key in ('seed_key_packet', 'recovery_key_packet')]
    return sorted(set(path.resolve() for path in paths))


def pins():
    return {str(path.relative_to(ROOT)): digest(path) for path in source_paths()}


def run(argv, log_path, timeout):
    with log_path.open('w', encoding='utf-8') as stream:
        result = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                timeout=timeout, check=False)
    return result.returncode


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=7401)
    parser.add_argument('--case-timeout', type=int, default=2400)
    args = parser.parse_args()

    subprocess.run([sys.executable, '-B', str(EXPORTER)], cwd=ROOT, check=True)
    before = pins()
    results_dir = HERE / 'results'
    results_dir.mkdir(exist_ok=True)
    build_log = results_dir / 'build.log'
    include = [
        '-I' + str(ROOT / 'fpga/experiments/cu66-v69/inverse'),
        '-I' + str(ROOT / 'fpga/experiments/cu66-v69/packet'),
    ]
    compile_command = [
        'docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '1',
        '--Wall', '-Wno-PINCONNECTEMPTY', '--top-module', 'cu70_receiver',
        '--Mdir', BUILD, '-CFLAGS', '-O2 -std=c++17', *include,
        *[str(ROOT / item) for item in REL], str(CPP),
    ]
    code = run(compile_command, build_log, 1800)
    if code:
        raise RuntimeError(f'Verilator build failed ({code}); see {build_log.relative_to(ROOT)}')

    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    seed_path = NATIVE / manifest['seed_key_packet']['path']
    recovery_path = NATIVE / manifest['recovery_key_packet']['path']
    rows = [line.split('\t') for line in CASES.read_text(encoding='utf-8').splitlines()]
    case_results = []
    summary_lines = [f'NEGATIVE_RUN seed={args.seed} cases={len(rows)} '
                     f'parent_tb_sha256={before[str(BENCH.relative_to(ROOT))]}']
    for index, row in enumerate(rows):
        name = row[0]
        case_tsv = results_dir / f'case-{index:02d}-{name}.tsv'
        case_tsv.write_text('\t'.join(row) + '\n', encoding='utf-8')
        log_path = results_dir / f'case-{index:02d}-{name}.log'
        command = ['docker', 'exec', CONTAINER, f'{BUILD}/Vcu70_receiver',
                   str(case_tsv), str(NATIVE), str(seed_path), str(recovery_path),
                   str(args.seed + index)]
        try:
            code = run(command, log_path, args.case_timeout)
            log_text = log_path.read_text(encoding='utf-8', errors='replace')
            passed = (code == 0 and
                      f'NEGATIVE_CASE_PASS name={name}' in log_text and
                      'NEGATIVES_PASS cases=1' in log_text and 'NEGATIVES_FAIL' not in log_text)
            error = None if passed else f'exit={code}; inspect {log_path.relative_to(ROOT)}'
        except subprocess.TimeoutExpired:
            passed = False
            error = f'timeout after {args.case_timeout}s; inspect {log_path.relative_to(ROOT)}'
            log_text = log_path.read_text(encoding='utf-8', errors='replace') if log_path.exists() else ''
        case_results.append({
            'name': name, 'category': row[1], 'packet': row[2], 'seed': args.seed + index,
            'status': 'PASS' if passed else 'FAIL', 'error': error,
            'log': str(log_path.relative_to(ROOT)), 'log_sha256': digest(log_path),
            'terminal_pass': bool(re.search(r'^NEGATIVE_CASE_PASS name=' + re.escape(name) + r'$', log_text, re.M)),
        })
        summary_lines.append(f"CASE_{'PASS' if passed else 'FAIL'} name={name}"
                             + ('' if passed else f' detail={error}'))

    after = pins()
    unchanged = before == after
    failures = [case['name'] for case in case_results if case['status'] != 'PASS']
    if not unchanged:
        failures.append('protected_sources_changed_during_run')
    terminal = ('NEGATIVES_PASS cases=28 failures=0 source_pins_unchanged=1'
                if not failures and len(case_results) == 28 else
                f'NEGATIVES_FAIL cases={len(case_results)} failed={len(failures)} '
                f'names={",".join(failures)} source_pins_unchanged={int(unchanged)}')
    summary_lines.append(terminal)
    summary_path = results_dir / 'summary.log'
    summary_path.write_text('\n'.join(summary_lines) + '\n', encoding='utf-8')
    result = {
        'schema': 'cu66-v70-negative-replay-v1',
        'status': 'PASS' if not failures and len(case_results) == 28 else 'FAIL',
        'scope': ('All negative cases use root packet/base/HUD parser path; original seed key and '
                  'key-24 recovery are accepted between cases. Golden data is native scoreboard only. '
                  'External RAM is transactional RAM; painter and scanout are completion/descriptor models.'),
        'case_count': len(case_results), 'failed_cases': failures,
        'source_unchanged': unchanged, 'source_sha256_before': before,
        'source_sha256_after': after,
        'build_command': compile_command, 'build_log': str(build_log.relative_to(ROOT)),
        'build_log_sha256': digest(build_log), 'case_results': case_results,
        'summary_log': str(summary_path.relative_to(ROOT)),
        'summary_log_sha256': digest(summary_path),
        'not_proven': ['physical SDRAM behavior', 'RTL painter pixels', 'physical scanout',
                       'processor service time', 'target timing/fit', 'physical frame rate'],
    }
    results_path = results_dir / 'results.json'
    results_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if result['status'] == 'PASS':
        print('NEGATIVES_PASS cases=28 failures=0 source_pins_unchanged=1 '
              f'build_log_sha256={result["build_log_sha256"]}')
        return 0
    print('NEGATIVES_FAIL ' + json.dumps({'failed_cases': failures, 'case_count': len(case_results)}))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
