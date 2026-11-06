#!/usr/bin/env python3
"""Independent direct-YUV/HUD physical BL8 miss trace; no display RTL claim."""
from collections import OrderedDict
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'fpga/experiments/cu66-v76/service'
RECTS=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))
def address(p,x,y):
 w=720 if p==0 else 360
 return 0x80000+(0,172800,216000)[p]+((y//8)*(w//8)+x//8)*32+(y%8)*4+(x%8)//2
class LRU:
 def __init__(self,n):self.n=n;self.d=OrderedDict()
 def miss(self,a):
  hit=a in self.d
  if hit:self.d.move_to_end(a)
  else:
   if len(self.d)==self.n:self.d.popitem(last=False)
   self.d[a]=1
  return not hit

def main():
 OUT.mkdir(exist_ok=True);cache=LRU(720);hud=LRU(192);trace=[];rows=[];allY=set();allH=set();logicalhud=0
 for s,u0 in enumerate(range(0,720,8)):
  sets=[set(),set(),set()];hs=set();hw=0;patchoff=0
  for u in range(u0,u0+8):
   for v in range(480):
    sets[0].add(address(0,u,v)//8)
    xs=(u//2,min(u//2+1,359))if u%2 else(u//2,)
    ys=(v//2,min(v//2+1,239))if v%2 else(v//2,)
    for x in xs:
     for y in ys:
      sets[1].add(address(1,x,y)//8);sets[2].add(address(2,x,y)//8)
  for x,y,w,h in RECTS:
   for u in range(max(u0,x),min(u0+8,x+w)):
    for v in range(y,y+h):hs.add((0x100000+patchoff+(v-y)*w+u-x)//8);hw+=1
   patchoff+=w*h
  assert patchoff==21120
  ys=[t for p in sets for t in sorted(p)if cache.miss(t)]
  hh=[t for t in sorted(hs)if hud.miss(t)]
  start=len(trace);trace += [(s,t*8)for t in ys+hh];allY.update(ys);allH.update(hh);logicalhud+=hw
  rows.append(dict(strip=s,u0=u0,trace_start=start,trace_count=len(ys)+len(hh),yuv_bursts=len(ys),HUD_bursts=len(hh),HUD_logical_words=hw,wire_bytes=16*(len(ys)+len(hh))))
 assert len(rows)==90 and len(allY)==32400 and len(allH)==2640 and logicalhud==21120
 assert sum(r['yuv_bursts']for r in rows)==32400
 assert sum(r['HUD_bursts']for r in rows)==2640
 header=ROOT/'experiments/cu66-native-v69/generated_constants.hpp';ht=header.read_text();refs=[]
 for plane,n in enumerate((5400,1350,1350)):
  vals=[int(x)for x in re.search(r'SAFE'+str(plane)+r'\['+str(n)+r'\]=\{([^}]+)\}',ht)[1].split(',')if x.strip()]
  assert len(vals)==n
  refs.extend((plane<<17)|i for i,v in enumerate(vals)if not v)
 assert len(refs)==7806
 refmem=OUT/'reference.mem';refmem.write_text(''.join(f'{x:08x}\n'for x in refs))
 mem=OUT/'trace.mem';mem.write_text(''.join(f'{(s<<24)|a:08x}\n'for s,a in trace))
 d=dict(schema='v76-direct-service-trace-v1',scope='Synthetic scheduled cache misses only; exact physical tile/HUD addressing, not RTLcache/renderer/ownership or actual CU66reference trace',YUV_cache_lines=720,HUD_cache_lines=192,cache_line_bytes=16,cache_state='cold at panel start; rolling LRU within panel',issue_order='per strip Y, Cb, Cr, HUD; ascending physical blocks per plane/patchset',rectangles=RECTS,total_bursts=len(trace),YUV_bursts=32400,HUD_bursts=2640,wire_bytes=len(trace)*16,deadline_ps=147403024,rows=rows,source_sha256={'scripts/cu66-v76/generate_service_trace.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),str(header.relative_to(ROOT)):hashlib.sha256(header.read_bytes()).hexdigest()},trace_sha256=hashlib.sha256(mem.read_bytes()).hexdigest(),reference_trace_sha256=hashlib.sha256(refmem.read_bytes()).hexdigest(),reference_count=7806,reference_scope='Ordered static profile nonhidden tileIDs from frozen SAFE maps; not timed livepacket/qmap execution')
 (OUT/'trace.json').write_text(json.dumps(d,indent=2)+'\n');print('SERVICE_TRACE_PASS bursts='+str(len(trace))+' max_strip_bursts='+str(max(r['trace_count']for r in rows)))
if __name__=='__main__':main()
