#!/usr/bin/env python3
"""Probe the complete admission function bodies with exact 32-bit arithmetic."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv'
FPGA = ROOT / 'fpga/experiments/cu66-v103-admission'
AREA = ROOT / 'experiments/python-gamebub-v103/admission'
CONTAINER = 'gamebub-cu66-v69-build'
BASELINE = '6d2ca3ae9abe207215d6130cfb0087fd07928917'
sys.path.insert(0, str(ROOT / 'scripts/cu66-v100'))
from run_rtl import resources


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def tile_domain():
    ts = set(range(8192))
    for bit in range(32):
        for delta in (-181, -180, -179, -91, -90, -89, -2, -1, 0, 1, 2,
                      44, 45, 46, 89, 90, 91, 179, 180, 181):
            t = (1 << bit) + delta
            if 0 <= t <= 0xffffffff:
                ts.add(t)
    ts.update(0xffffffff - i for i in range(512))
    for i in range(1024):
        for q in (i, 0xffffffff // 90 - i):
            for r in (0, 1, 44, 45, 46, 88, 89):
                t = q * 90 + r
                if t <= 0xffffffff:
                    ts.add(t)
    rng = 103501
    for _ in range(10000):
        rng ^= (rng << 13) & 0xffffffff
        rng ^= rng >> 17
        rng ^= (rng << 5) & 0xffffffff
        ts.add(rng)
    return sorted(ts)


def replay(path):
    domain = tile_domain()
    count = 0
    with gzip.open(path, 'rt') as trace:
        for line in trace:
            row = json.loads(line)
            p, t = count // len(domain), domain[count % len(domain)]
            assert p < 4 and row['plane'] == p and row['tile'] == t
            y, x = divmod(t, 90)
            expected = (y // 2) * 45 + x // 2 if p == 0 else t
            assert row['original'] == row['candidate'] == row['expected'] == expected
            count += 1
    assert count == 4 * len(domain)
    return dict(status='PASS', rows=count, tiles_per_plane=len(domain),
        oracle='Python unbounded integer divmod row/column geometry',
        domain='All 4 planes x [all tiles 0..8191; selected full-32-bit quotient/power/high boundaries; 10000 deterministic xorshift32 values]',
        scope='Exhaustive 13-bit tile subset plus sampled 32-bit boundary/random inputs; not exhaustive 32-bit RTL enumeration.')


def main():
    start = time.monotonic()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / stamp
    out.mkdir(parents=True, exist_ok=False)
    build = Path('/home/lori/gamebub-build/cu66-v69') / ('v103-admission-' + stamp)
    build.mkdir(exist_ok=False)
    candidate = FPGA / 'cs88_admission_v91i2a.sv'
    files = [SRC, candidate, *[FPGA / name for name in ('admission_original.sv',
        'admission_candidate.sv', 'admission_probe.sv', 'tb_admission.cpp', 'ports.json', 'change.json')],
        Path(__file__).resolve()]
    report = dict(schema='v103-admission-focused-rtl-v1', status='FAIL',
        baseline_revision=BASELINE, candidate=dict(path=str(candidate.relative_to(ROOT)), sha256=sha(candidate)),
        backend='Verilator 5.020 behavioral, explicitly retained existing backend',
        source_sha256={str(p.relative_to(ROOT)): sha(p) for p in files},
        commands=[], clock_edges=0, strict_warnings=True,
        assertions_disabled_or_downgraded=False,
        limits=['Combinational function probe only; no clocked protocol coverage.',
                'Full 32-bit identity justified algebraically; sampled RTL domain is not a formal proof.',
                'No mapped-netlist/native timing or hardware performance qualification.'])

    def command(argv, name, timeout):
        entry = dict(argv=argv, log=name, timeout_seconds=timeout, resource_gate=resources())
        report['commands'].append(entry)
        began = time.monotonic()
        with (out / name).open('w') as log:
            result = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=timeout + 15)
        entry.update(exit_code=result.returncode, wall_seconds=time.monotonic() - began)
        assert result.returncode == 0, ('command failure', name, result.returncode)

    try:
        report['resource_gate'] = resources()
        blob = subprocess.check_output(['git', 'show', BASELINE + ':' + str(SRC.relative_to(ROOT))], cwd=ROOT)
        assert hashlib.sha256(blob).hexdigest() == sha(SRC)
        extra = ',\n    input logic [1:0] probe_plane,\n    input logic [31:0] probe_tile,\n    output logic [31:0] probe_cell\n);'
        assign = '    assign probe_cell=cell_index(probe_plane,probe_tile);\n'
        for kind, production in [('original', SRC), ('candidate', candidate)]:
            text = (FPGA / ('admission_' + kind + '.sv')).read_text()
            text = text.replace('module admission_' + kind + ' (', 'module cs88_admission_v91i2a (', 1)
            text = text.replace(extra, ');', 1).replace(assign, '', 1)
            assert text == production.read_text(), 'adapter changed production body'
        report['verification_adapters_preserve_complete_production_body'] = True
        report['production_port_count'] = json.loads((FPGA / 'ports.json').read_text())['production_port_count']
        for source in files:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        copy = lambda p: str(out / 'sources' / p.relative_to(ROOT))
        mapped = '/build/' + build.name
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'verilator.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler.log', 30)
        command(['docker', 'exec', CONTAINER, 'timeout', '--kill-after=5s', '300s',
            'verilator', '--cc', '--exe', '--build', '-j', '2', '--assert', '-Wall',
            '--language', '1800-2017', '--top-module', 'admission_probe', '--Mdir', mapped,
            '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
            *[copy(FPGA / name) for name in ('admission_original.sv', 'admission_candidate.sv', 'admission_probe.sv', 'tb_admission.cpp')]],
            'compile.log', 300)
        assert '%Warning-' not in (out / 'compile.log').read_text(), 'strict warning policy'
        command(['docker', 'exec', CONTAINER, 'sha256sum', mapped + '/Vadmission_probe'], 'binary.log', 30)
        report['binary'] = dict(path=mapped + '/Vadmission_probe', sha256=(out / 'binary.log').read_text().split()[0])
        trace = out / 'trace.jsonl'
        command(['docker', 'exec', CONTAINER, 'timeout', '--kill-after=5s', '120s',
            mapped + '/Vadmission_probe', str(trace)], 'simulation.jsonl', 120)
        verdict = json.loads((out / 'simulation.jsonl').read_text())
        assert verdict['status'] == 'TEST_PASS' and verdict['clock_edges'] == 0
        assert verdict['cases'] == 4 * len(tile_domain())
        report['terminal_verdict'] = verdict
        raw_hash = sha(trace)
        packed = trace.with_suffix('.jsonl.gz')
        with trace.open('rb') as source, packed.open('wb') as dest:
            with gzip.GzipFile(fileobj=dest, mode='wb', filename='', mtime=0) as zipped:
                shutil.copyfileobj(source, zipped)
        assert hashlib.sha256(gzip.decompress(packed.read_bytes())).hexdigest() == raw_hash
        trace.unlink()
        report['trace_replay'] = dict(replay(packed), path=packed.name, sha256=sha(packed), raw_sha256=raw_hash)
        assert report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in files}
        report.update(status='PASS', actual_RTL_run=True, cases=verdict['cases'])
    except BaseException as error:
        report.update(error_class=type(error).__name__, error=str(error))
        raise
    finally:
        report['wall_seconds'] = time.monotonic() - start
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out / 'results.json', report)
        write(AREA / 'results.json', dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))))
        print('V103_ADMISSION', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
