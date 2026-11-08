#!/usr/bin/env python3
"""Strict P6 oracle reader; exact original RGB565 quantization and coordinates."""
import argparse
from collections import Counter
import json
from pathlib import Path


def compare(reference, dump):
    magic, dimensions, maximum, data = Path(reference).read_bytes().split(b'\n', 3)
    assert magic == b'P6' and maximum == b'255'
    w,h = map(int,dimensions.split())
    assert w > 0 and h > 0 and len(data) == w*h*3
    seen=bytearray(w*h);errors=Counter();exact=0;count=0
    for line in Path(dump).read_text().splitlines():
        xs,ys,ws=line.split();x,y,word=int(xs),int(ys),int(ws,16)
        assert 0<=x<w and 0<=y<h and 0<=word<=65535
        at=y*w+x;assert not seen[at];seen[at]=1;count+=1
        r,g,b=data[3*at:3*at+3]
        expected=((r>>3)<<11)|((g>>2)<<5)|(b>>3)
        exact+=word==expected
        for value,ref in zip(((word>>11)&31,(word>>5)&63,word&31),((expected>>11)&31,(expected>>5)&63,expected&31)):
            errors[abs(value-ref)]+=1
    assert count==w*h and all(seen)
    return dict(width=w,height=h,pixels=count,exact_rgb565_pixels=exact,
                max_abs_channel_quantized_units=max(errors),component_error_histogram=dict(sorted(errors.items())),
                reference_reader='stdlib strict P6; same RGB565 arithmetic as original Pillow comparator')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('reference',type=Path);p.add_argument('dump',type=Path);p.add_argument('--exact',action='store_true');a=p.parse_args()
    result=compare(a.reference,a.dump);print(json.dumps(result,indent=2,sort_keys=True))
    if a.exact and result['exact_rgb565_pixels']!=result['pixels']:raise SystemExit('exact mismatch')


if __name__=='__main__':main()
