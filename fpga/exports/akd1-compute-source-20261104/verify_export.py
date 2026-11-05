"""Portable integrity check; Python standard library only, no old repositories."""
import argparse,hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--manifest-sha256');a=ap.parse_args()
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
if a.manifest_sha256:assert sha(p/'manifest.json')==a.manifest_sha256
m=json.loads((p/'manifest.json').read_text())
for item in m['artifacts']:
 x=p/item['path'];assert x.is_file() and x.stat().st_size and sha(x)==item['sha256'],item['path']
assert len([b for b in json.loads((p/'design-inputs.json').read_text())['files'] if b['path'].endswith('.sv')])==21
assert sha(p/'selected-image/akd1-compute-rev4.1.bit')=='b1ca685e457446838b9d6c78b86f02c4b793dad42eccb3b5c50075d17e20e260'
print('EXPORT_INTEGRITY_PASS',len(m['artifacts']),'artifacts; selectedoriginalBIT unchanged; manifest',sha(p/'manifest.json'))
