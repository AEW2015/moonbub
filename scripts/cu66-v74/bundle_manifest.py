#!/usr/bin/env python3
"""Create/check the V74 artifact bundle's file-integrity manifest."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'docs/cu66-v74/bundle-manifest.json'
DIRS=('docs/cu66-v74','scripts/cu66-v74','fpga/experiments/cu66-v74')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def collect():
    files=[]
    for name in DIRS:
        files.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and p!=DEST and '__pycache__' not in p.parts and p.suffix!='.pyc')
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();cur=collect()
    if a.write:
        DEST.write_text(json.dumps({'schema':'cu66-v74-bundle-v1','scope':'file integrity only; test and cadence verdicts remain separate','baseline_v73':'78d35ddc45fb22732804967748f31042860dbdce','files_sha256':cur},indent=2)+'\n')
        print(f'WROTE_V74_BUNDLE files={len(cur)}');return
    if not DEST.is_file():raise SystemExit('V74_BUNDLE_FAIL manifest missing; run with --write after artifacts are final')
    old=json.loads(DEST.read_text()).get('files_sha256',{})
    missing=sorted(old.keys()-cur.keys());extra=sorted(cur.keys()-old.keys());changed=sorted(k for k in old.keys()&cur.keys() if old[k]!=cur[k])
    if missing or extra or changed:raise SystemExit(json.dumps({'status':'FAIL','missing':missing,'extra':extra,'changed':changed},indent=2))
    print(f'V74_BUNDLE_FILE_INTEGRITY_PASS files={len(cur)}')
if __name__=='__main__':main()
