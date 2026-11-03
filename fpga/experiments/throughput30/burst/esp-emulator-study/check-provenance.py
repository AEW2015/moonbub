#!/usr/bin/env python3
"""Check the recorded Windows build inventory against this repository."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[5]
firmware = root / 'firmware'
manifest = json.loads((firmware / 'evidence/build-manifest.json').read_text())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def recorded(path):
    return firmware / Path(path.replace('\\', '/'))
bad = []
for path, digest in manifest['source_inventory'].items():
    file = recorded(path)
    if not file.is_file() or sha(file) != digest:
        bad.append(path)
roles = {'firmware_elf', 'firmware_binary', 'application_uf2'}
artifacts = [a for a in manifest['artifacts'] if a['role'] in roles]
if {a['role'] for a in artifacts} != roles:
    raise SystemExit('manifest missing release artifact roles')
for item in artifacts:
    file = recorded(item['path'])
    if not file.is_file() or sha(file) != item['sha256']:
        bad.append(item['path'])
print(f"source inventory: {len(manifest['source_inventory'])} entries; release artifacts: {len(artifacts)}")
print(f'missing or mismatched: {len(bad)}')
for path in bad: print(path)
sys.exit(bool(bad))
