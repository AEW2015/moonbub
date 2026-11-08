#!/usr/bin/env python3
"""Resume V106's verified synthesis checkpoint in a separate bounded V107 run."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v107/resume'
BUILD_ROOT = Path('/home/lori/gamebub-build/cu66-v69')
PARENT = ROOT / 'experiments/python-gamebub-v106/native/20261108T025230842632Z/receipt.json'
FLOW = ROOT / 'fpga/experiments/cu66-v107-flow'
TOOLS = Path('/home/lori/acorn-nexys4-ddr/tools')
LICENSE = Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def memory():
    values = {line.split(':')[0]: int(line.split(':')[1].split()[0]) * 1024
              for line in Path('/proc/meminfo').read_text().splitlines()}
    full = next(line for line in Path('/proc/pressure/memory').read_text().splitlines()
                if line.startswith('full '))
    avg = float(next(field.split('=')[1] for field in full.split() if field.startswith('avg10=')))
    return dict(MemAvailable_bytes=values['MemAvailable'], PSI_full_avg10=avg)


def main():
    AREA.mkdir(parents=True, exist_ok=True)
    assert not list(AREA.glob('*/receipt.json')), 'One continuation attempt; preserve prior outcomes'
    parent = json.loads(PARENT.read_text())
    checkpoint = Path(parent['artifacts']['synth.dcp']['external_path'])
    digest = parent['artifacts']['synth.dcp']['sha256']
    assert parent['observed_exit_code'] == 124 and parent['synthesis_checkpoint_written']
    assert sha(checkpoint) == digest
    before = memory()
    assert before['MemAvailable_bytes'] >= 8 * 1024**3 and before['PSI_full_avg10'] < 1
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / stamp
    out.mkdir()
    build = BUILD_ROOT / ('v107-resume-' + stamp)
    build.mkdir()
    mapped = Path('/build') / build.name
    name = 'gamebub-v107-resume-' + stamp.lower()
    shutil.copyfile(PARENT, out / 'parent-receipt.json')
    shutil.copyfile(PARENT.parent / 'inputs.json', out / 'parent-inputs.json')
    shutil.copyfile(FLOW / 'resume.tcl', build / 'run.tcl')
    # Reuse the exact already-tested report recipe, without altering V106.
    report_source = ROOT / 'fpga/experiments/cu66-v106-flow/report.tcl'
    shutil.copyfile(report_source, build / 'report.tcl')
    for source, target in ((Path(__file__), out / 'resume_route.py'),
                           (build / 'run.tcl', out / 'run.tcl'),
                           (report_source, out / 'report.tcl')):
        shutil.copyfile(source, target)
    cmd = ['docker', 'run', '--rm', '--init', '--name', name,
           '--memory', '8g', '--memory-swap', '8g', '--cpus', '2', '--pids-limit', '2048',
           '--network', 'host', '--ulimit', 'core=0',
           '--mount', f'type=bind,src={TOOLS},dst=/opt/amd-tools,readonly',
           '--mount', f'type=bind,src={LICENSE},dst=/root/.Xilinx/license.dat,readonly',
           '--mount', f'type=bind,src={checkpoint},dst=/parent/synth.dcp,readonly',
           '--mount', f'type=bind,src={build},dst={mapped}',
           '-e', 'LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1',
           '-e', 'XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat', '-w', str(mapped),
           'acorn-nexys4-ddr:2026.1', 'timeout', '--signal=TERM', '--kill-after=15s', '1800s',
           '/opt/amd-tools/2026.1/Vivado/bin/vivado', '-mode', 'batch', '-nojournal', '-nolog',
           '-notrace', '-source', str(mapped / 'run.tcl'), '-tclargs', str(mapped)]
    receipt = dict(schema='v107-checkpoint-route-continuation-v1', status='RUNNING',
        command=cmd, build_external=str(build), part='xc7a100tcsg324-1', clock_period_ns=10.0,
        parent_receipt=dict(path=str(PARENT.relative_to(ROOT)), sha256=sha(PARENT)),
        parent_checkpoint=dict(path=str(checkpoint), sha256_before=digest, readonly_mount=True),
        source_sha256={str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
                       str((FLOW / 'resume.tcl').relative_to(ROOT)): sha(FLOW / 'resume.tcl'),
                       str(report_source.relative_to(ROOT)): sha(report_source)},
        explicit_synthesis_rerun=False, strategy='Default opt/place/route from preserved synthesis checkpoint',
        clock_or_exception_edits=False, tools_readonly=True, existing_legitimate_license_readonly=True,
        license_contents_logged=False, hostid_or_MAC_changed=False, hardware_contact=False,
        hardware_30fps=False, complete_decode_under10ms_validated=False, board_IO_CDC_qualified=False,
        max_threads=2, timeout_seconds=1800, memory_limit_bytes=8*1024**3,
        resource_before=before, memory_samples=[])
    write(out / 'receipt.json', receipt)
    start, last, high, stop, code = time.monotonic(), -30, 0, None, None
    print('V107_RESUME_STARTED', out.relative_to(ROOT), flush=True)
    try:
        with (out / 'vivado.log').open('w') as log:
            process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            while process.poll() is None:
                elapsed = time.monotonic() - start
                if elapsed - last >= 30:
                    sample = dict(elapsed_seconds=elapsed, **memory())
                    stats = subprocess.run(['docker', 'exec', name, 'cat', '/sys/fs/cgroup/memory.current'],
                                           capture_output=True, text=True, timeout=8)
                    sample['container_memory_bytes'] = int(stats.stdout.strip()) if stats.returncode == 0 and stats.stdout.strip().isdigit() else None
                    receipt['memory_samples'].append(sample)
                    high = high + 1 if sample['PSI_full_avg10'] >= 5 else 0
                    if sample['MemAvailable_bytes'] < 4 * 1024**3 or high >= 2:
                        stop = 'HOST_MEMORY_GATE'
                    print('V107_RESUME_MONITOR', json.dumps(sample), flush=True)
                    last = elapsed
                if elapsed > 1845:
                    stop = 'HOST_WALL_TIMEOUT'
                if stop:
                    subprocess.run(['docker', 'stop', '--time', '10', name], timeout=20,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                time.sleep(1)
            code = process.wait(timeout=30)
        text = (out / 'vivado.log').read_text(errors='replace')
        finished = code == 0 and 'V107_COMPONENT_ROUTE_FINISHED' in text
        receipt['status'] = 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' if finished else 'TIME_OR_RESOURCE_GATE' if stop or code in (124, 137) else 'TOOL_OR_BUILD_FAILED'
    finally:
        receipt.update(observed_exit_code=code, wall_seconds=time.monotonic()-start,
                       monitor_stop_reason=stop, log_sha256=sha(out / 'vivado.log'))
        receipt['parent_checkpoint'].update(sha256_after=sha(checkpoint), unchanged=sha(checkpoint)==digest)
        artifacts = {}
        for path in sorted((build / 'results').glob('*')):
            if not path.is_file():
                continue
            artifacts[path.name] = dict(sha256=sha(path), bytes=path.stat().st_size, external_path=str(path))
            if path.suffix in ('.rpt', '.txt', '.json', '.xdc', '.tsv') and path.stat().st_size < 8*1024**2:
                target = out / 'reports' / path.name
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(path, target)
        receipt['artifacts'] = artifacts
        receipt['retained_sha256'] = {str(path.relative_to(out)): sha(path)
            for path in sorted(out.rglob('*')) if path.is_file() and path.name != 'receipt.json'}
        write(out / 'receipt.json', receipt)
        write(AREA / 'results.json', dict(receipt, selected_receipt=str((out / 'receipt.json').relative_to(ROOT))))
        print('V107_RESUME_FINISHED', receipt['status'], code, flush=True)
    assert receipt['parent_checkpoint']['unchanged']
    if receipt['status'] != 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
