"""Package a successful explicit compile-only candidate; no device operations."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--release', required=True, type=Path)
    args = parser.parse_args()
    candidate, build, release = (p.resolve() for p in (args.candidate, args.build, args.release))
    root = Path('C:/moon').resolve()
    for p in (candidate, build, release):
        if root not in p.parents:
            raise ValueError('All candidate packaging paths must be under C:/moon')
    record = json.loads((build / 'result.json').read_text())
    if record['returncode'] or record['source_changes'] or record['native_changes']:
        raise ValueError('Build failed or source changed during build')
    elf = build / 'moonshine-rev4.elf'
    if hashlib.sha256(elf.read_bytes()).hexdigest() != record['elf_sha256']:
        raise ValueError('Build ELF binding mismatch')
    release.mkdir(parents=True, exist_ok=False)
    evidence = release / 'verification'
    evidence.mkdir()
    shutil.copyfile(elf, release / 'moonshine-rev4.elf')
    shutil.copyfile(build / 'compiled-sdkconfig.h', evidence / 'compiled-sdkconfig.h')
    shutil.copyfile(build / 'result.json', evidence / 'build-result.json')
    user = Path.home()
    py = user / '.espressif/python_env/idf5.4_py3.11_env/Scripts/python.exe'
    rustc = user / '.cargo/bin/rustc.exe'
    size = user / '.espressif/tools/xtensa-esp-elf/esp-14.2.0_20250730/xtensa-esp-elf/bin/xtensa-esp32s3-elf-size.exe'
    binary = release / 'moonshine-rev4.bin'
    uf2 = release / 'moonshine-rev4.uf2'
    commands = [
        ('elf2image', [str(py), '-m', 'esptool', '--chip', 'esp32s3', 'elf2image', '--flash_mode', 'dio', '--flash_freq', '80m', '--flash_size', '8MB', '--output', str(binary), str(release / 'moonshine-rev4.elf')]),
        ('image-info', [str(py), '-m', 'esptool', '--chip', 'esp32s3', 'image_info', str(binary)]),
        ('uf2', [str(py), str(candidate / 'tools/make_gamebub_uf2.py'), str(binary), str(uf2)]),
        ('parser-build', [str(rustc), '+stable', '--edition=2021', str(candidate / 'tools/verify_uf2.rs'), '-o', str(evidence / 'verify-uf2.exe')]),
        ('parser-check', [str(evidence / 'verify-uf2.exe'), str(uf2), str(binary)]),
        ('memory-budget', [str(py), str(candidate / 'tools/check_memory_budget.py'), '--sdkconfig', str(evidence / 'compiled-sdkconfig.h'), '--elf', str(release / 'moonshine-rev4.elf'), '--size-tool', str(size)]),
    ]
    results = []
    for label, command in commands:
        with (evidence / f'{label}.log').open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        results.append({'label': label, 'command': command, 'returncode': result.returncode})
        (evidence / 'commands.json').write_text(json.dumps(results, indent=2) + '\n')
        print(label, result.returncode, flush=True)
        if result.returncode:
            raise SystemExit(1)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in release.iterdir() if p.is_file()}
    (release / 'hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print('PACKAGING_AND_BUILD_GUARD_PASS; hardware runtime checks remain', flush=True)


if __name__ == '__main__':
    main()
