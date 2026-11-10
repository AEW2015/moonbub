#!/usr/bin/env python3
"""Bounded read-only observation of a source-bound existing routed checkpoint."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--label', choices=('baseline-v125', 'candidate'), required=True)
    p.add_argument('--license-file', type=Path, required=True)
    a = p.parse_args()
    record = json.loads(a.receipt.read_text())
    assert record['component_route_finished'] and record['clock_period_ns'] == 8.0
    assert record['source_snapshot_unchanged'] and record['recipe_unchanged']
    artifact = record.get('external_artifacts', record.get('artifacts', {}))['route.dcp']
    checkpoint = Path(artifact['external_path'])
    assert checkpoint.is_file() and sha(checkpoint) == artifact['sha256']
    script = HERE / 'inspect_pipeline.tcl'
    spec = importlib.util.spec_from_file_location('retained_v124_native_monitor', ROOT / 'scripts/cu66-v124/native.py')
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    m = monitor.memory()
    assert m['available_bytes'] >= 8 * 1024**3 and m['psi_full_avg10'] < 1 and m['combined_used_fraction'] < .85
    active = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    assert len([n for n in active if n.startswith('gamebub-v')]) < 2
    assert a.license_file.is_file()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'experiments/python-gamebub-v126/pipeline-inspection' / (a.label + '-' + stamp)
    out.mkdir(parents=True)
    name = 'gamebub-v126-inspect-' + stamp.lower()
    image = record['image_id']
    assert image == monitor.IMAGE
    cmd = ['docker', 'run', '--rm', '--init', '--name', name, '--memory', '8g',
           '--memory-swap', '8g', '--cpus', '2', '--pids-limit', '2048', '--ulimit', 'core=0',
           '--network', 'host', '--mount',
           'type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly',
           '--mount', f'type=bind,src={checkpoint},dst=/input/route.dcp,readonly',
           '--mount', f'type=bind,src={script},dst=/diagnostic/inspect_pipeline.tcl,readonly',
           '--mount', f'type=bind,src={out},dst=/output', '--mount',
           f'type=bind,src={a.license_file.resolve()},dst=/root/.Xilinx/license.dat,readonly',
           '-e', 'LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1',
           '-e', 'XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat', '-w', '/output', image,
           'timeout', '--kill-after=10s', '240s', '/opt/amd-tools/2026.1/Vivado/bin/vivado',
           '-mode', 'batch', '-nojournal', '-nolog', '-notrace', '-source',
           '/diagnostic/inspect_pipeline.tcl', '-tclargs', '/input/route.dcp', '/output']
    receipt = dict(schema='v126-readonly-pipeline-inspection-v1', status='RUNNING',
                   native_receipt=dict(path=str(a.receipt.resolve().relative_to(ROOT)), sha256=sha(a.receipt)),
                   checkpoint=artifact, script_sha256=sha(script), runner_sha256=sha(Path(__file__)),
                   command=cmd, image_id=image, label=a.label, resources_before=m,
                   qualification=False, new_implementation=False, hardware_contact=False,
                   memory_samples=[])
    def save():
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    save()
    start = time.monotonic()
    stop, high, last = None, 0, -30
    print('V126_READONLY_INSPECTION_STARTED',out.relative_to(ROOT),flush=True)
    with (out / 'vivado.log').open('w') as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            if elapsed - last >= 15:
                sample = monitor.memory()
                receipt['memory_samples'].append(dict(elapsed_seconds=elapsed, **sample))
                high = high + 1 if sample['psi_full_avg10'] >= 5 else 0
                last = elapsed
                if sample['available_bytes'] < 4 * 1024**3 or high >= 2 or sample['combined_used_fraction'] >= .90:
                    stop = 'HOST_MEMORY_PRESSURE'
            if elapsed > 270:
                stop = 'HOST_WALL_TIMEOUT'
            if stop:
                subprocess.run(['docker','stop','--time','10',name],capture_output=True,timeout=20)
                break
            time.sleep(1)
        code = proc.wait(timeout=30)
    log = (out / 'vivado.log').read_text(errors='replace')
    receipt.update(exit_code=code, wall_seconds=time.monotonic()-start, stop_reason=stop,
                   checkpoint_unchanged=sha(checkpoint)==artifact['sha256'])
    status_file = out / 'status.txt'
    completion = status_file.is_file() and \
        'V126_PIPELINE_READONLY_INSPECTION_COMPLETE' in status_file.read_text()
    receipt['status'] = 'PASS_READONLY_OBSERVATION' if code == 0 and \
        completion and receipt['checkpoint_unchanged'] else 'FAIL'
    receipt['artifact_sha256'] = {str(f.relative_to(out)):sha(f) for f in out.rglob('*')
                                  if f.is_file() and f.name != 'receipt.json'}
    save()
    print(receipt['status'],out.relative_to(ROOT),flush=True)
    if receipt['status'] != 'PASS_READONLY_OBSERVATION':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
