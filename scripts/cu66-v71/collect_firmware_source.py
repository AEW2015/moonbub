"""Copy exact selected v35 source to this branch; do not alter sealed producer."""
from pathlib import Path
import argparse, hashlib, json, shutil

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source = args.source.resolve()
out = (root/args.output).resolve()
out.mkdir(parents=True, exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
snapshot_path = source/'evidence/source-snapshot-v004.json'
snapshot = json.loads(snapshot_path.read_text())
copied = {}
for name, expected in snapshot['files'].items():
    path = source/name
    assert sha(path) == expected, name
    target = out/name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    assert sha(target) == expected
    copied[name] = expected
extras = ['README.md', 'review_source.py', 'target_retry.py', 'host_check.py',
          'package_release.py', 'evidence/source-snapshot-v004.json',
          'evidence/build-manifest.json', 'evidence/target-check-v004.json',
          'evidence/target-build-v004.json', 'evidence/host-control-result-v007.json',
          'evidence/sdk-profile-review.json', 'evidence/parent-source-review.json',
          'evidence/compiled-sdkconfig.h']
extras += [p.relative_to(source).as_posix() for p in (source/'licenses').rglob('*') if p.is_file()]
for name in extras:
    path = source/name
    target = out/name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    copied[name] = sha(path)
    assert sha(target) == copied[name]
(out/'SOURCE-BUNDLE.md').write_text('''# Exact v35 source bundle

This directory contains the exact 551 selected source files of the sealed local
v35 release, plus selected review metadata and original build/check helpers.
It preserves the ordinary firmware tree elsewhere in the repository.

The original build manifest is preserved byte for byte. Its absolute producer
paths refer to the original Windows workspace, and it references additional
local logs, earlier attempts and images intentionally omitted from this source
bundle. The manifest does not imply those artifacts are present here. The
selected sealed UF2/ELF/BIN remain in that workspace; a rebuild is a new image
and must be checked and hashed again. No physical installation is established.

Build prerequisites include the recorded esp193 toolchain, ESP-IDF 5.4.3,
Windows Xtensa C++ tools and the locked Rust dependencies. Original helpers
contain historical local target/output paths; inspect them before reuse.
Do not flash a default firmware build in place of this explicitly selected
variant. See the branch CU71 development status and local control ABI.
''', newline='\n')
(out/'source-bundle.json').write_text(json.dumps(dict(
    status='EXACT_SELECTED_SOURCE_COPY_IMAGES_NOT_INCLUDED', source_files=len(snapshot['files']),
    source_manifest_sha256=sha(snapshot_path), files=copied,
    original_manifest_sha256=sha(source/'evidence/build-manifest.json'),
    images_included=False, hardware=False,
), indent=2)+'\n')
assert all(sha(source/name) == expected for name, expected in snapshot['files'].items())
print(json.dumps(dict(output=str(out), source_files=len(snapshot['files']), copied_files=len(copied), hardware=False)))
