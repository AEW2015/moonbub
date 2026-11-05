"""Verify every packaged file and the portable source-binding closure."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest_path=ROOT/"manifest.json"
m=json.loads(manifest_path.read_text(encoding="utf-8"))
expected={row["path"]:row for row in m["artifacts"]}
actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p!=manifest_path}
if actual!=set(expected): raise SystemExit("manifest file set mismatch")
for rel,row in expected.items():
 p=ROOT/rel
 if p.stat().st_size!=row["bytes"] or sha(p)!=row["sha256"]: raise SystemExit(f"manifest hash/size mismatch: {rel}")
parent=ROOT/"provenance/parent-manifest.json"
if sha(parent)!="8d55a9dc17c2f42259e84e11bcd83c8f864bcbda34a54a93cc90ac0070c31d06": raise SystemExit("sealed parent manifest hash mismatch")
bind=json.loads((ROOT/"source-bindings.json").read_text(encoding="utf-8"))
for row in bind["entries"]:
 p=ROOT/row["path"]
 if p.stat().st_size!=row["bytes"] or sha(p)!=row["sha256"]: raise SystemExit(f"source binding mismatch: {row['path']}")
print(f"CP23_ROM_EXPORT_INTEGRITY_PASS files={len(expected)} bytes={sum(x['bytes'] for x in expected.values())} source_bindings={len(bind['entries'])}")
