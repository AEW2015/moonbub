#!/usr/bin/env python3
"""Compare inherited V105 reference with V107 aligned-reservoir full pipelines."""
import argparse
import datetime
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
# Read the shared gate without mutating sys.path or colliding with old helpers.
import importlib.util
_gate_spec = importlib.util.spec_from_file_location('v106_shared_gate', ROOT / 'scripts/cu66-v100/run_rtl.py')
_gate = importlib.util.module_from_spec(_gate_spec)
_gate_spec.loader.exec_module(_gate)
resources = _gate.resources
BASELINE = 'eececf35da97c9b14230d464ecde7576cb7840db'
CONTAINER = 'gamebub-cu66-v69-build'
# Load the frozen initial maps by exact file path, avoiding module-name ambiguity.
_parent_spec = importlib.util.spec_from_file_location('v106_initial_regress', ROOT / 'scripts/cu66-v106/regress.py')
_parent = importlib.util.module_from_spec(_parent_spec)
_parent_spec.loader.exec_module(_parent)
BASELINE_OVERRIDES = _parent.BASELINE_OVERRIDES
_sixth_spec = importlib.util.spec_from_file_location('v107_sixth_parent', ROOT / 'scripts/cu66-v106/locality_final/regress.py')
_sixth = importlib.util.module_from_spec(_sixth_spec)
_sixth_spec.loader.exec_module(_sixth)
_closure_spec = importlib.util.spec_from_file_location('v107_closure_parent', ROOT / 'scripts/cu66-v106/followup/regress.py')
_closure = importlib.util.module_from_spec(_closure_spec)
_closure_spec.loader.exec_module(_closure)
OVERRIDES = {
    'aligned': {**_sixth.OVERRIDES['local-guards-scratch-area'],
        'fpga/experiments/cu66-v91/br88_rice_elastic.sv': 'fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv'},
    'closure-aligned': {**_closure.OVERRIDES['closure'],
        'fpga/experiments/cu66-v91/br88_rice_elastic.sv': 'fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv'},
}
LANES = [(v, mode) for v in OVERRIDES for mode in ('fresh', 'canonical')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def pack(path):
    raw_hash = sha(path)
    target = path.with_suffix(path.suffix + '.gz')
    count = 0
    with path.open('rb') as source, target.open('wb') as dest:
        with gzip.GzipFile(fileobj=dest, mode='wb', filename='', mtime=0) as zipped:
            for line in source:
                if path.suffix == '.jsonl':
                    json.loads(line)
                zipped.write(line)
                count += 1
    require(hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest() == raw_hash, 'trace compression')
    path.unlink()
    return dict(path=target.name, sha256=sha(target), raw_sha256=raw_hash, records=count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=OVERRIDES, required=True)
    parser.add_argument('--mode', choices=['fresh', 'canonical'], required=True)
    parser.add_argument('--seeds', type=int, nargs=2, default=[107401, 107402])
    args = parser.parse_args()
    require(len(set(args.seeds)) == 2, 'two distinct seeds required')
    mode = args.mode
    require((args.variant, mode) in LANES, 'lane is outside frozen V107 matrix')
    baseline_overrides = {ROOT / old: ROOT / new for old, new in BASELINE_OVERRIDES.items()}
    overrides = {ROOT / old: ROOT / new for old, new in OVERRIDES[args.variant].items()}
    area = ROOT / 'experiments/python-gamebub-v107/regression' / args.variant / mode
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
    out = area / 'attempts' / stamp
    out.mkdir(parents=True, exist_ok=False)
    top = 'cs88_pipeline_v91j' if mode == 'fresh' else 'cs88_pipeline_v91k'
    cases_count, directed_count = (6, 13) if mode == 'fresh' else (22, 21)
    manifest = json.loads((ROOT / 'fpga/experiments/cu66-v100-baseline/frozen-inputs.json').read_text())
    if mode == 'canonical':
        rtl = [ROOT / name for name in manifest['rtl_sources']]
    else:
        rtl = [ROOT / ('fpga/experiments/' + name) for name in (
            'cu66-v91/br88_rice_elastic.sv', 'cu66-v91b/br88_context.sv',
            'cu66-v91d/br88_packet_ingress.sv', 'cu66-v91g2/packed_scratch_v91g2.sv',
            'cu66-v91h/br88_packet_ingress_v91h.sv', 'cu66-v91h/br88_packet_ingress_sync_v91h.sv',
            'cu66-v91h/br88_pipeline_v91h.sv', 'cu66-v91i2/cs88_admission_v91i2a.sv',
            'cu66-v91i2b/byte_refill_queue_v91i2b.sv', 'cu66-v91i2b/cs88_pipeline_v91i2b.sv',
            'cu66-v69/inverse/cu66_dequant.sv', 'cu66-v69/inverse/cu66_idct8x8.sv',
            'cu66-v91j/cu66_inverse_stream_v91j.sv', 'cu66-v91j/cs88_pipeline_v91j.sv')]
    bench = ROOT / ('fpga/experiments/cu66-v91j/tb_pipeline.cpp' if mode == 'fresh' else
                    'fpga/experiments/cu66-v91k/tb_pipeline.cpp')
    header = ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh'
    sources = sorted(set(rtl + [bench, header, *baseline_overrides.values(), *overrides.values(), Path(__file__).resolve(),
                               ROOT / 'scripts/cu66-v100/run_rtl.py', ROOT / 'scripts/cu66-v106/regress.py',
                               ROOT / 'scripts/cu66-v106/followup/regress.py', ROOT / 'scripts/cu66-v106/final/regress.py', ROOT / 'scripts/cu66-v106/pipeline/regress.py', ROOT / 'scripts/cu66-v106/locality_final/regress.py']))
    report = dict(schema='v107-paired-regression-v1', status='FAIL', mode=mode,
                  baseline_revision=BASELINE, baseline_overrides=BASELINE_OVERRIDES, variant=args.variant, top=top, seeds=args.seeds,
                  candidates=[dict(original=str(old.relative_to(ROOT)), path=str(new.relative_to(ROOT)), sha256=sha(new)) for old,new in overrides.items()],
                  backend='Verilator 5.020 behavioral, explicitly retained historical backend',
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  inputs={}, commands=[], runs=[], actual_RTL_run=False,
                  assertions_disabled_or_downgraded=False,
                  limits=['Component simulation only; no formal/mapped-netlist equivalence.',
                          'No full HUD/C2/publication, board CDC or routed timing proof.',
                          'No hardware 30fps or under10ms decode qualification.'])
    plain_inputs = []
    start = time.monotonic()

    def command(argv, name, timeout=900):
        if argv[:3] == ['docker', 'exec', CONTAINER] and name not in ('verilator.log', 'compiler.log'):
            argv = argv[:3] + ['timeout', '--signal=TERM', '--kill-after=5s', str(timeout - 10) + 's'] + argv[3:]
        entry = dict(argv=argv, log=name, timeout_seconds=timeout, exit_code=None)
        report['commands'].append(entry)
        began = time.monotonic()
        with (out / name).open('w') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, timeout=timeout)
        entry.update(exit_code=result.returncode, wall_seconds=time.monotonic() - began)
        require(result.returncode == 0, 'command failed ' + name)

    def input_file(source, name):
        dest = out / 'inputs' / source.name
        shutil.copyfile(source, dest)
        if source.suffix == '.gz':
            plain = out / name
            plain.write_bytes(gzip.decompress(dest.read_bytes()))
            plain_inputs.append(plain)
        else:
            plain = out / name
            shutil.copyfile(dest, plain)
        report['inputs'][name] = dict(source=str(source.relative_to(ROOT)),
            sha256=sha(dest), expanded_sha256=sha(plain), rows=len(plain.read_bytes().splitlines()))
        return plain

    try:
        report['resource_gate'] = resources()
        for name, digest in manifest['baseline_rtl_sha256'].items():
            require(sha(ROOT / name) == digest, 'frozen RTL changed ' + name)
        for path in set(rtl + [bench, header] + list(baseline_overrides.values())):
            original = subprocess.check_output(['git', 'show', BASELINE + ':' + str(path.relative_to(ROOT))], cwd=ROOT)
            require(hashlib.sha256(original).hexdigest() == sha(path), 'baseline source changed')
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        (out / 'inputs').mkdir()
        if mode == 'fresh':
            inputs = ROOT / 'experiments/python-gamebub-v99/cs88/rtl-facing-attempts/20261107T1909-new-user-q16'
            cases = input_file(inputs / 'cases.tsv.gz', 'cases.tsv')
            transforms = input_file(inputs / 'transform_tiles.tsv.gz', 'transform_tiles.tsv')
            canonical = None
        else:
            cases = input_file(ROOT / 'experiments/python-gamebub-v91i2/vectors/cases.tsv', 'cases.tsv')
            transforms = input_file(ROOT / 'experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz', 'transform_tiles.tsv')
            canonical = input_file(ROOT / 'experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz', 'canonical_goldens.tsv')
        snapshot = lambda p: str(out / 'sources' / p.relative_to(ROOT))
        with Path('/tmp/gamebub-v106-regression.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'verilator.log', 30)
            command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler.log', 30)
            for variant in ('baseline', 'candidate'):
                resources()
                build = '/build/v107-' + stamp + '-' + mode + '-' + variant
                mapping = dict(baseline_overrides)
                if variant == 'candidate':
                    mapping.update(overrides)
                paths = [mapping.get(p, p) for p in rtl]
                command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build',
                         '-j', '2', '--assert', '-Wall', '--language', '1800-2017',
                         '--top-module', top, '--Mdir', build,
                         '-I' + str(out / 'sources/fpga/experiments/cu66-v69/inverse'),
                         '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
                         *[snapshot(p) for p in paths], snapshot(bench)], 'compile-' + variant + '.log', 300)
                require('%Warning-' not in (out / ('compile-' + variant + '.log')).read_text(), 'strict warning policy')
                command(['docker', 'exec', CONTAINER, 'sha256sum', build + '/V' + top], 'binary-' + variant + '.log', 30)
                report.setdefault('binaries', {})[variant] = dict(path=build + '/V' + top,
                    sha256=(out / ('binary-' + variant + '.log')).read_text().split()[0])
            print('V107_COMPILES_PASS', mode, out, flush=True)
            for seed in args.seeds:
                row = dict(seed=seed, variants={}, equalities={})
                for variant in ('baseline', 'candidate'):
                    resources()
                    prefix = variant + '-' + str(seed)
                    events = out / (prefix + '-events.jsonl')
                    actual = out / (prefix + '-canonical.tsv')
                    argv = ['docker', 'exec', CONTAINER, report['binaries'][variant]['path'], str(cases), str(transforms)]
                    argv += [str(canonical)] if canonical else []
                    argv += [str(seed), str(events)] + ([str(actual)] if canonical else [])
                    command(argv, prefix + '-simulation.jsonl')
                    records = [json.loads(line) for line in (out / (prefix + '-simulation.jsonl')).read_text().splitlines()]
                    verdicts = [r for r in records if r['type'] == 'verdict']
                    require(len(verdicts) == 1, 'single terminal verdict required')
                    verdict = verdicts[0]
                    require(verdict['status'] == 'TEST_PASS' and verdict['seed'] == seed and
                            verdict['cases'] == cases_count and verdict['directed_checks'] == directed_count, 'terminal coverage')
                    require(len([r for r in records if r['type'] == 'case']) == cases_count, 'case completeness')
                    require(all(r.get('status') == 'PASS' for r in records if r['type'] in ('case', 'directed')), 'nonpass row')
                    row['variants'][variant] = dict(verdict=verdict)
                    report['actual_RTL_run'] = True
                for key, suffix in [('stdout', '-simulation.jsonl'), ('events', '-events.jsonl')] + ([('canonical', '-canonical.tsv')] if canonical else []):
                    row['equalities'][key] = sha(out / ('baseline-' + str(seed) + suffix)) == sha(out / ('candidate-' + str(seed) + suffix))
                    require(row['equalities'][key], 'baseline/candidate divergence ' + key)
                for variant in ('baseline', 'candidate'):
                    prefix = variant + '-' + str(seed)
                    row['variants'][variant]['events'] = pack(out / (prefix + '-events.jsonl'))
                    if canonical:
                        row['variants'][variant]['canonical_actual'] = pack(out / (prefix + '-canonical.tsv'))
                report['runs'].append(row)
        require(report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sources}, 'sources changed during test')
        report.update(status='PASS', case_profile_runs=cases_count * 4,
                      directed_checks=directed_count * 4,
                      exact_same_seed_transcripts_events_cycles=True)
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        for path in plain_inputs:
            path.unlink(missing_ok=True)
        for pattern in ('*-events.jsonl', '*-canonical.tsv'):
            for path in out.glob(pattern):
                report.setdefault('partial_artifacts', []).append(pack(path))
        report['wall_seconds'] = time.monotonic() - start
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (area / 'results.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V107_REGRESSION', mode, report['status'], out, flush=True)


if __name__ == '__main__':
    main()
