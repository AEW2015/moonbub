#!/usr/bin/env python3
"""Strict comparison for this C model's un-commented 720x480 P6 output."""
import json,sys
with open(sys.argv[1],'rb') as f:
 assert f.readline()==b'P6\n' and f.readline()==b'720 480\n' and f.readline()==b'255\n'
 data=f.read()
assert len(data)==720*480*3
seen=bytearray(720*480); count=0
with open(sys.argv[2]) as f:
 for line in f:
  xs,ys,ws=line.split();x,y,w=int(xs),int(ys),int(ws,16)
  assert 0<=x<720 and 0<=y<480 and 0<=w<=65535
  i=y*720+x; assert not seen[i];seen[i]=1
  r,g,b=data[3*i:3*i+3]; assert w==((r>>3)<<11)|((g>>2)<<5)|(b>>3),(x,y,w,r,g,b)
  count+=1
assert count==720*480
print(json.dumps({'pixels':count,'exact_rgb565_pixels':count}))
