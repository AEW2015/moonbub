#!/usr/bin/env python3
"""Strict standalone V97 synchronous DMA/FIFO RTL; optionally join native Rust trace."""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v97-forward'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--trace', type=Path)
    args = ap.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    sources = [AREA / 'v97_forward.sv', AREA / 'tb_forward.cpp', Path(__file__).resolve(), AREA / 'README.md']
    report = dict(schema='v97-standalone-synchronous-dma-fifo-v1', status='FAIL',
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources}, commands=[],
                  scope='Actual bounded FIFO/descriptor/CRC RTL at synchronous parallel DMA and command interface. No QSPI pins/timing, ESP32 execution, Wi-Fi, decoder or publication.',
                  fifo_capacity_bytes=2048, dma_slots=2, max_logical_dma_bytes=1400, dma_alignment_bytes=4,
                  native_trace_join_requested=bool(args.trace), hardware_validated=False)
    begin = time.monotonic()

    def command(argv, name, timeout):
        entry = dict(argv=argv, log=name, exit_code=None)
        report['commands'].append(entry)
        with (out / name).open('w') as log:
            result = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        entry['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Command failed ({result.returncode}): {out / name}')

    try:
        for p in sources:
            dest = out / 'sources' / p.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
        trace = None
        if args.trace:
            original = args.trace.resolve()
            paths = [Path(line.split(maxsplit=1)[1]) for line in original.read_text().splitlines() if line.startswith('GOLDEN ')]
            assert paths and all(p.is_file() for p in paths), 'Independent GOLDEN payload files required'
            report['native_trace'] = dict(path=str(original), sha256=sha(original), golden_sha256={str(p): sha(p) for p in paths})
            trace = out / 'vectors/gateway-trace.txt'
            trace.parent.mkdir()
            golden_map = {}
            for i, p in enumerate(dict.fromkeys(paths)):
                copy = trace.parent / f'golden-{i:04d}.bin'
                shutil.copyfile(p, copy)
                golden_map[str(p)] = str(copy)
            trace.write_text('\n'.join('GOLDEN ' + golden_map[line.split(maxsplit=1)[1]] if line.startswith('GOLDEN ') else line for line in original.read_text().splitlines()) + '\n')
        mem = {line.split(':')[0]: int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')}
        pressure = Path('/proc/pressure/memory').read_text()
        full = float(next(line for line in pressure.splitlines() if line.startswith('full ')).split()[1].split('=')[1])
        report['preflight'] = dict(mem_available_kib=mem['MemAvailable'], memory_psi_full_avg10=full)
        assert mem['MemAvailable'] >= 8*1024*1024 and full < 1.0, 'Memory/PSI compile gate failed'
        # Shared lock prevents multiple V97 compile invocations. External container process gate
        # also rejects concurrent compilers from other experiments without touching them.
        with open('/tmp/gamebub-cu66-verilator-compile.lock', 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            running = subprocess.check_output(['docker', 'exec', CONTAINER, 'sh', '-c', 'ps -eo comm='], text=True)
            assert not any(x.strip() in {'verilator', 'verilator_bin', 'cc1plus', 'g++', 'make'} for x in running.splitlines()), 'Existing build active in shared container'
            command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log', 30)
            command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
            build = '/build/v97-forward-' + out.name
            report['build_directory'] = build
            command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '2', '--assert', '-Wall', '--top-module', 'v97_forward', '--Mdir', build, '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror', *[str(out / 'sources' / p.relative_to(ROOT)) for p in sources[:2]]], 'compile.log', 300)
        command(['docker', 'exec', CONTAINER, build + '/Vv97_forward', *([str(trace)] if trace else [])], 'simulation.jsonl', 180)
        rows = [json.loads(line) for line in (out / 'simulation.jsonl').read_text().splitlines()]
        verdicts = [r for r in rows if r['type'] == 'verdict']
        assert len(verdicts)==1 and verdicts[0]['status']=='TEST_PASS'
        assert verdicts[0]['max_fifo']==2048 and verdicts[0]['max_slots']==2
        joins = [r for r in rows if r['type']=='native_join']
        assert not trace or len(joins)==1 and joins[0]['frames']>0 and joins[0]['status']=='PASS'
        assert report['source_sha256']=={str(p.relative_to(ROOT)): sha(p) for p in sources}, 'Source modified during build'
        report.update(status='PASS_STANDALONE_DMA_FIFO_RTL' if not trace else 'PASS_NATIVE_RUST_TO_DMA_FIFO_RTL_JOIN', verdict=verdicts[0], native_join=joins)
    except BaseException as error:
        report.update(error_class=type(error).__name__, error=str(error))
        raise
    finally:
        report['wall_seconds']=time.monotonic()-begin
        report['artifacts_sha256']={str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2)+'\n')
        (AREA / 'results.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2)+'\n')
        print('V97_FORWARD',report['status'],out,flush=True)


if __name__=='__main__':
    main()
