#!/usr/bin/env python3
"""Generate deterministic JPEG-only sequence without bulk RGB reference storage."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'host'))
from PIL import __version__ as pillow_version
from make_fixture import pattern
from moonshine.encoding import encode,validate_jpeg

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('output',type=Path)
p.add_argument('--frames',type=int,default=1800)
a=p.parse_args()
if not 1<=a.frames<=1800: p.error('frames must be 1..1800')
if a.output.exists() and any(a.output.iterdir()): p.error('output directory must be empty')
a.output.mkdir(parents=True,exist_ok=True)
rows=[];seen=set()
for i in range(a.frames):
    jpeg=encode(pattern(i),quality=65,subsampling='420');validate_jpeg(jpeg)
    digest=hashlib.sha256(jpeg).hexdigest()
    if digest in seen: raise RuntimeError(f'duplicate JPEG frame {i}')
    seen.add(digest)
    (a.output/f'{i:04d}.jpg').write_bytes(jpeg)
    rows.append({'id':i,'jpeg_bytes':len(jpeg),'jpeg_sha256':digest,'pts_num':i,'pts_den':30})
    if (i+1)%100==0: print(f'GENERATED_JPEG {i+1}/{a.frames}',flush=True)
(a.output/'manifest.json').write_text(json.dumps({'format_version':1,'frames':rows,'pillow_version':pillow_version,
   'source':'synthetic Moonbub pattern, not gameplay','fps':30,'width':720,'height':480,'profile':'Moonbub baseline 4:2:0 fixed Huffman'},indent=2)+'\n')
print(f'GENERATED_JPEG_PASS frames={a.frames}',flush=True)
