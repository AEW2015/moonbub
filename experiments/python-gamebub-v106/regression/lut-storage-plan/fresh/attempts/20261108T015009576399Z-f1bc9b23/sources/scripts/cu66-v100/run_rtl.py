#!/usr/bin/env python3
"""Run fresh V99 CS88 vectors through unchanged V91j RTL and its strict bench."""
import argparse
import datetime
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v100/rtl'
DEFAULT_VECTORS = ROOT / 'experiments/python-gamebub-v99/cs88/rtl-facing-attempts/20261107T1909-new-user-q16'
CONTAINER = 'gamebub-cu66-v69-build'
EXPECTED_DIRECTED = {
    'abort_queued_and_pending_refill', 'warm_reset_queued_and_pending_refill',
    'abort_accepted_write_drain_blocks_start', 'warm_reset_accepted_write_drain_blocks_start',
    'abort_held_residual', 'abort_owned_idct_job',
    'good_retry_after_failed_frame_without_reset', 'partial_cache_load_abort_releases_owner',
    'one_shot_cache_requires_fresh_preload', 'zero_frame_epoch_rejected',
    'snapshot_inputs_latched_every_case', 'serial_cache_tag_latched_first_byte',
    'all_coefficients_and_mapped_tuple_fields_exact',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def resources():
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    available = int(memory['MemAvailable'].split()[0]) * 1024
    pressure = Path('/proc/pressure/memory').read_text()
    full = next(line for line in pressure.splitlines() if line.startswith('full '))
    avg10 = float(dict(item.split('=') for item in full.split()[1:])['avg10'])
    need(available >= 8 * 1024**3, 'resource gate: MemAvailable below 8 GiB')
    need(avg10 < 1, 'resource gate: memory PSI full avg10 >= 1')
    return dict(mem_available_bytes=available, memory_psi=pressure, full_avg10=avg10,
                minimum_available_bytes=8 * 1024**3, maximum_full_avg10_exclusive=1,
                swap_alone_is_not_a_stop_condition=True)


def compress_trace(path):
    target = path.with_suffix(path.suffix + '.gz')
    original_sha = sha(path)
    records = 0
    with path.open('rb') as src, target.open('wb') as dest:
        with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=9) as zipped:
            for line in src:
                # Parse every focused event; a pathname alone is not trace evidence.
                json.loads(line)
                records += 1
                zipped.write(line)
    need(hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest() == original_sha,
         'compressed trace changed bytes')
    receipt = dict(path=target.name, gzip_sha256=sha(target), jsonl_sha256=original_sha,
                   records=records, parsed_every_record=True)
    path.unlink()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vectors', type=Path, default=DEFAULT_VECTORS)
    parser.add_argument('--seeds', type=int, nargs='+', default=[100401, 100402])
    parser.add_argument('--simulation-timeout', type=int, default=900)
    args = parser.parse_args()
    need(len(args.seeds) == len(set(args.seeds)) and len(args.seeds) >= 2,
         'require at least two distinct reproducible seeds')
    vectors = args.vectors.resolve()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    old_sv = [ROOT / ('fpga/experiments/' + name) for name in (
        'cu66-v91/br88_rice_elastic.sv', 'cu66-v91b/br88_context.sv',
        'cu66-v91d/br88_packet_ingress.sv', 'cu66-v91g2/packed_scratch_v91g2.sv',
        'cu66-v91h/br88_packet_ingress_v91h.sv', 'cu66-v91h/br88_packet_ingress_sync_v91h.sv',
        'cu66-v91h/br88_pipeline_v91h.sv', 'cu66-v91i2/cs88_admission_v91i2a.sv',
        'cu66-v91i2b/byte_refill_queue_v91i2b.sv', 'cu66-v91i2b/cs88_pipeline_v91i2b.sv')]
    math_sv = [ROOT / 'fpga/experiments/cu66-v69/inverse' / name
               for name in ('cu66_dequant.sv', 'cu66_idct8x8.sv')]
    adapter, wrapper, bench = [ROOT / 'fpga/experiments/cu66-v91j' / name for name in
                               ('cu66_inverse_stream_v91j.sv', 'cs88_pipeline_v91j.sv', 'tb_pipeline.cpp')]
    golden_report = json.loads((vectors / 'results.json').read_text())
    sources = sorted(set(old_sv + math_sv + [math_sv[0].with_name('cu66_quant_rom.svh'),
                    adapter, wrapper, bench, Path(__file__).resolve(),
                    ROOT / 'docs/cu66-v91j/math-contract.md'] +
                    [ROOT / path for path in golden_report['source_sha256']]))
    vector_paths = [vectors / name for name in ('cases.tsv.gz', 'transform_tiles.tsv.gz', 'results.json')]
    report = dict(schema='cu66-v100-fresh-cs88-rtl-v1', status='FAIL',
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  backend='Verilator (explicit configured historical backend; not Vivado/XSim)',
                  mode='behavioral, cycle-accurate compiled RTL with --assert -Wall',
                  top='cs88_pipeline_v91j', simulation_set='explicit non-project source list',
                  seeds=args.seeds, source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  vectors_sha256={p.name: sha(p) for p in vector_paths},
                  golden_report=str((vectors / 'results.json').relative_to(ROOT)), commands=[], runs=[],
                  scope='CS88 admission/BR88 coefficient decode, tile assembly, signed20 dequant and signed24 two-pass Q14 IDCT residuals. Exact coefficient/value/metadata comparison and existing cancellation/recovery assertions.',
                  exclusions=['No full pixel/prediction/reference/HUD/C2 publication proof.',
                              'No new synthesis, route frequency, timing closure, hardware FPS or transport claim.',
                              'No standalone inverse boundary corpus rerun; unchanged integrated bench only.',
                              'No statement/branch/toggle coverage database or formal proof.'],
                  hardware_distinct_30fps_proven=False, full_frame_decode_under10ms_proven=False,
                  full_frame_publication_timestamp=None, actual_RTL_run=False,
                  assertions_disabled_or_downgraded=False)
    began = time.monotonic()
    build = '/build/v100-' + out.name
    expansions = []

    def command(argv, name, timeout):
        entry = dict(argv=argv, log=name, timeout_seconds=timeout, exit_code=None)
        report['commands'].append(entry)
        started = time.monotonic()
        with (out / name).open('w') as log:
            try:
                result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=timeout, cwd=ROOT)
                entry['exit_code'] = result.returncode
            finally:
                entry['wall_seconds'] = time.monotonic() - started
        need(result.returncode == 0, f'command exit {result.returncode}: {name}')
        return (out / name).read_text()

    try:
        report['resource_preflight'] = resources()
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        (out / 'vectors').mkdir()
        for path in vector_paths:
            shutil.copyfile(path, out / 'vectors' / path.name)
        report['input_expansion'] = {}
        for name in ('cases.tsv', 'transform_tiles.tsv'):
            packed = out / 'vectors' / (name + '.gz')
            plain = out / name
            raw = gzip.decompress(packed.read_bytes())
            plain.write_bytes(raw)
            expansions.append(plain)
            receipt = dict(rows=len(raw.splitlines()), bytes=len(raw), sha256=sha(plain),
                           gzip_sha256=sha(packed), canonical_path='vectors/' + packed.name)
            expected = golden_report['vectors'][name]
            need(receipt['rows'] == expected['records'] and receipt['sha256'] == expected['sha256']
                 and receipt['gzip_sha256'] == expected['gzip_sha256'], 'golden manifest mismatch ' + name)
            report['input_expansion'][name] = receipt
        need(report['input_expansion']['cases.tsv']['rows'] == 3, 'expected three fresh fixtures')
        need(report['input_expansion']['transform_tiles.tsv']['rows'] == 17887, 'expected 17887 fresh tiles')
        for relative, expected in golden_report['source_sha256'].items():
            need(sha(ROOT / relative) == expected, 'golden source changed ' + relative)
        case_specs = []
        for line in (out / 'cases.tsv').read_text().splitlines():
            fields = line.split()
            case_specs.append(dict(id=fields[0], error=int(fields[1]),
                                   coefficient_samples=sum(0 if v == '-' else len(bytes.fromhex(v)) // 2
                                                           for v in fields[12:15])))
        report['case_specs'] = case_specs
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'bash', '-c',
                 'for tool in verilator verilator_bin g++ cc1plus; do resolved=$(command -v "$tool" || true); if [ -n "$resolved" ]; then readlink -f "$resolved"; sha256sum "$(readlink -f "$resolved")"; fi; done; compiler=$(g++ -print-prog-name=cc1plus); sha256sum "$compiler"'],
                'tool-hashes.log', 30)
        snapshot = lambda path: str(out / 'sources' / path.relative_to(ROOT))
        report['resource_before_compile'] = resources()
        # Cooperating V100 runners cannot consume the heavy-job slot together.
        with Path('/tmp/gamebub-v100-heavy.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2',
                     '--assert', '-Wall', '--top-module', 'cs88_pipeline_v91j', '--Mdir', build,
                     '-I' + str(out / 'sources/fpga/experiments/cu66-v69/inverse'),
                     '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
                     *[snapshot(p) for p in old_sv + math_sv + [adapter, wrapper, bench]]],
                    'compile-pipeline.log', 300)
            report['binary_sha256'] = command(['docker', 'exec', CONTAINER, 'sha256sum',
                                               build + '/Vcs88_pipeline_v91j'], 'binary-sha256.log', 30).split()[0]
            report['binary_path_outside_git'] = build + '/Vcs88_pipeline_v91j'
            for seed in args.seeds:
                report['resource_before_seed_' + str(seed)] = resources()
                name = f'seed-{seed}'
                command(['docker', 'exec', CONTAINER, build + '/Vcs88_pipeline_v91j',
                         str(out / 'cases.tsv'), str(out / 'transform_tiles.tsv'), str(seed),
                         str(out / (name + '-transform-events.jsonl'))], name + '-simulation.jsonl',
                        args.simulation_timeout)
                rows = [json.loads(line) for line in (out / (name + '-simulation.jsonl')).read_text().splitlines()]
                verdicts = [r for r in rows if r['type'] == 'verdict']
                need(len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS', 'missing explicit terminal TEST_PASS')
                verdict = verdicts[0]
                need(verdict['seed'] == seed and verdict['vectors'] == 3 and verdict['cases'] == 6
                     and verdict['configurations'] == 2, 'incomplete seed/case/profile coverage')
                case_rows = [r for r in rows if r['type'] == 'case']
                need(len(case_rows) == 6, 'missing case rows')
                for spec in case_specs:
                    for profile in (0, 1):
                        matches = [r for r in case_rows if r['id'] == spec['id'] and r['memory_profile'] == profile]
                        need(len(matches) == 1 and matches[0]['status'] == 'PASS' and
                             matches[0]['error'] == spec['error'], 'case/profile/error mismatch')
                directed = [r for r in rows if r['type'] == 'directed']
                need(len(directed) == 13 and all(r['status'] == 'PASS' for r in directed)
                     and {r['name'] for r in directed} == EXPECTED_DIRECTED
                     and set(verdict['directed_check_names']) == EXPECTED_DIRECTED, 'directed regression incomplete')
                trace = compress_trace(out / (name + '-transform-events.jsonl'))
                report['runs'].append(dict(seed=seed, terminal_verdict=verdict, cases=case_rows,
                                           directed=directed, transform_trace=trace))
                report['actual_RTL_run'] = True
        need(report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sources}, 'sources changed during run')
        need(report['vectors_sha256'] == {p.name: sha(p) for p in vector_paths}, 'vectors changed during run')
        report.update(status='PASS_FRESH_CS88_SIGNED20_DEQUANT_SIGNED24_IDCT_RTL',
                      functional_verdict='PASS', seeds_passed=len(report['runs']),
                      case_profile_runs_passed=6 * len(report['runs']),
                      directed_checks_passed=13 * len(report['runs']))
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        for plain in expansions:
            plain.unlink(missing_ok=True)
        for trace in sorted(out.glob('*-transform-events.jsonl')):
            report.setdefault('partial_traces', []).append(compress_trace(trace))
        report['wall_seconds'] = time.monotonic() - began
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'results.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V100_RTL', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
