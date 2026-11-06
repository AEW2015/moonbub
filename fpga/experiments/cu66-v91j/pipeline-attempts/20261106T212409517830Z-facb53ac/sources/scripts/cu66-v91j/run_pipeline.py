#!/usr/bin/env python3
"""Retain strict full V91j inverse-integration and adapter simulations."""
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
AREA = ROOT / 'fpga/experiments/cu66-v91j'
MODEL = ROOT / 'experiments/python-gamebub-v91j'
OLD_CASES = ROOT / 'experiments/python-gamebub-v91i2/vectors/cases.tsv'
OLD_MANIFEST = OLD_CASES.with_name('manifest.json')
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compress_trace(path):
    if not path.exists():
        return None
    target = path.with_suffix(path.suffix + '.gz')
    with path.open('rb') as src, target.open('wb') as dest:
        with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=9) as zipped:
            shutil.copyfileobj(src, zipped)
    raw = gzip.decompress(target.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == sha(path)
    receipt = dict(path=target.name, gzip_sha256=sha(target), jsonl_sha256=sha(path), records=len(raw.splitlines()))
    path.unlink()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, choices=(911401, 911402), default=911401)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'pipeline-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    old_sv = [ROOT / ('fpga/experiments/' + name) for name in (
        'cu66-v91/br88_rice_elastic.sv', 'cu66-v91b/br88_context.sv',
        'cu66-v91d/br88_packet_ingress.sv', 'cu66-v91g2/packed_scratch_v91g2.sv',
        'cu66-v91h/br88_packet_ingress_v91h.sv', 'cu66-v91h/br88_packet_ingress_sync_v91h.sv',
        'cu66-v91h/br88_pipeline_v91h.sv', 'cu66-v91i2/cs88_admission_v91i2a.sv',
        'cu66-v91i2b/byte_refill_queue_v91i2b.sv', 'cu66-v91i2b/cs88_pipeline_v91i2b.sv')]
    math_sv = [ROOT / 'fpga/experiments/cu66-v69/inverse' / name
               for name in ('cu66_dequant.sv', 'cu66_idct8x8.sv')]
    header = math_sv[0].with_name('cu66_quant_rom.svh')
    adapter, wrapper = (AREA / name for name in ('cu66_inverse_stream_v91j.sv', 'cs88_pipeline_v91j.sv'))
    cpp, standalone = (AREA / name for name in ('tb_pipeline.cpp', 'tb_inverse.cpp'))
    sources = [*old_sv, *math_sv, header, adapter, wrapper, cpp, standalone, MODEL / 'model.py',
               ROOT / 'docs/cu66-v91j/math-contract.md', Path(__file__).resolve()]
    vectors = MODEL / 'vectors'
    vector_paths = sorted(path for path in vectors.rglob('*') if path.is_file())
    report = dict(schema='cu66-v91j-integrated-inverse-rtl-v1', status='FAIL', seed=args.seed,
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(path.relative_to(ROOT)): sha(path) for path in sources},
                  vectors_sha256={str(path.relative_to(vectors)): sha(path) for path in vector_paths},
                  case_input=dict(path='cases.tsv', source=str(OLD_CASES.relative_to(ROOT)), sha256=sha(OLD_CASES),
                                  source_manifest=str(OLD_MANIFEST.relative_to(ROOT)), source_manifest_sha256=sha(OLD_MANIFEST)),
                  commands=[], scope='Actual CS88 BR88 coefficient pipeline -> bounded tile assembly -> frozen dequantizer and two-pass Q14 IDCT -> signed24 residual stream. No prediction, pixels, reference/HUD/hash validation or publication.',
                  hardware_distinct_30fps_proven=False, full_frame_decode_under10ms_proven=False,
                  full_frame_publication_timestamp=None)
    began = time.monotonic()
    build = '/build/v91j-' + out.name
    plain_tiles = out / 'transform_tiles.tsv'

    def command(argv, name, timeout):
        entry = dict(argv=argv, log=name, exit_code=None)
        report['commands'].append(entry)
        with (out / name).open('w') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, cwd=ROOT)
        entry['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Command exit {result.returncode}: {out / name}')

    try:
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        shutil.copytree(vectors, out / 'vectors')
        shutil.copyfile(OLD_CASES, out / 'cases.tsv')
        packed_path = out / 'vectors/transform_tiles.tsv.gz'
        raw = gzip.decompress(packed_path.read_bytes())
        plain_tiles.write_bytes(raw)
        report['input_expansion'] = dict(path=plain_tiles.name, compressed_path='vectors/transform_tiles.tsv.gz',
                                       compressed_sha256=sha(packed_path), uncompressed_sha256=sha(plain_tiles),
                                       rows=len(raw.splitlines()), retained='Canonical gzip retained; reconstruct this temporary plain TSV by gzip decompression.')
        assert report['input_expansion']['rows'] == 31706
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        snapshot = lambda path: str(out / 'sources' / path.relative_to(ROOT))
        base = ['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2', '--assert', '-Wall']
        includes = ['-I' + str(out / 'sources/fpga/experiments/cu66-v69/inverse')]
        flags = ['-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror']
        command(base + ['--top-module', 'cs88_pipeline_v91j', '--Mdir', build + '-pipeline', *includes, *flags,
                        *[snapshot(path) for path in old_sv + math_sv + [adapter, wrapper, cpp]]], 'compile-pipeline.log', 300)
        command(['docker', 'exec', CONTAINER, build + '-pipeline/Vcs88_pipeline_v91j',
                 str(out / 'cases.tsv'), str(plain_tiles), str(args.seed), str(out / 'transform-events.jsonl')],
                'simulation.jsonl', 900)
        rows = [json.loads(line) for line in (out / 'simulation.jsonl').read_text().splitlines()]
        verdicts = [row for row in rows if row['type'] == 'verdict']
        assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
        assert verdicts[0]['seed'] == args.seed and verdicts[0]['cases'] == 22
        report['verdict'] = verdicts[0]
        report['transform_trace'] = compress_trace(out / 'transform-events.jsonl')
        assert report['transform_trace'] is not None
        command(base + ['--top-module', 'cu66_inverse_stream_v91j', '--Mdir', build + '-inverse', *includes, *flags,
                        *[snapshot(path) for path in math_sv + [adapter, standalone]]], 'compile-inverse.log', 300)
        command(['docker', 'exec', CONTAINER, build + '-inverse/Vcu66_inverse_stream_v91j',
                 str(out / 'vectors/boundary.tsv'), str(args.seed)], 'inverse.jsonl', 90)
        boundaries = [json.loads(line) for line in (out / 'inverse.jsonl').read_text().splitlines()]
        final = [row for row in boundaries if row['type'] == 'verdict']
        assert len(final) == 1 and final[0]['status'] == 'TEST_PASS' and final[0]['seed'] == args.seed
        report['inverse_verdict'] = final[0]
        assert report['source_sha256'] == {str(path.relative_to(ROOT)): sha(path) for path in sources}
        assert report['vectors_sha256'] == {str(path.relative_to(vectors)): sha(path) for path in vector_paths}
        assert report['case_input']['sha256'] == sha(OLD_CASES)
        assert report['case_input']['source_manifest_sha256'] == sha(OLD_MANIFEST)
        report.update(status='PASS_INTEGRATED_DEQUANT_AND_IDCT_RESIDUALS', case_rows=22)
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        # Preserve exact canonical input bytes without duplicating a 40 MB plain
        # expansion in every retained attempt; its reconstruction hash is pinned.
        if plain_tiles.exists():
            plain_tiles.unlink()
        if 'transform_trace' not in report:
            partial = compress_trace(out / 'transform-events.jsonl')
            if partial:
                report['partial_transform_trace'] = partial
        report['wall_seconds'] = time.monotonic() - began
        report['artifacts_sha256'] = {str(path.relative_to(out)): sha(path)
                                     for path in sorted(out.rglob('*')) if path.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'pipeline-results.json').write_text(json.dumps(
            dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V91J_PIPELINE', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
