#!/usr/bin/env python3
"""Package-integrity check; functional and cadence verdicts remain separate."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'docs/cu66-v72/bundle-manifest.json'
DIRS=('docs/cu66-v72','scripts/cu66-v72','fpga/experiments/cu66-v72')
def collect():
 files=[]
 for name in DIRS:
  files.extend(p for p in(ROOT/name).rglob('*')if p.is_file()and p!=DEST
               and '__pycache__'not in p.parts and p.suffix!='.pyc')
 return{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(files)}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');a=parser.parse_args()
 current=collect()
 if a.write:
  DEST.write_text(json.dumps(dict(schema='cu66-v72-bundle-v1',scope='fileintegrityonly;notatestorcadenceverdict',
   baseline_v71='207b16d8f0e04a928810a294787609c6e664db71',plan_commit='207b16d8',files_sha256=current),indent=2)+'\n')
  print('WROTE_V72_BUNDLE files='+str(len(current)));return
 previous=json.loads(DEST.read_text())['files_sha256']
 missing=sorted(previous.keys()-current.keys());extra=sorted(current.keys()-previous.keys())
 changed=sorted(p for p in previous.keys()&current.keys()if previous[p]!=current[p])
 if missing or extra or changed:raise SystemExit(json.dumps(dict(status='FAIL',missing=missing,extra=extra,changed=changed),indent=2))
 print('V72_BUNDLE_FILE_INTEGRITY_PASS files='+str(len(current)))
if __name__=='__main__':main()
