#!/usr/bin/env python3
"""Strict V121 queue proof; --run consumes an explicitly granted heavy slot."""
import argparse
import collections
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'fpga/experiments/cu66-v121-request'
VER = SRC / 'verification'
AREA = ROOT / 'experiments/python-gamebub-v121/request'
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
GIB = 1024**3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temp.replace(path)


def verify():
    recipe = json.loads((SRC / 'edit-recipe.json').read_text())
    adapters = json.loads((SRC / 'verification-recipe.json').read_text())

    def reversible(meta):
        original = ROOT / meta['original']
        candidate = ROOT / meta['candidate']
        assert sha(original) == meta['original_sha256']
        text = original.read_text()
        for edit in meta['edits']:
            assert text.count(edit['before']) == 1
            text = text.replace(edit['before'], edit['after'], 1)
        assert candidate.read_text() == text and sha(candidate) == meta['candidate_sha256']
        for edit in reversed(meta['edits']):
            assert text.count(edit['after']) == 1
            text = text.replace(edit['after'], edit['before'], 1)
        assert text == original.read_text()

    reversible(recipe)
    for meta in adapters['adapters']:
        reversible(meta)
    reversible(adapters['legacy'])
    original = (ROOT / recipe['original']).read_text()
    candidate = (ROOT / recipe['candidate']).read_text()
    for block in re.findall(r'`ifndef SYNTHESIS.*?`endif', original, re.S):
        assert block in candidate
    assert recipe['added_public_cycles'] == recipe['old_assertions_removed'] == recipe['external_interface_changes'] == 0
    assert recipe['added_source_payload_bits'] == 32
    meta = adapters['legacy']
    needs = lambda s: collections.Counter(re.findall(r'need\(.*?\);', s, re.S))
    assert not needs((ROOT / meta['original']).read_text()) - needs((ROOT / meta['candidate']).read_text())
    assert (VER / 'tb_refill_legacy.frozen.cpp').read_bytes() == (ROOT / meta['original']).read_bytes()
    assert adapters['old_require_checks_removed'] == 0
    handoff = json.loads((ROOT / 'experiments/python-gamebub-v120/handoff.json').read_text())
    assert len(handoff['source_origins']) == 18
    for entry in handoff['source_origins'].values():
        assert sha(ROOT / entry['path']) == entry['sha256'], entry
    return recipe


