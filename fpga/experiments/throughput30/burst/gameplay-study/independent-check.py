#!/usr/bin/env python3
"""Quantify Pillow JPEG decode versus related C model in RGB565 units."""
import argparse, collections, hashlib, json, subprocess, tempfile
from pathlib import Path
from PIL import Image, __version__ as pillow_version
p=argparse.ArgumentParser();p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--cmodel',type=Path,required=True);p.add_argument('--frames',type=int,default=10);a=p.parse_args()
manifest=json.loads((a.fixtures/'manifest.json').read_text()); rows=[]; total=collections.Counter(); exact_total=0
with tempfile.TemporaryDirectory(prefix='gamebub-decoder-check-') as td:
 for e in manifest['frames'][:a.frames]:
  f=a.fixtures/f"{e['id']:04d}.jpg"; digest=hashlib.sha256(f.read_bytes()).hexdigest()
  if digest!=e['jpeg_sha256']:raise ValueError('fixture hash mismatch')
  ppm=Path(td)/'reference.ppm';subprocess.run([str(a.cmodel),str(f),str(ppm)],check=True,stdout=subprocess.DEVNULL)
  with Image.open(f) as im: jpeg=im.convert('RGB').tobytes()
  with Image.open(ppm) as im: c=im.convert('RGB').tobytes()
  if len(jpeg)!=720*480*3 or len(c)!=len(jpeg):raise ValueError('unexpected image size')
  h=collections.Counter();exact=0
  for i in range(0,len(c),3):
   delta=(abs((jpeg[i]>>3)-(c[i]>>3)),abs((jpeg[i+1]>>2)-(c[i+1]>>2)),abs((jpeg[i+2]>>3)-(c[i+2]>>3)))
   h.update(delta);exact+=delta==(0,0,0)
  total.update(h);exact_total+=exact
  rows.append({'id':e['id'],'jpeg_sha256':digest,'exact_rgb565_pixels':exact,'histogram':dict(sorted(h.items()))})
  ppm.unlink()
count=len(rows)*720*480
print(json.dumps({'frames':len(rows),'pillow_version':pillow_version,'pixels':count,'exact_rgb565_pixels':exact_total,'component_error_histogram':dict(sorted(total.items())),'max_abs_quantized_component_error':max(total),'per_frame':rows,'note':'Independent Pillow/libjpeg decode versus related C model. RGB565 units differ between red/blue (5 bit) and green (6 bit). Measures decoder differences, not visual quality or a validated pass threshold.'},indent=2))
