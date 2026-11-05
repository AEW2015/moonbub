"""Verify the portable v33 package and its selected source snapshot."""
import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
m=json.loads((p/'manifest.json').read_text()); rows=m['files']; expected={x['path'] for x in rows}
assert len(rows)==len(expected),'duplicate package path'
actual={f.relative_to(p).as_posix() for f in p.rglob('*') if f.is_file() and f!=(p/'manifest.json')}
assert actual==expected,{'missing':sorted(expected-actual),'unbound':sorted(actual-expected)}
for x in rows:
 f=p/x['path']; assert f.stat().st_size==x['bytes'] and sha(f)==x['sha256'],x['path']
s=json.loads((p/'provenance/source-snapshot.json').read_text()); assert len(s['files'])==574
for rel,digest in s['files'].items(): assert (p/rel).is_file() and sha(p/rel)==digest,rel
b=json.loads((p/'provenance/build-manifest.json').read_text()); assert b['source_inputs']==574 and b['source_snapshot_sha256']==sha(p/'provenance/source-snapshot.json')
assert m['candidate_manifest_sha256']==sha(p/'provenance/build-manifest.json')
assert m['source_snapshot_sha256']==sha(p/'provenance/source-snapshot.json')
print('V33_EXPORT_INTEGRITY_PASS',len(rows),'package files; 574 selected source inputs')