def memory():
    raw = Path('/proc/meminfo').read_text()
    mem = {line.split(':')[0]: int(line.split()[1])*1024 for line in raw.splitlines()}
    pressure = Path('/proc/pressure/memory').read_text()
    full = next(line for line in pressure.splitlines() if line.startswith('full '))
    combined = (mem['MemTotal']-mem['MemAvailable']+mem['SwapTotal']-mem['SwapFree'])/(mem['MemTotal']+mem['SwapTotal'])
    return dict(monotonic=time.monotonic(), available_bytes=mem['MemAvailable'],
                psi_full_avg10=float(full.split('avg10=')[1].split()[0]), combined=combined,
                meminfo=raw, memory_pressure=pressure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--root-grant')
    args = parser.parse_args()
    recipe = verify()
    if not args.run:
        print('V121_REQUEST_PREPARED_NOT_RUN', recipe['candidate_sha256'])
        return
    assert args.root_grant == 'ROOT_V121_REQUEST', 'Explicit parent heavy-slot grant required'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / stamp
    out.mkdir(parents=True)
    build = Path('/home/lori/gamebub-build/cu66-v69') / ('v121-request-' + stamp)
    build.mkdir()
    files = sorted(set([p for p in SRC.rglob('*') if p.is_file()] +
                       [p for p in Path(__file__).parent.iterdir() if p.is_file()] +
                       [ROOT / recipe['original'], ROOT / 'fpga/experiments/cu66-v91i2b/tb_refill_queue.cpp',
                        ROOT / 'docs/cu66-v121/request-design.md', ROOT / 'experiments/python-gamebub-v120/handoff.json']))
    report = dict(schema='v121-prepared-request-focused-v1', status='RUNNING', actual_RTL_run=False,
                  root_grant=args.root_grant, image=IMAGE, backend='Verilator 5.020', build_external=str(build),
                  source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files}, commands=[], runs=[], negative_runs=[],
                  candidate=dict(path=recipe['candidate'], sha256=recipe['candidate_sha256']),
                  strict_warnings=True, warning_suppression=False, assertions_disabled_or_downgraded=False,
                  old_require_checks_removed=0, added_public_cycles=0, sourceB18_unchanged=True,
                  comparison='Every original output exact before/after every tested edge; independent external accepted-request/byte/owner scoreboard.',
                  limits=['Finite focused queue simulation; complete component, timing, CDC and hardware qualification are separate gates.'])
    started = time.monotonic()

    def persist():
        write(out / 'results.json', report)

    def command(argv, name, cap, simulation=False, expected_failure=False):
        gate = memory()
        assert gate['available_bytes'] >= 8*GIB and gate['psi_full_avg10'] < 1 and gate['combined'] < .85, gate
        container = 'gamebub-v121-request-' + stamp.lower() + '-' + str(len(report['commands']))
        cmd = ['docker', 'run', '--rm', '--init', '--name', container, '--memory', '8g', '--memory-swap', '8g',
               '--cpus', '2', '--pids-limit', '2048', '--network', 'none', '--ulimit', 'core=0',
               '--mount', f'type=bind,src={build},dst=/work', '-w', '/work', IMAGE,
               'timeout', '--kill-after=5s', str(cap)+'s', *argv]
        entry = dict(argv=cmd, log=name, resource_before=gate, timeout_seconds=cap,
                     simulation=simulation, expected_failure=expected_failure)
        report['commands'].append(entry)
        if simulation:
            report['actual_RTL_run'] = True
        persist()
        began = time.monotonic()
        process = None
        reason = None
        high_psi = 0
        with (out / name).open('w') as log, (out / (name+'.resources.jsonl')).open('w') as samples:
            try:
                process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                while process.poll() is None:
                    sample = memory()
                    samples.write(json.dumps(sample, sort_keys=True)+'\n')
                    samples.flush()
                    high_psi = high_psi+1 if sample['psi_full_avg10'] >= 5 else 0
                    if sample['available_bytes'] < 4*GIB or sample['combined'] >= .9 or high_psi >= 2:
                        reason = 'RESOURCE_STOP'
                        raise RuntimeError(reason)
                    if time.monotonic()-began > cap+15:
                        reason = 'HOST_WATCHDOG'
                        raise RuntimeError(reason)
                    time.sleep(1)
                entry['exit_code'] = process.wait(timeout=10)
                if expected_failure:
                    assert entry['exit_code'] in (134, 139), (name, entry['exit_code'])
                else:
                    assert entry['exit_code'] == 0, (name, entry['exit_code'])
            finally:
                if process is not None and process.poll() is None:
                    stopped = subprocess.run(['docker', 'stop', '--time', '3', container], stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT, timeout=12)
                    (out / (name+'.stop.log')).write_bytes(stopped.stdout)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
                entry.update(wall_seconds=time.monotonic()-began, stop_reason=reason, resource_after=memory())
                persist()

    try:
        for path in files:
            dest = out / 'sources' / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
        for path in VER.iterdir():
            if path.suffix in ('.sv', '.cpp', '.hpp'):
                shutil.copyfile(path, build / path.name)
        shutil.copyfile(ROOT / recipe['original'], build / 'overflow-original.sv')
        shutil.copyfile(ROOT / recipe['candidate'], build / 'overflow-candidate.sv')
        report['compiled_source_sha256'] = {p.name:sha(p) for p in build.iterdir() if p.is_file()}
        command(['verilator', '--version'], 'version.log', 30)
        assert 'Verilator 5.020' in (out / 'version.log').read_text()
        flags = ['verilator', '--cc', '--exe', '--build', '-j', '1', '--assert', '-Wall',
                 '--language', '1800-2017', '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror']
        command(flags + ['--top-module', 'request_probe', '--Mdir', '/work/obj',
                        '/work/request_original.sv', '/work/request_candidate.sv', '/work/request_probe.sv',
                        '/work/tb_request.cpp'], 'compile.log', 300)
        assert '%Warning-' not in (out / 'compile.log').read_text()
        report['binary_sha256'] = sha(build / 'obj/Vrequest_probe')
        for seed in (121101, 121102):
            name = 'simulation-'+str(seed)+'.log'
            command(['/work/obj/Vrequest_probe', str(seed)], name, 120, simulation=True)
            rows = [json.loads(line) for line in (out / name).read_text().splitlines()]
            old = next(row for row in rows if row.get('type') == 'verdict')
            result = next(row for row in rows if row.get('type') == 'v121_request_verdict')
            assert old['status'] == result['status'] == 'TEST_PASS'
            assert old['directed_checks'] == 12 and result['legal_boundary_cases'] == 40
            assert result['stalled_full32_cases'] == 25 and result['random_cases'] == 2048
            assert result['physical_responses_on_revoke'] == 4
            report['runs'].append(dict(seed=seed, inherited=old, extension=result))
            persist()
        for label in ('original', 'candidate'):
            # Filenames deliberately match their original module name so -Wall
            # remains fatal without DECLFILENAME suppression.
            target = build / 'byte_refill_queue_v91i2b.sv'
            shutil.copyfile(build / ('overflow-'+label+'.sv'), target)
            command(flags + ['--top-module', 'byte_refill_queue_v91i2b', '--Mdir', '/work/obj-'+label,
                             '/work/byte_refill_queue_v91i2b.sv', '/work/tb_overflow.cpp'],
                    'compile-overflow-'+label+'.log', 180)
            assert '%Warning-' not in (out / ('compile-overflow-'+label+'.log')).read_text()
            report.setdefault('negative_binary_sha256', {})[label] = sha(build / ('obj-'+label+'/Vbyte_refill_queue_v91i2b'))
            for first in (0xffffffff, 0xfffffffe):
                name = 'negative-'+label+'-'+str(first)+'.log'
                command(['/work/obj-'+label+'/Vbyte_refill_queue_v91i2b', str(first)], name, 30,
                        simulation=True, expected_failure=True)
                log = (out / name).read_text()
                assert 'refill request span overflow' in log and 'MISSING_EXPECTED' not in log
                accepted = [line for line in log.splitlines() if line.startswith('NEGATIVE_ACCEPT ')]
                expected_ordinal = 0x100000000-first
                expected_last = f'NEGATIVE_ACCEPT edge={expected_ordinal} ordinal={expected_ordinal} address=0'
                assert len(accepted) == expected_ordinal+1 and accepted[-1] == expected_last, accepted
                report['negative_runs'].append(dict(variant=label, first_address=first,
                    expected_failure='refill request span overflow', accepted=accepted, log=name))
                persist()
        for first in (0xffffffff, 0xfffffffe):
            negative = [row for row in report['negative_runs'] if row['first_address'] == first]
            assert len(negative) == 2 and negative[0]['accepted'] == negative[1]['accepted']
        assert report['source_sha256'] == {str(p.relative_to(ROOT)):sha(p) for p in files}
        assert all(sha(out/'sources'/p.relative_to(ROOT)) == sha(p) for p in files)
        verify()
        report.update(status='PASS', frozen_after_focused_PASS=True)
    except BaseException as exc:
        report.update(status='FAIL', error_class=type(exc).__name__, error=str(exc))
        raise
    finally:
        report['wall_seconds'] = time.monotonic()-started
        report['artifact_sha256'] = {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*'))
                                     if p.is_file() and p.name != 'results.json'}
        persist()
        write(AREA / 'results.json', dict(status=report['status'], actual_RTL_run=report['actual_RTL_run'],
              selected_report=str((out/'results.json').relative_to(ROOT)), selected_report_sha256=sha(out/'results.json')))
        print('V121_REQUEST_FOCUSED', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
