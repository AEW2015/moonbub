"""Verify export manifest and selected source snapshot, read-only."""
import argparse, hashlib, json
from pathlib import Path
p=Path(__file__).resolve().parent
def sha(f): return hashlib.sha256(f.read_bytes()).hexdigest()
a=argparse.ArgumentParser();a.add_argument('--manifest-sha256');args=a.parse_args()
if args.manifest_sha256: assert sha(p/'manifest.json')==args.manifest_sha256
m=json.loads((p/'manifest.json').read_text()); rows=m['files']; expected={x['path'] for x in rows}
assert len(rows)==len(expected), 'duplicate path binding'
actual={f.relative_to(p).as_posix() for f in p.rglob('*') if f.is_file() and f != p/'manifest.json'}
assert actual==expected, {'missing':sorted(expected-actual),'unbound':sorted(actual-expected)}
for x in rows:
 f=p/x['path']; assert f.stat().st_size==x['bytes'] and sha(f)==x['sha256'], x['path']
s=json.loads((p/'provenance/source-snapshot.json').read_text()); assert len(s['files'])==572
for rel,digest in s['files'].items():
 f=p/rel; assert f.is_file() and sha(f)==digest, rel
b=json.loads((p/'provenance/build-manifest.json').read_text()); assert b['source_inputs']==len(s['files']) and b['source_snapshot_sha256']==sha(p/'provenance/source-snapshot.json')
assert m['candidate_manifest_sha256']==sha(p/'provenance/build-manifest.json')
assert not any(x in f.name.lower() for f in p.rglob('*') if f.is_file() for x in ['local_credentials'])
print('V32_EXPORT_INTEGRITY_PASS',len(rows),'package files;',len(s['files']),'selected source inputs')
