"""Publish exact sealed v36 source and selected metadata, excluding images."""
from pathlib import Path
import hashlib, json, shutil

root = Path(__file__).resolve().parents[2]
source = Path('C:/Users/lavat/codex/moonbub/firmware/experiments/v36-dual-local-fixture-20261106')
out = root / 'firmware/experiments/v36-dual-local-fixture-20261106'
out.mkdir(parents=True, exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((source / 'evidence/build-manifest.json').read_text())
snapshot = json.loads((source / manifest['source_snapshot']).read_text())
names = set(snapshot['files'])
names.update(['README.md', 'host_check.py', 'target_retry.py', 'review_source.py', 'package_release.py',
              'evidence/build-manifest.json', manifest['source_snapshot'],
              'evidence/target-check-v001.json', 'evidence/target-build-v001.json',
              'evidence/host-control-result-v001.json', 'evidence/release-summary.json',
              'evidence/compiled-sdkconfig.h', 'evidence/uf2-validation.log',
              'evidence/selected-frames-v001/result.json'])
names.update(p.relative_to(source).as_posix() for p in (source / 'licenses').rglob('*') if p.is_file())
names.update(p.relative_to(source).as_posix() for p in (source / 'provenance').glob('*.json'))
names.update(p.relative_to(source).as_posix() for p in (source / 'evidence/selected-frames-v001').glob('*.log'))
copied = {}
for name in sorted(names):
    expected = snapshot['files'].get(name)
    if expected is not None:
        assert sha(source / name) == expected
    dest = out / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / name, dest)
    copied[name] = sha(source / name)
    assert sha(dest) == copied[name]
(out / 'SOURCE-BUNDLE.md').write_text('''# V36 exact source bundle

The 551 selected source files match the sealed producer byte for byte. Selected
build, parser, frame and provenance metadata are included. ELF/BIN/UF2, compiled
objects, full local logs and vendor tools are intentionally omitted. Absolute
producer paths and omitted-artifact references in the original build manifest
do not establish those files are present in this checkout. Rebuilding creates
a new image requiring its own hash, packaging and verification.

Explicit USB G selects CU71 (43553731, ABI 00010000, caps 7); Y selects DY71
(44593731, ABI 00010000, caps f). Wrong identities reject before writes.
The historical USB_CU71_LOCAL log prefix is shared; requested_profile and
completed_profile distinguish the selected profile. There is no CU66 network
capability or new port. The installed hardware remains separate.

Target build and packaging, eighteen native-endpoint/model tests and actual
v36/native-to-DY71 CSR KEY/P correctness co-simulation passed offline. That
co-simulation used the earlier PIPE/grouped profile; later SYNCsafe/math and
split-bus integration are separate qualifications. No physical W/G/Y, target
heap/stack high-water, local display, final BIT pairing or 30 fps claim follows.
The new ELF prologue frames are individual measurements, not a full call-stack
proof. See docs/cu66-v71 for current board timing and morning test gates.

Prerequisites: recorded esp193, ESP-IDF 5.4.3, Windows Xtensa C++ tools and
locked Rust dependencies. Original helpers contain producer-specific paths;
inspect them before reuse. Preserve the selected firmware variant.
''', newline='\n')
(out / 'source-bundle.json').write_text(json.dumps(dict(
    status='EXACT_SELECTED_SOURCE_COPY_IMAGES_NOT_INCLUDED', source_files=len(snapshot['files']),
    source_manifest_sha256=sha(source / manifest['source_snapshot']), files=copied,
    original_manifest_sha256=sha(source / 'evidence/build-manifest.json'),
    images_included=False, hardware=False), indent=2) + '\n')
print(json.dumps(dict(output=str(out), source_files=len(snapshot['files']), copied_files=len(copied))))
