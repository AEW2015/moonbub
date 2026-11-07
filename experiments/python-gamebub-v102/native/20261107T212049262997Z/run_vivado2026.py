#!/usr/bin/env python3
"""Run one resource-bounded, prepared V102 OOC build in an owned container.

Existing installed tools and a legitimate existing license are mounted read
only. Host networking exposes the actual host identity used by that license;
no MAC/hostid replacement or license modification is performed.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
AREA = ROOT / 'experiments/python-gamebub-v102/native'
HOST_TOOLS = Path('/home/lori/acorn-nexys4-ddr/tools')
BUILD_ROOT = Path('/home/lori/gamebub-build/cu66-v69')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def memory():
    info = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        info[key] = int(value.split()[0]) * 1024
    pressure = next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    avg10 = float(next(x.split('=')[1] for x in pressure.split() if x.startswith('avg10=')))
    return {'MemAvailable_bytes': info['MemAvailable'], 'PSI_full_avg10': avg10}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--license-file', type=Path, required=True)
    ap.add_argument('--timeout', type=int, default=1800)
    args = ap.parse_args()
    build = args.build.resolve()
    build.relative_to(BUILD_ROOT)
    assert build.is_dir() and args.license_file.is_file()
    assert 60 <= args.timeout <= 1800
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / stamp
    out.mkdir(parents=True, exist_ok=False)
    name = 'gamebub-v102-ooc2026-' + stamp.lower()
    mapped = Path('/build') / build.relative_to(BUILD_ROOT)
    before = memory()
    assert before['MemAvailable_bytes'] >= 8 * 1024**3 and before['PSI_full_avg10'] < 1, 'launch resource gate denied'
    shutil.copyfile(Path(__file__), out / 'run_vivado2026.py')
    shutil.copyfile(build / 'inputs.json', out / 'inputs.json')
    (out / 'recipe-snapshot').mkdir()
    for filename in ('run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl'):
        shutil.copyfile(build / filename, out / 'recipe-snapshot' / filename)
    cmd = ['docker', 'run', '--rm', '--init', '--name', name,
        '--memory', '8g', '--memory-swap', '8g', '--cpus', '2', '--pids-limit', '2048',
        '--network', 'host', '--ulimit', 'core=0',
        '--mount', f'type=bind,src={HOST_TOOLS},dst=/opt/amd-tools,readonly',
        '--mount', f'type=bind,src={build},dst={mapped}',
        '--mount', f'type=bind,src={args.license_file.resolve()},dst=/root/.Xilinx/license.dat,readonly',
        '-e', 'LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1',
        '-e', 'XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat', '-w', str(mapped),
        'acorn-nexys4-ddr:2026.1', 'timeout', '--signal=TERM', '--kill-after=15s', str(args.timeout) + 's',
        '/opt/amd-tools/2026.1/Vivado/bin/vivado', '-mode', 'batch', '-nojournal', '-nolog', '-notrace',
        '-source', str(mapped / 'run.tcl'), '-tclargs', str(mapped)]
    receipt = {'schema': 'v102-vivado2026-ooc-build-v1', 'status': 'RUNNING', 'command': cmd,
        'build_external': str(build), 'container': name, 'part': 'xc7a100tcsg324-1', 'top': 'cs88_pipeline_v91k',
        'clock_period_ns': 10.0, 'clock_loaded_before_synthesis': True, 'max_threads': 2,
        'resource_before': before, 'memory_limit_bytes': 8 * 1024**3, 'timeout_seconds': args.timeout,
        'tools_readonly': True, 'existing_legitimate_license_readonly': True,
        'license_contents_logged': False, 'hostid_or_MAC_changed': False,
        'source_manifest_sha256': sha(build / 'inputs.json'), 'runner_sha256': sha(Path(__file__)),
        'recipe_snapshots_sha256': {n: sha(build / n) for n in ('run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl')},
        'other_project_modified': False, 'hardware_contact': False, 'bitstream_generated': False,
        'board_IO_timing_qualified': False, 'full_custom_top_qualified': False,
        'hardware_30fps': False, 'complete_validated_decode_under10ms': False}
    write(out / 'receipt.json', receipt)
    print('V102_BUILD_STARTED', out.relative_to(ROOT), build, name, flush=True)
    started = time.monotonic()
    high_pressure = 0
    stop_reason = None
    samples = []
    with (out / 'vivado.log').open('w') as log, (out / 'memory.jsonl').open('w') as telemetry:
        process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        last = -30.0
        while process.poll() is None:
            elapsed = time.monotonic() - started
            if elapsed - last >= 30:
                sample = {'elapsed_seconds': elapsed, **memory()}
                stats = subprocess.run(['docker', 'exec', name, 'cat', '/sys/fs/cgroup/memory.current'],
                                       capture_output=True, text=True, timeout=8)
                sample['container_memory_bytes'] = int(stats.stdout.strip()) if stats.returncode == 0 and stats.stdout.strip().isdigit() else None
                samples.append(sample)
                telemetry.write(json.dumps(sample) + '\n')
                telemetry.flush()
                high_pressure = high_pressure + 1 if sample['PSI_full_avg10'] >= 5 else 0
                if sample['MemAvailable_bytes'] < 4 * 1024**3:
                    stop_reason = 'HOST_AVAILABLE_BELOW_4GIB'
                if high_pressure >= 2:
                    stop_reason = 'SUSTAINED_HIGH_MEMORY_PRESSURE'
                print('V102_BUILD_MONITOR', json.dumps(sample), flush=True)
                last = elapsed
            if elapsed > args.timeout + 45:
                stop_reason = 'HOST_WALL_TIMEOUT'
            if stop_reason:
                subprocess.run(['docker', 'stop', '--time', '10', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
                break
            time.sleep(1)
        try:
            code = process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'kill', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            code = process.wait(timeout=15)
    text = (out / 'vivado.log').read_text(errors='replace')
    receipt.update({'observed_exit_code': code, 'wall_seconds': time.monotonic() - started,
        'monitor_stop_reason': stop_reason, 'memory_samples': samples,
        'log_sha256': sha(out / 'vivado.log'), 'synthesis_started': 'Starting synth_design' in text or 'Command: synth_design' in text,
        'synthesis_checkpoint_written': (build / 'results/synth.dcp').is_file(),
        'placement_reports_present': (build / 'results/place-timing-summary.rpt').is_file(),
        'routing_checkpoint_written': (build / 'results/route.dcp').is_file(),
        'component_route_finished': code == 0 and 'V102_COMPONENT_ROUTE_FINISHED' in text,
        'synthesis_only_finished': code == 0 and 'V102_SYNTH_ONLY_FINISHED' in text,
        'source_snapshot_unchanged': all(sha(build / 'snapshot' / n) == pin for n, pin in json.loads((build / 'inputs.json').read_text())['source_sha256'].items())})
    receipt['status'] = ('COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' if receipt['component_route_finished'] else
        'SYNTHESIS_ONLY_FINISHED_SIGNOFF_OPEN' if receipt['synthesis_only_finished'] else
        'TOOL_OR_BUILD_FAILED' if not stop_reason else 'STOPPED_RESOURCE_OR_TIME_GATE')
    artifacts = {}
    for path in sorted((build / 'results').glob('*')):
        if path.is_file():
            artifacts[path.name] = {'sha256': sha(path), 'bytes': path.stat().st_size, 'external_path': str(path)}
            if path.suffix in ('.rpt', '.txt', '.json', '.xdc', '.tsv') and path.stat().st_size < 8 * 1024**2:
                target = out / 'reports' / path.name
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(path, target)
    receipt['artifacts'] = artifacts
    write(out / 'receipt.json', receipt)
    print('V102_BUILD_FINISHED', receipt['status'], code, receipt['wall_seconds'], flush=True)


if __name__ == '__main__':
    main()
