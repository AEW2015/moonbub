"""Explicit compile-only GameBub candidate build. Never invokes a flash runner."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time


def source_manifest(source):
    excluded = {'target', '.embuild', '__pycache__', '.git', 'managed_components'}
    return {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(source.rglob('*')) if p.is_file()
            and not excluded.intersection(p.relative_to(source).parts)
            and p.name not in {'sdkconfig', 'sdkconfig.old'}}


def main():
    a = argparse.ArgumentParser(__doc__)
    a.add_argument('--source', required=True, type=Path)
    a.add_argument('--target', required=True, type=Path)
    a.add_argument('--output', required=True, type=Path)
    args = a.parse_args()
    root = Path('C:/moon').resolve()
    source, target, output = (p.resolve() for p in (args.source, args.target, args.output))
    for p in (source, target, output):
        if root not in p.parents:
            raise ValueError(f'Candidate source/output must be below C:/moon: {p}')
    if not (source / 'Cargo.lock').is_file():
        raise ValueError('Explicit source must contain locked handheld Cargo project')
    output.mkdir(parents=True, exist_ok=False)
    target.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    user = Path.home()
    prefixes = [user / '.cargo/bin',
                user / '.rustup/toolchains/esp193/xtensa-esp32-elf-clang/esp-clang/bin',
                user / '.espressif/python_env/idf5.4_py3.11_env/Scripts',
                user / '.espressif/tools/cmake/3.30.2/bin',
                user / '.espressif/tools/ninja/1.12.1']
    env['PATH'] = ';'.join(map(str, prefixes)) + ';' + env['PATH']
    env['CARGO_TARGET_DIR'] = str(target)
    env['LIBCLANG_PATH'] = str(prefixes[1] / 'libclang.dll')
    env['IDF_PATH'] = str(user / '.espressif/esp-idf/v5.4.3')
    env['GIT_CEILING_DIRECTORIES'] = str(source.parent)
    env['TEMP'] = env['TMP'] = str(root / 'tmp')
    env.pop('NoDefaultCurrentDirectoryInExePath', None)
    before = source_manifest(source)
    native_source = source.parent / 'native'
    native_before = source_manifest(native_source)
    (output / 'source-before.json').write_text(json.dumps(before, indent=2) + '\n')
    (output / 'native-before.json').write_text(json.dumps(native_before, indent=2) + '\n')
    command = [str(user / '.cargo/bin/cargo.exe'), '+esp193', 'build', '--offline',
               '--locked', '--release', '--features', 'rev4']
    start = time.monotonic()
    with (output / 'build.log').open('w') as log:
        result = subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = source_manifest(source)
    changes = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    native_after = source_manifest(native_source)
    native_changes = sorted(k for k in set(native_before) | set(native_after)
                            if native_before.get(k) != native_after.get(k))
    record = {'command': command, 'source': str(source), 'target': str(target),
              'seconds': time.monotonic() - start, 'returncode': result.returncode,
              'source_changes': changes, 'native_changes': native_changes, 'hardware': False}
    if result.returncode == 0:
        elf = target / 'xtensa-esp32s3-espidf/release/handheld'
        saved = output / 'moonshine-rev4.elf'
        shutil.copyfile(elf, saved)
        record['elf_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
        configs = list(elf.parent.glob('build/esp-idf-sys-*/out/build/config/sdkconfig.h'))
        if len(configs) != 1:
            raise RuntimeError(f'Expected one effective SDK config, found {configs}')
        shutil.copyfile(configs[0], output / 'compiled-sdkconfig.h')
    (output / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)
    if result.returncode or changes or native_changes:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
