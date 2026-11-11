#!/usr/bin/env python3
"""Freeze and run the native V97 host-to-portable-receiver exchange."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
AREA = ROOT / 'experiments/python-gamebub-v129/v97-negotiation'
IMAGE = 'sha256:e6e97e6db1c57d0f07530d7ae6912e455bb7079de7428f282a508a2fcca3fb5a'
TOOLS = Path('/home/lori/gamebub-tools')
FILES = ('firmware/handheld/src/streaming/protocol97.rs', 'host/moonshine/protocol97.py',
         'host/moonshine/__init__.py', 'scripts/cu66-v129/v97-negotiation/bridge.rs',
         'scripts/cu66-v129/v97-negotiation/exchange.py', 'scripts/cu66-v129/v97-negotiation/run.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    attempt = AREA / 'attempts' / stamp
    snapshot = attempt / 'sources'
    snapshot.mkdir(parents=True)
    source = {name: sha(ROOT / name) for name in FILES}
    for name in FILES:
        dest = snapshot / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)
        assert sha(dest) == source[name]
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    tracked = {}
    for name in FILES[:3]:
        tracked[name] = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT) == (ROOT / name).read_bytes()
    freeze = dict(schema='v129-v97-exchange-freeze-v1', source_sha256=source,
                  git_head=head, tracked_source_matches_head=tracked, image_id=IMAGE)
    write(attempt / 'freeze.json', freeze)
    command = ['docker', 'run', '--rm', '--init', '--network', 'none', '--cpus', '2',
               '--memory', '8g', '--memory-swap', '8g', '--pids-limit', '1024',
               '--mount', f'type=bind,src={snapshot},dst=/src,readonly',
               '--mount', f'type=bind,src={attempt},dst=/work',
               '--mount', f'type=bind,src={TOOLS},dst=/opt/gamebub-tools,readonly',
               '-e', 'CARGO_HOME=/opt/gamebub-tools/cargo', '-e', 'RUSTUP_HOME=/opt/gamebub-tools/rustup',
               '-e', 'PYTHONDONTWRITEBYTECODE=1', IMAGE, 'timeout', '--kill-after=5s', '120s', 'sh', '-c',
               'set -eu; /opt/gamebub-tools/cargo/bin/rustc +stable --version >&2; '
               '/opt/gamebub-tools/cargo/bin/rustc +stable --edition=2021 -D warnings -O '
               '/src/scripts/cu66-v129/v97-negotiation/bridge.rs -o /work/bridge; '
               'python3 /src/scripts/cu66-v129/v97-negotiation/exchange.py /work/bridge']
    receipt = dict(schema='v129-v97-native-exchange-v1', status='FAIL', source_sha256=source,
                   freeze_sha256=sha(attempt / 'freeze.json'), command=command, image_id=IMAGE,
                   scope='Portable V97 Python and Rust protocol only; not active MSV1 worker, Sunshine, ESP32, Wi-Fi, QSPI or FPGA.',
                   hardware_contact=False)
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=135)
        (attempt / 'stdout.log').write_text(result.stdout)
        (attempt / 'stderr.log').write_text(result.stderr)
        receipt['exit_code'] = result.returncode
        assert result.returncode == 0
        verdict = json.loads(result.stdout)
        assert verdict['status'] == 'PASS' and verdict['mutated_ack_bytes_rejected'] == 40
        assert verdict['research_profiles_checked'] == 4 and verdict['jpeg_fragments'] == 3
        assert all(sha(ROOT / n) == h and sha(snapshot / n) == h for n, h in source.items())
        receipt.update(status='PASS', verdict=verdict, snapshots_unchanged=True,
                       compiler_version=result.stderr.splitlines()[0], binary_sha256=sha(attempt / 'bridge'))
    except Exception as error:
        receipt['failure'] = repr(error)
        raise
    finally:
        receipt['artifacts'] = {str(p.relative_to(attempt)): sha(p) for p in attempt.rglob('*') if p.is_file() and p.name != 'receipt.json'}
        write(attempt / 'receipt.json', receipt)
    selector = dict(status='PASS', path=str((attempt / 'receipt.json').relative_to(ROOT)), sha256=sha(attempt / 'receipt.json'))
    write(AREA / 'results.json', selector)
    print(json.dumps(selector, sort_keys=True))


if __name__ == '__main__':
    main()
