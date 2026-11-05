"""Verify included v26 sources only; never requires omitted images/tool caches."""
import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
b=json.loads((p/'source-bindings.json').read_text())
for f in b['source_files']:assert sha(p/f['path'])==f['sha256'],f['path']
assert len(b['source_files'])==575
assert sha(p/'provenance/selected-build-manifest.json')==b['selected_manifest_sha256']
assert sha(p/'provenance/selected-prebuild-snapshot.json')==b['selected_snapshot_sha256']
if (p/'manifest.json').exists():
 for f in json.loads((p/'manifest.json').read_text())['artifacts']:assert sha(p/f['path'])==f['sha256'],f['path']
print('V26_SOURCE_INTEGRITY_PASS575_SELECTED_INPUTS; no target build or hardware')
