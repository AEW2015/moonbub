#!/usr/bin/env python3
"""Retain strict eight-byte row gather/write/hash ownership regressions."""
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
AREA = ROOT / 'fpga/experiments/cu66-v91l-rows'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, choices=(912101, 912102), default=912101)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'row-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    sources = [AREA / 'cu66_row_write_hash_join_v91l.sv', AREA / 'tb_rows.cpp', Path(__file__).resolve()]
    report = dict(schema='cu66-v91l-row-standalone-v1', status='FAIL', seed=args.seed,
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources}, commands=[],
                  scope='Standalone eight-byte tile-row gather/ACK/hash adapter; generated payloads, not gameplay frames or SDRAM timing.',
                  full_frame_integration_proven=False, hardware_distinct_30fps_proven=False,
                  full_frame_decode_under10ms_proven=False)
    build = '/build/v91l-row-' + out.name
    began = time.monotonic()

    def command(argv, log, timeout):
        item = dict(argv=argv, log=log, exit_code=None)
        report['commands'].append(item)
        with (out / log).open('w') as output:
            result = subprocess.run(argv, stdout=output, stderr=subprocess.STDOUT, timeout=timeout, cwd=ROOT)
        item['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'command exit {result.returncode}: {out / log}')

    try:
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        snap = lambda p: str(out / 'sources' / p.relative_to(ROOT))
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2',
                 '--assert', '-Wall', '--top-module', 'cu66_row_write_hash_join_v91l', '--Mdir', build,
                 '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror', snap(sources[0]), snap(sources[1])],
                'compile.log', 300)
        command(['docker', 'exec', CONTAINER, build + '/Vcu66_row_write_hash_join_v91l', str(args.seed)],
                'simulation.jsonl', 120)
        rows = [json.loads(line) for line in (out / 'simulation.jsonl').read_text().splitlines()]
        verdicts = [r for r in rows if r['type'] == 'verdict']
        assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
        assert verdicts[0]['seed'] == args.seed and verdicts[0]['exact_bytes'] == 4096
        assert verdicts[0]['directed_checks'] == 32
        assert len([r for r in rows if r['type'] == 'sample']) == 4096
        assert len([r for r in rows if r['type'] == 'directed']) == 32
        assert report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sources}
        report.update(status='PASS_ROW_ACK_BEFORE_ORDERED_HASH', verdict=verdicts[0])
    except BaseException as error:
        report.update(error_class=type(error).__name__, error=str(error))
        raise
    finally:
        log = out / 'simulation.jsonl'
        if log.exists():
            raw = log.read_bytes()
            packed = log.with_suffix('.jsonl.gz')
            packed.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
            assert gzip.decompress(packed.read_bytes()) == raw
            report['simulation_trace'] = dict(path=packed.name, gzip_sha256=sha(packed),
                                             raw_sha256=sha(log), rows=len(raw.splitlines()))
            log.unlink()
        report['wall_seconds'] = time.monotonic() - began
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'row-results.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('ROW_JOIN', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
