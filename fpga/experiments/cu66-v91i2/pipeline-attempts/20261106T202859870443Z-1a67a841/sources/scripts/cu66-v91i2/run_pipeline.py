#!/usr/bin/env python3
"""Retain strict seeded CS88-to-BR88 coefficient-placement simulations."""
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
AREA = ROOT / 'fpga/experiments/cu66-v91i2'
MODEL = ROOT / 'experiments/python-gamebub-v91i2'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compress_trace(path):
    if not path.exists():
        return None
    target = path.with_suffix(path.suffix + '.gz')
    with path.open('rb') as src, target.open('wb') as dest:
        with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=9) as compressed:
            shutil.copyfileobj(src, compressed)
    raw = gzip.decompress(target.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == sha(path)
    result = dict(path=target.name, gzip_sha256=sha(target),
                  jsonl_sha256=sha(path), records=len(raw.splitlines()))
    path.unlink()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=911201)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'pipeline-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    old_sv = [ROOT / ('fpga/experiments/' + name) for name in (
        'cu66-v91/br88_rice_elastic.sv', 'cu66-v91b/br88_context.sv',
        'cu66-v91d/br88_packet_ingress.sv', 'cu66-v91g2/packed_scratch_v91g2.sv',
        'cu66-v91h/br88_packet_ingress_v91h.sv',
        'cu66-v91h/br88_packet_ingress_sync_v91h.sv', 'cu66-v91h/br88_pipeline_v91h.sv')]
    new_sv = [AREA / 'cs88_admission_v91i2a.sv', AREA / 'cs88_pipeline_v91i2a.sv']
    cpp = AREA / 'tb_pipeline.cpp'
    sources = [*old_sv, *new_sv, cpp, MODEL / 'model.py', Path(__file__).resolve(),
               ROOT / 'docs/cu66-v91i2/contract.md']
    sources += sorted(AREA.glob('*.svh'))
    vectors = MODEL / 'vectors'
    vector_paths = sorted(p for p in vectors.rglob('*') if p.is_file())
    assert vector_paths and (vectors / 'cases.tsv').is_file()
    build = '/build/v91i2a-pipeline-' + out.name
    report = dict(schema='cu66-v91i2a-coefficient-placement-rtl-v1', status='FAIL',
                  seed=args.seed, source_revision=subprocess.check_output(
                      ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  vectors_sha256={str(p.relative_to(vectors)): sha(p) for p in vector_paths},
                  commands=[], build_directory=build,
                  scope='Actual restricted all-BR88 CS88 frame dispatch to frozen V91h and dense coefficient plane/tile/quantizer binding. No dequantization/IDCT, pixel/reference/HUD/hash validation or publication.',
                  hardware_distinct_30fps_proven=False,
                  full_frame_decode_under10ms_proven=False,
                  full_frame_publication_timestamp=None)
    started = time.monotonic()

    def command(argv, name, timeout):
        entry = dict(argv=argv, log=name, exit_code=None)
        report['commands'].append(entry)
        with (out / name).open('w') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=timeout, cwd=ROOT)
        entry['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Command exit {result.returncode}: {out / name}')

    try:
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        shutil.copytree(vectors, out / 'vectors')
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        snapshot = lambda p: str(out / 'sources' / p.relative_to(ROOT))
        command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build',
                 '-j', '2', '--assert', '-Wall', '--top-module', 'cs88_pipeline_v91i2a',
                 '--Mdir', build, '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
                 '-I' + str(out / 'sources' / AREA.relative_to(ROOT)),
                 *[snapshot(p) for p in old_sv + new_sv + [cpp]]], 'compile.log', 300)
        command(['docker', 'exec', CONTAINER, build + '/Vcs88_pipeline_v91i2a',
                 str(out / 'vectors/cases.tsv'), str(args.seed), str(out / 'tile-events.jsonl')],
                'simulation.jsonl', 600)
        rows = [json.loads(line) for line in (out / 'simulation.jsonl').read_text().splitlines()]
        cases = [row for row in rows if row['type'] == 'case']
        verdicts = [row for row in rows if row['type'] == 'verdict']
        assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
        verdict = verdicts[0]
        assert verdict['seed'] == args.seed and verdict['cases'] == len(cases)
        assert verdict['configurations'] == 2
        assert cases and len({(row['id'], row['memory_profile']) for row in cases}) == len(cases)
        assert all(row['status'] == 'PASS' and row['seed'] == args.seed for row in cases)
        assert {row['memory_profile'] for row in cases} == {0, 1}
        assert report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sources}
        assert report['vectors_sha256'] == {str(p.relative_to(vectors)): sha(p) for p in vector_paths}
        report['tile_trace'] = compress_trace(out / 'tile-events.jsonl')
        assert report['tile_trace'] is not None
        report.update(status='PASS_CS88_BR88_COEFFICIENT_PLACEMENT', verdict=verdict,
                      case_rows=len(cases), completed_rows=sum(row['error'] == 0 for row in cases),
                      rejected_rows=sum(row['error'] != 0 for row in cases))
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        if 'tile_trace' not in report:
            partial = compress_trace(out / 'tile-events.jsonl')
            if partial is not None:
                report['partial_tile_trace'] = partial
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p)
                                     for p in sorted(out.rglob('*')) if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'pipeline-results.json').write_text(json.dumps(
            dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V91I2A_PIPELINE', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
