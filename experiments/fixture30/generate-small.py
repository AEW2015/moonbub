#!/usr/bin/env python3
"""Create ten distinct validated 64x64 JPEGs for RTL component testing."""
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'host'))
from moonshine.encoding import validate_jpeg
out=Path(sys.argv[1])
if out.exists() and any(out.iterdir()): raise SystemExit('output directory must be empty')
out.mkdir(parents=True,exist_ok=True)
rows=[]
for frame in range(10):
    image=Image.new('RGB',(64,64),(8+frame*10,22,110))
    d=ImageDraw.Draw(image);d.rectangle((frame*4,8,frame*4+15,23),fill=(240,180,30))
    d.rectangle((4,40,59,45),fill=(30,frame*22,140))
    b=BytesIO();image.save(b,'JPEG',quality=65,subsampling=2,optimize=False,progressive=False)
    data=b.getvalue();validate_jpeg(data,expected=(64,64))
    (out/f'frame{frame:02d}.jpg').write_bytes(data)
    rows.append({'id':frame,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
if len({r['sha256'] for r in rows}) != 10: raise SystemExit('duplicate JPEGs')
(out/'small-manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
print('SMALL_FIXTURES_PASS 10 distinct 64x64 fixed-Huffman JPEGs')
