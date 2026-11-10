#!/usr/bin/env python3
"""Incremental fixture smoke in a private copy; never a qualification selector."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--failed-receipt', type=Path, required=True)
    ap.add_argument('--fixture-sha256', required=True)
    ap.add_argument('--fixture', type=Path, default=ROOT /
                    'fpga/experiments/cu66-v126-producer/verification/tb_successor.cpp')
    a = ap.parse_args()
    original = json.loads(a.failed_receipt.read_text())
    assert original['status'] == 'FAIL' and original['candidate']['sha256'] == sha(
        ROOT / 'fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv')
    fixture = a.fixture.resolve()
    fixture.relative_to(ROOT)
    assert sha(fixture) == a.fixture_sha256
    source = Path(original['build_external'])
    assert all(sha(source / n) == h for n, h in original['compiled_source_sha256'].items())
    assert sha(source / 'ready_probe-obj/Vready_probe') == original['binary_sha256']['ready_probe']
    helper = ROOT / 'scripts/cu66-v125/tile/qualify.py'
    spec = importlib.util.spec_from_file_location('frozen_v125_memory_only', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    memory = module.memory
    gate = memory()
    assert gate['available_bytes'] >= 8 * 1024**3 and gate['psi_full_avg10'] < 1 and gate['combined'] < .85
    active = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    assert len([n for n in active if n.startswith('gamebub-v126-')]) < 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'experiments/python-gamebub-v126/diagnostics' / stamp
    build = source.parent / ('v126-fixture-diagnostic-' + stamp)
    out.mkdir(parents=True)
    assert not build.exists()
    shutil.copytree(source, build, copy_function=shutil.copy2)
    shutil.copyfile(fixture, build / 'tb_successor.cpp')
    os.utime(build / 'tb_successor.cpp', None)
    for name, digest in original['compiled_source_sha256'].items():
        if name != 'tb_successor.cpp':
            assert sha(build / name) == digest, name
    generated = {str(p.relative_to(build)): sha(p) for p in (build / 'ready_probe-obj').iterdir()
                 if p.is_file() and p.suffix in ('.cpp', '.h', '.hpp', '.mk', '.o', '.a', '.gch')}
    report = dict(schema='v126-fixture-incremental-diagnostic-v1', status='RUNNING',
                  qualification=False, writes_qualification_selectors=False,
                  runner=dict(path=str(Path(__file__).resolve().relative_to(ROOT)), sha256=sha(Path(__file__))),
                  fresh_RTL_model_build=False, hardware_contact=False,
                  failed_receipt=dict(path=str(a.failed_receipt.resolve().relative_to(ROOT)), sha256=sha(a.failed_receipt)),
                  fixture=dict(path=str(fixture.relative_to(ROOT)), sha256=sha(fixture)),
                  memory_helper=dict(path=str(helper.relative_to(ROOT)), sha256=sha(helper)),
                  build_external=str(build), original_build_external=str(source),
                  image=IMAGE, resource_before=gate, generated_cache_before=generated, commands=[])

    def persist():
        (out / 'receipt.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')

    def run(argv, name, seconds):
        container = 'gamebub-v126-diagnostic-' + stamp.lower() + '-' + str(len(report['commands']))
        cmd = ['docker', 'run', '--rm', '--init', '--name', container,
               '--memory', '8g', '--memory-swap', '8g', '--cpus', '2', '--pids-limit', '2048',
               '--network', 'none', '--ulimit', 'core=0', '--mount',
               f'type=bind,src={build},dst=/work', '-w', '/work', IMAGE,
               'timeout', '--kill-after=5s', str(seconds) + 's', *argv]
        entry = dict(argv=cmd, exit_code=None, samples=[])
        report['commands'].append(entry)
        persist()
        start, high, stop = time.monotonic(), 0, None
        with (out / name).open('w') as log:
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            while proc.poll() is None:
                m = memory()
                entry['samples'].append(m)
                high = high + 1 if m['psi_full_avg10'] >= 5 else 0
                if m['available_bytes'] < 4 * 1024**3 or m['combined'] >= .90 or high >= 2:
                    stop = 'MEMORY_PRESSURE'
                if time.monotonic() - start > seconds + 20:
                    stop = 'HOST_TIMEOUT'
                if stop:
                    subprocess.run(['docker', 'stop', '--time', '5', container], capture_output=True, timeout=15)
                    break
                time.sleep(1)
            entry.update(exit_code=proc.wait(timeout=20), stop_reason=stop, wall_seconds=time.monotonic() - start)
        persist()
        assert entry['exit_code'] == 0 and stop is None, (name, entry)

    persist()
    print('V126_DIAGNOSTIC_STARTED', out.relative_to(ROOT), flush=True)
    try:
        run(['make', '-C', '/work/ready_probe-obj', '-f', 'Vready_probe.mk', '-j1'], 'fixture-compile.log', 180)
        text = (out / 'fixture-compile.log').read_text()
        assert 'tb_successor.o' in text and '-Werror' in text and ' -o Vready_probe' in text
        report['binary_sha256'] = sha(build / 'ready_probe-obj/Vready_probe')
        report['fixture_object_sha256'] = sha(build / 'ready_probe-obj/tb_successor.o')
        assert report['fixture_object_sha256'] != generated['ready_probe-obj/tb_successor.o']
        assert report['binary_sha256'] != original['binary_sha256']['ready_probe']
        run(['/work/ready_probe-obj/Vready_probe', 'generic', '126501', '/work/cases.tsv',
             '/work/diagnostic-trace.csv'], 'generic.log', 600)
        rows = [json.loads(x) for x in (out / 'generic.log').read_text().splitlines()]
        assert rows and all(r.get('status') == 'TEST_PASS' for r in rows)
        report.update(status='PASS_DIAGNOSTIC_ONLY', raw_terminal_rows=rows)
    except BaseException as e:
        report.update(status='FAIL_DIAGNOSTIC_ONLY', error=repr(e))
        raise
    finally:
        report['original_sources_unchanged'] = all(sha(source / n) == h for n, h in original['compiled_source_sha256'].items())
        report['original_binary_unchanged'] = sha(source / 'ready_probe-obj/Vready_probe') == original['binary_sha256']['ready_probe']
        report['unchanged_cached_model_objects'] = {n: sha(build / n) == h for n, h in generated.items()
                                                   if Path(n).name != 'tb_successor.o'}
        integrity = report['original_sources_unchanged'] and report['original_binary_unchanged'] and all(
            report['unchanged_cached_model_objects'].values())
        report['integrity_pass'] = integrity
        if not integrity:
            report['status'] = 'FAIL_DIAGNOSTIC_INTEGRITY'
        report['artifact_sha256'] = {p.name: sha(p) for p in out.iterdir() if p.is_file() and p.name != 'receipt.json'}
        persist()
        print(report['status'], out.relative_to(ROOT), flush=True)
        assert integrity, 'Diagnostic copy/original/model integrity failed'


if __name__ == '__main__':
    main()
