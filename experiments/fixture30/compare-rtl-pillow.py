#!/usr/bin/env python3
"""Compare a coordinate-tagged 64x64 RTL RGB565 dump to a Pillow-readable reference."""
import argparse
from collections import Counter
import json
from pathlib import Path
from PIL import Image, __version__ as pillow_version


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('jpeg',type=Path)
    parser.add_argument('dump',type=Path)
    parser.add_argument('--require-exact',action='store_true',help='require bit-exact RGB565 equality')
    args=parser.parse_args()
    with Image.open(args.jpeg) as src:
        image=src.convert('RGB')
        if image.size != (64,64): raise ValueError('expected a 64x64 fixture')
        rgb=list(image.getdata())
    seen=set(); component_errors=Counter(); exact=0; max_error=0
    for line in args.dump.read_text().splitlines():
        x_s,y_s,word_s=line.split(); x,y,word=int(x_s),int(y_s),int(word_s,16)
        if not 0<=x<64 or not 0<=y<64 or (x,y) in seen or not 0<=word<=0xffff:
            raise ValueError('invalid or duplicate pixel')
        seen.add((x,y))
        r,g,b=rgb[y*64+x]
        reference=((r>>3)<<11)|((g>>2)<<5)|(b>>3)
        actual=((word>>11)&31,(word>>5)&63,word&31)
        expected=((reference>>11)&31,(reference>>5)&63,reference&31)
        exact += word==reference
        for v,w in zip(actual,expected):
            e=abs(v-w);component_errors[e]+=1;max_error=max(max_error,e)
    if len(seen)!=4096: raise ValueError(f'missing pixels: got {len(seen)}')
    print(json.dumps({'pixels':4096,'pillow_version':pillow_version,'exact_rgb565_pixels':exact,
                      'different_rgb565_pixels':4096-exact,'max_abs_channel_quantized_units':max_error,
                      'component_error_histogram':dict(sorted(component_errors.items()))},indent=2))
    if args.require_exact and exact != 4096: raise SystemExit('RGB565 reference mismatch')
if __name__=='__main__': main()
