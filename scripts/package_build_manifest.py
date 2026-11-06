"""Package only hash-verified manifest artifacts, preserving workspace-relative paths."""
from pathlib import Path
import argparse,hashlib,json,zipfile
r=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--manifest',required=True);a.add_argument('--output',required=True);args=a.parse_args()
m=Path(args.manifest).resolve();out=Path(args.output).resolve();assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
manifest=json.loads(m.read_text());assert manifest['overall']=='PASS'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seen=set()
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED)as archive:
 for item in manifest['artifacts']:
  p=(r/item['path']).resolve();p.relative_to(r);assert p.is_file()and sha(p)==item['sha256'],p
  if item['path']not in seen:archive.write(p,item['path']);seen.add(item['path'])
 archive.write(m,m.relative_to(r).as_posix())
with zipfile.ZipFile(out)as archive:assert archive.testzip()is None
record=dict(path=str(out.relative_to(r)),sha256=sha(out),manifest_sha256=sha(m),unique_artifacts=len(seen),hardware=False)
out.with_suffix(out.suffix+'.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
