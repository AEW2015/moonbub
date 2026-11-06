#!/usr/bin/env python3
"""Retain strict BR88-to-canonical RTL and actual-memory RGB565 replay evidence."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91k'
MODEL = ROOT / 'experiments/python-gamebub-v91k'
OLD_CASES = ROOT / 'experiments/python-gamebub-v91i2/vectors/cases.tsv'
OLD_TRANSFORMS = ROOT / 'experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compress(path):
    if not path.exists():
        return None
    target = path.with_suffix(path.suffix + '.gz')
    with path.open('rb') as src, target.open('wb') as dest:
        with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=9) as zipped:
            shutil.copyfileobj(src, zipped)
    raw = gzip.decompress(target.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == sha(path)
    receipt = dict(path=target.name, gzip_sha256=sha(target), raw_sha256=sha(path), rows=len(raw.splitlines()))
    path.unlink()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, choices=(911501, 911502), default=911501)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'pipeline-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    old_sv = [ROOT / ('fpga/experiments/' + name) for name in (
        'cu66-v91/br88_rice_elastic.sv', 'cu66-v91b/br88_context.sv',
        'cu66-v91d/br88_packet_ingress.sv', 'cu66-v91g2/packed_scratch_v91g2.sv',
        'cu66-v91h/br88_packet_ingress_v91h.sv', 'cu66-v91h/br88_packet_ingress_sync_v91h.sv',
        'cu66-v91h/br88_pipeline_v91h.sv', 'cu66-v91i2/cs88_admission_v91i2a.sv',
        'cu66-v91i2b/byte_refill_queue_v91i2b.sv', 'cu66-v91j/cu66_inverse_stream_v91j.sv')]
    math_sv = [ROOT / 'fpga/experiments/cu66-v69/inverse' / name
               for name in ('cu66_dequant.sv', 'cu66_idct8x8.sv', 'cu66_reconstruct_tile.sv')]
    header = math_sv[0].with_name('cu66_quant_rom.svh')
    new_sv = [AREA / name for name in ('cs88_coefficients_v91k.sv', 'cu66_reconstruct_stream_v91k.sv', 'cs88_pipeline_v91k.sv')]
    cpp = AREA / 'tb_pipeline.cpp'
    rgb_sv, rgb_cpp = (AREA / 'rgb' / name for name in ('canonical_rgb565_v91k.sv', 'tb_rgb.cpp'))
    sources = [*old_sv, *math_sv, header, *new_sv, cpp, rgb_sv, rgb_cpp,
               MODEL / 'model.py', ROOT / 'docs/cu66-v91k/reconstruction-contract.md', Path(__file__).resolve()]
    vectors = MODEL / 'vectors'
    vector_paths = sorted(path for path in vectors.rglob('*') if path.is_file())
    report = dict(schema='cu66-v91k-canonical-and-rgb-rtl-v1', status='FAIL', seed=args.seed,
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(path.relative_to(ROOT)): sha(path) for path in sources},
                  vectors_sha256={str(path.relative_to(vectors)): sha(path) for path in vector_paths},
                  inputs_sha256={str(path.relative_to(ROOT)): sha(path) for path in
                                 (OLD_CASES, OLD_CASES.with_name('manifest.json'), OLD_TRANSFORMS)},
                  commands=[], input_expansions=[],
                  scope='Real BR88 frame -> signed residuals -> canonical reconstruction. Actual accepted canonical SRAM writes replayed through real byte-read RGB565 RTL. No HUD/hash validation/atomic publication.',
                  memory_service='Canonical ready means candidate byte write committed; reference tile read accepts one 64-byte owner, FAST8/SLOW12..24 edges. RGB replay makes nine separately acknowledged byte reads per pixel, FAST2/SLOW2..6 edges, plus finite request/output stalls. Separate simulations connected by exact actual candidate-memory bytes; summed fences are replay service, not a monolithic physical bus proof.',
                  hardware_distinct_30fps_proven=False, full_frame_decode_under10ms_proven=False,
                  full_frame_publication_timestamp=None, monolithic_full_frame_rtl_proven=False)
    began = time.monotonic()
    build = '/build/v91k-' + out.name
    temporary = []

    def command(argv, name, timeout):
        entry = dict(argv=argv, log=name, exit_code=None)
        report['commands'].append(entry)
        with (out / name).open('w') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, cwd=ROOT)
        entry['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Command exit {result.returncode}: {out / name}')

    def expand(source, target):
        raw = gzip.decompress(source.read_bytes())
        target.write_bytes(raw)
        temporary.append(target)
        report['input_expansions'].append(dict(path=target.name, compressed_path=str(source.relative_to(out)),
            compressed_sha256=sha(source), raw_sha256=sha(target), rows=len(raw.splitlines())))

    try:
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        shutil.copytree(vectors, out / 'vectors')
        shutil.copyfile(OLD_CASES, out / 'cases.tsv')
        (out / 'inputs').mkdir()
        shutil.copyfile(OLD_TRANSFORMS, out / 'inputs/transform_tiles.tsv.gz')
        expand(out / 'inputs/transform_tiles.tsv.gz', out / 'transform_tiles.tsv')
        expand(out / 'vectors/canonical_goldens.tsv.gz', out / 'canonical_goldens.tsv')
        expand(out / 'vectors/rgb_goldens.tsv.gz', out / 'rgb_goldens.tsv')
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        snapshot = lambda path: str(out / 'sources' / path.relative_to(ROOT))
        base = ['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2', '--assert', '-Wall']
        includes = ['-I' + str(out / 'sources/fpga/experiments/cu66-v69/inverse')]
        flags = ['-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror']
        command(base + ['--top-module', 'cs88_pipeline_v91k', '--Mdir', build + '-pipeline', *includes, *flags,
                        *[snapshot(path) for path in old_sv + math_sv + new_sv + [cpp]]], 'compile-pipeline.log', 300)
        command(['docker', 'exec', CONTAINER, build + '-pipeline/Vcs88_pipeline_v91k',
                 str(out / 'cases.tsv'), str(out / 'transform_tiles.tsv'), str(out / 'canonical_goldens.tsv'),
                 str(args.seed), str(out / 'events.jsonl'), str(out / 'canonical_actual.tsv')], 'simulation.jsonl', 900)
        rows = [json.loads(line) for line in (out / 'simulation.jsonl').read_text().splitlines()]
        verdicts = [row for row in rows if row['type'] == 'verdict']
        assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
        assert verdicts[0]['seed'] == args.seed and verdicts[0]['cases'] == 22
        report['verdict'] = verdicts[0]
        report['canonical_trace'] = compress(out / 'events.jsonl')
        assert report['canonical_trace'] is not None
        command(base + ['--top-module', 'canonical_rgb565_v91k', '--Mdir', build + '-rgb', *flags,
                        snapshot(rgb_sv), snapshot(rgb_cpp)], 'compile-rgb.log', 300)
        command(['docker', 'exec', CONTAINER, build + '-rgb/Vcanonical_rgb565_v91k',
                 str(out / 'canonical_actual.tsv'), str(out / 'rgb_goldens.tsv'), str(args.seed)], 'rgb.jsonl', 900)
        rgb_rows = [json.loads(line) for line in (out / 'rgb.jsonl').read_text().splitlines()]
        finals = [row for row in rgb_rows if row['type'] == 'verdict']
        assert len(finals) == 1 and finals[0]['status'] == 'TEST_PASS' and finals[0]['seed'] == args.seed
        assert finals[0]['cases'] == 12 and finals[0]['pixels'] == 4147200
        report['rgb_verdict'] = finals[0]
        report['canonical_actual'] = compress(out / 'canonical_actual.tsv')
        assert report['canonical_actual']['rows'] == 12
        assert report['source_sha256'] == {str(path.relative_to(ROOT)): sha(path) for path in sources}
        assert report['vectors_sha256'] == {str(path.relative_to(vectors)): sha(path) for path in vector_paths}
        assert all(sha(ROOT / name) == digest for name, digest in report['inputs_sha256'].items())
        report.update(status='PASS_CANONICAL_AND_BASE_RGB565_RTL_REPLAY', case_rows=22)
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        for target in temporary:
            if target.exists():
                target.unlink()
        for name, key in (('events.jsonl', 'partial_canonical_trace'), ('canonical_actual.tsv', 'partial_canonical_actual')):
            receipt = compress(out / name)
            if receipt:
                report[key] = receipt
        report['wall_seconds'] = time.monotonic() - began
        report['artifacts_sha256'] = {str(path.relative_to(out)): sha(path)
                                     for path in sorted(out.rglob('*')) if path.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'pipeline-results.json').write_text(json.dumps(
            dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V91K_PIPELINE', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
