"""Read-only independent artifact audit. Does not build, flash or access hardware."""
from pathlib import Path
import argparse, datetime, hashlib, json

parser = argparse.ArgumentParser()
parser.add_argument('--firmware', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.firmware.resolve()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest_path = root / 'evidence/build-manifest.json'
manifest_hash = sha(manifest_path)
manifest = json.loads(manifest_path.read_text())
assert manifest['status'] == 'PASS_OFFLINE_LOCAL_FIXTURE_GATES_PHYSICAL_NOT_RUN'
assert manifest['network_CU66_capability'] is False
checks = []

def verify(path, expected, category):
    actual = sha(path)
    assert actual == expected, f'{category} hash mismatch: {path}'
    checks.append(dict(path=str(path), sha256=actual, category=category))

for relative, details in manifest['artifacts'].items():
    verify(root / relative, details['sha256'], 'sealed_artifact')
for name, details in manifest['images'].items():
    path = Path(manifest['release_directory']) / name
    assert path.stat().st_size == details['bytes'], path
    verify(path, details['sha256'], 'selected_image')
snapshot = root / 'evidence/source-snapshot-v004.json'
verify(snapshot, manifest['source_snapshot_sha256'], 'source_manifest')
source = json.loads(snapshot.read_text())
for relative, expected in source['files'].items():
    verify(root / relative, expected, 'source')
assert sha(manifest_path) == manifest_hash
result = dict(
    status='PASS_READ_ONLY_SOURCE_AND_IMAGE_HASH_AUDIT_PHYSICAL_NOT_RUN',
    created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    manifest=str(manifest_path), manifest_sha256=manifest_hash,
    checks=len(checks), entries=checks,
    scope='Byte identity only; does not establish code safety, target stack/heap, SPI, timing or physical playback',
    hardware=False, flash=False,
)
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k:v for k,v in result.items() if k != 'entries'}, indent=2))
