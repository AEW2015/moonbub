#!/usr/bin/env python3
"""Prepare or dispatch read-only V119 routed-checkpoint introspection, not a physical trial."""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
AREA = ROOT / 'experiments/python-gamebub-v119/checkpoint-diagnostic'
RECEIPT = ROOT / 'experiments/python-gamebub-v119/integrated-study/native/20261109T171305710307Z/receipt.json'
TCL = ROOT / 'fpga/experiments/cu66-v119-diagnostic/inspect.tcl'
POLICY = ROOT / 'experiments/python-gamebub-v119/study-policy.json'
IMAGE = 'sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742'
LICENSE = pathlib.Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic')
TOOLS = pathlib.Path('/home/lori/acorn-nexys4-ddr/tools')
DCP_SHA = '37cd94f489fbd2c9c0a4983c1812f35f975bd2448d3ba380b8b695802ed2deba'
POLICY_SHA = 'bacc4de23540dc5ef0387a5b9eb3c092535532a61dbd3535ef4f3b106314dd95'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def memory():
    info = {m.group(1): int(m.group(2)) * 1024 for m in re.finditer(r'^(\w+):\s+(\d+) kB$', pathlib.Path('/proc/meminfo').read_text(), re.M)}
    pressure = pathlib.Path('/proc/pressure/memory').read_text()
    used_swap = info['SwapTotal'] - info['SwapFree']
    return dict(MemAvailable_bytes=info['MemAvailable'], PSI_full_avg10=float(re.search(r'^full avg10=([\d.]+)', pressure, re.M).group(1)), combined_used_fraction=(info['MemTotal'] - info['MemAvailable'] + used_swap) / (info['MemTotal'] + info['SwapTotal']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Root dispatcher only; otherwise prepare without running Vivado')
    parser.add_argument('--dispatch', type=pathlib.Path)
    args = parser.parse_args()
    native = json.loads(RECEIPT.read_text())
    assert native['component_route_finished'] and native['observed_exit_code'] == 0
    assert native['image_id'] == IMAGE and native['clock_period_ns'] == 8.0
    dcp = pathlib.Path(native['artifacts']['route.dcp']['external_path'])
    assert sha(dcp) == native['artifacts']['route.dcp']['sha256'] == DCP_SHA
    assert sha(POLICY) == POLICY_SHA
    assert LICENSE.is_file() and TOOLS.is_dir()
    policy = json.loads(POLICY.read_text())
    AREA.mkdir(parents=True, exist_ok=True)
    preparation = dict(schema='v119-readonly-checkpoint-diagnostic-v1', status='PREPARED_NOT_EXECUTED', input_receipt=str(RECEIPT.relative_to(ROOT)), input_receipt_sha256=sha(RECEIPT), checkpoint_path=str(dcp), checkpoint_sha256=DCP_SHA, diagnostic_tcl=str(TCL.relative_to(ROOT)), diagnostic_tcl_sha256=sha(TCL), wrapper_sha256=sha(pathlib.Path(__file__)), policy_sha256=POLICY_SHA, image_id=IMAGE, license_path=str(LICENSE), license_contents_logged=False, timeout_seconds=300, cpus=2, memory_limit_bytes=8589934592, memory_swap_limit_bytes=8589934592, new_physical_trial=False, positive_repeat=False, synthesis_executed=False, placement_executed=False, routing_executed=False, bitstream_generated=False, hardware_contact=False, root_dispatch_required=True, operand_lut_recursion_depth=2, operand_startpoint_lists_truncated=False, semantic_interpretation='unresolved until actual operand report is inspected')
    if not args.run:
        (AREA / 'prepared.json').write_text(json.dumps(preparation, indent=2) + '\n')
        print('PREPARED_NOT_EXECUTED ' + str(AREA / 'prepared.json'))
        return
    assert args.dispatch and args.dispatch.is_file(), 'Root dispatch JSON is required'
    dispatch = json.loads(args.dispatch.read_text())
    assert dispatch['status'] == 'APPROVED' and dispatch['scope'] == 'v119-readonly-checkpoint-diagnostic'
    assert dispatch['diagnostic_tcl_sha256'] == preparation['diagnostic_tcl_sha256'] and dispatch['wrapper_sha256'] == preparation['wrapper_sha256']
    active = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    assert sum(n.startswith('gamebub-v11') for n in active) < policy['max_heavy_jobs'], active
    before = memory()
    assert before['MemAvailable_bytes'] >= policy['launch_available_bytes'] and before['PSI_full_avg10'] < policy['launch_PSI_full_avg10_below'] and before['combined_used_fraction'] < policy['launch_combined_used_fraction_below'], before
    actual_image = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', 'acorn-nexys4-ddr:2026.1'], text=True).strip()
    assert actual_image == IMAGE
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / stamp
    out.mkdir(parents=True)
    (out / 'inspect.tcl').write_bytes(TCL.read_bytes())
    name = 'gamebub-v119-diagnostic-' + stamp.lower()
    cmd = ['docker', 'run', '--rm', '--init', '--name', name, '--memory', '8g', '--memory-swap', '8g', '--cpus', '2', '--pids-limit', '2048', '--network', 'host', '--ulimit', 'core=0', '--mount', f'type=bind,src={TOOLS},dst=/opt/amd-tools,readonly', '--mount', f'type=bind,src={dcp},dst=/input/route.dcp,readonly', '--mount', f'type=bind,src={out / "inspect.tcl"},dst=/diagnostic/inspect.tcl,readonly', '--mount', f'type=bind,src={out},dst=/output', '--mount', f'type=bind,src={LICENSE},dst=/root/.Xilinx/license.dat,readonly', '-e', 'LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1', '-e', 'XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat', '-w', '/output', IMAGE, 'timeout', '--kill-after=10s', '300s', '/opt/amd-tools/2026.1/Vivado/bin/vivado', '-mode', 'batch', '-nojournal', '-nolog', '-notrace', '-source', '/diagnostic/inspect.tcl']
    receipt = dict(preparation, status='RUNNING', dispatch_path=str(args.dispatch), dispatch_sha256=sha(args.dispatch), command=cmd, memory_before=before)
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    start = time.monotonic()
    samples = []
    stop = None
    try:
        with (out / 'vivado.log').open('w') as log:
            process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            previous_pressure = False
            while process.poll() is None:
                sample = dict(elapsed_seconds=time.monotonic() - start, **memory())
                samples.append(sample)
                pressure = sample['PSI_full_avg10'] >= policy['stop_PSI_full_avg10_at_least_twice']
                if sample['MemAvailable_bytes'] < policy['stop_available_bytes'] or sample['combined_used_fraction'] >= policy['stop_combined_used_fraction_at_least'] or (pressure and previous_pressure):
                    stop = 'HOST_MEMORY_GATE'
                if time.monotonic() - start > 315:
                    stop = 'WRAPPER_TIMEOUT'
                if stop:
                    subprocess.run(['docker', 'kill', name], capture_output=True, timeout=10, check=False)
                    break
                previous_pressure = pressure
                time.sleep(5)
            code = process.wait(timeout=15)
    except BaseException as exc:
        subprocess.run(['docker', 'kill', name], capture_output=True, timeout=10, check=False)
        receipt.update(status='DIAGNOSTIC_ERROR', error_type=type(exc).__name__)
        raise
    finally:
        receipt.update(checkpoint_sha256_after=sha(dcp), checkpoint_unchanged=sha(dcp) == DCP_SHA, diagnostic_tcl_unchanged=sha(TCL) == preparation['diagnostic_tcl_sha256'], elapsed_seconds=time.monotonic() - start, memory_samples=samples, stop_reason=stop)
        if 'code' in locals():
            complete = (out / 'status.txt').is_file() and (out / 'status.txt').read_text().startswith('V119_READONLY_CHECKPOINT_DIAGNOSTIC_COMPLETE')
            receipt.update(observed_exit_code=code, complete_marker=complete, status='CHECKPOINT_DIAGNOSTIC_FINISHED_INTERPRETATION_OPEN' if code == 0 and complete and not stop else 'DIAGNOSTIC_FAILED')
        receipt['artifacts_sha256'] = {p.name: sha(p) for p in out.iterdir() if p.is_file() and p.name != 'receipt.json'}
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        (AREA / 'results.json').write_text(json.dumps(dict(status=receipt['status'], receipt=str((out / 'receipt.json').relative_to(ROOT)), receipt_sha256=sha(out / 'receipt.json')), indent=2) + '\n')
    print(receipt['status'] + ' ' + str(out / 'receipt.json'))


if __name__ == '__main__':
    main()
