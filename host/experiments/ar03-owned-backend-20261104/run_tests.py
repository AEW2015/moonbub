"""Host-only bounded buffer tests; no hardware driver or live endpoint."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess, tempfile

HERE = Path(__file__).resolve().parent
HOST = HERE.parent.parent
CORE = HOST / 'ar03-receiver-core-20261104'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log-dir', type=Path, required=True)
    args = ap.parse_args()
    args.log_dir.mkdir(parents=True, exist_ok=True)
    copied = json.loads((CORE / 'source-snapshot.json').read_bytes())
    for rec in copied['files']:
        path = CORE / rec['export_relative_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == rec['sha256'], str(path)
    rustc = shutil.which('rustc') or str(Path.home() / '.cargo/bin/rustc.exe')
    probe = subprocess.run([rustc, '+stable', '--version'], capture_output=True, text=True)
    compiler = [rustc, '+stable'] if probe.returncode == 0 else [rustc]
    version = subprocess.check_output(compiler + ['--version'], text=True).strip()
    outcomes = []
    with tempfile.TemporaryDirectory(prefix='ar03-owned-backend-') as temp:
        temp = Path(temp)
        exe = temp / 'tests.exe'
        command = compiler + ['--edition=2021', '--test', str(HERE / 'tests/backend.rs'), '-o', str(exe)]
        build = subprocess.run(command, capture_output=True, text=True)
        (args.log_dir / 'compile.log').write_text(build.stdout + build.stderr, encoding='utf-8')
        assert build.returncode == 0, build.stderr
        result = subprocess.run([str(exe)], capture_output=True, text=True)
        (args.log_dir / 'tests.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        assert result.returncode == 0 and re.search(r'test result: ok\. 20 passed; 0 failed', result.stdout), result.stdout
        for name, body, diagnostic in [
            ('move', 'let _alias=b;drop(b);', 'E0382'),
            ('clone', 'let _alias=b.clone();', 'E0599'),
            ('borrow', 'let bytes=b.bytes(id,l).unwrap();drop(b);core::hint::black_box(bytes);', 'E0505'),
        ]:
            harness = temp / (name + '.rs')
            module = (CORE / 'handheld/src/streaming/ar03_lab/mod.rs').as_posix()
            backend = (HERE / 'src/backend.rs').as_posix()
            harness.write_text('#![allow(dead_code)]\n'
                f'#[path={json.dumps(module)}] mod ar03_lab;\n'
                f'#[path={json.dumps(backend)}] mod backend;\n'
                'use backend::*; use ar03_lab::packet::*;\n'
                f'fn bad<T:Fifo>(b:OwnedBackend<T>,id:Identity,l:BufferLease){{{body}}}\nfn main(){{}}\n', encoding='utf-8')
            check = subprocess.run(compiler + ['--edition=2021', str(harness), '-o', str(temp / (name + '.exe'))],
                                   capture_output=True, text=True)
            output = check.stdout + check.stderr
            (args.log_dir / (name + '.log')).write_text(output, encoding='utf-8')
            assert check.returncode != 0 and diagnostic in output, output
            outcomes.append({'case': name, 'required_diagnostic': diagnostic, 'rejected': True})
    report = {'status': 'PASS_HOST_ONLY', 'rustc': version, 'host_tests': 20,
              'compile_rejections': outcomes, 'hardware': 'UNEXECUTED',
              'source_sha256': {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (HERE / 'src/backend.rs', HERE / 'tests/backend.rs', Path(__file__))},
              'core_source_snapshot_sha256': hashlib.sha256((CORE / 'source-snapshot.json').read_bytes()).hexdigest(),
              'missing': ['physical FIFO driver', 'SPI/DMA integration', 'production negotiation/recovery', 'live endpoint', 'target runtime memory/stack proof'],
              'outputs': 'temporary binaries removed; logs only'}
    (args.log_dir / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
