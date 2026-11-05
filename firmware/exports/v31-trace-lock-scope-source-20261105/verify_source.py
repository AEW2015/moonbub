"""Verify every packaged file/path, plus every selected active input. Read-only."""
import argparse,hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
a=argparse.ArgumentParser();a.add_argument('--manifest-sha256');args=a.parse_args()
if args.manifest_sha256:assert sha(p/'manifest.json')==args.manifest_sha256
assert not any('local_credentials' in f.name.lower() for f in p.rglob('*') if f.is_file()),'credential file forbidden'
m=json.loads((p/'manifest.json').read_text());rows=m['files'];expected={x['path'] for x in rows}
assert len(rows)==len(expected),'Duplicate path binding'
actual={f.relative_to(p).as_posix() for f in p.rglob('*') if f.is_file() and f!=p/'manifest.json'}
assert actual==expected,{'missing':sorted(expected-actual),'unbound':sorted(actual-expected)}
for x in rows:
 f=p/x['path'];assert f.is_file() and f.stat().st_size==x['bytes'] and sha(f)==x['sha256'],x['path']
b=json.loads((p/'source-bindings.json').read_text());assert b['selected_inputs']==len(b['source_files'])==568
for x in b['source_files']:assert x['path'] in expected and sha(p/x['path'])==x['sha256'],x['path']
assert m['candidate_manifest_sha256']==sha(p/'provenance/build-manifest.json')==b['candidate_manifest_sha256']
print('V31_EXPORT_INTEGRITY_PASS',len(rows),'included files; all568 selected input paths including empty/nested-manifest files')
