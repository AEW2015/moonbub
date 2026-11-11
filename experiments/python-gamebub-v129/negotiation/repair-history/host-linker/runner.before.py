#!/usr/bin/env python3
"""Run a source-bound host test of the actual Rust receiver's codec boundary."""
import datetime
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AREA = ROOT / 'experiments/python-gamebub-v129/negotiation'
COMPILER = Path('/home/lori/gamebub-tools/rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin/rustc')
FILES = {
    'firmware/handheld/src/streaming/protocol.rs': '32a91ffaf0b39a82f11036be7e501765cd3f9fed6905c27b6efc01f358d79e64',
    'host/fixtures/pattern-msv1-packets.bin': '78c58cfcc4860761c33bcc7021e3db14e9fa66ef5e9a385ae1e4c00c82a6447f',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    script = Path(__file__).resolve()
    bench = script.with_name('receiver_guard.rs')
    for name, expected in FILES.items():
        actual = (ROOT / name).read_bytes()
        assert hashlib.sha256(actual).hexdigest() == expected
        assert subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT) == actual
    before = {str(p.relative_to(ROOT)): sha(p) for p in (script, bench)} | FILES
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    attempt = AREA / 'attempts' / stamp
    attempt.mkdir(parents=True)
    result = dict(schema='v129-actual-rust-receiver-codec-boundary-v1', status='FAIL',
                  source_sha256=before, git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_scope='Actual unchanged firmware protocol module, native host Rust execution; not ESP32, session, Wi-Fi, QSPI or FPGA execution.',
                  hardware_contact=False, actual_session_or_fpga_executed=False)
    try:
        result['compiler_version'] = subprocess.check_output([str(COMPILER), '--version'], text=True, timeout=15).strip()
        with tempfile.TemporaryDirectory(prefix='v129-receiver-') as directory:
            binary = Path(directory) / 'receiver_guard'
            command = [str(COMPILER), '--edition=2021', '-D', 'warnings', '-O', str(bench), '-o', str(binary)]
            build = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=120)
            (attempt / 'compile.log').write_text(build.stdout + build.stderr)
            result['compile_command'] = [*command[:-1], '<temporary binary>']
            result['compile_exit'] = build.returncode
            if build.returncode:
                raise RuntimeError('rustc failed; see compile.log')
            result['binary_sha256'] = sha(binary)
            run = subprocess.run([str(binary), str(ROOT / 'host/fixtures/pattern-msv1-packets.bin')],
                                 cwd=ROOT, text=True, capture_output=True, timeout=120)
            (attempt / 'run.log').write_text(run.stdout + run.stderr)
            result['run_exit'] = run.returncode
            if run.returncode:
                raise RuntimeError('receiver probe failed; see run.log')
            verdict = json.loads(run.stdout)
            assert verdict == dict(status='TEST_PASS', unknown_codec_ids_rejected=255,
                aborted_frame_recoveries=255, fixture_datagrams=26, jpeg_frame_bytes=26159,
                mislabeled_cs88_accepted_by_protocol=True, actual_rust_receiver=True,
                actual_session_or_fpga_executed=False)
            result['verdict'] = verdict
        assert all(sha(ROOT / path) == digest for path, digest in before.items())
        result['status'] = 'PASS'
    except Exception as error:
        result['failure'] = repr(error)
        raise
    finally:
        result['artifacts'] = {p.name: sha(p) for p in attempt.iterdir() if p.is_file() and p.name != 'receipt.json'}
        receipt = attempt / 'receipt.json'
        receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    selector = dict(status=result['status'], path=str(receipt.relative_to(ROOT)), sha256=sha(receipt))
    (AREA / 'results.json').write_text(json.dumps(selector, indent=2, sort_keys=True) + '\n')
    print('PASS_ACTUAL_RUST_RECEIVER_CODEC_BOUNDARY', selector['path'], selector['sha256'])


if __name__ == '__main__':
    main()
