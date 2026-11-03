#!/usr/bin/env python3
"""Compare coordinate-tagged RTL RGB565 dump with a Pillow-readable image."""
import argparse,json
from collections import Counter
from pathlib import Path
from PIL import Image, __version__ as pillow_version
p=argparse.ArgumentParser();p.add_argument('reference',type=Path);p.add_argument('dump',type=Path);p.add_argument('--exact',action='store_true');a=p.parse_args()
with Image.open(a.reference) as im:
 image=im.convert('RGB');w,h=image.size;rgb=image.load()
seen=bytearray(w*h); errors=Counter();exact=0;count=0
with a.dump.open() as f:
 for line in f:
  xs,ys,ws=line.split();x,y,word=int(xs),int(ys),int(ws,16)
  if not(0<=x<w and 0<=y<h and 0<=word<=65535) or seen[y*w+x]:raise ValueError('invalid, duplicate or out-of-bounds pixel')
  seen[y*w+x]=1;count+=1;r,g,b=rgb[x,y]
  expected=((r>>3)<<11)|((g>>2)<<5)|(b>>3)
  exact+=word==expected
  for value,ref in zip(((word>>11)&31,(word>>5)&63,word&31),((expected>>11)&31,(expected>>5)&63,expected&31)):
   errors[abs(value-ref)]+=1
if count!=w*h:raise ValueError(f'expected {w*h} pixels, got {count}')
print(json.dumps({'width':w,'height':h,'pixels':count,'pillow_version':pillow_version,'exact_rgb565_pixels':exact,'max_abs_channel_quantized_units':max(errors),'component_error_histogram':dict(sorted(errors.items()))},indent=2))
if a.exact and exact!=count:raise SystemExit('exact mismatch')
